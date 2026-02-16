"""
Telegram Voice Bot for AI Email Agent

This bot:
1. Receives voice messages from users
2. Transcribes them using Groq Whisper
3. Processes commands through MCP email agent
4. Responds with voice (TTS)
"""

import os
import logging
import tempfile
import sys
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent))  # Add project root to path
from agent.mcp_client import MCPEmailClient 

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class EmailBot:
    """
    Telegram bot for voice-controlled email management.
    """
    
    def __init__(self):
        """Initialize the bot."""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")
        
         # Initialize Groq for transcription
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        
        self.groq_client = Groq(api_key=self.groq_api_key)

        # MCP client
        self.mcp_client = None
        self.mcp_session = None

        logger.info("✅ Email Bot initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command.
        
        This is called when user first starts the bot.
        """
        welcome_message = """
🤖 **AI Email Agent - Voice Edition**

Welcome! I can help you manage your emails using voice messages.

**How to use:**
1. Send me a voice message
2. I'll transcribe and process your command
3. I'll respond with voice

**Example commands:**
🎤 "Check my Gmail"
🎤 "Find emails from John"
🎤 "Draft a reply to Sarah's email"
🎤 "Send an email to john@example.com"

**Text commands:**
/start - Show this message
/help - Get help

Try sending me a voice message now! 🎙️
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /help command.
        """
        help_message = """
📖 **Help - Voice Commands**

Send voice messages to control your email:

**Reading Emails:**
🎤 "Check my Gmail"
🎤 "Show my iCloud emails"
🎤 "Read my last email"

**Searching:**
🎤 "Find emails from john@example.com"
🎤 "Search for emails about meetings"
🎤 "Show me unread emails"

**Sending:**
🎤 "Send an email to john@example.com saying hello"
🎤 "Draft a reply to Sarah's email"

**Need help?** Just ask in a voice message!
        """
        
        await update.message.reply_text(
            help_message,
            parse_mode='Markdown'
        )

    async def transcribe_voice(self, voice_file_path: str) -> str:
        """
        Transcribe voice message using Groq Whisper.

        Groq Whisper supports:
        - Multiple languages (auto-detect)
        - High accuracy
        - Fast processing
        """
        try:
            logger.info(f"🎤 Transcribing audio file: {voice_file_path}")
            
            # Open audio file
            with open(voice_file_path, 'rb') as audio_file:
                # Call Groq Whisper API
                transcription = self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",  # Groq's Whisper model
                    language="en",  # Can set to "auto" for auto-detection
                    response_format="text"
                )
            
            logger.info(f"✅ Transcription: {transcription}")
            return transcription
            
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return None
    
    async def process_email_command(self, command: str) -> str:
        """
        Process email command through MCP agent.
        
        Args:
            command: Transcribed voice command (e.g., "check my gmail")
        
        Returns:
            Response text from agent
        
        This uses the SAME logic as your CLI agent, but returns text instead.
        """
        try:
            logger.info(f"🧠 Processing command: {command}")
            
            # Build tool descriptions for Groq
            tools_desc = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.mcp_client.available_tools
            ])
            
            # System prompt (same as CLI agent)
            system_prompt = f"""You are an email assistant with access to these MCP tools:

{tools_desc}

IMPORTANT INSTRUCTIONS:
1. For draft replies: Use draft_gmail_reply or draft_icloud_reply tools.
2. For searches: Use search_gmail with Gmail query syntax.
3. Always be helpful and professional.

When the user asks you to do something, respond with a JSON object:
{{
    "action": "call_tool" or "respond",
    "tool": "tool_name",
    "params": {{}},
    "message": "what to tell the user"
}}

Examples:
User: "check my gmail"
{{"action": "call_tool", "tool": "list_gmail_emails", "params": {{"max_results": 5}}, "message": "Fetching your Gmail..."}}

User: "find emails from john"
{{"action": "call_tool", "tool": "search_gmail", "params": {{"query": "from:john", "max_results": 5}}, "message": "Searching..."}}

Always respond with valid JSON only."""

            # Call Groq to decide what to do
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": command}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            assistant_response = response.choices[0].message.content
            
            # Parse JSON response
            import json
            try:
                decision = json.loads(assistant_response)
                
                if decision.get("action") == "call_tool":
                    # Call MCP tool
                    logger.info(f"🔧 Calling tool: {decision['tool']}")
                    
                    tool_result = await self.mcp_client.call_tool(
                        self.mcp_session,
                        decision["tool"],
                        **decision.get("params", {})
                    )
                    
                    # Format result for voice response
                    result_text = self._format_result_for_voice(tool_result, decision)
                    return result_text
                
                else:
                    # Just respond with message
                    return decision.get("message", assistant_response)
                    
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                return assistant_response
                
        except Exception as e:
            logger.error(f"❌ Error processing command: {e}")
            return "Sorry, I had trouble processing that command. Please try again."
    
    def _format_result_for_voice(self, tool_result, decision) -> str:
        """
        Format tool results in a voice-friendly way.
        
        Voice responses should be:
        - Concise (people don't like long voice messages)
        - Natural language (not JSON)
        - Action-oriented
        
        Args:
            tool_result: Result from MCP tool
            decision: The decision made by Groq
        
        Returns:
            Formatted text suitable for voice
        """
        # Handle list of emails
        if isinstance(tool_result, list):
            if not tool_result:
                return "You have no emails matching that query."
            
            # Limit to top 3 for voice (concise)
            emails_text = f"I found {len(tool_result)} emails. Here are the top 3:\n\n"
            
            for i, email in enumerate(tool_result[:3], 1):
                from_addr = email.get('from', 'Unknown')
                subject = email.get('subject', 'No subject')
                emails_text += f"{i}. From {from_addr}\n   Subject: {subject}\n\n"
            
            if len(tool_result) > 3:
                emails_text += f"...and {len(tool_result) - 3} more."
            
            return emails_text
        
        # Handle single email
        elif isinstance(tool_result, dict):
            if 'error' in tool_result:
                return f"Error: {tool_result['error']}"
            
            # Email read result
            if 'body' in tool_result:
                return (
                    f"Email from {tool_result.get('from', 'Unknown')}\n"
                    f"Subject: {tool_result.get('subject', 'No subject')}\n\n"
                    f"{tool_result['body'][:500]}..."  # Truncate long emails
                )
            
            # Draft result
            if tool_result.get('status') == 'draft_created':
                return (
                    f"📧 Draft created:\n\n"
                    f"To: {tool_result['to']}\n"
                    f"Subject: {tool_result['subject']}\n\n"
                    f"{tool_result['body']}\n\n"
                    f"Should I send this? Reply 'yes' or 'no'."
                )
            
            # Send result
            if tool_result.get('status') == 'sent':
                return f"✅ Email sent successfully!"
            
            # Generic dict
            return str(tool_result)
        
        # Fallback
        return str(tool_result)
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle voice messages from users.
        """
        user_name = update.effective_user.first_name
        logger.info(f"📥 Received voice message from {user_name}")
        
        # Send "processing" message
        processing_msg = await update.message.reply_text(
            "🎤 Listening..."
        )
        
        try:
            # Get voice file
            voice = update.message.voice
            voice_file = await context.bot.get_file(voice.file_id)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
                temp_path = temp_file.name
            
            # Download voice
            await voice_file.download_to_drive(temp_path)
            
            # Update status
            await processing_msg.edit_text("🔄 Transcribing...")
            
            # Transcribe
            transcribed_text = await self.transcribe_voice(temp_path)
            
            # Clean up
            os.unlink(temp_path)
            
            if not transcribed_text:
                await processing_msg.edit_text(
                    "❌ Couldn't transcribe. Please try again with clearer audio."
                )
                return
            
            logger.info(f"📝 Transcribed: {transcribed_text}")
            
            # Update status
            await processing_msg.edit_text(
                f"✅ Heard: _{transcribed_text}_\n\n⚙️ Processing...",
                parse_mode='Markdown'
            )
            
            # Process through MCP agent
            response_text = await self.process_email_command(transcribed_text)
            
            # Send response
            await update.message.reply_text(
                f"🤖 **Response:**\n\n{response_text}",
                parse_mode='Markdown'
            )
            
            # Delete processing message
            await processing_msg.delete()
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            await processing_msg.edit_text(
                "❌ Something went wrong. Please try again."
            )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle text messages.
        """
        await update.message.reply_text(
            "💬 I see you sent text!\n\n"
            "I work best with voice messages 🎤\n"
            "But text support is coming soon!\n\n"
            "Try sending a voice message instead."
        )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle errors.
        """
        logger.error(f"❌ Error: {context.error}")
        
        if update and update.message:
            await update.message.reply_text(
                "❌ Oops! Something went wrong.\n"
                "Please try again or contact support."
            )

    async def connect_mcp_async(self):
        """
        Connect to MCP server asynchronously.
        
        This is called once when the bot starts.
        """
        try:
            logger.info("🔌 Connecting to MCP server...")
            
            self.mcp_client = MCPEmailClient()
            
            # Connect and get session
            async for session in self.mcp_client.connect():
                self.mcp_session = session
                logger.info(f"✅ MCP connected - {len(self.mcp_client.available_tools)} tools available")
                break  # We only need one session
                
        except Exception as e:
            logger.error(f"❌ MCP connection failed: {e}")
            raise

    async def run_async(self):
        """
        Async bot startup.
        """
        # Connect to MCP first
        await self.connect_mcp_async()
        
        # Build application
        app = Application.builder().token(self.token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        app.add_error_handler(self.error_handler)
        
        logger.info("✅ Bot ready!")
        
        # Start polling
        await app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def run(self):
        """
        Start the bot (wrapper).
        """
        import asyncio
        asyncio.run(self.run_async())

def main():
    bot = EmailBot()
    bot.run()


if __name__ == "__main__":
    main()