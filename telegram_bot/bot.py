"""
Telegram Voice Bot for AI Email Agent - V4 (Text + Voice Responses)

This bot:
1. Receives voice messages from users
2. Transcribes them using Groq Whisper
3. Processes commands through MCP email agent
4. Responds with TEXT + VOICE (both)
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

    def _normalize_command(self, command: str) -> str:
        """
        Normalize transcription quirks.
        Converts spoken numbers to digits for reliable processing.
        e.g. "read email number two" -> "read email number 2"
        """
        number_words = {
            r'\bone\b': '1', r'\btwo\b': '2', r'\bthree\b': '3',
            r'\bfour\b': '4', r'\bfive\b': '5', r'\bsix\b': '6',
            r'\bseven\b': '7', r'\beight\b': '8', r'\bnine\b': '9',
            r'\bten\b': '10', r'\bfirst\b': '1', r'\bsecond\b': '2',
            r'\bthird\b': '3', r'\bfourth\b': '4', r'\bfifth\b': '5',
            r'\bsixth\b': '6', r'\bseventh\b': '7', r'\beighth\b': '8',
            r'\bninth\b': '9', r'\btenth\b': '10',
            # Common Whisper mishearings
            r'\bto\b': '2', r'\btoo\b': '2', r'\btu\b': '2',
            r'\bfor\b': '4', r'\bate\b': '8',
        }

        result = command.lower()
        for pattern, replacement in number_words.items():
            result = re.sub(pattern, replacement, result)

        if result != command.lower():
            logger.info(f"🔄 Normalized: '{command}' -> '{result}'")

        return result

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

    def _parse_recipient(self, from_header: str) -> str:
        """Extract email address from From header."""
        email_match = re.search(r'<(.+?)>', from_header)
        if email_match:
            return email_match.group(1)
        if '@' in from_header:
            return from_header.strip()
        return from_header.strip()

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

        if len(emails) == 1:
            text += "Say 'read it' or 'read this email' to read it."
        else:
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

    async def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech using Groq TTS (Orpheus).
        """
        try:
            # Limit text length for reasonable voice messages (max ~1000 chars)
            short_text = text[:1000]
            
            logger.info(f"🔊 Generating TTS for {len(short_text)} chars")
            
            # Generate speech using Groq Orpheus TTS
            response = self.groq_client.audio.speech.create(
                model="canopylabs/orpheus-v1-english",
                voice="diana",  # Feminine friendly voice
                input=short_text,
                response_format="wav"
            )
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(response.content)
                audio_path = f.name
            
            logger.info(f"✅ TTS generated: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def process_email_command(self, command: str, user_id: int = None):
        """
        Process email command through MCP agent.
        Returns: Tuple of (response_text, email_list or None)
        """
        try:
            logger.info(f"🧠 Processing: {command}")
            ctx = self._get_ctx(user_id)

            # Normalize BEFORE anything else
            command = self._normalize_command(command)
            command_lower = command.lower().strip()

            # ─────────────────────────────────────────
            # 1. SEND REPLY - highest priority
            # ─────────────────────────────────────────
            send_triggers = [
                'send reply', 'send it', 'yes send', 'send this',
                'send the reply', 'send that', 'yes', 'confirm',
                'go ahead', 'send now'
            ]
            is_send = any(trigger in command_lower for trigger in send_triggers)

            if is_send:
                if ctx["pending_draft"]:
                    draft = ctx["pending_draft"]
                    account = draft.get("account", "gmail")
                    send_tool = "send_icloud_email" if account == "icloud" else "send_gmail_email"

                    logger.info(f"📤 Sending to {draft['to']} via {send_tool}")

                    result = await self.mcp_client.call_tool(
                        send_tool,
                        to=draft["to"],
                        subject=draft["subject"],
                        body=draft["body"]
                    )

                    ctx["pending_draft"] = None

                    if isinstance(result, dict) and "error" in result:
                        return f"Failed to send: {result['error']}", None

                    return f"✅ Reply sent to {draft['to']}!", None
                else:
                    return "No pending draft to send. Say 'draft a reply' first.", None

            # ─────────────────────────────────────────
            # 2. CANCEL DRAFT
            # ─────────────────────────────────────────
            if 'cancel' in command_lower:
                if ctx["pending_draft"]:
                    ctx["pending_draft"] = None
                    return "❌ Draft cancelled.", None

            # ─────────────────────────────────────────
            # 3. READ EMAIL NUMBER X
            # ─────────────────────────────────────────
            is_read = (
                'read' in command_lower and
                not any(w in command_lower for w in ['draft', 'reply', 'respond', 'send'])
            )

            if is_read and ctx["email_list"]:

                # Single email auto-read triggers
                single_read_triggers = [
                    'read it', 'read this', 'open it', 'open this',
                    'read the email', 'read that', 'read the mail'
                ]
                is_single_trigger = any(t in command_lower for t in single_read_triggers)

                # Auto-read if only 1 email AND user says "read it" OR no number given
                if len(ctx["email_list"]) == 1 and (
                    is_single_trigger or not re.search(r'\b(\d+)\b', command_lower)
                ):
                    target = ctx["email_list"][0]
                    email_id = target["id"]
                    account = "icloud" if email_id.isdigit() else "gmail"
                    read_tool = "read_icloud_email" if account == "icloud" else "read_gmail_email"

                    logger.info(f"📖 Auto-reading single email: {email_id}")

                    result = await self.mcp_client.call_tool(read_tool, email_id=email_id)

                    if isinstance(result, dict) and "error" not in result:
                        result["id"] = email_id
                        result["account"] = account
                        result["list_number"] = 1
                        ctx["read_emails"]["1"] = result
                        ctx["last_action_email_num"] = "1"
                        logger.info(f"💾 Auto-stored: {result.get('subject')}")

                    return self._format_email_content(result), None

                # Multiple emails - need number
                email_number = None

                # Try digit first
                digit_match = re.search(r'\b(\d+)\b', command_lower)
                if digit_match:
                    email_number = int(digit_match.group(1))
                else:
                    # Try word numbers - skip non-number words
                    skip_words = {
                        'read', 'email', 'number', 'the', 'me', 'please',
                        'open', 'show', 'get', 'fetch', 'load', 'mail', 'a', 'an'
                    }
                    for word in command_lower.split():
                        if word in skip_words:
                            continue
                        num = self._word_to_number(word)
                        if num:
                            email_number = num
                            logger.info(f"🔢 Word number detected: '{word}' -> {num}")
                            break

                if email_number:
                    email_index = email_number - 1
                    if 0 <= email_index < len(ctx["email_list"]):
                        target = ctx["email_list"][email_index]
                        email_id = target["id"]
                        account = "icloud" if email_id.isdigit() else "gmail"
                        read_tool = "read_icloud_email" if account == "icloud" else "read_gmail_email"

                        logger.info(f"📖 Reading email #{email_number} id={email_id}")

                        result = await self.mcp_client.call_tool(read_tool, email_id=email_id)

                        if isinstance(result, dict) and "error" not in result:
                            result["id"] = email_id
                            result["account"] = account
                            result["list_number"] = email_number
                            ctx["read_emails"][str(email_number)] = result
                            ctx["last_action_email_num"] = str(email_number)
                            logger.info(f"💾 Stored #{email_number}: {result.get('subject')}")

                        return self._format_email_content(result), None
                    else:
                        return f"Only {len(ctx['email_list'])} emails in list.", None
                else:
                    return "Please specify which email number to read.", None

            # ─────────────────────────────────────────
            # 4. DRAFT REPLY
            # ─────────────────────────────────────────
            draft_triggers = [
                'draft', 'reply to', 'respond to',
                'write back', 'write a reply', 'compose'
            ]
            is_draft = any(t in command_lower for t in draft_triggers)

            if is_draft:
                target_email_num = None

                explicit_match = re.search(
                    r'(?:email|number|mail|#)\s*(\d+)',
                    command_lower
                )
                if explicit_match:
                    target_email_num = int(explicit_match.group(1))
                    logger.info(f"📝 Explicit number: #{target_email_num}")
                else:
                    skip_words = {
                        'draft', 'reply', 'respond', 'write', 'compose',
                        'email', 'number', 'mail', 'a', 'an', 'the', 'to',
                        'for', 'this', 'that', 'my', 'me', 'please'
                    }
                    for word in command_lower.split():
                        if word in skip_words:
                            continue
                        num = self._word_to_number(word)
                        if num:
                            target_email_num = num
                            logger.info(f"📝 Word number: #{target_email_num}")
                            break

                # Get email data
                target_email_data = None

                if target_email_num and str(target_email_num) in ctx["read_emails"]:
                    target_email_data = ctx["read_emails"][str(target_email_num)]
                    logger.info(f"✅ Using specified email #{target_email_num}")

                elif ctx["last_action_email_num"] and ctx["last_action_email_num"] in ctx["read_emails"]:
                    target_email_num = ctx["last_action_email_num"]
                    target_email_data = ctx["read_emails"][target_email_num]
                    logger.info(f"✅ Using last read email #{target_email_num}")

                else:
                    return (
                        "Please read an email first.\n"
                        "Say 'read email number 1' then 'draft a reply'.",
                        None
                    )

                # Extract reply hint
                reply_hint = ""
                hint_match = re.search(
                    r'(?:saying|that|message|reply with|respond with|tell them|write)\s+(.+)',
                    command_lower
                )
                if hint_match:
                    reply_hint = hint_match.group(1)
                    logger.info(f"💬 Reply hint: {reply_hint}")

                # Build fresh draft
                from_addr = target_email_data.get("from", "")
                subject = target_email_data.get("subject", "")
                body = target_email_data.get("body", "")
                account = target_email_data.get("account", "gmail")
                recipient = self._parse_recipient(from_addr)
                reply_subject = subject if subject.lower().startswith('re:') else f"Re: {subject}"

                logger.info(f"📧 Drafting for #{target_email_num}: to={recipient} via {account}")

                reply_body = await self._generate_reply_body(
                    original_from=from_addr,
                    original_subject=subject,
                    original_body=self._strip_html(body),
                    reply_hint=reply_hint
                )

                # OVERWRITE pending_draft completely
                ctx["pending_draft"] = {
                    "to": recipient,
                    "subject": reply_subject,
                    "body": reply_body,
                    "account": account,
                    "for_email_num": target_email_num
                }

                logger.info(f"💾 Draft saved: to={recipient} account={account} for #{target_email_num}")

                return (
                    f"📧 DRAFT REPLY (email #{target_email_num}):\n\n"
                    f"To: {recipient}\n"
                    f"Subject: {reply_subject}\n\n"
                    f"{reply_body}\n\n"
                    f"---\n"
                    f"Say 'send reply' to send or 'cancel' to cancel."
                ), None

            # ─────────────────────────────────────────
            # 5. NORMAL GROQ PROCESSING
            # ─────────────────────────────────────────
            tools_desc = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.mcp_client.available_tools
            ])

            context_summary = ""
            if ctx["email_list"]:
                context_summary += f"Loaded emails: {len(ctx['email_list'])}\n"
            if ctx["read_emails"]:
                for num, data in ctx["read_emails"].items():
                    context_summary += f"Read email #{num}: '{data.get('subject', '?')}' from {data.get('from', '?')}\n"
            if ctx["pending_draft"]:
                context_summary += f"Pending draft to: {ctx['pending_draft']['to']}\n"

            system_prompt = f"""You are an email assistant.

Available MCP tools:
{tools_desc}

SESSION CONTEXT:
{context_summary if context_summary else 'No emails loaded yet.'}

RULES:
1. "read email X", "draft reply", "send reply" -> respond with action "respond" (handled by system).
2. "check gmail" -> list_gmail_emails with query "category:primary" max_results 10.
3. "check icloud" -> list_icloud_emails max_results 10.
4. "find emails from NAME" -> search_gmail.
5. Always return valid JSON only.

Response format:
{{"action": "call_tool" or "respond", "tool": "...", "params": {{}}, "message": "..."}}

Examples:
"check my gmail" -> {{"action": "call_tool", "tool": "list_gmail_emails", "params": {{"max_results": 10, "query": "category:primary"}}, "message": "Fetching Gmail..."}}
"check icloud" -> {{"action": "call_tool", "tool": "list_icloud_emails", "params": {{"max_results": 10}}, "message": "Fetching iCloud..."}}
"find emails from Nike" -> {{"action": "call_tool", "tool": "search_gmail", "params": {{"query": "from:Nike", "max_results": 5}}, "message": "Searching..."}}
"send email to john@x.com saying hello" -> {{"action": "call_tool", "tool": "send_gmail_email", "params": {{"to": "john@x.com", "subject": "Hello", "body": "hello"}}, "message": "Sending..."}}
"read email 1" or "draft reply" or "send reply" -> {{"action": "respond", "message": "On it!"}}"""

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

                    if isinstance(tool_result, list):
                        if len(tool_result) > 0:
                            ctx["email_list"] = tool_result
                            ctx["read_emails"] = {}
                            ctx["last_action_email_num"] = None
                            ctx["pending_draft"] = None
                            logger.info(f"💾 New list: {len(tool_result)} emails")
                            return self._format_email_list(tool_result), tool_result
                        return "No emails found.", None

                    if isinstance(tool_result, dict):
                        if "error" in tool_result:
                            return f"Error: {tool_result['error']}", None
                        if tool_result.get("status") == "sent":
                            return "✅ Email sent!", None
                        return str(tool_result), None

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
            "🤖 AI Email Agent - V4 Voice Edition\n\n"
            "HOW TO USE:\n"
            "1. Say or type 'check my Gmail' or 'check my iCloud'\n"
            "2. Say or type 'read email number 1'\n"
            "3. Say or type 'draft a reply'\n"
            "4. Say or type 'send reply'\n\n"
            "✨ NEW: I now respond with VOICE + TEXT!\n\n"
            "COMMANDS:\n"
            "/help - All voice commands\n"
            "/status - See what I remember\n"
            "/clear - Clear my memory\n"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📖 COMMANDS (voice or text):\n\n"
            "LISTING:\n"
            "- 'Check my Gmail'\n"
            "- 'Check my iCloud'\n"
            "- 'Show my last 10 emails'\n\n"
            "READING:\n"
            "- 'Read email number 1'\n"
            "- 'Read email number two'\n"
            "- 'Read it' (when only 1 result)\n\n"
            "DRAFTING:\n"
            "- 'Draft a reply'\n"
            "- 'Draft a reply for email 2'\n"
            "- 'Draft a reply saying I will attend'\n\n"
            "SENDING:\n"
            "- 'Send reply'\n"
            "- 'Cancel'\n\n"
            "SEARCHING:\n"
            "- 'Find emails from John'\n"
            "- 'Search emails about meetings'\n"
            "- 'Show unread emails'\n\n"
            "TIPS:\n"
            "- Works with VOICE and TEXT!\n"
            "- I respond with TEXT + VOICE (both)\n"
            "- Use /status to see context\n"
            "- Use /clear to reset memory\n"
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current bot context/memory for this user."""
        user_id = update.effective_user.id
        ctx = self._get_ctx(user_id)

        msg = "📊 CURRENT STATUS:\n\n"

        if ctx["email_list"]:
            msg += f"📋 Emails loaded: {len(ctx['email_list'])}\n"
            for i, email in enumerate(ctx["email_list"][:5], 1):
                msg += f"  {i}. {email.get('subject', 'No subject')[:30]}\n"
            if len(ctx["email_list"]) > 5:
                msg += f"  ... and {len(ctx['email_list']) - 5} more\n"
        else:
            msg += "📋 Emails loaded: None\n"

        msg += "\n"

        if ctx["read_emails"]:
            msg += "📖 Read emails:\n"
            for num, data in ctx["read_emails"].items():
                msg += f"  #{num}: {data.get('subject', '?')[:30]} ({data.get('account', '?')})\n"
        else:
            msg += "📖 Read emails: None\n"

        msg += "\n"

        if ctx["last_action_email_num"]:
            msg += f"👆 Last read: Email #{ctx['last_action_email_num']}\n"
        else:
            msg += "👆 Last read: None\n"

        msg += "\n"

        if ctx["pending_draft"]:
            draft = ctx["pending_draft"]
            msg += "📝 Pending draft:\n"
            msg += f"  To: {draft['to']}\n"
            msg += f"  Subject: {draft['subject']}\n"
            msg += f"  Account: {draft['account']}\n"
            msg += f"  For email: #{draft.get('for_email_num', '?')}\n"
        else:
            msg += "📝 Pending draft: None\n"

        await update.message.reply_text(msg)

    async def clear_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear all context/memory for this user."""
        user_id = update.effective_user.id
        self.user_context[user_id] = {
            "email_list": [],
            "read_emails": {},
            "pending_draft": None,
            "last_action_email_num": None,
        }
        await update.message.reply_text(
            "🗑️ Memory cleared!\n\n"
            "Start fresh by saying 'check my Gmail'."
        )

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages from users - V4 with TTS response."""
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
            await processing_msg.edit_text(
                f"✅ Heard: {transcribed_text}\n\n⚙️ Processing..."
            )

            response_text, email_list = await self.process_email_command(
                transcribed_text, user_id
            )

            # Send TEXT response
            await update.message.reply_text(f"🤖 Response:\n\n{response_text}")
            
            # V4: ALWAYS generate and send VOICE response
            await processing_msg.edit_text("🔊 Generating voice response...")
            voice_path = await self.text_to_speech(response_text)
            
            if voice_path:
                with open(voice_path, 'rb') as audio:
                    await update.message.reply_voice(voice=audio)
                os.unlink(voice_path)  # Clean up temp file
                logger.info("✅ Voice response sent")
            else:
                logger.warning("⚠️ TTS failed, text-only response sent")
            
            await processing_msg.delete()

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await processing_msg.edit_text("❌ Something went wrong. Try again.")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - V4 with TTS response."""
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name
        text = update.message.text

        logger.info(f"💬 Text from {user_name}: {text}")

        processing_msg = await update.message.reply_text("⚙️ Processing...")

        try:
            response_text, email_list = await self.process_email_command(text, user_id)
            
            # Send TEXT response
            await update.message.reply_text(f"🤖 Response:\n\n{response_text}")
            
            # V4: ALWAYS generate and send VOICE response
            await processing_msg.edit_text("🔊 Generating voice response...")
            voice_path = await self.text_to_speech(response_text)
            
            if voice_path:
                with open(voice_path, 'rb') as audio:
                    await update.message.reply_voice(voice=audio)
                os.unlink(voice_path)  # Clean up temp file
                logger.info("✅ Voice response sent")
            else:
                logger.warning("⚠️ TTS failed, text-only response sent")
            
            await processing_msg.delete()

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await processing_msg.edit_text("❌ Something went wrong. Try again.")

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
        logger.info("🚀 Starting Telegram bot V4...")

        app = Application.builder().token(self.token).post_init(self.post_init).build()

        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("status", self.status_command))
        app.add_handler(CommandHandler("clear", self.clear_command))
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        app.add_error_handler(self.error_handler)

        logger.info("✅ Bot ready with TTS!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    bot = EmailBot()
    bot.run()


if __name__ == "__main__":
    main()