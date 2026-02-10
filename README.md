# 🤖 AI Email Agent with MCP

A fully-functional AI email agent that manages Gmail and iCloud emails using the **Model Context Protocol (MCP)**, powered by Groq's LLaMA 3.3 70B model.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![MCP](https://img.shields.io/badge/MCP-Enabled-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 What This Does

This AI agent can:
- ✅ **Read emails** from both Gmail and iCloud
- ✅ **Send emails** through Gmail or iCloud
- ✅ **Understand natural language** commands (e.g., "check my gmail", "send an email to john@example.com")
- ✅ **Use MCP architecture** for modularity and reusability
- ✅ **Process commands intelligently** using Groq's LLaMA model

## 🏗️ Architecture
```
┌─────────────┐
│    You      │
└──────┬──────┘
       │ Natural language commands
       ▼
┌─────────────────────┐
│   Agent (Groq AI)   │ ◄── Decides what to do
└──────┬──────────────┘
       │ Tool calls
       ▼
┌─────────────────────┐
│    MCP Client       │ ◄── Communicates with server
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
│   ├── __init__.py
│   ├── client.py          # Main agent with Groq integration
│   └── mcp_client.py      # MCP client wrapper
├── mcp_server/
│   ├── __init__.py
│   ├── server.py          # MCP server exposing email tools
│   └── email_tools.py     # Gmail & iCloud handlers
├── .env                   # API keys & credentials (DO NOT COMMIT)
├── .gitignore
├── credentials.json       # Gmail OAuth credentials (DO NOT COMMIT)
├── requirements.txt
├── test_email.py          # Test email handlers
├── test_mcp_client.py     # Test MCP connection
└── README.md
```

## 🚀 Setup Guide

### Prerequisites

- Python 3.10 or higher
- Gmail account
- iCloud/Apple Mail account
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Step 1: Clone & Install Dependencies
```bash
# Clone the repository
git clone <your-repo-url>
cd ai-gmail-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Gmail API Setup

1. **Go to [Google Cloud Console](https://console.cloud.google.com/)**
2. **Create a new project** (e.g., "EmailAgent")
3. **Enable Gmail API:**
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app"
   - Download the JSON file
   - **Rename it to `credentials.json`** and place it in project root
5. **Configure OAuth Consent Screen:**
   - Go to "APIs & Services" → "OAuth consent screen"
   - User type: **External**
   - Fill in required fields (app name, email)
   - **Add test users:** Add your Gmail address
   - Scopes: The code will request appropriate scopes automatically

### Step 3: iCloud App-Specific Password

Since iCloud doesn't have an API, we use IMAP/SMTP with app-specific passwords:

1. Go to [appleid.apple.com](https://appleid.apple.com/)
2. Sign in
3. Navigate to **"Sign-In and Security"** → **"App-Specific Passwords"**
4. Click **"Generate an app-specific password"**
5. Name it "Email Agent"
6. **Copy the generated password** (format: `xxxx-xxxx-xxxx-xxxx`)

### Step 4: Environment Variables

Create a `.env` file in the project root:
```env
# iCloud credentials
ICLOUD_EMAIL=your-email@icloud.com
ICLOUD_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Groq API key
GROQ_API_KEY=gsk_your_groq_api_key_here
```

**Get your Groq API key:**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Navigate to API Keys
4. Create a new key
5. Copy it to your `.env` file

### Step 5: Security - .gitignore

**CRITICAL:** Create `.gitignore` to prevent committing sensitive files:
```gitignore
# Credentials and tokens
credentials.json
token.pickle
*.pickle

# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
.venv/

