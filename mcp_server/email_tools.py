import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

# Gmail API scopes - permissions needed
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


class GmailHandler:
    def __init__(self, credentials_path="credentials.json"):
        self.credentials_path = credentials_path
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """
        Handles OAuth 2.0 authentication with Gmail.
        """
        creds = None

        # Check for saved credentials
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                creds.refresh(Request())
            else:
                # Do full OAuth flow (opens browser)
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials for next time
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        # Build the Gmail service
        self.service = build("gmail", "v1", credentials=creds)

    def list_emails(self, max_results=10, query=""):
        """
        Fetch a list of emails from inbox.
        """
        try:
            # Get list of message IDs
            results = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    maxResults=max_results,
                    q=query,  # Gmail search syntax
                )
                .execute()
            )

            messages = results.get("messages", [])

            if not messages:
                return []

            # Fetch details for each message
            email_list = []
            for message in messages:
                msg = (
                    self.service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message["id"],
                        format="metadata",  # Only get headers, not full body
                        metadataHeaders=["From", "Subject", "Date"],
                    )
                    .execute()
                )

                # Extract headers
                headers = msg["payload"]["headers"]
                email_data = {
                    "id": msg["id"],
                    "snippet": msg.get("snippet", ""),  # Preview text
                    "from": next(
                        (h["value"] for h in headers if h["name"] == "From"), "Unknown"
                    ),
                    "subject": next(
                        (h["value"] for h in headers if h["name"] == "Subject"),
                        "No Subject",
                    ),
                    "date": next(
                        (h["value"] for h in headers if h["name"] == "Date"), "Unknown"
                    ),
                }
                email_list.append(email_data)

            return email_list

        except Exception as e:
            return {"error": str(e)}
    
    def search_emails(self, query: str, max_results=20):
        """
        Search Gmail with advanced query syntax.
        
        Examples of queries:
        - "from:john@example.com" - emails from John
        - "subject:meeting" - emails with "meeting" in subject
        - "after:2024/01/01 before:2024/12/31" - date range
        - "is:unread" - only unread emails
        - "has:attachment" - emails with attachments
        - "from:john subject:project is:unread" - combine filters
        """
        # This just calls list_emails with the query
        return self.list_emails(max_results=max_results, query=query)

    def read_email(self, email_id):
        """
        Get the full content of a specific email.
        """
        try:
            msg = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=email_id,
                    format="full",  # Get full email including body
                )
                .execute()
            )

            # Extract headers
            headers = msg["payload"]["headers"]
            subject = next(
                (h["value"] for h in headers if h["name"] == "Subject"), "No Subject"
            )
            from_email = next(
                (h["value"] for h in headers if h["name"] == "From"), "Unknown"
            )
            date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")

            # Extract body (this is the tricky part)
            body = self._get_email_body(msg["payload"])

            return {
                "id": email_id,
                "subject": subject,
                "from": from_email,
                "date": date,
                "body": body,
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_email_body(self, payload):
        """
        Helper function to extract email body from Gmail's nested structure.
        """
        body = ""

        # Check if email has parts (multipart)
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    # Plain text found - decode it
                    if "data" in part["body"]:
                        body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                            "utf-8"
                        )
                        break
        else:
            # Simple email - body is directly in payload
            if "body" in payload and "data" in payload["body"]:
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        return body

    def send_email(self, to, subject, body):
        """
        Send an email from your Gmail account.
        """
        try:
            # Create the email
            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject

            # Encode in base64
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            # Send it
            send_result = (
                self.service.users()
                .messages()
                .send(userId="me", body={"raw": raw_message})
                .execute()
            )

            return {"status": "sent", "message_id": send_result["id"]}

        except Exception as e:
            return {"error": str(e)}


