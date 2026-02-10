"""
MCP Client for Email Agent - Clean Version
"""

import asyncio
import sys
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPEmailClient:
    """
    MCP client that connects to the email server.
    """
    
    def __init__(self):
        self.session = None
        self.available_tools = []
        self._exit_stack = []
        
    async def __aenter__(self):
        """
        Async context manager entry.
        
        Usage:
            async with MCPEmailClient() as client:
                result = await client.call_tool("list_gmail_emails")
        """
        # Get path to server script
        project_root = Path(__file__).parent.parent
        server_script = project_root / "mcp_server" / "server.py"
        
        if not server_script.exists():
            raise FileNotFoundError(f"Server not found: {server_script}")
        
        # Configure server parameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(server_script)],
            env=None
        )
        
        # Start server (using context manager properly)
        self._stdio_context = stdio_client(server_params)
        read, write = await self._stdio_context.__aenter__()
        
        # Create session
        self._session_context = ClientSession(read, write)
        self.session = await self._session_context.__aenter__()
        
        # Initialize
        await self.session.initialize()
        
        # Get tools
        response = await self.session.list_tools()
        self.available_tools = response.tools
        
        print(f"✅ Connected to MCP server")
        print(f"📧 Available tools: {len(self.available_tools)}")
        for tool in self.available_tools:
            print(f"   - {tool.name}")
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit - cleanup.
        """
        # Cleanup in reverse order
        if self._session_context:
            await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
        if self._stdio_context:
            await self._stdio_context.__aexit__(exc_type, exc_val, exc_tb)
    
    async def call_tool(self, tool_name: str, **kwargs):
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool parameters
        
        Returns:
            Tool result (parsed from JSON)
        """
        if not self.session:
            raise RuntimeError("Client not connected. Use 'async with MCPEmailClient()' pattern")
        
        # Call the tool
        result = await self.session.call_tool(tool_name, arguments=kwargs)
        
        # Parse the result
        if result.content:
            text = result.content[0].text
            return json.loads(text)
        
        return None