"""
JAWIR OS - Function Calling Executor
======================================
Executor yang handle Gemini native function calling loop.
Gemini autonomously memilih tools via bind_tools() dan
executor menjalankan tools, mengirim hasil balik ke Gemini,
lalu loop sampai Gemini memberi final response.

Architecture:
    User Query → Gemini (with tools bound)
                    ↓
              tool_calls? → Execute tools → Return results → Loop
                    ↓ (no tool calls)
              Final Response → Done
"""

import asyncio
import logging
import time
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)

from agent.tools_registry import get_all_tools
from agent.api_rotator import get_api_key, mark_key_rate_limited, mark_key_disabled
from agent.tool_analytics import ToolAnalytics
from agent.tool_cache import ToolCache
from agent.tool_quota import ToolQuota

logger = logging.getLogger("jawir.agent.function_calling_executor")


# ============================================
# System Prompt for Function Calling Agent
# ============================================

FUNCTION_CALLING_SYSTEM_PROMPT = """Kamu adalah JAWIR (Just Another Wise Intelligent Resource), asisten AI personal yang bijaksana dengan sentuhan budaya Jawa yang sopan.

IDENTITAS:
- Nama: JAWIR (Just Another Wise Intelligent Resource)
- Sifat: Bijaksana, sopan, helpful, dengan sentuhan Jawa
- Bahasa: Indonesia campur Jawa halus (kromo inggil) untuk sapaan

KEMAMPUAN TOOLS:
Kamu punya akses ke beberapa tools. Gunakan tools dengan BIJAK:

🔍 PENCARIAN & INFO:
- web_search: Untuk mencari informasi terkini dari internet (harga, berita, cuaca, kurs)

⚡ ELEKTRONIKA:
- generate_kicad_schematic: Untuk mendesain rangkaian elektronika dengan KiCAD

🐍 PYTHON:
- run_python_code: Untuk menjalankan kode Python (kalkulasi, data processing)

📧 GMAIL:
- gmail_search: Untuk mencari email di Gmail
- gmail_send: Untuk mengirim email via Gmail

📁 GOOGLE DRIVE:
- drive_search: Untuk mencari file di Google Drive
- drive_list: Untuk melihat isi folder Google Drive

📅 GOOGLE CALENDAR:
- calendar_list_events: Untuk melihat jadwal di Google Calendar
- calendar_create_event: Untuk membuat event di Google Calendar

📊 GOOGLE SHEETS:
- sheets_read: Untuk membaca data dari Google Sheets
- sheets_write: Untuk menulis data ke Google Sheets
- sheets_create: Untuk membuat spreadsheet baru

📄 GOOGLE DOCS:
- docs_read: Untuk membaca isi Google Docs
- docs_create: Untuk membuat dokumen baru

📝 GOOGLE FORMS:
- forms_read: Untuk melihat respons Google Forms
- forms_create: Untuk membuat form baru

🎓 POLINEMA SIAKAD:
PENTING: Untuk data SIAKAD Polinema, LANGSUNG buka halaman di browser menggunakan open_url (JANGAN pakai polinema tools karena sering error). URL SIAKAD:
  - Jadwal: https://siakad.polinema.ac.id/mahasiswa/jadwal/index/gm/akademik
  - Presensi: https://siakad.polinema.ac.id/mahasiswa/presensi/index/gm/akademik
  - Nilai: https://siakad.polinema.ac.id/mahasiswa/akademik/index/gm/akademik
  - Biodata: https://siakad.polinema.ac.id/mahasiswa/biodata/index/gm/general
  - Kalender Akademik: https://siakad.polinema.ac.id/mahasiswa/kalenderakd/index/gm/akademik
Ketika user minta "lihat jadwal kuliah" → langsung panggil open_url dengan URL jadwal di atas.
Ketika user minta "cek presensi" → langsung panggil open_url dengan URL presensi di atas.

🖥️ DESKTOP CONTROL:
- open_app: Untuk membuka aplikasi desktop (chrome, spotify, notepad, vscode, dll)
- open_url: Untuk membuka URL di browser
- close_app: Untuk menutup aplikasi desktop

📡 IoT INTEGRATION:
- iot_list_devices: Untuk melihat semua device IoT yang terhubung
- iot_get_device_state: Untuk mengecek status device IoT
- iot_set_device_state: Untuk mengontrol device IoT (kipas, alarm)

ATURAN PENGGUNAAN TOOLS:
1. JANGAN gunakan tools untuk sapaan/greeting (halo, hai, selamat pagi)
2. JANGAN gunakan tools untuk pertanyaan identitas (siapa kamu, namamu siapa)
3. JANGAN gunakan tools untuk terima kasih atau basa-basi
4. JANGAN gunakan tools untuk pertanyaan konsep/penjelasan (apa itu X, cara kerja Y) → jawab langsung
5. GUNAKAN web_search HANYA jika butuh data TERKINI yang berubah (harga, berita, cuaca, kurs)
6. GUNAKAN google tools HANYA jika user secara eksplisit minta akses email/drive/kalender/sheets/docs/forms
7. GUNAKAN open_app/open_url/close_app HANYA jika user minta buka/tutup aplikasi
8. Pilih SATU tool yang paling tepat, jangan panggil banyak tools sekaligus kecuali memang diperlukan
9. UNTUK POLINEMA SIAKAD: LANGSUNG gunakan open_url untuk buka halaman SIAKAD (jadwal/presensi/nilai/biodata) - JANGAN pakai polinema_get_akademik atau polinema_get_biodata karena scraper sering error

GAYA JAWABAN:
- Informatif, terstruktur, dan mudah dipahami
- Gunakan emoji secukupnya untuk memperjelas
- Untuk sapaan: gunakan bahasa Jawa sopan (Sugeng, Lur!)
- Untuk konten teknis: gunakan bahasa Indonesia yang jelas
- Berikan contoh jika membantu pemahaman
"""