# IDE
.vscode/
.idea/
```

### Step 6: Test Components

**Test email handlers (no MCP):**
```bash
python test_email.py
```

Expected output:
- Lists 3 recent emails from Gmail
- Lists 3 recent emails from iCloud

**Test MCP client:**
```bash
python test_mcp_client.py
```

Expected output:
- Connects to MCP server
- Lists available tools
- Fetches Gmail emails via MCP
- Clean exit with no errors

### Step 7: Run the Agent
```bash
python agent/client.py
```

**Example commands:**
```
You: check my gmail
You: show me unread emails from iCloud
You: read email with ID <email-id>
You: send an email to john@example.com with subject "Hello" saying "Hi John!"
```

**To exit:** Type `exit`, `quit`, `bye`, or press `Ctrl+C`

## 🛠️ How MCP Works

**Model Context Protocol (MCP)** is a standardized way for AI applications to connect to external tools and data sources.

### Why MCP?

- ✅ **Modularity:** Email handlers are separate from the agent
- ✅ **Reusability:** The MCP server can be used by other projects
- ✅ **Scalability:** Easy to add more tools (calendar, tasks, etc.)
- ✅ **Industry Standard:** Used by Claude, other AI platforms

### MCP Flow

1. **Server starts** and exposes tools (list_gmail_emails, send_email, etc.)
2. **Client connects** via stdio (standard input/output)
3. **Agent asks Groq** what to do with user's command
4. **Groq responds** with which tool to call
5. **Client calls tool** via MCP protocol (JSON-RPC)
6. **Server executes** the tool and returns result
7. **Agent formats** and shows result to user

## 🐛 Troubleshooting

### OAuth Error: "Access Denied"

**Problem:** Google says the app isn't verified.

**Solution:**
1. Go to Google Cloud Console
2. "APIs & Services" → "OAuth consent screen"
3. Scroll to "Test users"
4. Add your Gmail address
5. Try authenticating again

### iCloud Login Failed

**Problem:** "Login failed" error for iCloud.

**Solution:**
1. Make sure you're using an **app-specific password**, not your regular password
2. Check that `ICLOUD_EMAIL` and `ICLOUD_PASSWORD` are correct in `.env`
3. If using 2FA, you MUST use app-specific password

### MCP Server Won't Start

**Problem:** Server starts but client can't connect.

**Solution:**
1. Make sure you're running from project root
2. Check that `mcp_server/server.py` exists
3. Verify virtual environment is activated
4. Try running server manually: `python mcp_server/server.py` (should wait silently)

### Import Errors

**Problem:** `ModuleNotFoundError` or import issues.

**Solution:**
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (must be 3.10+)

### Groq API Errors

**Problem:** "Invalid API key" or rate limit errors.

**Solution:**
1. Verify `GROQ_API_KEY` in `.env` is correct
2. Check you have credits at [console.groq.com](https://console.groq.com)
3. Free tier has rate limits - wait a moment if hit

## 📦 Dependencies
```
mcp[cli]>=1.0.0                  # Model Context Protocol
google-auth-oauthlib>=1.0.0      # Gmail OAuth
google-auth-httplib2>=0.1.0      # Gmail authentication
google-api-python-client>=2.0.0  # Gmail API
groq>=0.4.0                      # Groq API client
python-dotenv>=1.0.0             # Environment variables
```

## 🎓 What I Learned

New Skills this project taught me:

1. **Async Python:** Managing async context managers, coroutines, and event loops
2. **Email Protocols:** Differences between API (Gmail) and IMAP/SMTP (iCloud)
3. **Error Handling:** Proper cleanup and graceful shutdowns in async code

## 🚧 Known Limitations

- Gmail API has daily quotas (10,000 requests/day for free tier)
- iCloud IMAP is slower than Gmail API
- Groq free tier has rate limits
- No email threading/conversation view yet
- No attachment support yet

## 🔮 Future Enhancements (v2)

- [ ] Telegram bot integration with voice messages
- [ ] Docker containerization
- [ ] Email drafting and templates
- [ ] Attachment handling
- [ ] Email search and filters
- [ ] Calendar integration
- [ ] Multi-account support
- [ ] Web UI

## 📄 License

MIT License - feel free to use this project for learning or building your own email agent!

## 🙏 Acknowledgments

- **Groq** for fast LLaMA inference
- **Google** for Gmail API
- Hours of debugging that taught me everything 😅

## 📧 Contact

Built with ❤️ by Samy Metref

- GitHub: [@predaaaasaaaaaaa](https://github.com/predaaaasaaaaaaa)
- Email: metref.samypro@gmail.com

---

⭐ **Star this repo if you found it helpful!**