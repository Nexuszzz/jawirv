"""
JAWIR OS - ReAct Agent Executor
================================
True ReAct (Reasoning and Acting) Agent implementation.

ReAct Loop Pattern:
    1. THOUGHT: Agent reasons about what to do next
    2. ACTION: Agent chooses and executes a tool
    3. OBSERVATION: Agent sees the tool result
    4. EVALUATION: Agent evaluates if goal achieved or needs retry
    5. MEMORY: Agent remembers what worked/failed
    6. LOOP: If not done, go back to THOUGHT with new context

Key Features:
- Self-correction on errors (retry with different strategy)
- Memory of attempts (avoid repeating failures)
- Structured thinking output
- Iterative refinement until goal achieved
"""

import asyncio
import logging
import time
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)

from agent.tools_registry import get_all_tools
from agent.api_rotator import get_api_key
from agent.tool_analytics import ToolAnalytics
from agent.tool_cache import ToolCache
from agent.tool_quota import ToolQuota

logger = logging.getLogger("jawir.agent.react_executor")


# ============================================
# ReAct State Tracking
# ============================================

class ActionStatus(Enum):
    """Status of an action attempt."""
    SUCCESS = "success"
    ERROR = "error"
    RETRY = "retry"
    SKIPPED = "skipped"


@dataclass
class ThoughtStep:
    """Single thought in the ReAct chain."""
    iteration: int
    thought: str           # What am I trying to do?
    reasoning: str         # Why this approach?
    confidence: float      # 0.0 - 1.0
    

@dataclass
class ActionStep:
    """Single action taken by the agent."""
    iteration: int
    tool_name: str
    tool_args: dict
    expected_outcome: str  # What I expect to get


@dataclass
class ObservationStep:
    """Observation from an action."""
    iteration: int
    tool_name: str
    result: str
    status: ActionStatus
    error_message: Optional[str] = None
    

@dataclass
class EvaluationStep:
    """Evaluation after observation."""
    iteration: int
    goal_achieved: bool
    what_worked: str
    what_failed: str
    next_strategy: Optional[str] = None  # If not done, what to try next


@dataclass
class AgentMemory:
    """Agent's memory of the current task."""
    goal: str
    attempts: list = field(default_factory=list)
    successful_tools: list = field(default_factory=list)
    failed_tools: list = field(default_factory=list)
    learned: list = field(default_factory=list)  # Lessons learned
    
    def add_attempt(self, tool: str, args: dict, status: ActionStatus, result: str):
        """Record an attempt."""
        self.attempts.append({
            "tool": tool,
            "args": args,
            "status": status.value,
            "result_preview": result[:200] if result else None,
        })
        if status == ActionStatus.SUCCESS:
            self.successful_tools.append(tool)
        else:
            self.failed_tools.append(tool)
    
    def add_learning(self, lesson: str):
        """Record a lesson learned."""
        self.learned.append(lesson)
    
    def get_context_for_retry(self) -> str:
        """Get context string for retry attempts."""
        context = []
        if self.failed_tools:
            context.append(f"Tools yang sudah gagal: {', '.join(self.failed_tools)}")
        if self.learned:
            context.append(f"Pembelajaran: {'; '.join(self.learned)}")
        return "\n".join(context)


# ============================================
# ReAct System Prompt
# ============================================

