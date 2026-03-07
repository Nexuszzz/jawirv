"""
JAWIR OS - Tool Chaining Framework
=====================================
Framework untuk chaining output tool A → input tool B.

Memungkinkan Gemini menyusun pipeline multi-step dimana
hasil satu tool menjadi input tool berikutnya.

Usage:
    from agent.tool_chain import ToolChain, ChainStep

    chain = ToolChain(
        name="search_and_design",
        steps=[
            ChainStep(tool_name="web_search", input_mapping={"query": "$user_input"}),
            ChainStep(tool_name="run_python_code", input_mapping={"code": "$prev_output"}),
        ]
    )
    result = await chain.execute(user_input="ESP32 pinout diagram")

Architecture:
    - ChainStep: Single step in a chain (tool_name + input_mapping)
    - ChainContext: Carries data between steps ($user_input, $prev_output, $step_N_output)
    - ToolChain: Ordered sequence of ChainSteps with execution logic
    - ChainRegistry: Named chains for reuse
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("jawir.agent.tool_chain")


# ============================================
# Data Structures
# ============================================

@dataclass
class ChainStep:
    """
    A single step in a tool chain.
    
    Attributes:
        tool_name: Name of the tool to execute (must exist in registry)
        input_mapping: Dict mapping tool param → value source
            Special values:
                "$user_input" → original user input
                "$prev_output" → output of previous step
                "$step_N_output" → output of step N (0-indexed)
                any other string → literal value
        transform: Optional function to transform prev output before passing
        description: Human-readable description of this step
    """
    tool_name: str
    input_mapping: dict[str, str] = field(default_factory=dict)
    transform: Optional[Any] = None  # Callable[[str], str]
    description: str = ""


@dataclass
class ChainContext:
    """
    Execution context carrying data between chain steps.
    
    Attributes:
        user_input: Original user input
        step_outputs: Dict of step_index → output string
        current_step: Index of current step
        metadata: Additional metadata
    """
    user_input: str = ""
    step_outputs: dict[int, str] = field(default_factory=dict)
    current_step: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def prev_output(self) -> str:
        """Get output of the previous step."""
        if self.current_step > 0:
            return self.step_outputs.get(self.current_step - 1, "")
        return self.user_input
    
    def resolve_value(self, value: str) -> str:
        """
        Resolve a value reference to its actual value.
        
        Args:
            value: Value reference string
            
        Returns:
            Resolved value
        """
        if value == "$user_input":
            return self.user_input
        elif value == "$prev_output":
            return self.prev_output
        elif value.startswith("$step_") and value.endswith("_output"):
            try:
                step_idx = int(value.replace("$step_", "").replace("_output", ""))
                return self.step_outputs.get(step_idx, "")
            except ValueError:
                return value
        else:
            return value  # Literal value


@dataclass
class ChainResult:
    """
    Result of a chain execution.
    
    Attributes:
        success: Whether all steps completed
        final_output: Output from the last step
        step_results: List of per-step results
        total_time_ms: Total execution time
        error: Error message if any step failed
    """
    success: bool = False
    final_output: str = ""
    step_results: list[dict] = field(default_factory=list)
    total_time_ms: float = 0.0
    error: str = ""


# ============================================
# Tool Chain
# ============================================

class ToolChain:
    """
    Ordered sequence of tool executions where output flows forward.
    
    Example:
        chain = ToolChain(
            name="research_and_summarize",
            steps=[
                ChainStep(
                    tool_name="web_search",
                    input_mapping={"query": "$user_input"},
                    description="Search for information"
                ),
                ChainStep(
                    tool_name="run_python_code",
                    input_mapping={
                        "code": "$prev_output"
                    },
                    transform=lambda output: f"text = '''{output}'''\\nprint(len(text.split()))",
                    description="Count words in search results"
                ),
            ]
        )
        result = await chain.execute(user_input="latest ESP32 news")
    """
    
    def __init__(
        self,
        name: str,
        steps: list[ChainStep],
        description: str = "",
        stop_on_error: bool = True,
    ):
        self.name = name
        self.steps = steps
        self.description = description
        self.stop_on_error = stop_on_error
    
    async def execute(
        self,
        user_input: str,
        tools_map: Optional[dict] = None,
    ) -> ChainResult:
        """
        Execute the chain from start to finish.
        
        Args:
            user_input: The original user input
            tools_map: Optional dict of tool_name → tool object.
                       If None, loads from registry.
        
        Returns:
            ChainResult with final output and step details
        """
        start_time = time.perf_counter()
        ctx = ChainContext(user_input=user_input)
        chain_result = ChainResult()
        
        # Load tools if not provided
        if tools_map is None:
            tools_map = self._load_tools_map()
        
        logger.info(f"🔗 Starting chain '{self.name}' ({len(self.steps)} steps)")
        
        for i, step in enumerate(self.steps):
            ctx.current_step = i
            step_start = time.perf_counter()
            
            logger.info(f"  Step {i+1}/{len(self.steps)}: {step.tool_name} "
                        f"({step.description or 'no description'})")
            
            # Check tool exists
            tool = tools_map.get(step.tool_name)
            if tool is None:
                error_msg = f"Tool '{step.tool_name}' not found in registry"
                logger.error(f"  ❌ {error_msg}")
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
            
            # Resolve input arguments
            try:
                kwargs = {}
                for param, value_ref in step.input_mapping.items():
                    resolved = ctx.resolve_value(value_ref)
                    
                    # Apply transform if provided
                    if step.transform and value_ref in ("$prev_output", "$user_input"):
                        resolved = step.transform(resolved)
                    
                    kwargs[param] = resolved
                
                # Execute tool
                if asyncio.iscoroutinefunction(tool.coroutine):
                    output = await tool.ainvoke(kwargs)
                else:
                    output = tool.invoke(kwargs)
                
                output_str = str(output)
                ctx.step_outputs[i] = output_str
                
                step_time = (time.perf_counter() - step_start) * 1000
                logger.info(f"  ✅ Step {i+1} done ({step_time:.0f}ms, "
                           f"output={len(output_str)} chars)")
                
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
                logger.error(f"  ❌ {error_msg}")
                
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
        
        # Finalize
        chain_result.total_time_ms = round(
            (time.perf_counter() - start_time) * 1000, 2
        )
        
        if not chain_result.error:
            chain_result.success = True
            # Final output is the last step's output
            last_step = len(self.steps) - 1
            chain_result.final_output = ctx.step_outputs.get(last_step, "")
        
        logger.info(f"🔗 Chain '{self.name}' completed: "
                    f"{'✅' if chain_result.success else '❌'} "
                    f"({chain_result.total_time_ms}ms)")
        
        return chain_result
    
    def _load_tools_map(self) -> dict:
        """Load tools from registry and build name→tool map."""
        from agent.tools_registry import get_all_tools
        tools = get_all_tools()
        return {t.name: t for t in tools}
    
    def __repr__(self) -> str:
        step_names = " → ".join(s.tool_name for s in self.steps)
        return f"ToolChain('{self.name}': {step_names})"


# ============================================
# Chain Registry (Named Chains)
# ============================================

class ChainRegistry:
    """
    Registry of named tool chains for reuse.
    
    Usage:
        registry = ChainRegistry()
        registry.register(my_chain)
        chain = registry.get("my_chain")
        result = await chain.execute(user_input="...")
    """
    
    _instance: Optional["ChainRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._chains = {}
        return cls._instance
    
    def register(self, chain: ToolChain) -> None:
        """Register a named chain."""
        self._chains[chain.name] = chain
        logger.info(f"📋 Chain registered: '{chain.name}' ({len(chain.steps)} steps)")
    
    def get(self, name: str) -> Optional[ToolChain]:
        """Get a chain by name."""
        return self._chains.get(name)
    
    def list_chains(self) -> list[str]:
        """List all registered chain names."""
        return list(self._chains.keys())
    
    def remove(self, name: str) -> bool:
        """Remove a chain by name."""
        if name in self._chains:
            del self._chains[name]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all registered chains."""
        self._chains.clear()
    
    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None
