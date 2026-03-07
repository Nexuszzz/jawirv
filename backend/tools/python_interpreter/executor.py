"""
JAWIR OS - Python Code Executor
================================
Execute Python code dengan session management dan safety features.
"""

import os
import sys
import subprocess
import tempfile
import traceback
import builtins
from io import StringIO
from typing import Dict, Any, Optional, List
from pathlib import Path


class ReplSession:
    """Manages a Python REPL session with persistent state."""
    
    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or os.getcwd()
        self.locals = {
            "__builtins__": builtins,
            "__name__": "__main__",
            "__doc__": None,
            "__package__": None,
        }
        self.history = []
        
    def execute(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute Python code in this session.
        
        Args:
            code: Python code to execute
            timeout: Optional timeout (not enforced for inline execution)
            
        Returns:
            Dict with stdout, stderr, result, and status
        """
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        # Save original streams
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout_capture, stderr_capture
        
        result_value = None
        status = 0
        
        try:
            # Change to working directory for execution
            old_cwd = os.getcwd()
            os.chdir(self.working_dir)
            
            try:
                # Try to evaluate as expression first
                try:
                    result_value = eval(code, self.locals)
                    if result_value is not None:
                        print(repr(result_value))
                except SyntaxError:
                    # If not an expression, execute as statement
                    exec(code, self.locals)
                    
            except Exception:
                traceback.print_exc()
                status = 1
            finally:
                os.chdir(old_cwd)
                
        finally:
            # Restore original streams
            sys.stdout, sys.stderr = old_stdout, old_stderr
            
        # Store in history
        self.history.append({
            "code": code,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "status": status
        })
            
        return {
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "result": result_value,
            "status": status
        }


class PythonExecutor:
    """
    Python Code Executor untuk JAWIR OS.
    Supports inline execution (fast) dan subprocess execution (isolated).
    """
    
    def __init__(self, working_dir: str = None):
        self.working_dir = Path(working_dir or "D:/sijawir/python_workspace").absolute()
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, ReplSession] = {}
        
    def get_session(self, session_id: str = "default") -> ReplSession:
        """Get or create a REPL session."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ReplSession(str(self.working_dir))
        return self.sessions[session_id]
    
    def execute_inline(self, code: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Execute code inline (fast, with state persistence).
        
        Args:
            code: Python code to execute
            session_id: Session ID for state persistence
            
        Returns:
            Dict with stdout, stderr, status
        """
        session = self.get_session(session_id)
        return session.execute(code)
    
    def execute_subprocess(self, code: str, timeout: int = 300) -> Dict[str, Any]:
        """
        Execute code in subprocess (isolated, no state).
        
        Args:
            code: Python code to execute
            timeout: Timeout in seconds
            
        Returns:
            Dict with stdout, stderr, status
        """
        temp_file = None
        try:
            # Create temp file
            fd, temp_file = tempfile.mkstemp(suffix='.py', text=True, dir=str(self.working_dir))
            
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(code)
                f.flush()
                os.fsync(f.fileno())
            
            # Windows compatibility
            if sys.platform == "win32":
                import time
                time.sleep(0.05)
            
            # Execute
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            result = subprocess.run(
                [sys.executable, temp_file],
                cwd=str(self.working_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creation_flags if sys.platform == "win32" else 0,
                encoding='utf-8',
                errors='replace',
                stdin=subprocess.DEVNULL
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds",
                "status": -1
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error executing code: {str(e)}",
                "status": -1
            }
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def execute(self, code: str, mode: str = "inline", session_id: str = "default", timeout: int = 300) -> Dict[str, Any]:
        """
        Execute Python code with specified mode.
        
        Args:
            code: Python code to execute
            mode: "inline" (fast, stateful) or "subprocess" (isolated)
            session_id: Session ID for inline mode
            timeout: Timeout for subprocess mode
            
        Returns:
            Dict with stdout, stderr, status
        """
        if mode == "inline":
            return self.execute_inline(code, session_id)
        else:
            return self.execute_subprocess(code, timeout)
    
    def clear_session(self, session_id: str = "default") -> bool:
        """Clear a session's state."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        sessions = []
        for session_id, session in self.sessions.items():
            sessions.append({
                "id": session_id,
                "history_count": len(session.history),
                "variables": len([k for k in session.locals.keys() if not k.startswith('__')])
            })
        return sessions
    
    def install_package(self, package_name: str, upgrade: bool = False) -> Dict[str, Any]:
        """Install a Python package."""
        cmd = [sys.executable, "-m", "pip", "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package_name)
        
        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                creationflags=creation_flags if sys.platform == "win32" else 0,
                encoding='utf-8',
                errors='replace'
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e)
            }
