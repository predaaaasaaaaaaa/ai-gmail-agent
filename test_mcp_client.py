"""
Test the MCP client connection.
"""

import asyncio
from agent.mcp_client import MCPEmailClient


async def main():
    """Test MCP connection and tool calling."""
    print("🧪 Testing MCP Client...")
    print("=" * 50)
    
    # Use async context manager - automatic cleanup!
    async with MCPEmailClient() as client:
        print("\n✅ Session established!")
        
        # Test calling a tool
        print("\n🔧 Testing tool call: list_gmail_emails")
        result = await client.call_tool(
            "list_gmail_emails",
            max_results=3
        )
        
        print("\n📧 Result:")
        if isinstance(result, list):
            for email in result:
                print(f"  - {email.get('subject', 'No subject')}")
        else:
            print(f"  {result}")
        
        print("\n✅ MCP client test passed!")
    
    # Context manager automatically cleans up here
    print("🧹 Cleanup complete!")


if __name__ == "__main__":
    asyncio.run(main())