class FunctionCallingExecutor:
    """
    Executor for Gemini function calling agent.
    
    Handles the tool execution loop:
    1. Send query to Gemini (with tools bound)
    2. If Gemini returns tool_calls → execute tools
    3. Append tool results to message history
    4. Re-invoke Gemini with updated history
    5. Loop until Gemini gives final text response or max iterations reached
    """

    def __init__(self):
        """Initialize executor with tools and LLM."""
        self.tools = get_all_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.llm = self._create_llm()
        
        logger.info(
            f"🤖 FunctionCallingExecutor initialized with {len(self.tools)} tools: "
            f"{[t.name for t in self.tools]}"
        )

    def _create_llm(self):
        """Create Gemini LLM with tools bound via bind_tools()."""
        api_key = get_api_key()
        
        # Model from settings (default: gemini-3-pro-preview)
        # Also check env var for override (useful in testing)
        import os
        from app.config import settings
        model_name = os.environ.get("GEMINI_MODEL") or settings.gemini_model
        
        logger.info(f"🧠 Creating LLM with model: {model_name}")
        
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True,
            request_timeout=90,
        )
        logger.info(f"🧠 LLM created successfully")
        # CRITICAL: bind_tools enables native Gemini function calling
        return llm.bind_tools(self.tools)

    @staticmethod
    def _normalize_content(content) -> str:
        """Normalize Gemini response content to plain string.
        
        Gemini 3.x models may return content as list of dicts:
        [{'type': 'text', 'text': 'Hello...', 'extras': {...}}]
        This normalizes it to a plain string.
        """
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # Extract text from list of content parts
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(item.get("text", str(item)))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    def _refresh_llm(self):
        """Refresh LLM with new API key (for rotation on rate limit)."""
        self.llm = self._create_llm()

    async def execute(
        self,
        user_query: str,
        max_iterations: int = 5,
        streamer: Optional[Any] = None,
        history_messages: Optional[list] = None,
    ) -> dict[str, Any]:
        """
        Execute the function calling agent loop.
        
        Args:
            user_query: The user's question or command
            max_iterations: Max tool execution loops (default 5)
            streamer: Optional AgentStatusStreamer for real-time UI updates
            history_messages: Optional conversation history (LangChain messages)
            
        Returns:
            Dictionary with:
                - final_response: str - The final text response
                - tool_calls_history: list - All tool calls made
                - iterations: int - Number of iterations used
                - execution_time: float - Total time in seconds
        """
        start_time = time.time()

        # Initialize messages with system prompt
        messages = [SystemMessage(content=FUNCTION_CALLING_SYSTEM_PROMPT)]
        
        # Add conversation history if provided
        if history_messages:
            messages.extend(history_messages)
            logger.info(f"📝 Loaded {len(history_messages)} history messages")
        else:
            messages.append(HumanMessage(content=user_query))

        # Track query in analytics
        ToolAnalytics.get_instance().record_query()

        tool_calls_history = []
        iteration = 0
        final_response = None

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"🔄 Iteration {iteration}/{max_iterations}")

            try:
                # Step 1: Invoke Gemini (with timeout protection)
                if streamer and iteration == 1:
                    await streamer.send_thinking("Memahami permintaan Anda...")

                try:
                    response = await asyncio.wait_for(
                        self.llm.ainvoke(messages),
                        timeout=60,  # 60s max per Gemini API call
                    )
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.error(f"⏰ Gemini API timeout at iteration {iteration}")
                    # Try refreshing with new API key
                    try:
                        self._refresh_llm()
                        logger.info("🔄 LLM refreshed after timeout, retrying...")
                        continue
                    except Exception:
                        final_response = "Mohon maaf, koneksi ke AI sedang lambat. Silakan coba lagi."
                        break

                # Step 2: Check if Gemini returned tool_calls
                if not response.tool_calls:
                    # No tool calls = final response
                    final_response = self._normalize_content(response.content)
                    logger.info(f"✅ Final response received (iteration {iteration})")
                    break

                # Step 3: Process each tool call (parallel if multiple)
                # Add the AI message with tool calls to history
                messages.append(response)

                if len(response.tool_calls) > 1:
                    # PARALLEL execution for multiple tool calls
                    logger.info(f"⚡ Parallel execution: {len(response.tool_calls)} tool calls")
                    analytics = ToolAnalytics.get_instance()
                    
                    async def _exec_single_tool(tc):
                        """Execute a single tool call and return (ToolMessage, history_entry)."""
                        t_name = tc["name"]
                        t_args = tc["args"]
                        t_id = tc.get("id", f"call_{iteration}_{t_name}")
                        
                        logger.info(f"🔧 Tool call: {t_name}({t_args})")
                        
                        tool = self.tool_map.get(t_name)
                        if not tool:
                            not_found = f"Tool '{t_name}' tidak tersedia. Tools yang ada: {list(self.tool_map.keys())}"
                            analytics.record(t_name, success=False, error_msg="not_found")
                            return (
                                ToolMessage(content=not_found, tool_call_id=t_id),
                                {"tool_name": t_name, "args": t_args, "result": not_found, "status": "not_found", "iteration": iteration},
                            )
                        
                        # Check cache first
                        cache = ToolCache.get_instance()
                        cached_result = cache.get(t_name, t_args)
                        if cached_result is not None:
                            logger.info(f"🗄️ Cache HIT for {t_name}")
                            analytics.record(t_name, success=True, duration=0.0)
                            return (
                                ToolMessage(content=str(cached_result), tool_call_id=t_id),
                                {"tool_name": t_name, "args": t_args, "result": str(cached_result)[:1000], "status": "cached", "iteration": iteration},
                            )
                        
                        # Check quota
                        quota = ToolQuota.get_instance()
                        if not quota.check_and_consume(t_name):
                            quota_msg = f"Quota exceeded untuk tool '{t_name}'. Maksimum penggunaan sudah tercapai dalam session ini."
                            logger.warning(f"🔒 Quota exceeded: {t_name}")
                            analytics.record(t_name, success=False, error_msg="quota_exceeded")
                            return (
                                ToolMessage(content=quota_msg, tool_call_id=t_id),
                                {"tool_name": t_name, "args": t_args, "result": quota_msg, "status": "quota_exceeded", "iteration": iteration},
                            )
                        
                        try:
                            tool_start = time.time()
                            result = await tool.ainvoke(t_args)
                            tool_duration = time.time() - tool_start
                            result_str = str(result)
                            if len(result_str) > 5000:
                                result_str = result_str[:5000] + "\n...(truncated)"
                            logger.info(f"✅ Tool '{t_name}' executed successfully")
                            analytics.record(t_name, success=True, duration=tool_duration)
                            # Cache the result for future use
                            cache.set(t_name, t_args, result_str)
                            return (
                                ToolMessage(content=result_str, tool_call_id=t_id),
                                {"tool_name": t_name, "args": t_args, "result": result_str[:1000], "status": "success", "iteration": iteration},
                            )
                        except Exception as e:
                            tool_duration = time.time() - tool_start
                            error_msg = f"Error executing {t_name}: {str(e)}"
                            logger.error(f"❌ {error_msg}")
                            analytics.record(t_name, success=False, duration=tool_duration, error_msg=str(e))
                            return (
                                ToolMessage(content=error_msg, tool_call_id=t_id),
                                {"tool_name": t_name, "args": t_args, "result": error_msg, "status": "error", "iteration": iteration},
                            )
                    
                    # Send status update for parallel execution
                    if streamer:
                        tool_names = [tc["name"] for tc in response.tool_calls]
                        await streamer.send_status(
                            "executing_tool",
                            f"Menjalankan {len(response.tool_calls)} tools secara paralel: {', '.join(tool_names)}",
                            {"tools": tool_names, "parallel": True},
                        )
                    
                    # Execute all tool calls concurrently
                    results = await asyncio.gather(
                        *[_exec_single_tool(tc) for tc in response.tool_calls],
                        return_exceptions=True,
                    )
                    
                    for r in results:
                        if isinstance(r, Exception):
                            # Shouldn't happen since _exec_single_tool catches exceptions
                            logger.error(f"❌ Unexpected parallel error: {r}")
                            continue
                        tool_msg, history_entry = r
                        messages.append(tool_msg)
                        tool_calls_history.append(history_entry)
                    
                    if streamer:
                        await streamer.send_status(
                            "tool_completed",
                            f"{len(response.tool_calls)} tools selesai",
                            {"parallel": True},
                        )
                    
                else:
                    # SEQUENTIAL execution for single tool call
                    analytics = ToolAnalytics.get_instance()
                    cache = ToolCache.get_instance()
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        tool_call_id = tool_call.get("id", f"call_{iteration}_{tool_name}")

                        logger.info(f"🔧 Tool call: {tool_name}({tool_args})")

                        # Send status update to UI
                        if streamer:
                            await streamer.send_status(
                                "executing_tool",
                                f"Menggunakan {tool_name}...",
                                {"tool_name": tool_name, "args": tool_args},
                            )

                        # Check cache first
                        cached_result = cache.get(tool_name, tool_args)
                        if cached_result is not None:
                            logger.info(f"🗄️ Cache HIT for {tool_name}")
                            analytics.record(tool_name, success=True, duration=0.0)
                            messages.append(ToolMessage(
                                content=str(cached_result),
                                tool_call_id=tool_call_id,
                            ))
                            tool_calls_history.append({
                                "tool_name": tool_name,
                                "args": tool_args,
                                "result": str(cached_result)[:1000],
                                "status": "cached",
                                "iteration": iteration,
                            })
                            if streamer:
                                await streamer.send_status(
                                    "tool_completed",
                                    f"{tool_name} selesai (cached)",
                                    {"tool_name": tool_name, "cached": True},
                                )
                            continue

                        # Check quota
                        quota = ToolQuota.get_instance()
                        if not quota.check_and_consume(tool_name):
                            quota_msg = f"Quota exceeded untuk tool '{tool_name}'. Maksimum penggunaan sudah tercapai dalam session ini."
                            logger.warning(f"🔒 Quota exceeded: {tool_name}")
                            analytics.record(tool_name, success=False, error_msg="quota_exceeded")
                            messages.append(ToolMessage(
                                content=quota_msg,
                                tool_call_id=tool_call_id,
                            ))
                            tool_calls_history.append({
                                "tool_name": tool_name,
                                "args": tool_args,
                                "result": quota_msg,
                                "status": "quota_exceeded",
                                "iteration": iteration,
                            })
                            continue

                        # Execute the tool
                        tool = self.tool_map.get(tool_name)
                        if tool:
                            try:
                                tool_start = time.time()
                                tool_result = await tool.ainvoke(tool_args)
                                tool_duration = time.time() - tool_start
                                result_str = str(tool_result)

                                # Truncate very long results
                                if len(result_str) > 5000:
                                    result_str = result_str[:5000] + "\n...(truncated)"

                                messages.append(ToolMessage(
                                    content=result_str,
                                    tool_call_id=tool_call_id,
                                ))

                                tool_calls_history.append({
                                    "tool_name": tool_name,
                                    "args": tool_args,
                                    "result": result_str[:1000],  # Store abbreviated
                                    "status": "success",
                                    "iteration": iteration,
                                })

                                logger.info(f"✅ Tool '{tool_name}' executed successfully")
                                analytics.record(tool_name, success=True, duration=tool_duration)
                                # Cache result for future use
                                cache.set(tool_name, tool_args, result_str)

                                # Send tool result to UI — both as status AND as tool_result event
                                if streamer:
                                    await streamer.send_status(
                                        "tool_completed",
                                        f"{tool_name} selesai",
                                        {"tool_name": tool_name, "result_preview": result_str[:200]},
                                    )
                                    # Also send dedicated tool_result event for UI ToolResults panel
                                    await streamer.send_tool_result(
                                        tool_name=tool_name,
                                        status="success",
                                        data={
                                            "title": f"{tool_name}",
                                            "summary": result_str[:500],
                                            "duration": round(tool_duration, 2),
                                        }
                                    )

                            except Exception as e:
                                tool_duration = time.time() - tool_start
                                error_msg = f"Error executing {tool_name}: {str(e)}"
                                logger.error(f"❌ {error_msg}")
                                analytics.record(tool_name, success=False, duration=tool_duration, error_msg=str(e))

                                messages.append(ToolMessage(
                                    content=error_msg,
                                    tool_call_id=tool_call_id,
                                ))

                                tool_calls_history.append({
                                    "tool_name": tool_name,
                                    "args": tool_args,
                                    "result": error_msg,
                                    "status": "error",
                                    "iteration": iteration,
                                })

                                # Send error tool_result to UI
                                if streamer:
                                    await streamer.send_tool_result(
                                        tool_name=tool_name,
                                        status="error",
                                        data={
                                            "title": f"{tool_name} (error)",
                                            "summary": str(e)[:300],
                                            "duration": round(tool_duration, 2),
                                        }
                                    )
                        else:
                            # Tool not found
                            not_found_msg = f"Tool '{tool_name}' tidak tersedia. Tools yang ada: {list(self.tool_map.keys())}"
                            analytics.record(tool_name, success=False, error_msg="not_found")
                            messages.append(ToolMessage(
                                content=not_found_msg,
                                tool_call_id=tool_call_id,
                            ))

                            tool_calls_history.append({
                                "tool_name": tool_name,
                                "args": tool_args,
                                "result": not_found_msg,
                                "status": "not_found",
                                "iteration": iteration,
                            })

                # Loop back to invoke Gemini with tool results

            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Execution error at iteration {iteration}: {error_msg}")

                # Handle API key issues
                if "PERMISSION_DENIED" in error_msg or "leaked" in error_msg.lower():
                    # Try refreshing LLM with new key
                    try:
                        self._refresh_llm()
                        logger.info("🔄 LLM refreshed with new API key")
                        continue  # Retry with new key
                    except Exception:
                        pass

                elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    try:
                        self._refresh_llm()
                        logger.info("🔄 Rate limited, switched to new API key")
                        continue
                    except Exception:
                        pass

                # If we can't recover, return error
                final_response = f"Mohon maaf, terjadi kesalahan: {error_msg}"
                break

        # If max iterations reached without final response
        if final_response is None:
            final_response = (
                "Mohon maaf, JAWIR membutuhkan terlalu banyak langkah untuk menjawab pertanyaan ini. "
                "Silakan coba dengan pertanyaan yang lebih spesifik."
            )
            logger.warning(f"⚠️ Max iterations ({max_iterations}) reached without final response")

        execution_time = time.time() - start_time

        # Structured metrics for monitoring (Task 4.2)
        metrics = {
            "iterations": iteration,
            "tool_call_count": len(tool_calls_history),
            "execution_time_seconds": round(execution_time, 3),
            "tools_used": list({tc["tool_name"] for tc in tool_calls_history}),
            "tool_errors": sum(1 for tc in tool_calls_history if tc["status"] != "success"),
            "max_iterations_hit": final_response is not None and iteration >= max_iterations,
        }

        logger.info(
            f"📊 FC Metrics: iterations={metrics['iterations']}, "
            f"tool_calls={metrics['tool_call_count']}, "
            f"tools_used={metrics['tools_used']}, "
            f"errors={metrics['tool_errors']}, "
            f"time={metrics['execution_time_seconds']}s"
        )

        return {
            "final_response": final_response,
            "tool_calls_history": tool_calls_history,
            "iterations": iteration,
            "execution_time": execution_time,
            "metrics": metrics,
        }
