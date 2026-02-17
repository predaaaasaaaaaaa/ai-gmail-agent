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
        self.mcp_session = None

        # Per-user context memory
        # {user_id: {"last_emails": [...], "last_read_email": {...}}}
        self.user_context = {}

        logger.info("✅ Email Bot initialized")

    def _get_user_context(self, user_id: int) -> dict:
        """Get or create user context."""
        if user_id not in self.user_context:
            self.user_context[user_id] = {
                "last_emails": [],
                "last_read_email": None,
            }
        return self.user_context[user_id]

    def _strip_html(self, text: str) -> str:
        """
        Strip HTML tags from email body.
        Some emails are HTML formatted - we need plain text.
        """
        if not text:
            return text

        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', text)

        # Decode HTML entities (&amp; &lt; etc.)
        clean = html.unescape(clean)

        # Remove excessive whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()

        # Limit length
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

    def _format_email_list(self, emails: list) -> str:
        """Format email list as plain text."""
        if not emails:
            return "You have no emails matching that query."

        num_to_show = min(len(emails), 10)
        text = f"Found {len(emails)} emails. Showing top {num_to_show}:\n\n"

        for i, email in enumerate(emails[:num_to_show], 1):
            from_addr = email.get("from", "Unknown")
            subject = email.get("subject", "No subject")
            # Clean up long from addresses
            if len(from_addr) > 40:
                from_addr = from_addr[:40] + "..."
            text += f"{i}. From: {from_addr}\n"
            text += f"   Subject: {subject}\n\n"

        text += "Say 'read email number 1' to read the first one."
        return text

    def _format_email_content(self, email_data: dict) -> str:
        """Format single email content as plain text."""
        if not email_data:
            return "Could not read email."

        if "error" in email_data:
            return f"Error reading email: {email_data['error']}"

        from_addr = email_data.get('from', 'Unknown')
        subject = email_data.get('subject', 'No subject')
        body = email_data.get('body', 'No content')

        # Strip HTML if present
        body = self._strip_html(body)

        return (
            f"From: {from_addr}\n"
            f"Subject: {subject}\n\n"
            f"{body}"
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_message = (
            "🤖 AI Email Agent - Voice Edition\n\n"
            "Welcome! I help you manage emails with voice.\n\n"
            "HOW TO USE:\n"
            "1. Send a voice message\n"
            "2. I'll transcribe and process it\n"
            "3. I'll respond with text\n\n"
            "EXAMPLE COMMANDS:\n"
            "🎤 'Check my Gmail'\n"
            "🎤 'Read email number 1'\n"
            "🎤 'Draft a reply'\n"
            "🎤 'Send reply'\n\n"
            "Type /help for more commands."
        )
        await update.message.reply_text(welcome_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_message = (
            "📖 VOICE COMMANDS HELP\n\n"
            "READING:\n"
            "🎤 'Check my Gmail'\n"
            "🎤 'Check my iCloud'\n"
            "🎤 'Read email number 1'\n\n"
            "SEARCHING:\n"
            "🎤 'Find emails from John'\n"
            "🎤 'Search for emails about meetings'\n"
            "🎤 'Show unread emails'\n\n"
            "REPLYING (after reading an email):\n"
            "🎤 'Draft a reply'\n"
            "🎤 'Send reply'\n"
            "🎤 'Reply saying I will attend'\n\n"
            "SENDING:\n"
            "🎤 'Send email to john@example.com saying hello'\n"
        )
        await update.message.reply_text(help_message)

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

    async def process_email_command(self, command: str, user_id: int = None):
        """
        Process email command through MCP agent.
        
        Returns:
            Tuple of (response_text, email_list or None)
        """
        try:
            logger.info(f"🧠 Processing: {command}")
            ctx = self._get_user_context(user_id)

            # ─────────────────────────────────────────
            # HANDLE "read email number X" locally
            # ─────────────────────────────────────────
            read_match = re.search(r"read\s+(?:email\s+)?(?:number\s+)?(\d+)", command.lower())
            email_number = None

            if read_match:
                email_number = int(read_match.group(1))
            else:
                word_match = re.search(r"read\s+(?:email\s+)?(?:number\s+)?(\w+)", command.lower())
                if word_match:
                    email_number = self._word_to_number(word_match.group(1))

            if email_number and ctx["last_emails"]:
                email_index = email_number - 1
                if 0 <= email_index < len(ctx["last_emails"]):
                    target_email = ctx["last_emails"][email_index]
                    email_id = target_email["id"]

                    logger.info(f"📖 Reading email {email_number}: {email_id}")

                    read_tool = "read_icloud_email" if email_id.isdigit() else "read_gmail_email"
                    result = await self.mcp_client.call_tool(read_tool, email_id=email_id)

                    # Store as last read email for context
                    if isinstance(result, dict) and "error" not in result:
                        ctx["last_read_email"] = result
                        ctx["last_read_email"]["id"] = email_id
                        ctx["last_read_email"]["account"] = "icloud" if email_id.isdigit() else "gmail"
                        logger.info(f"💾 Stored last read email: {result.get('subject', 'Unknown')}")

                    formatted = self._format_email_content(result)
                    return formatted, None
                else:
                    return f"Sorry, you only have {len(ctx['last_emails'])} emails in the list.", None

            # ─────────────────────────────────────────
            # HANDLE "draft reply" / "send reply" locally
            # ─────────────────────────────────────────
            command_lower = command.lower()

            # Check if user wants to draft/send reply to last read email
            is_draft = any(word in command_lower for word in ['draft', 'reply', 'respond', 'write back'])
            is_send_reply = any(word in command_lower for word in ['send reply', 'send it', 'yes send'])

            if is_draft and ctx["last_read_email"]:
                last_email = ctx["last_read_email"]
                from_addr = last_email.get("from", "")
                subject = last_email.get("subject", "")
                body = last_email.get("body", "")

                # Extract reply content from command if provided
                # e.g. "draft a reply saying I will attend"
                reply_content_match = re.search(r'(?:saying|that|with|message)\s+(.+)', command_lower)
                if reply_content_match:
                    reply_hint = reply_content_match.group(1)
                else:
                    reply_hint = ""

                # Parse email address from "From" field
                email_match = re.search(r'<(.+?)>', from_addr)
                recipient = email_match.group(1) if email_match else from_addr.strip()

                # Reply subject
                reply_subject = subject if subject.lower().startswith('re:') else f"Re: {subject}"

                # Generate reply body using Groq
                reply_body = await self._generate_reply_body(
                    original_from=from_addr,
                    original_subject=subject,
                    original_body=self._strip_html(body),
                    reply_hint=reply_hint
                )

                # Store pending draft in context
                ctx["pending_draft"] = {
                    "to": recipient,
                    "subject": reply_subject,
                    "body": reply_body,
                    "account": last_email.get("account", "gmail")
                }

                response = (
                    f"📧 DRAFT REPLY:\n\n"
                    f"To: {recipient}\n"
                    f"Subject: {reply_subject}\n\n"
                    f"{reply_body}\n\n"
                    f"Say 'send reply' to send or 'cancel' to cancel."
                )
                return response, None

            # Check if user wants to send the pending draft
            if is_send_reply and ctx.get("pending_draft"):
                draft = ctx["pending_draft"]
                account = draft.get("account", "gmail")
                send_tool = "send_icloud_email" if account == "icloud" else "send_gmail_email"

                result = await self.mcp_client.call_tool(
                    send_tool,
                    to=draft["to"],
                    subject=draft["subject"],
                    body=draft["body"]
                )

                # Clear pending draft
                ctx["pending_draft"] = None

                if isinstance(result, dict) and "error" in result:
                    return f"Failed to send: {result['error']}", None
                return f"✅ Reply sent to {draft['to']}!", None

            # Cancel pending draft
            if 'cancel' in command_lower and ctx.get("pending_draft"):
                ctx["pending_draft"] = None
                return "❌ Draft cancelled.", None

            # ─────────────────────────────────────────
            # NORMAL GROQ PROCESSING
            # ─────────────────────────────────────────
            tools_desc = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.mcp_client.available_tools
            ])

            # Include context in system prompt
            context_info = ""
            if ctx["last_read_email"]:
                context_info = f"""
CURRENT CONTEXT:
- Last read email from: {ctx['last_read_email'].get('from', 'Unknown')}
- Last read email subject: {ctx['last_read_email'].get('subject', 'Unknown')}
- Account: {ctx['last_read_email'].get('account', 'gmail')}
"""

            system_prompt = f"""You are an email assistant with access to these MCP tools:

{tools_desc}

{context_info}

IMPORTANT INSTRUCTIONS:
1. When user says "read email X" where X is a number - respond with action "respond" only (handled by system).
2. When user says "draft reply" or "send reply" - respond with action "respond" only (handled by system).
3. When user says "check gmail" - use list_gmail_emails with query "category:primary".
4. When user says "check icloud" - use list_icloud_emails.
5. When user wants to send to a NAME (not email address) - use search_gmail to find their email first.
6. Always respond with valid JSON only.

Respond with:
{{
    "action": "call_tool" or "respond",
    "tool": "tool_name",
    "params": {{}},
    "message": "message to user"
}}

Examples:
User: "check my gmail"
{{"action": "call_tool", "tool": "list_gmail_emails", "params": {{"max_results": 10, "query": "category:primary"}}, "message": "Fetching Gmail..."}}

User: "check my icloud"
{{"action": "call_tool", "tool": "list_icloud_emails", "params": {{"max_results": 10}}, "message": "Fetching iCloud..."}}

User: "find emails from Nike"
{{"action": "call_tool", "tool": "search_gmail", "params": {{"query": "from:Nike", "max_results": 5}}, "message": "Searching for Nike emails..."}}

User: "read email 1" or "draft reply" or "send reply"
{{"action": "respond", "message": "Handling that for you..."}}

User: "send email to john@example.com saying hello"
{{"action": "call_tool", "tool": "send_gmail_email", "params": {{"to": "john@example.com", "subject": "Hello", "body": "hello"}}, "message": "Sending email..."}}

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
            logger.info(f"🤖 Groq response: {assistant_response}")

            try:
                decision = json.loads(assistant_response)

                if decision.get("action") == "call_tool":
                    logger.info(f"🔧 Calling tool: {decision['tool']}")

                    tool_result = await self.mcp_client.call_tool(
                        decision["tool"], **decision.get("params", {})
                    )

                    # Store email list in context
                    if isinstance(tool_result, list) and len(tool_result) > 0:
                        ctx["last_emails"] = tool_result
                        return self._format_email_list(tool_result), tool_result

                    # Handle single email result
                    if isinstance(tool_result, dict):
                        if "error" in tool_result:
                            return f"Error: {tool_result['error']}", None
                        if tool_result.get("status") == "sent":
                            return "✅ Email sent successfully!", None
                        if tool_result.get("status") == "draft_created":
                            ctx["pending_draft"] = {
                                "to": tool_result["to"],
                                "subject": tool_result["subject"],
                                "body": tool_result["body"],
                                "account": "gmail"
                            }
                            return (
                                f"📧 DRAFT REPLY:\n\n"
                                f"To: {tool_result['to']}\n"
                                f"Subject: {tool_result['subject']}\n\n"
                                f"{tool_result['body']}\n\n"
                                f"Say 'send reply' to send or 'cancel' to cancel."
                            ), None

                        return str(tool_result), None

                    return str(tool_result), None

                else:
                    return decision.get("message", assistant_response), None

            except json.JSONDecodeError:
                return assistant_response, None

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return "Sorry, something went wrong. Please try again.", None

    async def _generate_reply_body(
        self,
        original_from: str,
        original_subject: str,
        original_body: str,
        reply_hint: str = ""
    ) -> str:
        """
        Generate a professional reply body using Groq.
        
        Args:
            original_from: Sender of original email
            original_subject: Subject of original email
            original_body: Body of original email
            reply_hint: User's hint about what to say
        
        Returns:
            Generated reply body text
        """
        prompt = f"""Write a professional email reply.

Original email:
From: {original_from}
Subject: {original_subject}
Body: {original_body[:500]}

User wants to reply{f' saying: {reply_hint}' if reply_hint else ''}.

Write ONLY the email body text. No subject line, no "To:", just the body.
Keep it professional, concise, and friendly.
Sign off with just "Best regards" on a new line."""

        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

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

            # Update email list in context if returned
            if email_list:
                ctx = self._get_user_context(user_id)
                ctx["last_emails"] = email_list

            # Send response as plain text (NO parse_mode to avoid Markdown issues)
            await update.message.reply_text(f"🤖 Response:\n\n{response_text}")

            await processing_msg.delete()

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await processing_msg.edit_text("❌ Something went wrong. Please try again.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        await update.message.reply_text(
            "💬 Text received!\n\n"
            "I work best with voice messages 🎤\n"
            "Try sending a voice message instead."
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
            logger.info(f"✅ MCP connected - {len(self.mcp_client.available_tools)} tools available")
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