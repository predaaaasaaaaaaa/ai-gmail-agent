"""
Email Agent Client

This is the "brain" that:
1. Takes your natural language commands
2. Connects to the MCP server
3. Uses Groq LLM to decide which tools to call
4. Executes the tools and returns results
"""

import asyncio
import json
from groq import Groq
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmailAgent:
    def __init__(self):
        """
        Initialize the email agent.
        """
        self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.session = None
        self.available_tools = []
        self.conversation_history = []
        self.client_context = None

    async def connect_to_mcp_server(self):
        """
        Connect to the MCP server.
        """
        # Get absolute path to server script
        import pathlib

        current_dir = pathlib.Path(__file__).parent.parent  # Go up to project root
        server_script = current_dir / "mcp_server" / "server.py"

        if not server_script.exists():
            raise FileNotFoundError(f"MCP server not found at: {server_script}")

        print(f"🔧 Starting MCP server: {server_script}")

        # Server parameters
        server_params = StdioServerParameters(
            command="python", args=[str(server_script)], env=None
        )

        # Connect to server
        self.client_context = stdio_client(server_params)
        read_stream, write_stream = await self.client_context.__aenter__()

        # Create and initialize session
        self.session = ClientSession(read_stream, write_stream)

        # Initialize must be called before any other operations
        init_result = await self.session.initialize()

        # Now fetch available tools
        tools_response = await self.session.list_tools()
        self.available_tools = tools_response.tools

        print(f"✅ Connected to MCP server")
        print(f"📧 Available tools: {len(self.available_tools)}")
        for tool in self.available_tools:
            print(f"   - {tool.name}")

    async def cleanup(self):
        """
        Cleanup when shutting down the agent.
        """
        if self.client_context:
            await self.client_context.__aexit__(None, None, None)

    async def process_command(self, user_input: str) -> str:
        """
        Process a user command using the LLM.
        """
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})

        # Create system prompt with available tools
        system_prompt = self._create_system_prompt()

        # Call Groq to decide what to do
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                *self.conversation_history,
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        assistant_message = response.choices[0].message.content

        self.conversation_history.append(
            {"role": "assistant", "content": assistant_message}
        )

        return assistant_message

    def _create_system_prompt(self) -> str:
        """
        Create the system prompt that tells the LLM:
        """
        tools_description = "\n".join(
            [f"- {tool.name}: {tool.description}" for tool in self.available_tools]
        )

        return f"""You are an email assistant that helps manage Gmail and iCloud emails.

You have access to these tools:
{tools_description}

When the user asks you to do something with emails:
1. Decide which tool(s) you need to call
2. Call them with the appropriate parameters
3. Present the results in a friendly, organized way

For example:
- "check my emails" → call list_gmail_emails and list_icloud_emails
- "read the email from John" → first list emails, find John's email ID, then call read_gmail_email or read_icloud_email
- "send an email to john@example.com saying hello" → call send_gmail_email with the parameters

Always be helpful and concise. Don't make up information - only use real data from the tools.
"""


# ============================================
# CLI Interface
# ============================================


async def main():
    """
    Main CLI loop for the email agent.
    """
    print("🤖 Email Agent starting...")
    print("=" * 50)

    # Initialize agent
    agent = EmailAgent()

    try:
        # Connect to MCP server
        await agent.connect_to_mcp_server()

        print("\n" + "=" * 50)
        print("✨ Agent ready! Type your commands.")
        print("💡 Examples:")
        print("   - check my gmail")
        print("   - show me unread emails")
        print("   - read the latest email")
        print("   - send an email to someone@example.com")
        print("\nType 'exit' to quit")
        print("=" * 50 + "\n")

        # Main loop
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("👋 Goodbye!")
                    break

                if not user_input:
                    continue

                # Process command
                print("🤔 Thinking...")
                response = await agent.process_command(user_input)
                print(f"\n🤖 Agent: {response}\n")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    finally:
        # Cleanup on exit
        print("🧹 Cleaning up...")
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
