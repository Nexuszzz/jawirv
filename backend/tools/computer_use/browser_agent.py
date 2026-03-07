# Copyright 2025-2026 JAWIR OS
# Browser Agent - Gemini Computer Use Agent untuk browser automation
"""
Browser Agent
=============
Agent yang menggunakan Gemini Vision untuk browser automation.

Cara kerja:
1. Ambil screenshot dari browser
2. Kirim screenshot + query ke Gemini model
3. Model analyze visual & return function calls
4. Execute function calls via PlaywrightComputer
5. Repeat sampai task complete

Features:
- Vision-based automation (model "melihat" screenshot)
- Natural language task description
- Multi-step task execution
- Auto-retry & error handling
- Thinking mode (show reasoning)
"""

import os
import time
import base64
from typing import Literal, Optional, Union, Any, List

from .computer import Computer, EnvState

# Try import Google GenAI
try:
    from google import genai
    from google.genai import types
    from google.genai.types import (
        Part,
        GenerateContentConfig,
        Content,
        Candidate,
        FunctionResponse,
        FinishReason,
    )
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️ google-genai not installed. Run: pip install google-genai")


# Maximum screenshots to keep in conversation history
MAX_RECENT_SCREENSHOTS = 3

# Predefined browser control functions
BROWSER_FUNCTIONS = [
    "open_web_browser",
    "click_at",
    "hover_at",
    "type_text_at",
    "scroll_document",
    "scroll_at",
    "wait_seconds",
    "go_back",
    "go_forward",
    "search",
    "navigate",
    "key_combination",
    "drag_and_drop",
]


