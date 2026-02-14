# 🤖 AI Email Agent with MCP - V2

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-Enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://hub.docker.com/r/samymetref/ai-email-agent)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent AI email assistant powered by Groq's LLaMA 3.3 70B and Model Context Protocol (MCP). Manage Gmail and iCloud emails using natural language commands.

## ✨ Features

### Core Capabilities
- ✅ **Read Emails** - Access Gmail and iCloud messages
- ✅ **Send Emails** - Compose and send via natural language
- ✅ **Advanced Search** - Find emails by sender, subject, date, and more
- ✅ **Draft Replies** - AI-generated replies with approval workflow
- ✅ **MCP Architecture** - Modular, reusable tool system
- ✅ **Dockerized** - One-command deployment

### V2 New Features 🆕
- 🔍 **Email Search**
  - Gmail: Full query syntax (`from:`, `subject:`, `after:`, `is:unread`, `has:attachment`)
  - iCloud: Basic sender search
  - Natural language queries: "find emails from john about meetings"

- ✉️ **Smart Draft Replies**
  - AI generates professional responses
  - Preview before sending
  - Approval required (no accidental sends)
  - Example: "draft a reply to John's email saying I'll attend the meeting"

## 🏗️ Architecture
```
┌─────────────┐
│    You      │
└──────┬──────┘
       │ Natural language
       ▼
┌─────────────────────┐
│   Agent (Groq AI)   │ ◄── Decides actions
└──────┬──────────────┘
       │ Tool calls
       ▼
┌─────────────────────┐
│    MCP Client       │ ◄── Protocol layer
└──────┬──────────────┘
       │ JSON-RPC
       ▼
┌─────────────────────┐
│    MCP Server       │ ◄── Exposes email tools
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Email Handlers     │ ◄── Gmail API + iCloud IMAP/SMTP
└─────────────────────┘
```

## 📁 Project Structure
```
ai-gmail-agent/
├── agent/
│   ├── client.py          # Main agent with Groq integration
│   └── mcp_client.py      # MCP client wrapper
├── mcp_server/
│   ├── server.py          # MCP server (exposes 10+ email tools)
│   └── email_tools.py     # Gmail & iCloud handlers
├── .env                   # API keys (not committed)
├── credentials.json       # Gmail OAuth (not committed)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🚀 Quick Start

### Option 1: Docker Hub (Recommended)

**Pull and run the pre-built image:**
```bash
# Pull latest version
docker pull samymetref/ai-email-agent:latest

# Windows PowerShell
docker run -it --rm `
  -v ${PWD}/credentials.json:/app/credentials.json:ro `
  -v ${PWD}/token.pickle:/app/token.pickle `
  -v ${PWD}/.env:/app/.env:ro `
  samymetref/ai-email-agent:latest

# Linux/Mac
docker run -it --rm \
  -v $(pwd)/credentials.json:/app/credentials.json:ro \
  -v $(pwd)/token.pickle:/app/token.pickle \
  -v $(pwd)/.env:/app/.env:ro \
  samymetref/ai-email-agent:latest
```

### Option 2: Docker Compose (Local Build)
```bash
# Clone repository
git clone https://github.com/samymetref/ai-gmail-agent
cd ai-gmail-agent

# Build and run
docker-compose build
docker-compose run --rm email-agent
```

### Option 3: Python (Without Docker)
```bash
# Clone and setup
git clone https://github.com/samymetref/ai-gmail-agent
cd ai-gmail-agent

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run
python agent/client.py
```

## ⚙️ Setup Requirements

### Prerequisites

Before running, you need:

1. **Gmail OAuth Credentials** (one-time setup, ~15 min)
2. **Groq API Key** (free at [console.groq.com](https://console.groq.com))
3. **iCloud App-Specific Password** (if using iCloud)

### Step 1: Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Gmail API**
4. Create **OAuth 2.0 Client ID** (Desktop app)
5. Download credentials → save as `credentials.json`
6. Configure OAuth consent screen
7. Add yourself as test user

[Detailed Guide](https://developers.google.com/gmail/api/quickstart/python)

### Step 2: Get Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create API key
4. Copy it

### Step 3: iCloud Setup (Optional)

1. Go to [appleid.apple.com](https://appleid.apple.com)
2. Security → App-Specific Passwords
3. Generate password for "Email Agent"
4. Copy the password

### Step 4: Create `.env` File

Create `.env` in project root:
```env
# Groq API
GROQ_API_KEY=gsk_your_groq_api_key_here

# iCloud (optional)
ICLOUD_EMAIL=your-email@icloud.com
ICLOUD_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

## 💬 Usage Examples

### Basic Commands
```bash
You: check my gmail
You: show me my icloud emails
You: read my last email
You: send an email to john@example.com saying "Meeting at 3pm"
```

### Advanced Search (V2)
```bash
You: find emails from john@example.com
You: search for emails about "project"
You: show me unread emails from last week
You: find emails with attachments from sarah
You: search for emails after 2024/01/01 about meetings
```

