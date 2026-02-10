"""
MCP Server for Email Operations
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path so we can import email_tools
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import json

# Import email handlers
from email_tools import GmailHandler, iCloudHandler

# Initialize email handlers
gmail_handler = GmailHandler(credentials_path="credentials.json")
icloud_handler = iCloudHandler()

# Create MCP server instance
app = Server("email-agent-server")

# ============================================
# TOOL DEFINITIONS
# ============================================


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Define what tools are available to MCP clients.

    Each tool has:
    - name: Unique identifier
    - description: What it does (helps AI decide when to use it)
    - inputSchema: What parameters it accepts (JSON Schema format)

    The AI reads these descriptions to decide which tool to call!
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
                        "default": 10,
                    },
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (optional)",
                        "default": "",
                    },
                },
            },
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
                        "default": 10,
                    }
                },
            },
        ),
        Tool(
            name="read_gmail_email",
            description="Read the full content of a specific Gmail email by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The Gmail message ID",
                    }
                },
                "required": ["email_id"],
            },
        ),
        Tool(
            name="read_icloud_email",
            description="Read the full content of a specific iCloud email by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The iCloud message ID",
                    }
                },
                "required": ["email_id"],
            },
        ),
        Tool(
            name="send_gmail_email",
            description="Send an email via Gmail",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {
                        "type": "string",
                        "description": "Email body (plain text)",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        ),
        Tool(
            name="send_icloud_email",
            description="Send an email via iCloud",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {
                        "type": "string",
                        "description": "Email body (plain text)",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        ),
    ]


# ============================================
# TOOL EXECUTION
# ============================================


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Execute a tool when the MCP client calls it.

    This function routes tool calls to the appropriate handler.

    Args:
        name: The tool name (e.g., "list_gmail_emails")
        arguments: The parameters passed by the client

    Returns:
        The tool result wrapped in TextContent

    How this works:
    1. Client calls a tool (e.g., "list_gmail_emails")
    2. This function receives the call
    3. Routes to the correct email handler
    4. Returns the result back to the client
    """

    try:
        # Route to appropriate handler based on tool name
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

        else:
            result = {"error": f"Unknown tool: {name}"}

        # Convert result to JSON string and wrap in TextContent
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


# ============================================
# SERVER STARTUP
# ============================================


async def main():
    """
    Start the MCP server.

    Uses stdio (standard input/output) for communication.
    This means the server communicates via command line I/O.

    The client will talk to this server by:
    - Sending JSON-RPC requests to stdin
    - Reading JSON-RPC responses from stdout
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