class BrowserAgent:
    """Agent untuk browser automation dengan Gemini Vision."""
    
    def __init__(
        self,
        browser_computer: Computer,
        query: str,
        model_name: str = "gemini-3-flash-preview",
        verbose: bool = True,
        max_iterations: int = 20,
    ):
        """
        Initialize BrowserAgent.
        
        Args:
            browser_computer: PlaywrightComputer instance
            query: Natural language task description
            model_name: Gemini model to use
            verbose: Show detailed output
            max_iterations: Maximum iterations before stopping
        """
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai not installed. Run: pip install google-genai")
        
        self._browser = browser_computer
        self._query = query
        self._model_name = model_name
        self._verbose = verbose
        self._max_iterations = max_iterations
        self._iteration = 0
        self.final_result = None
        
        # Initialize Gemini client
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY atau GOOGLE_API_KEY environment variable tidak ditemukan!")
        
        self._client = genai.Client(api_key=api_key)
        
        # Conversation history
        self._contents: List[Content] = []
        
        # System instruction
        self._system_instruction = """You are JAWIR Browser Agent, an AI assistant that controls a web browser to complete tasks.

IMPORTANT RULES:
1. You can ONLY see what's on the screen through screenshots
2. You MUST use the provided functions to interact with the browser
3. Coordinates are in pixels, relative to the browser viewport
4. Always wait for pages to load after navigation
5. If a task cannot be completed, explain why

AVAILABLE FUNCTIONS:
- click_at(x, y): Click at coordinates
- type_text_at(x, y, text, press_enter, clear_before_typing): Type text
- scroll_document(direction): Scroll page (up/down/left/right)
- scroll_at(x, y, direction, magnitude): Scroll at position
- navigate(url): Go to URL
- go_back(): Browser back
- go_forward(): Browser forward
- search(): Go to search engine
- key_combination(keys): Press key combo (e.g., ["control", "c"])
- wait_seconds(seconds): Wait for loading
- hover_at(x, y): Hover at position
- drag_and_drop(x, y, destination_x, destination_y): Drag element

When task is complete, respond with your final answer WITHOUT any function calls.
"""

    def _create_initial_message(self) -> Content:
        """Create initial message with screenshot."""
        # Get current state
        state = self._browser.current_state()
        
        # Encode screenshot
        screenshot_b64 = base64.b64encode(state.screenshot).decode('utf-8')
        
        return Content(
            role="user",
            parts=[
                Part(text=f"Task: {self._query}\n\nCurrent URL: {state.url}"),
                Part(inline_data=types.Blob(
                    mime_type="image/png",
                    data=state.screenshot
                ))
            ]
        )

    def _get_model_response(self, max_retries: int = 3) -> Optional[Any]:
        """Get response from Gemini model."""
        for attempt in range(max_retries):
            try:
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=self._contents,
                    config=GenerateContentConfig(
                        system_instruction=self._system_instruction,
                        temperature=0.7,
                        max_output_tokens=4096,
                        tools=[
                            types.Tool(function_declarations=self._get_function_declarations())
                        ]
                    )
                )
                return response
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️ API error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    print(f"❌ API failed after {max_retries} attempts: {e}")
                    return None
        return None

    def _get_function_declarations(self) -> List[types.FunctionDeclaration]:
        """Get function declarations for Gemini."""
        return [
            types.FunctionDeclaration(
                name="click_at",
                description="Click at specific x,y coordinates on the webpage",
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X coordinate in pixels"},
                        "y": {"type": "integer", "description": "Y coordinate in pixels"},
                    },
                    "required": ["x", "y"]
                }
            ),
            types.FunctionDeclaration(
                name="type_text_at",
                description="Type text at specific coordinates",
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "X coordinate"},
                        "y": {"type": "integer", "description": "Y coordinate"},
                        "text": {"type": "string", "description": "Text to type"},
                        "press_enter": {"type": "boolean", "description": "Press Enter after typing"},
                        "clear_before_typing": {"type": "boolean", "description": "Clear existing text first"},
                    },
                    "required": ["x", "y", "text"]
                }
            ),
            types.FunctionDeclaration(
                name="scroll_document",
                description="Scroll the entire webpage",
                parameters={
                    "type": "object",
                    "properties": {
                        "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                    },
                    "required": ["direction"]
                }
            ),
            types.FunctionDeclaration(
                name="scroll_at",
                description="Scroll at specific position",
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                        "magnitude": {"type": "integer", "description": "Scroll amount in pixels"},
                    },
                    "required": ["x", "y", "direction"]
                }
            ),
            types.FunctionDeclaration(
                name="navigate",
                description="Navigate to a URL",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to navigate to"},
                    },
                    "required": ["url"]
                }
            ),
            types.FunctionDeclaration(
                name="go_back",
                description="Go back to previous page",
                parameters={"type": "object", "properties": {}}
            ),
            types.FunctionDeclaration(
                name="go_forward",
                description="Go forward to next page",
                parameters={"type": "object", "properties": {}}
            ),
            types.FunctionDeclaration(
                name="search",
                description="Go to search engine homepage",
                parameters={"type": "object", "properties": {}}
            ),
            types.FunctionDeclaration(
                name="key_combination",
                description="Press keyboard shortcut",
                parameters={
                    "type": "object",
                    "properties": {
                        "keys": {"type": "string", "description": "Keys separated by + (e.g., control+c)"},
                    },
                    "required": ["keys"]
                }
            ),
            types.FunctionDeclaration(
                name="wait_seconds",
                description="Wait for page to load",
                parameters={
                    "type": "object",
                    "properties": {
                        "seconds": {"type": "integer", "description": "Seconds to wait"},
                    },
                    "required": ["seconds"]
                }
            ),
            types.FunctionDeclaration(
                name="hover_at",
                description="Hover mouse at coordinates",
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                    },
                    "required": ["x", "y"]
                }
            ),
            types.FunctionDeclaration(
                name="drag_and_drop",
                description="Drag from one position to another",
                parameters={
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer", "description": "Start X"},
                        "y": {"type": "integer", "description": "Start Y"},
                        "destination_x": {"type": "integer", "description": "End X"},
                        "destination_y": {"type": "integer", "description": "End Y"},
                    },
                    "required": ["x", "y", "destination_x", "destination_y"]
                }
            ),
        ]

    def _handle_action(self, function_call: Any) -> EnvState:
        """Execute function call and return new state."""
        name = function_call.name
        args = function_call.args or {}
        
        if self._verbose:
            print(f"  🎯 {name}({args})")
        
        if name == "click_at":
            return self._browser.click_at(args["x"], args["y"])
        elif name == "type_text_at":
            return self._browser.type_text_at(
                x=args["x"],
                y=args["y"],
                text=args["text"],
                press_enter=args.get("press_enter", False),
                clear_before_typing=args.get("clear_before_typing", True),
            )
        elif name == "scroll_document":
            return self._browser.scroll_document(args["direction"])
        elif name == "scroll_at":
            return self._browser.scroll_at(
                x=args["x"],
                y=args["y"],
                direction=args["direction"],
                magnitude=args.get("magnitude", 800),
            )
        elif name == "navigate":
            return self._browser.navigate(args["url"])
        elif name == "go_back":
            return self._browser.go_back()
        elif name == "go_forward":
            return self._browser.go_forward()
        elif name == "search":
            return self._browser.search()
        elif name == "key_combination":
            keys = args["keys"].split("+")
            return self._browser.key_combination(keys)
        elif name == "wait_seconds":
            return self._browser.wait_seconds(args.get("seconds", 5))
        elif name == "hover_at":
            return self._browser.hover_at(args["x"], args["y"])
        elif name == "drag_and_drop":
            return self._browser.drag_and_drop(
                x=args["x"],
                y=args["y"],
                destination_x=args["destination_x"],
                destination_y=args["destination_y"],
            )
        else:
            raise ValueError(f"Unknown function: {name}")

    def _extract_text(self, candidate: Candidate) -> Optional[str]:
        """Extract text from response."""
        if not candidate.content or not candidate.content.parts:
            return None
        
        texts = []
        for part in candidate.content.parts:
            if hasattr(part, 'text') and part.text:
                texts.append(part.text)
        
        return " ".join(texts) if texts else None

    def _extract_function_calls(self, candidate: Candidate) -> List[Any]:
        """Extract function calls from response."""
        if not candidate.content or not candidate.content.parts:
            return []
        
        calls = []
        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                calls.append(part.function_call)
        
        return calls

    def run_one_iteration(self) -> Literal["COMPLETE", "CONTINUE", "ERROR"]:
        """Run one iteration of the agent loop."""
        self._iteration += 1
        
        if self._iteration > self._max_iterations:
            print(f"⚠️ Reached max iterations ({self._max_iterations})")
            return "COMPLETE"
        
        if self._verbose:
            print(f"\n{'='*50}")
            print(f"🔄 Iteration {self._iteration}")
            print(f"{'='*50}")
        
        # Get model response
        response = self._get_model_response()
        if not response or not response.candidates:
            print("❌ No response from model")
            return "ERROR"
        
        candidate = response.candidates[0]
        
        # Add model response to history
        if candidate.content:
            self._contents.append(candidate.content)
        
        # Extract reasoning and function calls
        reasoning = self._extract_text(candidate)
        function_calls = self._extract_function_calls(candidate)
        
        if self._verbose and reasoning:
            print(f"\n💭 Reasoning: {reasoning[:200]}...")
        
        # If no function calls, task is complete
        if not function_calls:
            if self._verbose:
                print(f"\n✅ Task Complete!")
                if reasoning:
                    print(f"📝 Result: {reasoning}")
            self.final_result = reasoning
            return "COMPLETE"
        
        # Execute function calls
        function_responses = []
        for fc in function_calls:
            try:
                state = self._handle_action(fc)
                
                # Create function response with screenshot
                function_responses.append(
                    FunctionResponse(
                        name=fc.name,
                        response={"url": state.url, "status": "success"}
                    )
                )
                
                # Add screenshot as next user message
                self._contents.append(
                    Content(
                        role="user",
                        parts=[
                            Part(text=f"Action {fc.name} completed. Current URL: {state.url}"),
                            Part(inline_data=types.Blob(
                                mime_type="image/png",
                                data=state.screenshot
                            ))
                        ]
                    )
                )
                
            except Exception as e:
                print(f"❌ Action error: {e}")
                function_responses.append(
                    FunctionResponse(
                        name=fc.name,
                        response={"error": str(e), "status": "failed"}
                    )
                )
        
        # Cleanup old screenshots to save tokens
        self._cleanup_old_screenshots()
        
        return "CONTINUE"

    def _cleanup_old_screenshots(self):
        """Remove old screenshots to prevent token overflow."""
        screenshot_count = 0
        for content in reversed(self._contents):
            if content.role == "user" and content.parts:
                has_image = any(
                    hasattr(part, 'inline_data') and part.inline_data
                    for part in content.parts
                )
                if has_image:
                    screenshot_count += 1
                    if screenshot_count > MAX_RECENT_SCREENSHOTS:
                        # Remove image data from old messages
                        content.parts = [
                            part for part in content.parts
                            if not (hasattr(part, 'inline_data') and part.inline_data)
                        ]

    def run(self) -> str:
        """Run the agent until completion."""
        print(f"\n🚀 Starting Browser Agent")
        print(f"📋 Task: {self._query}")
        print(f"🤖 Model: {self._model_name}")
        
        # Initialize with first screenshot
        self._contents.append(self._create_initial_message())
        
        # Agent loop
        status = "CONTINUE"
        while status == "CONTINUE":
            status = self.run_one_iteration()
        
        if status == "ERROR":
            return "Task failed due to errors"
        
        return self.final_result or "Task completed"


