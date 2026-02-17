# 🤖 AI Email Agent with MCP - V3 (Telegram Voice Bot)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://hub.docker.com/r/samymetref/ai-email-agent)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://telegram.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent AI email assistant powered by Groq's LLaMA 3.3 70B and Model Context Protocol (MCP). Manage Gmail and iCloud emails via **voice messages** on Telegram or natural language text commands.

---

## 🎉 What's New in V3

**🎤 Telegram Voice Bot** - Your personal email assistant you can talk to!

- **Voice Control** - Send voice messages in Telegram to manage emails
- **Text Commands** - Type commands if you prefer
- **Smart Context Memory** - Bot remembers all read emails and drafts
- **AI Reply Generation** - Professional email replies with custom hints
- **Whisper Transcription** - Groq Whisper handles voice-to-text
- **Multi-Account** - Seamless Gmail + iCloud switching
- **Auto-Read Single Results** - Just say "read it" when there's 1 email
- **Session Management** - `/status` to see what bot remembers, `/clear` to reset

---

## ✨ All Features

### Core Capabilities
- ✅ **Read Emails** - Gmail (primary inbox) + iCloud
- ✅ **Send Emails** - Compose via natural language
- ✅ **Advanced Search** - Find by sender, subject, date, keywords
- ✅ **Draft Replies** - AI-generated with approval workflow
- ✅ **Voice + Text Input** - Works both ways
- ✅ **Context Awareness** - Remembers conversation state
- ✅ **MCP Architecture** - Modular, reusable tools
- ✅ **Dockerized** - One-command deployment

### V3 Telegram Bot Commands

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
"Search emails about meetings" - Search by keyword
```

---

## 🏗️ Architecture
```
┌─────────────────┐
│  Telegram User  │
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
└─────────────────────┘
```

---

## 📁 Project Structure
```
ai-gmail-agent/
├── telegram_bot/
│   └── bot.py              # V3 Telegram bot (voice + text)
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

## 🚀 Quick Start - V3 Telegram Bot

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

# Groq API
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
git clone https://github.com/samymetref/ai-gmail-agent
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
docker pull samymetref/ai-email-agent:v3

# Run bot
docker run -d \
  --name email-bot \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/token.pickle:/app/token.pickle \
  -v $(pwd)/.env:/app/.env:ro \
  samymetref/ai-email-agent:v3 \
  python telegram_bot/bot.py
```

---

### Step 7: Use Your Bot!

1. Open Telegram
2. Search for your bot (`@my_email_assistant_bot`)
3. Send `/start`
4. **Try voice commands:**
   - 🎤 "Check my Gmail"
   - 🎤 "Read email number 1"
   - 🎤 "Draft a reply"
   - 🎤 "Send reply"

**Or type the same commands!**

---

## 💬 Usage Examples

### Basic Flow
```
🎤 Voice: "Check my Gmail"
🤖 Bot: Found 10 emails. Showing top 10:
        1. From: john@company.com
           Subject: Meeting tomorrow
        
        2. From: sarah@startup.io
           Subject: Project update
        ...

🎤 Voice: "Read email number 1"
🤖 Bot: From: john@company.com
        Subject: Meeting tomorrow
        
        Hi, can we meet tomorrow at 3pm?
        Let me know!

