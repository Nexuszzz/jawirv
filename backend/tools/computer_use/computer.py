# Copyright 2025-2026 JAWIR OS
# Base Computer Class - Abstract interface untuk browser environments
"""
Computer Base Class
===================
Abstract interface untuk browser automation environments.
Bisa diextend untuk Playwright, Browserbase, dll.
"""

import abc
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class EnvState:
    """State dari browser environment setelah action."""
    screenshot: bytes  # PNG screenshot
    url: str  # Current URL


class Computer(abc.ABC):
    """Abstract base class untuk browser environments."""

    @abc.abstractmethod
    def screen_size(self) -> tuple[int, int]:
        """Returns the screen size of the environment."""
        pass

    @abc.abstractmethod
    def open_web_browser(self) -> EnvState:
        """Opens the web browser."""
        pass

    @abc.abstractmethod
    def click_at(self, x: int, y: int) -> EnvState:
        """Clicks at a specific x, y coordinate on the webpage.
        
        The 'x' and 'y' values are absolute pixel coordinates.
        """
        pass

    @abc.abstractmethod
    def hover_at(self, x: int, y: int) -> EnvState:
        """Hovers at a specific x, y coordinate on the webpage.
        
        May be used to explore sub-menus that appear on hover.
        """
        pass

    @abc.abstractmethod
    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool = False,
        clear_before_typing: bool = True,
    ) -> EnvState:
        """Types text at a specific x, y coordinate.
        
        Args:
            x: X coordinate to click before typing
            y: Y coordinate to click before typing
            text: Text to type
            press_enter: Whether to press Enter after typing
            clear_before_typing: Whether to clear existing text first
        """
        pass

    @abc.abstractmethod
    def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> EnvState:
        """Scrolls the entire webpage."""
        pass

    @abc.abstractmethod
    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int = 800,
    ) -> EnvState:
        """Scrolls at a specific coordinate."""
        pass

    @abc.abstractmethod
    def wait_seconds(self, seconds: int = 5) -> EnvState:
        """Waits for specified seconds."""
        pass

    @abc.abstractmethod
    def go_back(self) -> EnvState:
        """Navigates back to the previous webpage."""
        pass

    @abc.abstractmethod
    def go_forward(self) -> EnvState:
        """Navigates forward to the next webpage."""
        pass

    @abc.abstractmethod
    def search(self) -> EnvState:
        """Jumps to search engine homepage."""
        pass

    @abc.abstractmethod
    def navigate(self, url: str) -> EnvState:
        """Navigates directly to a specified URL."""
        pass

    @abc.abstractmethod
    def key_combination(self, keys: list[str]) -> EnvState:
        """Presses keyboard keys and combinations.
        
        Example: ["control", "c"] for Ctrl+C
        """
        pass

    @abc.abstractmethod
    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        """Drag and drop from (x,y) to (destination_x, destination_y)."""
        pass

    @abc.abstractmethod
    def current_state(self) -> EnvState:
        """Returns the current state (screenshot + URL)."""
        pass