# ============================================
# SIMPLIFIED BROWSER TASK FUNCTIONS
# ============================================

def run_browser_task(
    task: str,
    initial_url: str = "https://www.google.com",
    headless: bool = False,
    model: str = "gemini-3-flash-preview",
    verbose: bool = True,
) -> str:
    """
    Run a browser task using Gemini Computer Use.
    
    Args:
        task: Natural language task description
        initial_url: Starting URL
        headless: Run browser without GUI
        model: Gemini model to use
        verbose: Show detailed output
    
    Returns:
        Result string
    
    Example:
        result = run_browser_task("Search for Python tutorials on YouTube")
    """
    from .playwright_computer import PlaywrightComputer
    
    try:
        with PlaywrightComputer(
            initial_url=initial_url,
            headless=headless,
            highlight_mouse=verbose,
        ) as browser:
            agent = BrowserAgent(
                browser_computer=browser,
                query=task,
                model_name=model,
                verbose=verbose,
            )
            return agent.run()
    except Exception as e:
        return f"Error: {e}"


def browse_and_search(query: str, search_engine: str = "google") -> str:
    """
    Search something on web using browser automation.
    
    Args:
        query: Search query
        search_engine: google, youtube, bing
    
    Returns:
        Result string
    """
    engine_urls = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "bing": "https://www.bing.com",
    }
    
    url = engine_urls.get(search_engine.lower(), "https://www.google.com")
    task = f"Search for '{query}' and tell me the top results"
    
    return run_browser_task(task=task, initial_url=url)


def fill_web_form(url: str, form_data: dict, submit: bool = True) -> str:
    """
    Fill a web form automatically.
    
    Args:
        url: URL of the form page
        form_data: Dictionary of field names/labels and values
        submit: Whether to submit the form
    
    Returns:
        Result string
    """
    fields_str = ", ".join([f"{k}: {v}" for k, v in form_data.items()])
    task = f"Fill the form with: {fields_str}"
    if submit:
        task += ". Then submit the form."
    
    return run_browser_task(task=task, initial_url=url)