🎤 Voice: "Draft a reply saying I'll be there"
🤖 Bot: 📧 DRAFT REPLY (email #1):
        
        To: john@company.com
        Subject: Re: Meeting tomorrow
        
        Hi John,
        
        Thank you for reaching out. I'll be there 
        tomorrow at 3pm. Looking forward to it!
        
        Best regards
        ---
        Say 'send reply' to send or 'cancel' to cancel.

🎤 Voice: "Send reply"
🤖 Bot: ✅ Reply sent to john@company.com!
```

### Advanced Search
```
🎤 "Find emails from Nike"
🤖 Found 1 email:
   1. From: Nike <updates@nike.com>
      Subject: New collection
   
   Say 'read it' to read it.

🎤 "Read it"
🤖 [Reads email automatically]

🎤 "Search emails about meetings"
🤖 Found 5 emails...
```

### Context Management
```
💬 Type: /status
🤖 Bot: 📊 CURRENT STATUS:
        
        📋 Emails loaded: 10
        📖 Read emails:
           #1: Meeting tomorrow (gmail)
           #2: Project update (gmail)
        
        👆 Last read: Email #2
        📝 Pending draft: None
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Bot Framework** | python-telegram-bot 20.0+ |
| **Speech-to-Text** | Groq Whisper Large V3 |
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

# Look for: "✅ Bot ready!"
# If not, check .env file has TELEGRAM_BOT_TOKEN
```

### Voice not transcribing

**Problem:** Bot says "Couldn't transcribe"

**Solution:**
- Check Groq API key in `.env`
- Verify API quota: [console.groq.com](https://console.groq.com)
- Try shorter voice message (< 10 seconds)

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

### What's Never Committed

🚫 `credentials.json` - Gmail OAuth  
🚫 `token.pickle` - Gmail access token  
🚫 `.env` - All API keys  

### Best Practices

1. **Revoke access** anytime: [Google Account](https://myaccount.google.com/permissions)
2. **Delete bot** anytime: Send `/deletebot` to @BotFather
3. **Use test account** for development
4. **Keep `.env` private** - never share

---

## 📊 Version History

### V3 (Current) - Telegram Voice Bot
**Released:** February 2026

**New:**
- 🎤 Telegram bot with voice + text support
- 🧠 Context-aware conversation memory
- 🤖 AI-powered reply generation
- 📱 Mobile-friendly (Telegram app)
- 🔄 Whisper transcription normalization
- 📊 `/status` command for transparency
- 🗑️ `/clear` command to reset

**Features:**
- Voice message support via Groq Whisper
- Smart context tracking (remembers all read emails)
- Multi-account drafting (Gmail/iCloud auto-detection)
- Single-result auto-read ("read it" when 1 email)
- Word number support ("two" = 2)
- HTML email cleaning
- Session persistence

### V2 - MCP Email Agent
**Released:** January 2026

**New:**
- Model Context Protocol architecture
- 10 email tools (list, read, send, search, draft)
- Gmail advanced search
- Draft reply workflow
- CLI interface

### V1 - Basic Email Bot
**Released:** January 2026

**Features:**
- Simple Gmail read/send
- Basic CLI commands

---

## 🎯 Roadmap

### V4 (Planned)
- 🔊 **TTS Voice Responses** - Bot replies with voice
- 📎 **Attachment Support** - Send/receive files
- 🗓️ **Calendar Integration** - Schedule from emails
- 🔔 **Push Notifications** - Real-time email alerts
- 🌐 **Multi-language** - Support more languages
- 📊 **Analytics Dashboard** - Email insights

---

## 📄 License

MIT License - Free to use, modify, and distribute

---

## 🙏 Acknowledgments

- **Groq** - Fast LLaMA inference + Whisper API
- **Telegram** - Bot platform
- **Google** - Gmail API
- **Apple** - iCloud IMAP/SMTP
- **Anthropic** - MCP protocol inspiration

---

## 📧 Links

- **Docker Hub:** (https://hub.docker.com/repository/registry-1.docker.io/samymetref/ai-email-agent/general)
- **GitHub:** [https://github.com/predaaaasaaaaaaa](https://github.com/predaaaasaaaaaaa/ai-gmail-agent)
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
A: Groq free tier is generous. If you hit limits, wait 24h or upgrade to paid.

**Q: Can I host this on a server?**  
A: Yes! Use Docker on any VPS (AWS, DigitalOcean, etc.). Keep `.env` secure.

---

**Built with ❤️ by [Samy Metref](https://github.com/predaaaasaaaaaaa)**

⭐ **Star this repo if you find it useful!**  
💡 **Questions? Open an issue!**  
🐳 **Docker Hub:** Check latest version!  

---

**Ready to manage your emails with your voice? Get started in 10 minutes! 🚀**