import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class iCloudHandler:
    def __init__(self):
        """
        iCloud email handler using IMAP and SMTP.
        """
        self.email = os.getenv("ICLOUD_EMAIL")
        self.password = os.getenv("ICLOUD_PASSWORD")
        self.imap_server = "imap.mail.me.com"
        self.smtp_server = "smtp.mail.me.com"
        self.imap_port = 993
        self.smtp_port = 587

    def list_emails(self, max_results=10, mailbox='INBOX'):
        """
        Fetch emails from iCloud using IMAP.
        
        Args:
            max_results: Number of emails to fetch
            mailbox: Which folder to read from (INBOX, Sent, Drafts, etc.)
        
        Returns:
            List of email metadata
        """
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email, self.password)
            
            # Select mailbox
            mail.select(mailbox)
            
            # Search for all emails
            status, messages = mail.search(None, 'ALL')
            
            # Get list of email IDs
            email_ids = messages[0].split()
            
            # Get the most recent emails (IMAP returns oldest first, so reverse)
            email_ids = email_ids[-max_results:][::-1]
            
            email_list = []
            
            for email_id in email_ids:
                # Fetch email headers only (faster than fetching full body)
                status, msg_data = mail.fetch(email_id, '(RFC822.HEADER)')
                
                # Parse the email
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Decode subject (might be encoded)
                subject = self._decode_header(msg.get('Subject', 'No Subject'))
                from_email = msg.get('From', 'Unknown')
                date = msg.get('Date', 'Unknown')
                
                # CRITICAL FIX: email_id from IMAP is bytes, convert to string
                # DO NOT call .decode() directly - check type first!
                if isinstance(email_id, bytes):
                    email_id_str = email_id.decode()
                elif isinstance(email_id, int):
                    email_id_str = str(email_id)
                else:
                    email_id_str = str(email_id)  # Fallback
                
                email_list.append({
                    'id': email_id_str,  # ← Now always a string, no .decode()
                    'subject': subject,
                    'from': from_email,
                    'date': date,
                    'snippet': f"iCloud email from {from_email}"
                })
            
            mail.close()
            mail.logout()
            
            return email_list
            
        except Exception as e:
            return {'error': str(e)}

        except Exception as e:
            return {"error": str(e)}

    def _decode_header(self, header):
        """
        Decode email headers that might be encoded.
        """
        if header is None:
            return ""

        decoded_parts = decode_header(header)
        decoded_header = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_header += part.decode(encoding or "utf-8")
            else:
                decoded_header += part

        return decoded_header

    def read_email(self, email_id):
        """
        Get full email content from iCloud.
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email, self.password)
            mail.select("INBOX")

            # FIX: Ensure email_id is bytes for IMAP
            # Handle both string and int inputs
            if isinstance(email_id, str):
                email_id_bytes = email_id.encode()
            elif isinstance(email_id, int):
                email_id_bytes = str(email_id).encode()
            else:
                email_id_bytes = email_id  # Already bytes

            # Fetch the full email
            status, msg_data = mail.fetch(email_id_bytes, "(RFC822)")

            # Parse email
            msg = email.message_from_bytes(msg_data[0][1])

            subject = self._decode_header(msg.get("Subject", "No Subject"))
            from_email = msg.get("From", "Unknown")
            date = msg.get("Date", "Unknown")

            # Extract body
            body = self._get_email_body(msg)

            mail.close()
            mail.logout()

            return {
                "id": str(email_id),    # Return as Stringg
                "subject": subject,
                "from": from_email,
                "date": date,
                "body": body,
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_email_body(self, msg):
        """
        Extract plain text body from email message.
        """
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
        else:
            # Simple email
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                body = msg.get_payload()

        return body

    def send_email(self, to, subject, body):
        """
        Send email via iCloud SMTP.
        """
        try:
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable encryption
            server.login(self.email, self.password)

            # Send email
            server.send_message(msg)
            server.quit()

            return {"status": "sent", "to": to}

        except Exception as e:
            return {"error": str(e)}
    
    def search_emails_by_sender(self, sender: str, max_results=20):
        """
        Search iCloud emails by sender.
        
        Note: iCloud IMAP has very limited search capabilities compared to Gmail.
        This searches for emails where the 'From' field contains the sender string.
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email, self.password)
            mail.select('INBOX')
            
            search_criteria = f'(FROM "{sender}")'
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                mail.close()
                mail.logout()
                return {'error': 'Search failed'}
            
            # Get email IDs
            email_ids = messages[0].split()
            
            if not email_ids:
                mail.close()
                mail.logout()
                return []
            
            # Get most recent matches
            email_ids = email_ids[-max_results:][::-1]
            
            email_list = []
            
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822.HEADER)')
                
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = self._decode_header(msg.get('Subject', 'No Subject'))
                from_email = msg.get('From', 'Unknown')
                date = msg.get('Date', 'Unknown')
                
                # Convert email_id properly
                if isinstance(email_id, bytes):
                    email_id_str = email_id.decode()
                elif isinstance(email_id, int):
                    email_id_str = str(email_id)
                else:
                    email_id_str = str(email_id)
                
                email_list.append({
                    'id': email_id_str,
                    'subject': subject,
                    'from': from_email,
                    'date': date,
                    'snippet': f"iCloud email from {from_email}"
                })
            
            mail.close()
            mail.logout()
            
            return email_list
            
        except Exception as e:
            return {'error': str(e)}