REACT_SYSTEM_PROMPT = """Kamu adalah JAWIR (Just Another Wise Intelligent Resource), AI Agent yang OTONOM dan PROAKTIF.

## IDENTITAS
- Nama: JAWIR (Just Another Wise Intelligent Resource)  
- Tipe: Autonomous ReAct Agent
- Gaya: Bijaksana dengan sentuhan Jawa

## POLA PIKIR REACT (WAJIB DIIKUTI)

Untuk SETIAP langkah, kamu HARUS berpikir dengan pola:

1. **THOUGHT** (Pikiran): 
   - Apa tujuan saya?
   - Apa yang sudah saya ketahui?
   - Apa yang perlu saya cari tahu?

2. **ACTION** (Tindakan):
   - Tool apa yang paling tepat?
   - Parameter apa yang dibutuhkan?
   
3. **OBSERVATION** (Observasi):
   - Apa hasil dari tool?
   - Apakah hasilnya sesuai harapan?

4. **EVALUATION** (Evaluasi):
   - Apakah tujuan tercapai?
   - Jika belum, apa yang harus dicoba selanjutnya?
   - Jika error, apa strategi alternatif?

## KEMAMPUAN TOOLS

🔍 **Pencarian Web**:
- `web_search`: Cari info terkini (berita, harga, cuaca)

⚡ **Elektronika**:
- `generate_kicad_schematic`: Desain rangkaian elektronika

🐍 **Python**:
- `run_python_code`: Jalankan kode Python untuk kalkulasi/processing

📧 **Gmail**:
- `gmail_search`: Cari email
- `gmail_send`: Kirim email

📁 **Google Drive**:
- `drive_search`: Cari file di Drive
- `drive_list`: List isi folder

📅 **Google Calendar**:
- `calendar_list_events`: Lihat jadwal
- `calendar_create_event`: Buat event

📊 **Google Sheets**:
- `sheets_read`, `sheets_write`, `sheets_create`

📄 **Google Docs**:
- `docs_read`, `docs_create`

📝 **Google Forms**:
- `forms_read`, `forms_create`

🖥️ **Desktop Control**:
- `open_app`: Buka aplikasi (notepad, chrome, vscode, spotify)
- `open_url`: Buka URL di browser
- `close_app`: Tutup aplikasi

## ATURAN SELF-CORRECTION

1. **Jika tool error**: Jangan langsung menyerah! 
   - Analisis errornya
   - Coba parameter yang berbeda
   - Atau coba tool alternatif

2. **Jika hasil tidak sesuai**: 
   - Evaluasi apa yang salah
   - Refine query/parameter
   - Coba lagi dengan pendekatan baru

3. **Jika stuck setelah 3x retry sama**:
   - Beri tahu user dengan jujur
   - Jelaskan apa yang sudah dicoba
   - Sarankan alternatif manual

## ATURAN KAPAN TIDAK PERLU TOOL

- Sapaan (halo, selamat pagi) → jawab langsung dengan Jawa
- Identitas (siapa kamu) → jelaskan JAWIR
- Pertanyaan konsep (apa itu X) → jawab dari knowledge
- Terima kasih → balas dengan sopan

## GAYA BAHASA
- Sapaan: Jawa halus (Sugeng, Lur!)
- Teknis: Indonesia jelas dengan emoji
- Error: Tetap sopan, jangan blame user
"""


