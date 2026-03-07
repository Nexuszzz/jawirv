"""
JAWIR OS - Python Code Execution Tool
=======================================
Tool untuk menjalankan kode Python secara aman.
"""

import logging
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

logger = logging.getLogger("jawir.agent.tools.python")


class PythonCodeInput(BaseModel):
    """Input schema for Python code execution."""
    code: str = Field(description="Kode Python yang akan dieksekusi. Contoh: 'print(2+2)' atau 'import math; print(math.pi)'")


def create_python_executor_tool() -> StructuredTool:
    """Create Python code execution tool."""

    async def _run_python(code: str) -> str:
        """Execute Python code dan return output."""
        import subprocess
        import sys
        import tempfile
        import os

        try:
            # Write code to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_path = f.name

            # Execute with timeout
            result = subprocess.run(
                [sys.executable, temp_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(temp_path),
            )

            # Cleanup
            os.unlink(temp_path)

            output = ""
            if result.stdout:
                output += f"Output:\n{result.stdout}"
            if result.stderr:
                output += f"\nErrors:\n{result.stderr}"
            if not output.strip():
                output = "Code executed successfully (no output)"

            return output.strip()

        except subprocess.TimeoutExpired:
            return "❌ Error: Eksekusi timeout (maks 30 detik)"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    return StructuredTool.from_function(
        func=_run_python,
        coroutine=_run_python,
        name="run_python_code",
        description=(
            "Eksekusi kode Python dan return hasilnya. "
            "Gunakan untuk kalkulasi, data processing, atau menjalankan script sederhana. "
            "Timeout: 30 detik. Contoh: 'print(2**10)' atau perhitungan matematika."
        ),
        args_schema=PythonCodeInput,
    )
