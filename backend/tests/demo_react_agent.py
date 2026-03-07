"""
JAWIR ReAct Agent - Self-Correction Demo
=========================================
Demonstrates the ReAct agent's ability to:
1. Reason before acting (THOUGHT)
2. Execute tools (ACTION)
3. Analyze results (OBSERVATION)
4. Learn from errors and retry (SELF-CORRECTION)
"""

import asyncio
import json
import websockets
from datetime import datetime

WS_URL = "ws://localhost:8000/ws/chat"


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def print_box(title, content, color=Colors.CYAN):
    """Print a boxed message."""
    width = 70
    print(f"\n{color}╭{'─' * width}╮{Colors.END}")
    print(f"{color}│ {Colors.BOLD}{title:^{width-2}}{Colors.END}{color} │{Colors.END}")
    print(f"{color}├{'─' * width}┤{Colors.END}")
    for line in content.split('\n'):
        while len(line) > width - 4:
            print(f"{color}│ {line[:width-4]} │{Colors.END}")
            line = line[width-4:]
        print(f"{color}│ {line:{width-2}} │{Colors.END}")
    print(f"{color}╰{'─' * width}╯{Colors.END}")


async def demo_react_loop(query: str, title: str):
    """Demo ReAct loop with detailed output."""
    print_box(title, f"Query: {query}", Colors.BLUE)
    
    thinking_count = 0
    action_count = 0
    observation_count = 0
    
    try:
        async with websockets.connect(WS_URL, ping_interval=None) as ws:
            await ws.send(json.dumps({
                "type": "user_message",
                "data": {"content": query}
            }))
            
            print(f"\n{Colors.CYAN}┌─ ReAct Loop Started ────────────────────────────────────────┐{Colors.END}")
            
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
                            print(f"{Colors.CYAN}│{Colors.END}")
                            print(f"{Colors.CYAN}│ {Colors.YELLOW}💭 THOUGHT #{thinking_count}:{Colors.END}")
                            print(f"{Colors.CYAN}│    {Colors.DIM}{message}{Colors.END}")
                            
                        elif status == "executing_tool":
                            action_count += 1
                            tool_name = details.get("tool_name", "unknown")
                            tool_args = details.get("args", {})
                            print(f"{Colors.CYAN}│{Colors.END}")
                            print(f"{Colors.CYAN}│ {Colors.GREEN}🔧 ACTION #{action_count}:{Colors.END}")
                            print(f"{Colors.CYAN}│    Tool: {Colors.BOLD}{tool_name}{Colors.END}")
                            if tool_args:
                                args_str = str(tool_args)[:50]
                                print(f"{Colors.CYAN}│    Args: {Colors.DIM}{args_str}...{Colors.END}")
                            
                        elif status == "tool_completed":
                            observation_count += 1
                            result_preview = details.get("result_preview", "")[:100]
                            print(f"{Colors.CYAN}│ {Colors.MAGENTA}👀 OBSERVATION #{observation_count}:{Colors.END}")
                            print(f"{Colors.CYAN}│    {Colors.DIM}Result: {result_preview}...{Colors.END}")
                            
                        elif status == "tool_error":
                            error = details.get("error", "Unknown error")
                            print(f"{Colors.CYAN}│ {Colors.RED}❌ ERROR:{Colors.END}")
                            print(f"{Colors.CYAN}│    {Colors.RED}{error}{Colors.END}")
                            print(f"{Colors.CYAN}│ {Colors.YELLOW}🔄 SELF-CORRECTION: Trying alternative approach...{Colors.END}")
                            
                    elif msg_type == "agent_response":
                        content = data.get("content", "")
                        print(f"{Colors.CYAN}│{Colors.END}")
                        print(f"{Colors.CYAN}└─ ReAct Loop Complete ──────────────────────────────────────┘{Colors.END}")
                        
                        # Stats
                        print(f"\n{Colors.BOLD}📊 Stats:{Colors.END}")
                        print(f"   Thoughts: {thinking_count}")
                        print(f"   Actions:  {action_count}")
                        print(f"   Observations: {observation_count}")
                        
                        # Response
                        print_box("✅ FINAL RESPONSE", content[:400], Colors.GREEN)
                        return True
                        
                except asyncio.TimeoutError:
                    print(f"{Colors.RED}⏰ Timeout!{Colors.END}")
                    return False
                    
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        return False


async def main():
    """Run ReAct demo."""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   {Colors.BOLD}🧠 JAWIR ReAct Agent - Self-Correction Demo 🧠{Colors.END}{Colors.CYAN}                           ║
║                                                                              ║
║   This demo shows how JAWIR thinks and acts like a true AI Agent:            ║
║                                                                              ║
║   1. THOUGHT  → Reasons about what to do                                     ║
║   2. ACTION   → Executes a tool                                              ║
║   3. OBSERVE  → Analyzes the result                                          ║
║   4. EVALUATE → Decides if goal achieved                                     ║
║   5. RETRY    → If error, tries a different approach                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}
    """)
    
    # Demo scenarios
    scenarios = [
        ("Halo JAWIR, siapa kamu?", "🎭 Scenario 1: Direct Response (No Tools)"),
        ("Berapa 50 faktorial? Hitung pakai Python", "🐍 Scenario 2: Python Tool"),
        ("Cari berita terbaru tentang Apple", "🔍 Scenario 3: Web Search Tool"),
        ("Buka notepad", "🖥️ Scenario 4: Desktop Control"),
    ]
    
    for query, title in scenarios:
        await demo_react_loop(query, title)
        await asyncio.sleep(2)
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Demo Complete!{Colors.END}")
    print(f"{Colors.DIM}JAWIR is a true ReAct Agent with self-correction capabilities.{Colors.END}\n")


if __name__ == "__main__":
    asyncio.run(main())