### Draft Replies (V2)
```bash
You: draft a reply to John's email
Agent: [Shows draft]
       Should I send this? (yes/no/edit)
You: yes
Agent: ✅ Email sent!

# Or with context:
You: draft a reply to the email from Sarah saying I'll attend the meeting
Agent: [Generates professional reply]
       Should I send this?
You: yes
```

### Gmail Search Syntax

Supported Gmail query operators:
- `from:email@example.com` - emails from sender
- `to:email@example.com` - emails to recipient
- `subject:keyword` - subject contains keyword
- `after:YYYY/MM/DD` - emails after date
- `before:YYYY/MM/DD` - emails before date
- `is:unread` - only unread emails
- `is:read` - only read emails
- `has:attachment` - has attachments
- Combine: `from:john subject:meeting is:unread`

## 🛠️ Tech Stack

- **Python 3.11** - Core language
- **MCP (Model Context Protocol)** - Tool architecture
- **Groq API** - LLaMA 3.3 70B for AI reasoning
- **Gmail API** - Google email integration
- **IMAP/SMTP** - iCloud email access
- **Docker** - Containerization

## 🧪 Development

### Run Tests
```bash
# Test email handlers
python test_email.py

# Test MCP client
python test_mcp_client.py
```

### Project Commands
```bash
# Run locally
python agent/client.py

# Run with Docker
docker-compose run --rm email-agent

# Rebuild Docker image
docker-compose build

# Push to Docker Hub
docker-compose build
docker tag ai-gmail-agent-email-a:latest samymetref/ai-email-agent:latest
docker push samymetref/ai-email-agent:latest
```

## 🐛 Troubleshooting

### Gmail OAuth Error

**Problem:** "Access denied" when authenticating

**Solution:**
1. Go to Google Cloud Console
2. OAuth consent screen → Test users
3. Add your Gmail address
4. Try again

### iCloud Login Failed

**Problem:** "Authentication failed"

**Solution:**
- Use app-specific password (not regular password)
- Verify credentials in `.env` file
- Check iCloud account status

### Docker Issues

**Problem:** Container won't start

**Solution:**
```bash
# Ensure Docker Desktop is running
# Check files exist:
ls credentials.json .env

# Clear cache and rebuild:
docker-compose build --no-cache
```

## 📦 MCP Tools Available

The agent has access to these MCP tools:

| Tool | Description |
|------|-------------|
| `list_gmail_emails` | Fetch recent Gmail messages |
| `list_icloud_emails` | Fetch recent iCloud messages |
| `read_gmail_email` | Read full Gmail content |
| `read_icloud_email` | Read full iCloud content |
| `send_gmail_email` | Send via Gmail |
| `send_icloud_email` | Send via iCloud |
| `search_gmail` | Advanced Gmail search |
| `search_icloud` | Search iCloud by sender |
| `draft_gmail_reply` | Draft Gmail reply (needs approval) |
| `draft_icloud_reply` | Draft iCloud reply (needs approval) |

## 🔐 Security & Privacy

- ✅ Credentials stored locally (never in Docker image)
- ✅ OAuth tokens encrypted by Google
- ✅ API keys in `.env` (gitignored)
- ✅ Draft approval required (no auto-send)
- ✅ All data processed locally

**Never committed to Git:**
- `credentials.json`
- `token.pickle`
- `.env`

## 🚧 Roadmap

### V3 (Planned)
- [ ] Telegram bot integration
- [ ] Voice message support
- [ ] Email templates
- [ ] Attachment handling
- [ ] Calendar integration
- [ ] Multi-account support
- [ ] Web UI

## 📊 Changelog

### V2.0 (February 2026)
- ✨ Added advanced email search (Gmail query syntax)
- ✨ Added draft reply feature with approval workflow
- 🔍 Search by sender, subject, date, attachments
- ✉️ AI-generated professional replies
- 🛡️ Safety: Approval required before sending

### V1.0 (February 2026)
- 🎉 Initial release
- ✅ Gmail & iCloud integration
- ✅ MCP architecture
- ✅ Groq AI integration
- ✅ Docker deployment

## 📄 License

MIT License - Free to use and modify

## 🙏 Acknowledgments

- **Groq** - Fast LLaMA inference
- **Google** - Gmail API
- **ICloud** - IMAP/SMTP

## 📧 Links

- **Docker Hub:** (https://hub.docker.com/repository/registry-1.docker.io/samymetref/ai-email-agent/general)
- **GitHub:** [https://github.com/predaaaasaaaaaaa](https://github.com/predaaaasaaaaaaa/ai-gmail-agent)

---

**Built with ❤️ by [Samy Metref](https://github.com/predaaaasaaaaaaa)**

⭐ Star this repo if you find it useful!

💡 Questions? Open an issue!

🐳 Docker pulls: Check Docker Hub!