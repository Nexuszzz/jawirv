"""
JAWIR OS - Conditional Tool Execution
========================================
IF-THEN logic untuk tool execution berdasarkan kondisi dan hasil sebelumnya.

Memungkinkan Gemini membuat keputusan apakah step berikutnya perlu
dijalankan berdasarkan output step sebelumnya.

Usage:
    from agent.tool_conditional import ConditionalChain, Condition

    chain = ConditionalChain(
        name="smart_search",
        steps=[
            ConditionalStep(
                tool_name="web_search",
                input_mapping={"query": "$user_input"},
            ),
            ConditionalStep(
                tool_name="run_python_code",
                input_mapping={"code": "$prev_output"},
                condition=Condition.contains("Error"),  # Only if error
                skip_message="Search successful, no processing needed",
            ),
        ]
    )
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from agent.tool_chain import ChainStep, ChainContext, ChainResult, ToolChain

logger = logging.getLogger("jawir.agent.tool_conditional")


# ============================================
# Condition Builders
# ============================================

class Condition:
    """
    Factory for common condition functions.
    
    Each method returns a Callable[[ChainContext], bool].
    """
    
    @staticmethod
    def always() -> Callable[[ChainContext], bool]:
        """Always execute this step."""
        return lambda ctx: True
    
    @staticmethod
    def never() -> Callable[[ChainContext], bool]:
        """Never execute this step (skip)."""
        return lambda ctx: False
    
    @staticmethod
    def contains(text: str, case_sensitive: bool = False) -> Callable[[ChainContext], bool]:
        """Execute if previous output contains text."""
        def check(ctx: ChainContext) -> bool:
            output = ctx.prev_output
            if case_sensitive:
                return text in output
            return text.lower() in output.lower()
        return check
    
    @staticmethod
    def not_contains(text: str, case_sensitive: bool = False) -> Callable[[ChainContext], bool]:
        """Execute if previous output does NOT contain text."""
        def check(ctx: ChainContext) -> bool:
            output = ctx.prev_output
            if case_sensitive:
                return text not in output
            return text.lower() not in output.lower()
        return check
    
    @staticmethod
    def matches(pattern: str) -> Callable[[ChainContext], bool]:
        """Execute if previous output matches regex pattern."""
        compiled = re.compile(pattern, re.IGNORECASE)
        return lambda ctx: bool(compiled.search(ctx.prev_output))
    
    @staticmethod
    def output_longer_than(length: int) -> Callable[[ChainContext], bool]:
        """Execute if previous output is longer than N characters."""
        return lambda ctx: len(ctx.prev_output) > length
    
    @staticmethod
    def output_shorter_than(length: int) -> Callable[[ChainContext], bool]:
        """Execute if previous output is shorter than N characters."""
        return lambda ctx: len(ctx.prev_output) < length
    
    @staticmethod
    def prev_step_succeeded() -> Callable[[ChainContext], bool]:
        """Execute if the previous step produced non-empty output without error markers."""
        def check(ctx: ChainContext) -> bool:
            output = ctx.prev_output
            error_markers = ["❌", "Error", "Failed", "error:", "Exception"]
            if not output.strip():
                return False
            return not any(m.lower() in output.lower() for m in error_markers)
        return check
    
    @staticmethod
    def prev_step_failed() -> Callable[[ChainContext], bool]:
        """Execute if the previous step had error markers in output."""
        def check(ctx: ChainContext) -> bool:
            output = ctx.prev_output
            error_markers = ["❌", "Error", "Failed", "error:", "Exception"]
            return any(m.lower() in output.lower() for m in error_markers)
        return check
    
    @staticmethod
    def custom(fn: Callable[[ChainContext], bool]) -> Callable[[ChainContext], bool]:
        """Use a custom condition function."""
        return fn
    
    @staticmethod
    def all_of(*conditions: Callable[[ChainContext], bool]) -> Callable[[ChainContext], bool]:
        """Execute if ALL conditions are true (AND logic)."""
        return lambda ctx: all(c(ctx) for c in conditions)
    
    @staticmethod
    def any_of(*conditions: Callable[[ChainContext], bool]) -> Callable[[ChainContext], bool]:
        """Execute if ANY condition is true (OR logic)."""
        return lambda ctx: any(c(ctx) for c in conditions)
    
    @staticmethod
    def none_of(*conditions: Callable[[ChainContext], bool]) -> Callable[[ChainContext], bool]:
        """Execute if NONE of the conditions are true (NOT logic)."""
        return lambda ctx: not any(c(ctx) for c in conditions)


# ============================================
# Conditional Step
# ============================================

@dataclass
class ConditionalStep(ChainStep):
    """
    A chain step with an optional condition for execution.
    
    Attributes:
        condition: Function that evaluates ChainContext → bool.
                   If False, step is skipped.
        skip_message: Message logged when step is skipped.
        fallback_output: Output to use when step is skipped.
    """
    condition: Optional[Callable[[ChainContext], bool]] = None
    skip_message: str = "Step skipped (condition not met)"
    fallback_output: str = ""


# ============================================
# Conditional Chain
# ============================================

class ConditionalChain(ToolChain):
    """
    Extension of ToolChain with conditional step execution.
    
    Steps can have conditions that determine whether they run.
    Skipped steps use their fallback_output instead.
    """
    
    def __init__(
        self,
        name: str,
        steps: list[ConditionalStep],
        description: str = "",
        stop_on_error: bool = True,
    ):
        super().__init__(
            name=name,
            steps=steps,
            description=description,
            stop_on_error=stop_on_error,
        )
    
    async def execute(
        self,
        user_input: str,
        tools_map: Optional[dict] = None,
    ) -> ChainResult:
        """
        Execute chain with conditional step evaluation.
        
        For each step:
        1. Evaluate condition (if any)
        2. If True or no condition → execute tool
        3. If False → skip, use fallback_output
        """
        import time
        start_time = time.perf_counter()
        ctx = ChainContext(user_input=user_input)
        chain_result = ChainResult()
        
        if tools_map is None:
            tools_map = self._load_tools_map()
        
        logger.info(f"🔗 Starting conditional chain '{self.name}' ({len(self.steps)} steps)")
        
        for i, step in enumerate(self.steps):
            ctx.current_step = i
            
            # Check condition
            if isinstance(step, ConditionalStep) and step.condition is not None:
                should_run = step.condition(ctx)
                
                if not should_run:
                    logger.info(f"  ⏭️ Step {i+1} SKIPPED: {step.skip_message}")
                    ctx.step_outputs[i] = step.fallback_output
                    chain_result.step_results.append({
                        "step": i,
                        "tool_name": step.tool_name,
                        "success": True,
                        "skipped": True,
                        "skip_reason": step.skip_message,
                        "time_ms": 0,
                    })
                    continue
            
            # Execute step (delegate to parent logic)
            step_start = time.perf_counter()
            
            tool = tools_map.get(step.tool_name)
            if tool is None:
                error_msg = f"Tool '{step.tool_name}' not found"
                chain_result.step_results.append({
                    "step": i,
                    "tool_name": step.tool_name,
                    "success": False,
                    "error": error_msg,
                    "time_ms": 0,
                })
                if self.stop_on_error:
                    chain_result.error = error_msg
                    break
                continue
            
            try:
                import asyncio
                kwargs = {}
                for param, value_ref in step.input_mapping.items():
                    resolved = ctx.resolve_value(value_ref)
                    if step.transform and value_ref in ("$prev_output", "$user_input"):
                        resolved = step.transform(resolved)
                    kwargs[param] = resolved
                
                if asyncio.iscoroutinefunction(tool.coroutine):
                    output = await tool.ainvoke(kwargs)
                else:
                    output = tool.invoke(kwargs)
                
                output_str = str(output)
                ctx.step_outputs[i] = output_str
                
                step_time = (time.perf_counter() - step_start) * 1000
                logger.info(f"  ✅ Step {i+1} done ({step_time:.0f}ms)")
                
                chain_result.step_results.append({
                    "step": i,
                    "tool_name": step.tool_name,
                    "success": True,
                    "output_length": len(output_str),
                    "output_preview": output_str[:200],
                    "time_ms": round(step_time, 2),
                })
                
            except Exception as e:
                step_time = (time.perf_counter() - step_start) * 1000
                error_msg = f"Step {i+1} ({step.tool_name}) failed: {str(e)}"
                chain_result.step_results.append({
                    "step": i,
                    "tool_name": step.tool_name,
                    "success": False,
                    "error": str(e),
                    "time_ms": round(step_time, 2),
                })
                if self.stop_on_error:
                    chain_result.error = error_msg
                    break
        
        chain_result.total_time_ms = round(
            (time.perf_counter() - start_time) * 1000, 2
        )
        
        if not chain_result.error:
            chain_result.success = True
            last_step = len(self.steps) - 1
            chain_result.final_output = ctx.step_outputs.get(last_step, "")
        
        return chain_result
