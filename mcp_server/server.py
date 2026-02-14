"""
MCP Server for Email Operations
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import json
from email_tools import GmailHandler, iCloudHandler

# Initialize email handlers
gmail_handler = GmailHandler(credentials_path='credentials.json')
icloud_handler = iCloudHandler()

# Create MCP server
app = Server("email-agent-server")

# ============================================
# TOOL DEFINITIONS
# ============================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Define available tools for MCP clients.
    
    The AI will read these descriptions to decide which tool to call.
    """
    return [
        Tool(
            name="list_gmail_emails",
            description="Fetch recent emails from Gmail. Can filter by search query (e.g., 'is:unread', 'from:someone@example.com')",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "number",
                        "description": "Number of emails to fetch (default: 10)",
                        "default": 10
                    },
                    "query": {
                        "type": "string", 
                        "description": "Gmail search query (optional)",
                        "default": ""
                    }
                }
            }
        ),
        Tool(
            name="list_icloud_emails",
            description="Fetch recent emails from iCloud/Apple Mail",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "number",
                        "description": "Number of emails to fetch (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="read_gmail_email",
            description="Read the full content of a specific Gmail email by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The Gmail message ID"
                    }
                },
                "required": ["email_id"]
            }
        ),
        Tool(
            name="read_icloud_email",
            description="Read the full content of a specific iCloud email by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The iCloud message ID"
                    }
                },
                "required": ["email_id"]
            }
        ),
        Tool(
            name="send_gmail_email",
            description="Send an email via Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body (plain text)"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        ),
        Tool(
            name="send_icloud_email",
            description="Send an email via iCloud",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body (plain text)"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        ),
         Tool(
            name="search_gmail",
            description="Search Gmail emails with advanced filters. Supports: from:email, subject:text, after:YYYY/MM/DD, before:YYYY/MM/DD, is:unread, has:attachment. Combine multiple filters with spaces.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'from:john@example.com subject:meeting', 'is:unread after:2024/01/01')"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["query"]
            }
        ),
        
        Tool(
            name="search_icloud",
            description="Search iCloud emails. Note: iCloud IMAP has limited search - best for 'from:' searches. For complex queries, use Gmail.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sender": {
                        "type": "string",
                        "description": "Email address or name to search for in 'From' field"
                    },
                    "max_results": {
                        "type": "number",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20
                    }
                },
                "required": ["sender"]
            }
        ),

        Tool(
            name="draft_gmail_reply",
            description="Draft a reply to a specific Gmail email. Returns the draft content for user approval before sending.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The Gmail message ID to reply to"
                    },
                    "reply_body": {
                        "type": "string",
                        "description": "The body text of the reply email"
                    }
                },
                "required": ["email_id", "reply_body"]
            }
        ),
        
        Tool(
            name="draft_icloud_reply",
            description="Draft a reply to a specific iCloud email. Returns the draft content for user approval before sending.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The iCloud message ID to reply to"
                    },
                    "reply_body": {
                        "type": "string",
                        "description": "The body text of the reply email"
                    }
                },
                "required": ["email_id", "reply_body"]
            }
        )
    ]

# ============================================
# TOOL EXECUTION
# ============================================

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Execute a tool when the MCP client calls it.
    
    Routes tool calls to the appropriate email handler.
    """
    try:
        # Route to appropriate handler
        if name == "list_gmail_emails":
            max_results = arguments.get("max_results", 10)
            query = arguments.get("query", "")
            result = gmail_handler.list_emails(max_results=max_results, query=query)
            
        elif name == "list_icloud_emails":
            max_results = arguments.get("max_results", 10)
            result = icloud_handler.list_emails(max_results=max_results)
            
        elif name == "read_gmail_email":
            email_id = arguments["email_id"]
            result = gmail_handler.read_email(email_id)
            
        elif name == "read_icloud_email":
            email_id = arguments["email_id"]
            result = icloud_handler.read_email(email_id)
            
        elif name == "send_gmail_email":
            to = arguments["to"]
            subject = arguments["subject"]
            body = arguments["body"]
            result = gmail_handler.send_email(to, subject, body)
            
        elif name == "send_icloud_email":
            to = arguments["to"]
            subject = arguments["subject"]
            body = arguments["body"]
            result = icloud_handler.send_email(to, subject, body)
        
        elif name == "search_gmail":
            query = arguments["query"]
            max_results = arguments.get("max_results", 20)
            result = gmail_handler.search_emails(query=query, max_results=max_results)
            
        elif name == "search_icloud":
            sender = arguments["sender"]
            max_results = arguments.get("max_results", 20)
            result = icloud_handler.search_emails_by_sender(sender=sender, max_results=max_results)
        
        elif name == "draft_gmail_reply":
            email_id = arguments["email_id"]
            reply_body = arguments["reply_body"]
            result = gmail_handler.draft_reply(email_id, reply_body)
            
        elif name == "draft_icloud_reply":
            email_id = arguments["email_id"]
            reply_body = arguments["reply_body"]
            result = icloud_handler.draft_reply(email_id, reply_body)
            
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # Return result as JSON
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]

# ============================================
# SERVER STARTUP
# ============================================

async def main():
    """
    Start the MCP server using stdio for communication.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())