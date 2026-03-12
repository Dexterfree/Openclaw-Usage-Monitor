"""
Theme definitions for OpenCLAW Token Usage Monitor.

This module provides color themes and styling for the terminal UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from rich.console import Console
from rich.theme import Theme as RichTheme


class ColorScheme(str, Enum):
    """Available color schemes."""

    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class Theme:
    """
    Terminal color theme configuration.

    Defines colors for different UI elements and states.
    """

    # Semantic colors
    success: str = "green"
    warning: str = "yellow"
    error: str = "red"
    info: str = "blue"
    value: str = "cyan"
    dim: str = "dim white"
    header: str = "bold magenta"

    # Token usage colors
    token_bar_ok: str = "green"
    token_bar_warning: str = "yellow"
    token_bar_critical: str = "red"

    # Progress bar colors
    progress_complete: str = "green"
    progress_remaining: str = "dim white"

    # Model colors (for distribution bars)
    model_colors: list[str] = (
        "blue",
        "cyan",
        "green",
        "yellow",
        "magenta",
        "red",
    )

    # Table colors
    table_header: str = "bold cyan"
    table_row: str = "white"
    table_border: str = "dim cyan"

    # Timestamp colors
    timestamp: str = "dim cyan"

    def to_rich_theme(self) -> RichTheme:
        """
        Convert to Rich Theme object.

        Returns:
            RichTheme for use with Console
        """
        return RichTheme({
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info,
            "value": self.value,
            "dim": self.dim,
            "header": self.header,
        })


# Light theme
LIGHT_THEME = Theme(
    success="green",
    warning="yellow",
    error="red",
    info="blue",
    value="blue",
    dim="dim black",
    header="bold magenta",
    token_bar_ok="green",
    token_bar_warning="yellow",
    token_bar_critical="red",
    progress_complete="green",
    progress_remaining="dim white",
    table_header="bold blue",
    table_row="black",
    table_border="dim blue",
    timestamp="dim blue",
)

# Dark theme (default)
DARK_THEME = Theme(
    success="green",
    warning="yellow",
    error="red",
    info="cyan",
    value="cyan",
    dim="dim white",
    header="bold magenta",
    token_bar_ok="green",
    token_bar_warning="yellow",
    token_bar_critical="red",
    progress_complete="green",
    progress_remaining="dim white",
    table_header="bold cyan",
    table_row="white",
    table_border="dim cyan",
    timestamp="dim cyan",
)


def get_theme(scheme: str = "auto") -> Theme:
    """
    Get the appropriate theme based on color scheme.

    Args:
        scheme: Color scheme ("auto", "light", "dark")

    Returns:
        Theme object
    """
    if scheme == ColorScheme.LIGHT:
        return LIGHT_THEME
    if scheme == ColorScheme.DARK:
        return DARK_THEME

    # Auto-detect terminal background
    return _detect_theme()


def _detect_theme() -> Theme:
    """
    Detect the terminal theme based on environment.

    Returns:
        Detected Theme object (defaults to dark)
    """
    import os

    # Check COLORFGBG environment variable (some terminals set this)
    colorfgbg = os.environ.get("COLORFGBG", "")
    if colorfgbg:
        try:
            # Format is usually "foreground;background"
            fg, bg = colorfgbg.split(";")[:2]
            bg_int = int(bg)
            # Background colors 0-7 are typically dark
            if bg_int > 7:
                return LIGHT_THEME
        except (ValueError, IndexError):
            pass

    # Default to dark theme
    return DARK_THEME


def create_console(theme: Optional[Theme] = None) -> Console:
    """
    Create a Rich Console with the given theme.

    Args:
        theme: Theme to use (defaults to auto-detected)

    Returns:
        Configured Console object
    """
    if theme is None:
        theme = get_theme()

    return Console(theme=theme.to_rich_theme())


# Legacy aliases for backward compatibility
def get_color_for_percentage(percentage: float, theme: Theme) -> str:
    """
    Get the appropriate color for a percentage value.

    Args:
        percentage: Percentage value (0-100+)
        theme: Theme to use for colors

    Returns:
        Color string
    """
    if percentage >= 90:
        return theme.token_bar_critical
    if percentage >= 75:
        return theme.token_bar_warning
    return theme.token_bar_ok


def get_status_color(status: str, theme: Theme) -> str:
    """
    Get the color for a status string.

    Args:
        status: Status string (ok, warning, error, etc.)
        theme: Theme to use for colors

    Returns:
        Color string
    """
    status_colors = {
        "ok": theme.success,
        "warning": theme.warning,
        "error": theme.error,
        "info": theme.info,
        "success": theme.success,
        "critical": theme.error,
    }
    return status_colors.get(status.lower(), theme.value)
