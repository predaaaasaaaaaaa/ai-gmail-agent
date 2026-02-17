"""
Telegram Voice Bot for AI Email Agent

This bot:
1. Receives voice messages from users
2. Transcribes them using Groq Whisper
3. Processes commands through MCP email agent
4. Responds with text
"""
import os
import logging
import tempfile
import sys
import re
import json
import html
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent))
from agent.mcp_client import MCPEmailClient

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class EmailBot:

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")

        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in .env")

        self.groq_client = Groq(api_key=self.groq_api_key)
        self.mcp_client = None

        # Per-user context memory
        # {
        #   user_id: {
        #     "email_list": [...],           # Last fetched list
        #     "read_emails": {               # All emails read this session
        #       "1": {email_data},           # Key = number from list
        #       "2": {email_data},
        #     },
        #     "pending_draft": None,         # Draft waiting to be sent
        #     "last_action_email_num": None, # Last email number user interacted with
        #   }
        # }
        self.user_context = {}

        logger.info("✅ Email Bot initialized")

    def _get_ctx(self, user_id: int) -> dict:
        """Get or create user context."""
        if user_id not in self.user_context:
            self.user_context[user_id] = {
                "email_list": [],
                "read_emails": {},
                "pending_draft": None,
                "last_action_email_num": None,
            }
        return self.user_context[user_id]

    def _strip_html(self, text: str) -> str:
        """Strip HTML tags from email body."""
        if not text:
            return text
        clean = re.sub(r'<[^>]+>', ' ', text)
        clean = html.unescape(clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:800]

    def _word_to_number(self, word: str) -> int:
        """Convert word numbers to integers."""
        word_to_num = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
            'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
            'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10
        }
        return word_to_num.get(word.lower())

    def _extract_email_number(self, command: str) -> int:
        """
        Extract email number from command.
        """
        command_lower = command.lower()

        # Try digit first: "email 1", "email number 1", "number 1"
        digit_match = re.search(
            r'(?:email\s+)?(?:number\s+)?(\d+)',
            command_lower
        )
        if digit_match:
            return int(digit_match.group(1))

        # Try word: "email one", "email number two"
        word_match = re.search(
            r'(?:email\s+)?(?:number\s+)?(\w+)',
            command_lower
        )
        if word_match:
            return self._word_to_number(word_match.group(1))

        return None

    def _format_email_list(self, emails: list) -> str:
        """Format email list as plain text."""
        if not emails:
            return "You have no emails matching that query."

        num_to_show = min(len(emails), 10)
        text = f"Found {len(emails)} emails. Showing top {num_to_show}:\n\n"

        for i, email in enumerate(emails[:num_to_show], 1):
            from_addr = email.get("from", "Unknown")
            subject = email.get("subject", "No subject")
            if len(from_addr) > 40:
                from_addr = from_addr[:40] + "..."
            text += f"{i}. From: {from_addr}\n"
            text += f"   Subject: {subject}\n\n"

        text += "Say 'read email number 1' to read any email."
        return text

    def _format_email_content(self, email_data: dict) -> str:
        """Format single email content as plain text."""
        if not email_data or "error" in email_data:
            return f"Error reading email: {email_data.get('error', 'Unknown error')}"

        from_addr = email_data.get('from', 'Unknown')
        subject = email_data.get('subject', 'No subject')
        body = self._strip_html(email_data.get('body', 'No content'))

        return (
            f"From: {from_addr}\n"
            f"Subject: {subject}\n\n"
            f"{body}"
        )

    def _parse_recipient(self, from_header: str) -> str:
        """Extract email address from From header."""
        email_match = re.search(r'<(.+?)>', from_header)
        if email_match:
            return email_match.group(1)
        # Check if it looks like a plain email
        if '@' in from_header:
            return from_header.strip()
        return from_header.strip()

    async def _generate_reply_body(
        self,
        original_from: str,
        original_subject: str,
        original_body: str,
        reply_hint: str = ""
    ) -> str:
        """Generate professional reply body using Groq."""
        prompt = f"""Write a professional email reply.

Original email:
From: {original_from}
Subject: {original_subject}
Body: {original_body[:500]}

{f'User wants to reply saying: {reply_hint}' if reply_hint else 'Write a polite acknowledgment reply.'}

Write ONLY the email body. No subject, no To/From headers.
Keep it professional, concise and friendly.
End with: Best regards"""

        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    async def process_email_command(self, command: str, user_id: int = None):
        """
        Process email command through MCP agent.
        Returns: Tuple of (response_text, email_list or None)
        """
        try:
            logger.info(f"🧠 Processing: {command}")
            ctx = self._get_ctx(user_id)
            command_lower = command.lower()

            # ─────────────────────────────────────────
            # 1. HANDLE "send reply" / "yes send it"
            # ─────────────────────────────────────────
            send_triggers = ['send reply', 'send it', 'yes send', 'send this', 'send the reply', 'send that']
            is_send_reply = any(trigger in command_lower for trigger in send_triggers)

            if is_send_reply and ctx["pending_draft"]:
                draft = ctx["pending_draft"]
                account = draft.get("account", "gmail")
                send_tool = "send_icloud_email" if account == "icloud" else "send_gmail_email"

                logger.info(f"📤 Sending reply via {send_tool} to {draft['to']}")

                result = await self.mcp_client.call_tool(
                    send_tool,
                    to=draft["to"],
                    subject=draft["subject"],
                    body=draft["body"]
                )

                # Clear pending draft after sending
                ctx["pending_draft"] = None

                if isinstance(result, dict) and "error" in result:
                    return f"Failed to send: {result['error']}", None

                return f"✅ Reply sent to {draft['to']}!", None

            # ─────────────────────────────────────────
            # 2. HANDLE "cancel draft"
            # ─────────────────────────────────────────
            if 'cancel' in command_lower and ctx["pending_draft"]:
                ctx["pending_draft"] = None
                return "❌ Draft cancelled.", None

            # ─────────────────────────────────────────
            # 3. HANDLE "read email number X"
            # ─────────────────────────────────────────
            is_read_command = 'read' in command_lower and not any(
                w in command_lower for w in ['draft', 'reply', 'respond', 'send']
            )

            if is_read_command and ctx["email_list"]:
                email_number = self._extract_email_number(
                    re.sub(r'read\s+', '', command_lower, count=1)
                )

                if email_number:
                    email_index = email_number - 1

                    if 0 <= email_index < len(ctx["email_list"]):
                        target = ctx["email_list"][email_index]
                        email_id = target["id"]

                        read_tool = "read_icloud_email" if email_id.isdigit() else "read_gmail_email"
                        account = "icloud" if email_id.isdigit() else "gmail"

                        logger.info(f"📖 Reading email {email_number} ({email_id})")

                        result = await self.mcp_client.call_tool(read_tool, email_id=email_id)

                        if isinstance(result, dict) and "error" not in result:
                            # Store read email with its NUMBER as key
                            result["id"] = email_id
                            result["account"] = account
                            result["list_number"] = email_number
                            ctx["read_emails"][str(email_number)] = result
                            ctx["last_action_email_num"] = str(email_number)
                            logger.info(f"💾 Stored email #{email_number}: {result.get('subject', '?')}")

                        return self._format_email_content(result), None
                    else:
                        return f"Sorry, only {len(ctx['email_list'])} emails in list.", None

            # ─────────────────────────────────────────
            # 4. HANDLE "draft reply for email X" / "draft reply"
            # ─────────────────────────────────────────
            is_draft_command = any(
                w in command_lower for w in ['draft', 'reply to', 'respond to', 'write back', 'write a reply']
            )

            if is_draft_command:
                # Check if user specified which email number to reply to
                email_number = None

                # Try to find "for email X" or "to email X" or "email number X"
                for_match = re.search(
                    r'(?:for|to)\s+(?:email\s+)?(?:number\s+)?(\d+|\w+)',
                    command_lower
                )
                if for_match:
                    num_str = for_match.group(1)
                    if num_str.isdigit():
                        email_number = int(num_str)
                    else:
                        email_number = self._word_to_number(num_str)

                # If no number found, use last interacted email
                if not email_number:
                    last_num = ctx["last_action_email_num"]
                    if last_num:
                        email_number = int(last_num)

                logger.info(f"📝 Draft requested for email #{email_number}")

                # Get the email from context
                target_email = None
                if email_number and str(email_number) in ctx["read_emails"]:
                    target_email = ctx["read_emails"][str(email_number)]
                elif ctx["last_action_email_num"] and ctx["last_action_email_num"] in ctx["read_emails"]:
                    target_email = ctx["read_emails"][ctx["last_action_email_num"]]

                if not target_email:
                    return (
                        "I don't have that email in context.\n"
                        "Please read the email first by saying 'read email number X'.",
                        None
                    )

                from_addr = target_email.get("from", "")
                subject = target_email.get("subject", "")
                body = target_email.get("body", "")
                account = target_email.get("account", "gmail")

                # Extract reply hint from command
                reply_hint_match = re.search(
                    r'(?:saying|that|message|reply\s+with|respond\s+with)\s+(.+)',
                    command_lower
                )
                reply_hint = reply_hint_match.group(1) if reply_hint_match else ""

                recipient = self._parse_recipient(from_addr)
                reply_subject = subject if subject.lower().startswith('re:') else f"Re: {subject}"

                # Generate reply using AI
                reply_body = await self._generate_reply_body(
                    original_from=from_addr,
                    original_subject=subject,
                    original_body=self._strip_html(body),
                    reply_hint=reply_hint
                )

                # Store pending draft with account info
                ctx["pending_draft"] = {
                    "to": recipient,
                    "subject": reply_subject,
                    "body": reply_body,
                    "account": account,
                    "for_email_num": email_number
                }

                logger.info(f"💾 Draft created for email #{email_number} via {account}")

                return (
                    f"📧 DRAFT REPLY (for email #{email_number}):\n\n"
                    f"To: {recipient}\n"
                    f"Subject: {reply_subject}\n\n"
                    f"{reply_body}\n\n"
                    f"Say 'send reply' to send or 'cancel' to cancel."
                ), None

            # ─────────────────────────────────────────
            # 5. NORMAL GROQ PROCESSING
            # ─────────────────────────────────────────
            tools_desc = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.mcp_client.available_tools
            ])

            # Build context summary for Groq
            context_summary = ""
            if ctx["email_list"]:
                context_summary += f"User has {len(ctx['email_list'])} emails loaded in memory.\n"
            if ctx["read_emails"]:
                read_list = [
                    f"Email #{num}: {data.get('subject', '?')} from {data.get('from', '?')}"
                    for num, data in ctx["read_emails"].items()
                ]
                context_summary += "Read emails:\n" + "\n".join(read_list) + "\n"
            if ctx["pending_draft"]:
                context_summary += f"Pending draft to: {ctx['pending_draft']['to']}\n"

            system_prompt = f"""You are an email assistant with access to these MCP tools:

{tools_desc}

CURRENT SESSION CONTEXT:
{context_summary if context_summary else 'No emails loaded yet.'}

IMPORTANT RULES:
1. "read email X", "draft reply", "send reply" are handled by the system - respond with action "respond".
2. "check gmail" -> list_gmail_emails with query "category:primary" max_results 10.
3. "check icloud" -> list_icloud_emails max_results 10.
4. "find emails from NAME" -> search_gmail with from:NAME.
5. To send a NEW email (not a reply) to an email address -> send_gmail_email.
6. Always return valid JSON only.

Response format:
{{
    "action": "call_tool" or "respond",
    "tool": "tool_name",
    "params": {{}},
    "message": "message"
}}

Examples:
User: "check my gmail"
{{"action": "call_tool", "tool": "list_gmail_emails", "params": {{"max_results": 10, "query": "category:primary"}}, "message": "Fetching Gmail..."}}

User: "check icloud"
{{"action": "call_tool", "tool": "list_icloud_emails", "params": {{"max_results": 10}}, "message": "Fetching iCloud..."}}

User: "find emails from Nike"
{{"action": "call_tool", "tool": "search_gmail", "params": {{"query": "from:Nike", "max_results": 5}}, "message": "Searching..."}}

User: "send email to john@example.com saying hello there"
{{"action": "call_tool", "tool": "send_gmail_email", "params": {{"to": "john@example.com", "subject": "Hello", "body": "hello there"}}, "message": "Sending..."}}

User: "read email 1" or "draft reply" or "send reply"
{{"action": "respond", "message": "On it!"}}

Always respond with valid JSON only."""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": command},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            assistant_response = response.choices[0].message.content
            logger.info(f"🤖 Groq: {assistant_response}")

            try:
                decision = json.loads(assistant_response)

                if decision.get("action") == "call_tool":
                    logger.info(f"🔧 Tool: {decision['tool']}")

                    tool_result = await self.mcp_client.call_tool(
                        decision["tool"], **decision.get("params", {})
                    )

                    # Email list result
                    if isinstance(tool_result, list):
                        if len(tool_result) > 0:
                            # Store in context
                            ctx["email_list"] = tool_result
                            # Clear read emails when new list is loaded
                            ctx["read_emails"] = {}
                            ctx["last_action_email_num"] = None
                            ctx["pending_draft"] = None
                            logger.info(f"💾 Stored {len(tool_result)} emails in context")
                            return self._format_email_list(tool_result), tool_result
                        else:
                            return "No emails found.", None

                    # Single result
                    if isinstance(tool_result, dict):
                        if "error" in tool_result:
                            return f"Error: {tool_result['error']}", None
                        if tool_result.get("status") == "sent":
                            return "✅ Email sent successfully!", None
                        return str(tool_result), None

                    return str(tool_result), None

                else:
                    return decision.get("message", "Done!"), None

            except json.JSONDecodeError:
                return assistant_response, None

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return "Sorry, something went wrong. Please try again.", None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 AI Email Agent - Voice Edition\n\n"
            "HOW TO USE:\n"
            "1. Say 'check my Gmail' or 'check my iCloud'\n"
            "2. Say 'read email number 1' to read any email\n"
            "3. Say 'draft a reply' to draft a response\n"
            "4. Say 'send reply' to send the draft\n\n"
            "Type /help for all commands."
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📖 VOICE COMMANDS:\n\n"
            "LISTING:\n"
            "🎤 'Check my Gmail'\n"
            "🎤 'Check my iCloud'\n"
            "🎤 'Show my last 10 emails'\n\n"
            "READING:\n"
            "🎤 'Read email number 1'\n"
            "🎤 'Read email number two'\n\n"
            "DRAFTING:\n"
            "🎤 'Draft a reply' (for last read email)\n"
            "🎤 'Draft a reply for email 2'\n"
            "🎤 'Draft a reply saying I will attend'\n\n"
            "SENDING:\n"
            "🎤 'Send reply'\n"
            "🎤 'Cancel' (to cancel draft)\n\n"
            "SEARCHING:\n"
            "🎤 'Find emails from John'\n"
            "🎤 'Search for emails about meetings'\n"
            "🎤 'Show unread emails'\n"
        )

    async def transcribe_voice(self, voice_file_path: str) -> str:
        """Transcribe voice message using Groq Whisper."""
        try:
            logger.info(f"🎤 Transcribing: {voice_file_path}")
            with open(voice_file_path, "rb") as audio_file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    language="en",
                    response_format="text",
                )
            logger.info(f"✅ Transcription: {transcription}")
            return transcription
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return None

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages from users."""
        user_name = update.effective_user.first_name
        user_id = update.effective_user.id
        logger.info(f"📥 Voice from {user_name}")

        processing_msg = await update.message.reply_text("🎤 Listening...")

        try:
            voice = update.message.voice
            voice_file = await context.bot.get_file(voice.file_id)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
                temp_path = temp_file.name

            await voice_file.download_to_drive(temp_path)
            await processing_msg.edit_text("🔄 Transcribing...")

            transcribed_text = await self.transcribe_voice(temp_path)
            os.unlink(temp_path)

            if not transcribed_text:
                await processing_msg.edit_text("❌ Couldn't transcribe. Try again.")
                return

            logger.info(f"📝 Transcribed: {transcribed_text}")
            await processing_msg.edit_text(f"✅ Heard: {transcribed_text}\n\n⚙️ Processing...")

            response_text, email_list = await self.process_email_command(transcribed_text, user_id)

            # Send as plain text - NO parse_mode
            await update.message.reply_text(f"🤖 Response:\n\n{response_text}")
            await processing_msg.delete()

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await processing_msg.edit_text("❌ Something went wrong. Try again.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        await update.message.reply_text(
            "I work best with voice messages 🎤\n"
            "Try sending a voice message!"
        )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        logger.error(f"❌ Error: {context.error}")
        if update and update.message:
            await update.message.reply_text("❌ Something went wrong. Please try again.")

    async def connect_mcp_async(self):
        """Connect to MCP server asynchronously."""
        try:
            logger.info("🔌 Connecting to MCP server...")
            self.mcp_client = MCPEmailClient()
            self.mcp_client = await self.mcp_client.__aenter__()
            logger.info(f"✅ MCP connected - {len(self.mcp_client.available_tools)} tools")
        except Exception as e:
            logger.error(f"❌ MCP connection failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def post_init(self, application):
        """Called after application is initialized."""
        await self.connect_mcp_async()

    def run(self):
        """Start the bot."""
        logger.info("🚀 Starting Telegram bot...")

        app = Application.builder().token(self.token).post_init(self.post_init).build()

        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        app.add_error_handler(self.error_handler)

        logger.info("✅ Bot ready!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    bot = EmailBot()
    bot.run()


if __name__ == "__main__":
    main()