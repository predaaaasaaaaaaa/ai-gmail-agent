"""
Email Agent Client - Simplified Version
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

# Load environment
load_dotenv()

class EmailAgent:
    def __init__(self):
        """Simple email agent without MCP for now."""
        self.groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.conversation_history = []
        
        # Import email handlers directly (no MCP for v1)
        sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_server"))
        from email_tools import GmailHandler, iCloudHandler
        
        print("🔧 Initializing email handlers...")
        self.gmail = GmailHandler(credentials_path='credentials.json')
        self.icloud = iCloudHandler()
        print("✅ Email handlers ready")
    
    def execute_tool(self, tool_name: str, **kwargs):
        """
        Execute an email tool.
        
        Available tools:
        - list_gmail_emails
        - list_icloud_emails
        - read_gmail_email
        - read_icloud_email
        - send_gmail_email
        - send_icloud_email
        """
        try:
            if tool_name == "list_gmail_emails":
                return self.gmail.list_emails(
                    max_results=kwargs.get('max_results', 10),
                    query=kwargs.get('query', '')
                )
            
            elif tool_name == "list_icloud_emails":
                return self.icloud.list_emails(
                    max_results=kwargs.get('max_results', 10)
                )
            
            elif tool_name == "read_gmail_email":
                return self.gmail.read_email(kwargs['email_id'])
            
            elif tool_name == "read_icloud_email":
                return self.icloud.read_email(kwargs['email_id'])
            
            elif tool_name == "send_gmail_email":
                return self.gmail.send_email(
                    kwargs['to'],
                    kwargs['subject'],
                    kwargs['body']
                )
            
            elif tool_name == "send_icloud_email":
                return self.icloud.send_email(
                    kwargs['to'],
                    kwargs['subject'],
                    kwargs['body']
                )
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def process_command(self, user_input: str) -> str:
        """
        Process user command with Groq.
        
        The LLM will tell us which tools to call in JSON format.
        """
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # System prompt
        system_prompt = """You are an email assistant. You have these tools available:

1. list_gmail_emails(max_results, query) - List Gmail emails
2. list_icloud_emails(max_results) - List iCloud emails
3. read_gmail_email(email_id) - Read full Gmail email
4. read_icloud_email(email_id) - Read full iCloud email
5. send_gmail_email(to, subject, body) - Send Gmail
6. send_icloud_email(to, subject, body) - Send iCloud email

When the user asks you to do something, respond with a JSON object:
{
    "action": "call_tool" or "respond",
    "tool": "tool_name",
    "params": {...},
    "message": "what to tell the user"
}

Examples:
User: "check my gmail"
Response: {"action": "call_tool", "tool": "list_gmail_emails", "params": {"max_results": 10}, "message": "Fetching your Gmail..."}

User: "hello"
Response: {"action": "respond", "message": "Hi! I can help you manage your Gmail and iCloud emails. What would you like to do?"}

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
        
        # Try to parse as JSON
        try:
            command = json.loads(assistant_response)
            
            if command.get("action") == "call_tool":
                # Execute the tool
                tool_result = self.execute_tool(
                    command["tool"],
                    **command.get("params", {})
                )
                
                # Format result for user
                if isinstance(tool_result, list):
                    result_text = f"{command.get('message', 'Results:')}\n\n"
                    for i, item in enumerate(tool_result[:5], 1):
                        result_text += f"{i}. From: {item.get('from', 'Unknown')}\n"
                        result_text += f"   Subject: {item.get('subject', 'No subject')}\n"
                        result_text += f"   ID: {item.get('id', 'N/A')}\n\n"
                    
                    final_response = result_text
                else:
                    final_response = f"{command.get('message', '')}\n\n{json.dumps(tool_result, indent=2)}"
            else:
                final_response = command.get("message", assistant_response)
        
        except json.JSONDecodeError:
            # If not JSON, just return the response
            final_response = assistant_response
        
        self.conversation_history.append({
            "role": "assistant",
            "content": final_response
        })
        
        return final_response


def main():
    """Simple synchronous main loop."""
    print("🤖 Email Agent starting...")
    print("=" * 50)
    
    try:
        agent = EmailAgent()
        
        print("\n" + "=" * 50)
        print("✨ Agent ready!")
        print("💡 Try: 'check my gmail' or 'list my icloud emails'")
        print("Type 'exit' to quit")
        print("=" * 50 + "\n")
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("🤔 Processing...")
            response = agent.process_command(user_input)
            print(f"\n🤖 Agent:\n{response}\n")
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()