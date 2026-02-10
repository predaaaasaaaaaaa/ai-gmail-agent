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

    