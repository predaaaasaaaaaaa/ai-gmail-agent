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
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv

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
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle voice messages from users.
        """
        logger.info(f"📥 Received voice message from {update.effective_user.first_name}")
        
        # For now, just acknowledge receipt
        await update.message.reply_text(
            "🎤 Voice message received!\n\n"
            "🔧 Transcription coming in next step...\n\n"
            f"Duration: {update.message.voice.duration}s"
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