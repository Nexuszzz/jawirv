"""
Test ReAct with tools that MUST be executed.
These queries cannot be answered without tools.
"""

import asyncio
import json
import websockets
from datetime import datetime

WS_URL = "ws://localhost:8000/ws/chat"


class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


async def test_with_tools(query: str, desc: str):
    """Test a query that requires tool execution."""
    print(f"\n{'='*70}")
    print(f"{Colors.BOLD}📝 Test: {desc}{Colors.END}")
    print(f"{Colors.DIM}Query: {query}{Colors.END}")
    print('='*70)
    
    thinking_count = 0
    action_count = 0
    tools_used = []
    
    try:
        async with websockets.connect(WS_URL, ping_interval=None) as ws:
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {"content": query}
            }))
            
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=120)
                    data = json.loads(msg)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "agent_status":
                        status = data.get("status", "")
                        message = data.get("message", "")
                        details = data.get("details", {})
                        
                        if status == "thinking":
                            thinking_count += 1
                            print(f"  {Colors.YELLOW}💭 THOUGHT #{thinking_count}:{Colors.END} {message[:60]}...")
                            
                        elif status == "executing_tool":
                            action_count += 1
                            tool_name = details.get("tool_name", "unknown")
                            tools_used.append(tool_name)
                            print(f"  {Colors.GREEN}🔧 ACTION #{action_count}:{Colors.END} {tool_name}")
                            
                        elif status == "tool_completed":
                            result_preview = details.get("result_preview", "")[:60]
                            print(f"  {Colors.MAGENTA}👀 OBSERVE:{Colors.END} {result_preview}...")
                            
                        elif status == "tool_error":
                            error = details.get("error", "")[:60]
                            print(f"  {Colors.RED}❌ ERROR:{Colors.END} {error}")
                            print(f"  {Colors.YELLOW}🔄 SELF-CORRECTION: Retrying...{Colors.END}")
                            
                    elif msg_type == "agent_response":
                        content = data.get("content", "")
                        print(f"\n  {Colors.GREEN}✅ RESPONSE:{Colors.END}")
                        # Word wrap response
                        for i in range(0, min(len(content), 200), 60):
                            print(f"     {content[i:i+60]}")
                        if len(content) > 200:
                            print("     ...")
                        
                        # Stats
                        print(f"\n  {Colors.BOLD}📊 Stats:{Colors.END}")
                        print(f"     Thoughts: {thinking_count}")
                        print(f"     Actions:  {action_count}")
                        print(f"     Tools:    {', '.join(tools_used) if tools_used else 'None'}")
                        
                        return action_count > 0
                        
                except asyncio.TimeoutError:
                    print(f"  {Colors.RED}⏰ Timeout!{Colors.END}")
                    return False
                    
    except Exception as e:
        print(f"  {Colors.RED}Error: {e}{Colors.END}")
        return False


async def main():
    """Run tests that require tool execution."""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   {Colors.BOLD}🧠 JAWIR ReAct Agent - Tool Execution Test 🧠{Colors.END}{Colors.CYAN}                           ║
║                                                                              ║
║   These queries MUST use tools - they cannot be answered from knowledge.     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    # Queries that MUST use tools (cannot be answered from knowledge)
    tests = [
        # Python - must execute to get actual result
        ("Jalankan kode Python ini: print(sum(range(1, 101)))", "Python Exec - Sum 1-100"),
        
        # Web search - needs current data
        ("Berapa nilai tukar USD ke IDR hari ini?", "Web Search - Currency Rate"),
        
        # Google Drive - needs API access
        ("List 3 file teratas di Google Drive saya", "Drive - List Files"),
        
        # Gmail - needs API access
        ("Cari email dengan subject meeting", "Gmail - Search"),
    ]
    
    results = []
    
    for query, desc in tests:
        used_tools = await test_with_tools(query, desc)
        results.append((desc, used_tools))
        await asyncio.sleep(2)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"{Colors.BOLD}📊 SUMMARY{Colors.END}")
    print('='*70)
    
    for desc, used_tools in results:
        status = f"{Colors.GREEN}✅ Used Tools{Colors.END}" if used_tools else f"{Colors.RED}❌ No Tools{Colors.END}"
        print(f"  {status} - {desc}")
    
    tools_used = sum(1 for _, used in results if used)
    print(f"\n  Total: {tools_used}/{len(results)} tests used tools")


if __name__ == "__main__":
    asyncio.run(main())