class ReActExecutor:
    """
    True ReAct Agent Executor.
    
    Implements the full ReAct loop with:
    - Explicit reasoning before each action
    - Observation and evaluation after each action
    - Memory of attempts to avoid repetition
    - Self-correction on errors
    """

    def __init__(self):
        """Initialize ReAct executor."""
        self.tools = get_all_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.llm = self._create_llm()
        self.analytics = ToolAnalytics.get_instance()
        self.cache = ToolCache.get_instance()
        self.quota = ToolQuota.get_instance()
        
        logger.info(
            f"🧠 ReActExecutor initialized with {len(self.tools)} tools: "
            f"{[t.name for t in self.tools]}"
        )

    def _create_llm(self):
        """Create Gemini LLM with tools bound."""
        api_key = get_api_key()
        
        import os
        from app.config import settings
        model_name = os.environ.get("GEMINI_MODEL") or settings.gemini_model
        
        logger.info(f"🧠 Creating ReAct LLM with model: {model_name}")
        
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
            request_timeout=90,
        )
        return llm.bind_tools(self.tools)

    def _refresh_llm(self):
        """Refresh LLM with new API key."""
        self.llm = self._create_llm()

    @staticmethod
    def _normalize_content(content) -> str:
        """Normalize Gemini response content to string."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(item.get("text", str(item)))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    async def _execute_tool(
        self,
        tool_name: str,
        tool_args: dict,
        tool_call_id: str,
        memory: AgentMemory,
        streamer: Optional[Any] = None,
    ) -> tuple[str, ActionStatus]:
        """
        Execute a single tool with full tracking.
        
        Returns:
            Tuple of (result_string, status)
        """
        # NOTE: executing_tool status is sent by the main loop caller,
        # so we don't duplicate it here.

        # Check cache
        cached = self.cache.get(tool_name, tool_args)
        if cached is not None:
            logger.info(f"🗄️ Cache HIT: {tool_name}")
            self.analytics.record(tool_name, success=True, duration=0.0)
            memory.add_attempt(tool_name, tool_args, ActionStatus.SUCCESS, cached)
            if streamer:
                await streamer.send_status(
                    "tool_completed",
                    f"✅ {tool_name} (cached)",
                    {"cached": True},
                )
            return cached, ActionStatus.SUCCESS

        # Check quota
        if not self.quota.check_and_consume(tool_name):
            msg = f"Quota exceeded untuk {tool_name}"
            logger.warning(f"🔒 {msg}")
            self.analytics.record(tool_name, success=False, error_msg="quota")
            memory.add_attempt(tool_name, tool_args, ActionStatus.SKIPPED, msg)
            return msg, ActionStatus.SKIPPED

        # Get tool
        tool = self.tool_map.get(tool_name)
        if not tool:
            msg = f"Tool '{tool_name}' tidak tersedia"
            logger.error(msg)
            self.analytics.record(tool_name, success=False, error_msg="not_found")
            memory.add_attempt(tool_name, tool_args, ActionStatus.ERROR, msg)
            return msg, ActionStatus.ERROR

        # Execute tool
        try:
            start_time = time.time()
            result = await tool.ainvoke(tool_args)
            duration = time.time() - start_time
            
            result_str = str(result)
            if len(result_str) > 5000:
                result_str = result_str[:5000] + "\n...(truncated)"
            
            logger.info(f"✅ Tool '{tool_name}' success in {duration:.2f}s")
            self.analytics.record(tool_name, success=True, duration=duration)
            self.cache.set(tool_name, tool_args, result_str)
            memory.add_attempt(tool_name, tool_args, ActionStatus.SUCCESS, result_str)
            
            if streamer:
                await streamer.send_status(
                    "tool_completed",
                    f"✅ {tool_name} selesai ({duration:.1f}s)",
                    {"result_preview": result_str[:200]},
                )
            
            return result_str, ActionStatus.SUCCESS
            
        except Exception as e:
            error_msg = str(e)
            duration = time.time() - start_time
            
            logger.error(f"❌ Tool '{tool_name}' error: {error_msg}")
            self.analytics.record(tool_name, success=False, duration=duration, error_msg=error_msg)
            memory.add_attempt(tool_name, tool_args, ActionStatus.ERROR, error_msg)
            memory.add_learning(f"Tool {tool_name} dengan args {tool_args} menghasilkan error: {error_msg}")
            
            if streamer:
                await streamer.send_status(
                    "tool_error",
                    f"❌ {tool_name} error",
                    {"error": error_msg[:100]},
                )
            
            return f"Error: {error_msg}", ActionStatus.ERROR

    async def execute(
        self,
        user_query: str,
        max_iterations: int = 50,  # Increased for extreme stress tests and complex workflows
        max_retries_per_tool: int = 2,
        streamer: Optional[Any] = None,
        history_messages: Optional[list] = None,
        file_data: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Execute the ReAct agent loop.
        
        The loop continues until:
        1. Agent returns final response (no more tool calls)
        2. Max iterations reached
        3. Agent explicitly says it's done
        
        Args:
            user_query: User's question or command
            max_iterations: Maximum ReAct loops (default 50 for extreme stress tests)
            max_retries_per_tool: Max retries per tool on error (default 2)
            streamer: Optional status streamer for UI
            history_messages: Optional conversation history (LangChain messages)
            file_data: Optional file data (for multimodal image input)
            
        Returns:
            Dictionary with final_response, thinking_trace, tool_history, metrics
        """
        start_time = time.time()
        
        # Initialize memory
        memory = AgentMemory(goal=user_query)
        
        # Initialize message history with system prompt
        messages = [SystemMessage(content=REACT_SYSTEM_PROMPT)]
        
        # Add conversation history if provided (includes summary & user info)
        if history_messages:
            messages.extend(history_messages)
            logger.info(f"📝 Loaded {len(history_messages)} history messages for context")
        
        # Add current user query with image if available
        # Note: Even with history, we add current message because history
        # might not include the current query or its attached image
        if file_data and file_data.get("type") == "image":
            # Create multimodal message with image and text
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{file_data['mime_type']};base64,{file_data['data']}"
                }
            }
            text_content = {"type": "text", "text": user_query}
            messages.append(HumanMessage(content=[image_content, text_content]))
            logger.info(f"📷 Added multimodal message with image: {file_data.get('filename', 'unknown')}")
        elif not history_messages:
            # Only add text message if no history (history already includes query)
            messages.append(HumanMessage(content=user_query))
        
        # Track analytics
        self.analytics.record_query()
        
        # Tracking structures
        thinking_trace = []  # All thoughts, actions, observations
        tool_calls_history = []
        retry_counts = {}  # tool_name -> retry count
        
        iteration = 0
        final_response = None
        
        # ============================================
        # Helper: Send heartbeat during long operations
        # ============================================
        async def send_heartbeat(streamer, iteration: int, phase: str):
            """Send heartbeat status to keep connection alive."""
            if streamer:
                elapsed = time.time() - start_time
                await streamer.send_status(
                    "thinking",
                    f"[{elapsed:.0f}s] {phase} (langkah {iteration})...",
                    {"iteration": iteration, "elapsed": elapsed, "phase": phase}
                )
        
        # ============================================
        # Main ReAct Loop
        # ============================================
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"🔄 ReAct Iteration {iteration}/{max_iterations}")
            
            if streamer:
                await streamer.send_status(
                    "iteration_start",
                    f"Iterasi {iteration}/{max_iterations}",
                    {"iteration": iteration, "max": max_iterations}
                )
            
            try:
                # Step 1: THOUGHT - Invoke Gemini to think and decide
                # Use asyncio.wait_for with heartbeat for long API calls
                
                async def invoke_with_heartbeat():
                    """Invoke LLM with periodic heartbeats."""
                    # Start the LLM call
                    task = asyncio.create_task(self.llm.ainvoke(messages))
                    
                    # While waiting, send heartbeats every 10 seconds
                    heartbeat_interval = 10
                    elapsed_in_call = 0
                    
                    while not task.done():
                        try:
                            # Wait for task with short timeout
                            result = await asyncio.wait_for(
                                asyncio.shield(task),
                                timeout=heartbeat_interval
                            )
                            return result
                        except asyncio.TimeoutError:
                            # Task not done yet, send heartbeat
                            elapsed_in_call += heartbeat_interval
                            await send_heartbeat(streamer, iteration, f"Memproses ({elapsed_in_call}s)")
                            
                            if elapsed_in_call >= 90:
                                # Total timeout exceeded
                                task.cancel()
                                raise asyncio.TimeoutError("LLM call exceeded 90s")
                    
                    return await task
                
                response = await invoke_with_heartbeat()
                
                # Extract thought/reasoning from response content
                thought_content = self._normalize_content(response.content) if response.content else ""
                
                # Step 2: Check if this is final response (no tool calls)
                if not response.tool_calls:
                    final_response = thought_content
                    
                    # Record the final thought
                    thinking_trace.append({
                        "type": "final_thought",
                        "iteration": iteration,
                        "content": final_response[:500],
                    })
                    
                    logger.info(f"✅ Final response at iteration {iteration}")
                    
                    # Send final thought if short
                    if streamer and thought_content and len(thought_content) < 200:
                        await streamer.send_status(
                            "thinking",
                            thought_content[:150],
                            {"iteration": iteration, "final": True}
                        )
                    
                    if streamer:
                        await streamer.send_status(
                            "done",
                            f"Selesai dalam {iteration} langkah",
                            {"iteration": iteration}
                        )
                    break
                
                # Step 3: ACTION - Process tool calls
                messages.append(response)
                
                # Send THOUGHT - show reasoning before actions
                if streamer and thought_content:
                    thought_preview = thought_content[:150] + "..." if len(thought_content) > 150 else thought_content
                    await streamer.send_status(
                        "thinking",
                        thought_preview,
                        {"iteration": iteration, "has_actions": True}
                    )
                
                # Send PLANNING - list tools to execute
                tool_names = [tc["name"] for tc in response.tool_calls]
                if streamer:
                    await streamer.send_status(
                        "planning",
                        f"Akan menjalankan: {', '.join(tool_names)}",
                        {"tools": tool_names, "count": len(tool_names)}
                    )
                
                for tool_idx, tool_call in enumerate(response.tool_calls):
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    tool_id = tool_call.get("id", f"call_{iteration}_{tool_name}")
                    
                    # Record thought before action
                    thinking_trace.append({
                        "type": "thought",
                        "iteration": iteration,
                        "tool": tool_name,
                        "reasoning": f"Menggunakan {tool_name} untuk {memory.goal}",
                    })
                    
                    # Check retry limits
                    retry_key = f"{tool_name}:{hash(str(tool_args))}"
                    current_retries = retry_counts.get(retry_key, 0)
                    
                    if current_retries >= max_retries_per_tool:
                        # Too many retries for this exact call
                        skip_msg = f"Sudah mencoba {tool_name} {current_retries}x dengan parameter yang sama, mencari alternatif..."
                        logger.warning(f"⚠️ {skip_msg}")
                        
                        memory.add_learning(f"Tool {tool_name} tidak berhasil setelah {current_retries} percobaan")
                        
                        messages.append(ToolMessage(
                            content=f"RETRY_LIMIT_REACHED: {skip_msg}. Coba pendekatan lain atau parameter berbeda.",
                            tool_call_id=tool_id,
                        ))
                        
                        thinking_trace.append({
                            "type": "observation",
                            "iteration": iteration,
                            "tool": tool_name,
                            "status": "retry_limit",
                            "message": skip_msg,
                        })
                        
                        continue
                    
                    # Execute the tool
                    logger.info(f"🔧 ACTION: {tool_name}({tool_args})")
                    
                    # Send executing_tool status for real-time display
                    if streamer:
                        await streamer.send_status(
                            "executing_tool",
                            f"Menjalankan {tool_name}...",
                            {"tool": tool_name, "args": tool_args}
                        )
                    
                    thinking_trace.append({
                        "type": "action",
                        "iteration": iteration,
                        "tool": tool_name,
                        "args": tool_args,
                    })
                    
                    result, status = await self._execute_tool(
                        tool_name,
                        tool_args,
                        tool_id,
                        memory,
                        streamer,
                    )
                    
                    # Send OBSERVATION - tool result status
                    if streamer:
                        result_preview = result[:150] if result else "No result"
                        status_icon = "✅" if status == ActionStatus.SUCCESS else "❌"
                        await streamer.send_status(
                            "observation",
                            f"{status_icon} {tool_name}: {result_preview}",
                            {"tool": tool_name, "status": status.value, "result": result[:300]}
                        )
                    
                    # Record tool call
                    tool_calls_history.append({
                        "tool_name": tool_name,
                        "args": tool_args,
                        "result": result[:1000],
                        "status": status.value,
                        "iteration": iteration,
                    })
                    
                    # Step 4: OBSERVATION
                    thinking_trace.append({
                        "type": "observation",
                        "iteration": iteration,
                        "tool": tool_name,
                        "status": status.value,
                        "result_preview": result[:300],
                    })
                    
                    # Step 5: EVALUATION (implicit in message to LLM)
                    if status == ActionStatus.ERROR:
                        retry_counts[retry_key] = current_retries + 1
                        
                        # Add context about the error and retry status
                        error_context = memory.get_context_for_retry()
                        result_with_context = f"{result}\n\n[SELF-CORRECTION HINT: {error_context}. Coba approach lain atau parameter berbeda.]"
                        
                        messages.append(ToolMessage(
                            content=result_with_context,
                            tool_call_id=tool_id,
                        ))
                        
                        thinking_trace.append({
                            "type": "evaluation",
                            "iteration": iteration,
                            "success": False,
                            "retry_count": retry_counts[retry_key],
                            "will_retry": retry_counts[retry_key] < max_retries_per_tool,
                        })
                    else:
                        # Success - add result normally
                        messages.append(ToolMessage(
                            content=result,
                            tool_call_id=tool_id,
                        ))
                        
                        thinking_trace.append({
                            "type": "evaluation",
                            "iteration": iteration,
                            "success": True,
                        })
                
                # Loop continues - Gemini will see results and decide next step
                
            except asyncio.TimeoutError:
                logger.error(f"⏰ Timeout at iteration {iteration}")
                try:
                    self._refresh_llm()
                    logger.info("🔄 LLM refreshed after timeout")
                    continue
                except Exception:
                    final_response = "Mohon maaf, koneksi timeout. Silakan coba lagi."
                    break
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ ReAct loop error: {error_msg}")
                
                # Try API key rotation
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    try:
                        self._refresh_llm()
                        continue
                    except Exception:
                        pass
                
                final_response = f"Mohon maaf, terjadi kesalahan: {error_msg}"
                break
        
        # ============================================
        # Handle max iterations - compile results from successful tools
        # ============================================
        
        if final_response is None:
            # Build a comprehensive response from what was done
            summary_parts = []
            
            # Collect successful tool results
            successful_results = [tc for tc in tool_calls_history if tc["status"] == "success"]
            
            if successful_results:
                summary_parts.append("Berikut hasil yang berhasil dikumpulkan:\n")
                for tc in successful_results:
                    tool_name = tc["tool_name"]
                    result_preview = tc.get("result", "")[:500]
                    summary_parts.append(f"**{tool_name}**: {result_preview}\n")
            else:
                summary_parts.append("Mohon maaf, JAWIR membutuhkan terlalu banyak langkah untuk menyelesaikan permintaan ini.")
            
            if memory.successful_tools:
                summary_parts.append(f"\n✅ Tools berhasil: {', '.join(memory.successful_tools)}")
            if memory.failed_tools:
                summary_parts.append(f"\n❌ Tools gagal: {', '.join(memory.failed_tools)}")
            
            final_response = "\n".join(summary_parts)
            logger.warning(f"⚠️ Max iterations reached: {max_iterations}")
        
        # ============================================
        # Compile metrics and return
        # ============================================
        
        execution_time = time.time() - start_time
        
        metrics = {
            "iterations": iteration,
            "tool_calls": len(tool_calls_history),
            "unique_tools": list(set(tc["tool_name"] for tc in tool_calls_history)),
            "errors": sum(1 for tc in tool_calls_history if tc["status"] == "error"),
            "retries": sum(retry_counts.values()),
            "execution_time_seconds": round(execution_time, 3),
            "memory_learnings": len(memory.learned),
        }
        
        logger.info(
            f"📊 ReAct Complete: iterations={metrics['iterations']}, "
            f"tools={metrics['tool_calls']}, errors={metrics['errors']}, "
            f"retries={metrics['retries']}, time={metrics['execution_time_seconds']}s"
        )
        
        return {
            "final_response": final_response,
            "thinking_trace": thinking_trace,
            "tool_calls_history": tool_calls_history,
            "memory": {
                "goal": memory.goal,
                "successful_tools": memory.successful_tools,
                "failed_tools": memory.failed_tools,
                "learned": memory.learned,
            },
            "iterations": iteration,
            "execution_time": execution_time,
            "metrics": metrics,
        }


# Singleton instance
_react_executor: Optional[ReActExecutor] = None


def get_react_executor() -> ReActExecutor:
    """Get or create the ReAct executor singleton."""
    global _react_executor
    if _react_executor is None:
        _react_executor = ReActExecutor()
    return _react_executor
