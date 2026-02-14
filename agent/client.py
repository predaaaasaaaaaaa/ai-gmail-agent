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
        self.pending_draft = None
    
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
        
        Handles draft approvals specially.
        """
        # Check if user is responding to a pending draft
        if self.pending_draft:
            user_response = user_input.lower().strip()
            
            if user_response in ['yes', 'y', 'send', 'send it']:
                # User approved - send the email!
                draft = self.pending_draft
                self.pending_draft = None 
                
                # Determine which account to use
                if 'gmail' in draft.get('account', 'gmail'):
                    result = await self.mcp_client.call_tool(
                        "send_gmail_email",
                        to=draft['to'],
                        subject=draft['subject'],
                        body=draft['body']
                    )
                else:
                    result = await self.mcp_client.call_tool(
                        "send_icloud_email",
                        to=draft['to'],
                        subject=draft['subject'],
                        body=draft['body']
                    )
                
                if 'error' in result:
                    return f"❌ Failed to send: {result['error']}"
                else:
                    return f"✅ Email sent to {draft['to']}!"
            
            elif user_response in ['no', 'n', 'cancel', 'abort']:
                # User cancelled
                self.pending_draft = None
                return "❌ Draft cancelled. Email not sent."
            
            elif user_response in ['edit', 'modify', 'change']:
                # User wants to edit (future feature)
                self.pending_draft = None
                return "✏️ Draft editing not implemented yet. Please draft a new reply with your changes."
            
            else:
                # User said something else while draft is pending
                return "⚠️ You have a pending draft. Please respond with:\n- 'yes' to send\n- 'no' to cancel\n- 'edit' to modify (not implemented yet)"
        
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

IMPORTANT INSTRUCTIONS:
1. For draft replies: Use draft_gmail_reply or draft_icloud_reply tools. The agent will handle user approval.
2. When user says "draft a reply to X", first find the email, then use the draft tool with AI-generated reply text.
3. For searches: Use search_gmail with Gmail query syntax (from:, subject:, is:unread, etc.)
4. Always be helpful and professional in generated email text.

When the user asks you to do something, respond with a JSON object:
{{
    "action": "call_tool" or "respond",
    "tool": "tool_name",
    "params": {{}},
    "message": "what to tell the user"
}}

Examples:
User: "draft a reply to john's email"
{{"action": "call_tool", "tool": "search_gmail", "params": {{"query": "from:john", "max_results": 1}}, "message": "Finding John's email..."}}
Then: {{"action": "call_tool", "tool": "draft_gmail_reply", "params": {{"email_id": "xxx", "reply_body": "AI-generated professional reply"}}, "message": "Drafting reply..."}}

Always respond with valid JSON only."""

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
                
                # Check if this is a draft reply result
                if isinstance(tool_result, dict) and tool_result.get('status') == 'draft_created':
                    # Store the draft and ask for approval
                    self.pending_draft = {
                        'to': tool_result['to'],
                        'subject': tool_result['subject'],
                        'body': tool_result['body'],
                        'account': 'gmail' if 'gmail' in command["tool"] else 'icloud'
                    }
                    
                    final_response = f"""📧 Draft Reply Created:

To: {tool_result['to']}
Subject: {tool_result['subject']}

{tool_result['body']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Should I send this? 
- Type 'yes' to send
- Type 'no' to cancel
- Type 'edit' to modify"""
                
                # Format regular tool results
                elif isinstance(tool_result, list):
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
                # Ctrl+C during input
                print("\n\n👋 Goodbye!")
                break
            
            except asyncio.CancelledError:
                # Async task cancelled (Ctrl+C during execution)
                print("\n\n👋 Goodbye!")
                break
    
    except KeyboardInterrupt:
        # Ctrl+C during startup
        print("\n\n👋 Goodbye!")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always cleanup MCP
        print("🧹 Cleaning up...")
        try:
            await agent.cleanup_mcp()
            print("✅ Cleanup complete!")
        except Exception:
            pass  # Suppress cleanup errors


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Final catch for any Ctrl+C
        print("\n👋 Exited cleanly!")


if __name__ == "__main__":
    asyncio.run(main())