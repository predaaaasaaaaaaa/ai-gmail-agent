# 🤖 AI Email Agent with MCP - V4 (Voice Conversational Bot)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://hub.docker.com/r/samymetref/ai-email-agent)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://telegram.org/)
[![Groq](https://img.shields.io/badge/Groq-Powered-orange.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent AI email assistant powered by Groq's LLaMA 3.3 70B and Model Context Protocol (MCP). Manage Gmail and iCloud emails via **natural voice conversation** on Telegram.

---

## 🎉 What's New in V4 Final

**🗣️ Fully Conversational AI** - Bot doesn't just transcribe, it *talks* back!

### New Features
- **🔊 Text-to-Speech (TTS)** - Bot responds with voice using Groq Orpheus
- **🎯 Smart Voice System** - Only speaks conversation, not data
- **💬 Natural Q&A** - Ask "What can you do?" or "Is this secure?"
- **🎲 Dynamic Variations** - Never repeats the same response twice
- **🧠 Off-Topic Detection** - Gracefully handles non-email questions
- **👂 Human-Like Interaction** - Feels like talking to a real assistant

### V4 Interaction Example
```
🎤 You: "Check my Gmail"
📝 Bot: [Lists 10 emails in text]
🔊 Bot: "Here are your latest 10 emails. Which one would you like me to read?"

🎤 You: "Read email number 2"
📝 Bot: [Shows full email content]
🔊 Bot: "Here's email number 2. Would you like me to draft a reply?"

🎤 You: "Draft a reply"
📝 Bot: [Shows AI-generated draft]
🔊 Bot: "I've drafted a reply for email 2. Would you like me to send it?"

🎤 You: "Send it"
📝 Bot: "✅ Reply sent!"
🔊 Bot: "Done! Reply sent. Anything else I can help you with?"
```

---

## ✨ All Features

### V4 Voice Intelligence
- ✅ **Groq Whisper (STT)** - Understands your voice commands
- ✅ **Groq Orpheus TTS** - Responds with natural voice (diana voice)
- ✅ **Smart Voice Triggers** - Only speaks when needed (conversation, not data)
- ✅ **Dynamic Variations** - 3-5 response variations per action (never repeats)
- ✅ **Natural Q&A** - Answers "What can you do?" and "Is this secure?"
- ✅ **Off-Topic Handling** - Redirects gracefully to email tasks

### Core Email Capabilities
- ✅ **Read Emails** - Gmail (primary inbox) + iCloud
- ✅ **Send Emails** - Compose via natural language
- ✅ **Advanced Search** - Find by sender, subject, date, keywords
- ✅ **Draft Replies** - AI-generated with approval workflow
- ✅ **Voice + Text Input** - Works both ways
- ✅ **Context Awareness** - Remembers conversation state
- ✅ **MCP Architecture** - Modular, reusable tools
- ✅ **Dockerized** - One-command deployment

### V4 Telegram Bot Commands

**Setup Commands:**
```
/start - Initialize bot
/help - See all commands
/status - View bot memory (emails, drafts, context)
/clear - Reset session memory
```

**Voice/Text Commands:**
```
"Check my Gmail" - List primary inbox emails
"Check my iCloud" - List iCloud emails
"Read email number 2" - Read specific email
"Read it" - Auto-read when only 1 result
"Draft a reply" - Generate reply for last read email
"Draft a reply for email 3" - Generate reply for specific email
"Draft a reply saying I will attend" - Custom reply hint
"Send reply" - Send pending draft
"Cancel" - Cancel pending draft
"Find emails from Nike" - Search by sender
"What can you do?" - See capabilities
"Is this secure?" - Security explanation
```

---

## 🏗️ Architecture
```
┌─────────────────┐
│  Telegram User  │ ◄── Voice Input
└────────┬────────┘
         │ Voice Message
         ▼
┌─────────────────────┐
│  Groq Whisper API   │ ◄── Speech-to-Text
└────────┬────────────┘
         │ Transcribed Text
         ▼
┌─────────────────────┐
│  Telegram Bot       │ ◄── Context Management
└────────┬────────────┘
         │ Command
         ▼
┌─────────────────────┐
│  Groq LLaMA 3.3 70B │ ◄── AI Decision Making
└────────┬────────────┘
         │ Tool Calls
         ▼
┌─────────────────────┐
│   MCP Client        │ ◄── Protocol Layer
└────────┬────────────┘
         │ JSON-RPC
         ▼
┌─────────────────────┐
│   MCP Server        │ ◄── 10+ Email Tools
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Email Handlers     │ ◄── Gmail API + iCloud IMAP/SMTP
└─────────┬───────────┘
         │
         ▼
┌─────────────────────┐
│  Groq Orpheus TTS   │ ◄── Text-to-Speech (Voice Response)
└─────────────────────┘
         │
         ▼
┌─────────────────┐
│  Telegram User  │ ◄── Voice + Text Response
└─────────────────┘
```

---

## 📁 Project Structure
```
ai-gmail-agent/
├── telegram_bot/
│   └── bot.py              # V4 Telegram bot (voice conversation)
├── agent/
│   ├── client.py           # V2 CLI agent
│   └── mcp_client.py       # MCP client wrapper
├── mcp_server/
│   ├── server.py           # MCP server
│   └── email_tools.py      # Gmail & iCloud handlers
├── .env                    # API keys (not committed)
├── credentials.json        # Gmail OAuth (not committed)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start - V4 Telegram Bot

### Prerequisites

You'll need:
1. **Telegram Account** - To use the bot
2. **Telegram Bot Token** - From @BotFather
3. **Gmail OAuth Credentials** - One-time setup (~15 min)
4. **Groq API Key** - Free at [console.groq.com](https://console.groq.com)
5. **iCloud App Password** - Optional, for iCloud emails

---

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow prompts:
   - Bot name: `My Email Assistant`
   - Username: `my_email_assistant_bot` (must end in `bot`)
4. Copy the **bot token** (looks like `1234567890:ABCdef...`)
5. Save it - you'll need it in `.env`

---

### Step 2: Get Gmail API Credentials

**Option A: Quick Video Tutorial**
- Watch: [Gmail API Setup (5 min)](https://www.youtube.com/watch?v=hBC0ppS6vS0)

**Option B: Step-by-Step**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → name it "Email Agent"
3. Enable **Gmail API**:
   - APIs & Services → Library
   - Search "Gmail API" → Enable
4. Create OAuth credentials:
   - APIs & Services → Credentials
   - Create Credentials → OAuth Client ID
   - Application type: **Desktop app**
   - Download JSON → rename to `credentials.json`
5. Configure OAuth consent:
   - OAuth consent screen
   - User type: **External**
   - Add yourself as test user
   - Scopes: Add Gmail scopes

[Full Guide](https://developers.google.com/gmail/api/quickstart/python)

---

### Step 3: Get Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free - no credit card)
3. API Keys → Create new key
4. Copy it

**Note:** One Groq API key gives you access to:
- Whisper (Speech-to-Text)
- LLaMA 3.3 70B (AI reasoning)
- Orpheus TTS (Text-to-Speech)

---

### Step 4: iCloud Setup (Optional)

**If you want iCloud email support:**

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Sign in → Security section
3. App-Specific Passwords → Generate
4. Label: "Email Agent Bot"
5. Copy the password (format: `xxxx-xxxx-xxxx-xxxx`)

---

### Step 5: Create `.env` File

Create `.env` in project root:
```env
# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Groq API (one key for everything!)
GROQ_API_KEY=gsk_your_groq_api_key_here

# iCloud (optional)
ICLOUD_EMAIL=your-email@icloud.com
ICLOUD_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

---

### Step 6: Run the Bot

**Option 1: Python (Local)**
```bash
# Clone repo
git clone https://github.com/predaaaasaaaaaaa/ai-gmail-agent
cd ai-gmail-agent

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run Telegram bot
python telegram_bot/bot.py
```

**First run:** Browser will open for Gmail OAuth → sign in → allow access

**Option 2: Docker (Recommended)**
```bash
# Pull latest image
docker pull samymetref/ai-email-agent:v4

# Run bot
docker run -d \
  --name email-bot \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/token.pickle:/app/token.pickle \
  -v $(pwd)/.env:/app/.env:ro \
  samymetref/ai-email-agent:v4 \
  python telegram_bot/bot.py
```

---

### Step 7: Experience Voice Conversation!

1. Open Telegram
2. Search for your bot (`@my_email_assistant_bot`)
3. Send `/start`
4. **Have a voice conversation:**
   - 🎤 "Check my Gmail"
   - 🔊 Bot speaks: "Here are your latest 10 emails..."
   - 🎤 "Read email number 1"
   - 🔊 Bot speaks: "Here's email number 1. Would you like me to draft a reply?"
   - 🎤 "Yes, draft a reply"
   - 🔊 Bot speaks: "I've drafted a reply. Would you like me to send it?"

**Or type the same commands - works both ways!**

---

## 💬 Usage Examples

### V4 Conversational Flow
```
🎤 You (Voice): "Check my Gmail"

📝 Bot (Text): 
Found 10 emails. Showing top 10:
1. From: john@company.com
   Subject: Meeting tomorrow
2. From: sarah@startup.io
   Subject: Project update
...

🔊 Bot (Voice): "Here are your latest 10 emails. Which one would you like me to read?"

───────────────────────────────────

🎤 You (Voice): "Read email number 1"

📝 Bot (Text):
From: john@company.com
Subject: Meeting tomorrow

Hi, can we meet tomorrow at 3pm?
Let me know!

🔊 Bot (Voice): "Here's email number 1. Would you like me to draft a reply, or read another email?"

───────────────────────────────────

🎤 You (Voice): "Draft a reply saying I'll be there"

📝 Bot (Text):
📧 DRAFT REPLY (email #1):

To: john@company.com
Subject: Re: Meeting tomorrow

Hi John,

Thank you for reaching out. I'll be there 
tomorrow at 3pm. Looking forward to it!

Best regards
---
Say 'send reply' to send or 'cancel' to cancel.

🔊 Bot (Voice): "I've drafted a reply for email number 1. Would you like me to send it?"

───────────────────────────────────

🎤 You (Voice): "Send it"

📝 Bot (Text): ✅ Reply sent to john@company.com!

🔊 Bot (Voice): "Done! Reply sent. Anything else I can help you with?"
```

### Natural Q&A
```
🎤 You: "What can you do?"

📝 Bot: [Full capabilities list with emojis]

🔊 Bot: "I've listed everything I can do for you. Feel free to ask me anything!"

───────────────────────────────────

🎤 You: "Is this secure?"

📝 Bot: [Complete security explanation]

🔊 Bot: "Your data is completely safe with me. Everything stays on your device!"
```

### Off-Topic Handling
```
🎤 You: "What's the weather today?"

📝 Bot: "I'm an email assistant, so I focus on managing your inbox! 
I can check Gmail and iCloud, read emails, draft replies, and 
search messages. Try saying 'check my Gmail'!"

🔊 Bot: "I'm focused on emails! Want me to check your inbox?"
```

### Advanced Search
```
🎤 "Find emails from Nike"

📝 Found 2 emails:
1. From: Nike <updates@nike.com>
   Subject: New collection
2. From: Nike <promo@nike.com>
   Subject: 20% off sale

🔊 "I found 2 emails. Which one would you like to read?"

🎤 "Read email 1"
🔊 "Here's email number 1. Would you like me to draft a reply?"
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Bot Framework** | python-telegram-bot 20.0+ |
| **Speech-to-Text** | Groq Whisper Large V3 |
| **Text-to-Speech** | Groq Orpheus (diana voice) |
| **AI Reasoning** | Groq LLaMA 3.3 70B |
| **Protocol** | Model Context Protocol (MCP) |
| **Gmail** | Gmail API (OAuth 2.0) |
| **iCloud** | IMAP/SMTP |
| **Language** | Python 3.11+ |
| **Deployment** | Docker |

---

## 🔧 Development

### Run Tests
```bash
# Test Telegram bot
python telegram_bot/bot.py

# Test MCP client
python test_mcp_client.py

# Test email handlers
python test_email.py
```

### Project Commands
```bash
# Run bot locally
python telegram_bot/bot.py

# Run with Docker
docker-compose up telegram-bot

# Rebuild Docker
docker-compose build

# View logs
docker logs -f email-bot
```

---

## 🐛 Troubleshooting

### Bot doesn't respond

**Problem:** Bot shows "online" but doesn't reply

**Solution:**
```bash
# Check logs
python telegram_bot/bot.py

# Look for: "✅ Bot ready with off-topic detection!"
# If not, check .env file has TELEGRAM_BOT_TOKEN
```

### Voice not transcribing

**Problem:** Bot says "Couldn't transcribe"

**Solution:**
- Check Groq API key in `.env`
- Verify API quota: [console.groq.com](https://console.groq.com)
- Try shorter voice message (< 10 seconds)

### TTS not working

**Problem:** Bot sends text but no voice response

**Solution:**
- Check Groq API daily limits (3600 tokens/day for TTS)
- Voice messages are under 200 chars each
- Wait 24 hours if rate limited
- Check logs for "✅ Voice sent"

### Gmail OAuth error

**Problem:** "Access denied" when signing in

**Solution:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. OAuth consent screen → Add test users
3. Add your Gmail address
4. Delete `token.pickle` and try again

### iCloud authentication failed

**Problem:** "Authentication failed"

**Solution:**
- Use **app-specific password**, not regular password
- Verify `.env` has correct format: `xxxx-xxxx-xxxx-xxxx`
- Check Apple ID security settings

### Docker won't start

**Problem:** Container exits immediately

**Solution:**
```bash
# Check files exist
ls credentials.json .env

# Check .env format
cat .env

# View container logs
docker logs email-bot

# Rebuild without cache
docker-compose build --no-cache
```

---

## 📦 Available MCP Tools

The bot uses these email tools via MCP:

| Tool | Description | Example |
|------|-------------|---------|
| `list_gmail_emails` | Fetch Gmail inbox | "Check my Gmail" |
| `list_icloud_emails` | Fetch iCloud inbox | "Check my iCloud" |
| `read_gmail_email` | Read Gmail content | "Read email number 1" |
| `read_icloud_email` | Read iCloud content | "Read email 2" |
| `send_gmail_email` | Send via Gmail | Used after "Send reply" |
| `send_icloud_email` | Send via iCloud | Auto-detected |
| `search_gmail` | Advanced Gmail search | "Find emails from Nike" |
| `search_icloud` | Search iCloud by sender | "Find iCloud from John" |
| `draft_gmail_reply` | Draft Gmail reply | Auto-detected |
| `draft_icloud_reply` | Draft iCloud reply | Auto-detected |

---

## 🔐 Security & Privacy

### What's Safe

✅ All credentials stored **locally** (never uploaded)  
✅ OAuth tokens encrypted by Google  
✅ API keys in `.env` (gitignored)  
✅ Draft approval required (no auto-send)  
✅ Voice processed via Groq (encrypted HTTPS)  
✅ No data stored on Telegram servers  
✅ **Open source** - audit the code yourself!  

### What's Never Committed

🚫 `credentials.json` - Gmail OAuth  
🚫 `token.pickle` - Gmail access token  
🚫 `.env` - All API keys  

### What Groq Processes

✅ Voice transcription (Whisper) - No email content  
✅ AI reasoning (LLaMA) - Command interpretation only  
✅ Voice generation (Orpheus) - Conversational responses only  

**Groq NEVER sees your email content!**

### Best Practices

1. **Revoke access** anytime: [Google Account](https://myaccount.google.com/permissions)
2. **Delete bot** anytime: Send `/deletebot` to @BotFather
3. **Use test account** for development
4. **Keep `.env` private** - never share

---

## 📊 Version History

### V4 (Current) - Voice Conversational AI
**Released:** February 2026

**New:**
- 🔊 Text-to-Speech voice responses (Groq Orpheus)
- 🎯 Smart voice system (only speaks conversation)
- 💬 Natural Q&A ("What can you do?", "Is this secure?")
- 🎲 Dynamic response variations (never repeats)
- 🧠 Off-topic detection & graceful redirect
- 👂 Human-like conversation flow

**Features:**
- Voice input AND output (full conversation)
- Context-aware TTS messages
- Token-optimized (200 chars max per voice)
- 3-5 response variations per action
- Capabilities & security explanations
- Friendly off-topic handling

### V3 - Telegram Voice Bot
**Released:** February 2026

**New:**
- 🎤 Telegram bot with voice + text support
- 🧠 Context-aware conversation memory
- 🤖 AI-powered reply generation
- 📱 Mobile-friendly (Telegram app)
- 🔄 Whisper transcription normalization

### V2 - MCP Email Agent
**Released:** January 2026

**New:**
- Model Context Protocol architecture
- 10 email tools (list, read, send, search, draft)
- Gmail advanced search

### V1 - Basic Email Bot
**Released:** January 2026

**Features:**
- Simple Gmail read/send
- Basic CLI commands

---

## 🎯 Roadmap

### V5 (Planned)
- 📎 **Attachment Support** - Send/receive files
- 🗓️ **Calendar Integration** - Schedule from emails
- 🔔 **Push Notifications** - Real-time email alerts
- 🌐 **Multi-language** - Support more languages
- 🎨 **Voice Style Selection** - Choose TTS voice
- 👥 **Multi-user** - Family/team bot access
- 📊 **Analytics Dashboard** - Email insights

---

## 📄 License

MIT License - Free to use, modify, and distribute

---

## 🙏 Acknowledgments

- **Groq** - Fast LLaMA inference, Whisper API & Orpheus TTS
- **Telegram** - Bot platform
- **Google** - Gmail API
- **Apple** - iCloud IMAP/SMTP
- **Anthropic** - MCP protocol inspiration

---

## 📧 Links

- **Docker Hub:** [samymetref/ai-email-agent](https://hub.docker.com/r/samymetref/ai-email-agent)
- **GitHub:** [predaaaasaaaaaaa/ai-gmail-agent](https://github.com/predaaaasaaaaaaa/ai-gmail-agent)
- **Groq Console:** [console.groq.com](https://console.groq.com)
- **MCP Docs:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open Pull Request

---

## ❓ FAQ

**Q: Is this free?**  
A: Yes! Groq API is free (with limits). Gmail API is free. Telegram is free.

**Q: Does the bot store my emails?**  
A: No. Everything is processed in real-time and stored locally on your machine.

**Q: Can other people use my bot?**  
A: No. Your bot is private. Only you can access it (unless you share the link).

**Q: What if I run out of Groq credits?**  
A: Groq free tier: 3600 TTS tokens/day. Each voice message ~50-200 tokens. Wait 24h if you hit limits.

**Q: Can I choose a different voice?**  
A: Yes! Edit `bot.py` line 363: `voice="diana"` → Options: diana, hannah, autumn (feminine) or troy, austin, daniel (masculine)

**Q: Can I host this on a server?**  
A: Yes! Use Docker on any VPS (AWS, DigitalOcean, etc.). Keep `.env` secure.

**Q: Why does the bot speak some responses but not others?**  
A: By design! Bot sends TEXT for data (email lists, content) and VOICE for conversation (questions, confirmations). This saves tokens and is faster.

---

**Built with ❤️ by [Samy Metref](https://github.com/predaaaasaaaaaaa)**

⭐ **Star this repo if you find it useful!**  
💡 **Questions? Open an issue!**  
🐳 **Docker Hub:** Check latest version!  

---

**Ready to have voice conversations with your email assistant? Get started in 10 minutes! 🚀**