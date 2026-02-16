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
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle voice messages from users.
        """
        user_name = update.effective_user.first_name
        logger.info(f"📥 Received voice message from {user_name}")
        
        # Send "processing" message
        processing_msg = await update.message.reply_text(
            "🎤 Listening to your voice message..."
        )
        
        try:
            # Get voice file
            voice = update.message.voice
            voice_file = await context.bot.get_file(voice.file_id)
            
            # Create temporary file to store audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as temp_file:
                temp_path = temp_file.name
            
            # Download voice message
            await voice_file.download_to_drive(temp_path)
            logger.info(f"📥 Downloaded voice to: {temp_path}")
            
            # Update status
            await processing_msg.edit_text("🔄 Transcribing your message...")
            
            # Transcribe with Groq Whisper
            transcribed_text = await self.transcribe_voice(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if transcribed_text:
                logger.info(f"📝 Transcribed: {transcribed_text}")
                
                # Show user what was heard
                await processing_msg.edit_text(
                    f"✅ **I heard:**\n\n"
                    f"_{transcribed_text}_\n\n"
                    f"🔧 Processing your request...",
                    parse_mode='Markdown'
                )
            
                # For now, just echo back
                await update.message.reply_text(
                    f"📝 You said: _{transcribed_text}_\n\n"
                    f"⚙️ Email processing coming in Phase 3!",
                    parse_mode='Markdown'
                )
            else:
                await processing_msg.edit_text(
                    "❌ Sorry, I couldn't transcribe your message.\n"
                    "Please try again with clearer audio."
                )
                
        except Exception as e:
            logger.error(f"❌ Error handling voice: {e}")
            await processing_msg.edit_text(
                "❌ Oops! Something went wrong processing your voice message.\n"
                "Please try again."
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
    
    def run(self):
        """
        Start the bot.
        """
        logger.info("🚀 Starting Telegram bot...")
        
        # Create application
        app = Application.builder().token(self.token).build()
        
        # Add command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        
        # Add message handlers
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        # Add error handler
        app.add_error_handler(self.error_handler)
        
        logger.info("✅ Bot is running! Send /start in Telegram to begin.")
        logger.info("Press Ctrl+C to stop.")
        
        # Start polling (bot will run forever)
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    bot = EmailBot()
    bot.run()


if __name__ == "__main__":
    main()