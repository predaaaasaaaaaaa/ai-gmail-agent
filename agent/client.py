"""
Email Agent Client - MCP Powered Version
"""

import asyncio
import json
import os
from groq import Groq
from dotenv import load_dotenv
from mcp_client import MCPEmailClient

# Load environment
load_dotenv()


class EmailAgent:
    """
    Email agent powered by MCP and Groq.
    
    Architecture:
    You → Agent → Groq (decides what to do) → MCP Client → MCP Server → Email handlers
    """
    
    def __init__(self):
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.mcp_client = None
        self.conversation_history = []
        self.available_tools = []
    
    async def connect_mcp(self):
        """Connect to MCP server and get available tools."""
        self.mcp_client = await MCPEmailClient().__aenter__()
        self.available_tools = self.mcp_client.available_tools
        return self.mcp_client
    
    async def cleanup_mcp(self):
        """Cleanup MCP connection."""
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)
    
    async def process_command(self, user_input: str) -> str:
        """
        Process user command with Groq + MCP.
        
        Flow:
        1. User asks something
        2. Groq decides which tool to call
        3. We call it via MCP
        4. Return formatted result
        """
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Build tool descriptions for Groq
        tools_desc = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.available_tools
        ])
        
        # System prompt
        system_prompt = f"""You are an email assistant with access to these MCP tools:

{tools_desc}

When the user asks you to do something, respond with a JSON object:
{{
    "action": "call_tool" or "respond",
    "tool": "tool_name",
    "params": {{}},
    "message": "what to tell the user"
}}

Examples:
User: "check my gmail"
{{"action": "call_tool", "tool": "list_gmail_emails", "params": {{"max_results": 10}}, "message": "Fetching your Gmail..."}}

User: "hello"
{{"action": "respond", "message": "Hi! I can help you manage your emails. What would you like to do?"}}

Always respond with valid JSON only. Be helpful and concise."""

        # Call Groq
        response = self.groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                *self.conversation_history
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        assistant_response = response.choices[0].message.content
        
        # Parse and execute
        try:
            command = json.loads(assistant_response)
            
            if command.get("action") == "call_tool":
                # Call MCP tool
                tool_result = await self.mcp_client.call_tool(
                    command["tool"],
                    **command.get("params", {})
                )
                
                # Format result
                if isinstance(tool_result, list):
                    result_text = f"{command.get('message', 'Results:')}\n\n"
                    for i, item in enumerate(tool_result[:10], 1):
                        result_text += f"{i}. From: {item.get('from', 'Unknown')}\n"
                        result_text += f"   Subject: {item.get('subject', 'No subject')}\n"
                        result_text += f"   ID: {item.get('id', 'N/A')}\n\n"
                    
                    final_response = result_text
                else:
                    final_response = f"{command.get('message', '')}\n\n{json.dumps(tool_result, indent=2)}"
            else:
                final_response = command.get("message", assistant_response)
        
        except json.JSONDecodeError:
            final_response = assistant_response
        
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })
        
        return final_response


async def main():
    """Async main loop for the MCP-powered agent."""
    print("🤖 Email Agent starting (MCP Mode)...")
    print("=" * 50)
    
    agent = EmailAgent()
    
    try:
        # Connect to MCP
        await agent.connect_mcp()
        
        print("\n" + "=" * 50)
        print("✨ Agent ready!")
        print("💡 Try: 'check my gmail' or 'list my icloud emails'")
        print("Type 'exit' to quit")
        print("=" * 50 + "\n")
        
        # Main loop
        while True:
            try:
                # Get input (run in executor to not block async)
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(
                    None, 
                    lambda: input("You: ").strip()
                )
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                print("🤔 Processing...")
                response = await agent.process_command(user_input)
                print(f"\n🤖 Agent:\n{response}\n")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
    
    finally:
        # Cleanup MCP
        print("🧹 Cleaning up...")
        await agent.cleanup_mcp()


if __name__ == "__main__":
    asyncio.run(main())