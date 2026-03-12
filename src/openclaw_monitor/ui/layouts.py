"""
Layout definitions for OpenCLAW Token Usage Monitor.

This module provides layout templates for different view modes.
"""

from __future__ import annotations

from typing import List, Optional


class Layout:
    """Base layout class."""

    def get_template(self) -> List[str]:
        """Get the layout template as a list of strings."""
        return []


class RealtimeLayout(Layout):
    """Layout for realtime monitoring view."""

    def get_template(self) -> List[str]:
        """Get the realtime monitoring layout template."""
        return [
            "",  # Spacing
            "{header}",
            "",
            "{status_line}",
            "",
            "{token_usage_section}",
            "{model_distribution_section}",
            "{session_section}",
            "",
            "{prediction_section}",
            "",
            "{footer}",
        ]


class DailyLayout(Layout):
    """Layout for daily report view."""

    def get_template(self) -> List[str]:
        """Get the daily report layout template."""
        return [
            "",
            "{header}",
            "",
            "{summary_section}",
            "",
            "{daily_table}",
            "",
            "{footer}",
        ]


class MonthlyLayout(Layout):
    """Layout for monthly report view."""

    def get_template(self) -> List[str]:
        """Get the monthly report layout template."""
        return [
            "",
            "{header}",
            "",
            "{summary_section}",
            "",
            "{monthly_table}",
            "",
            "{footer}",
        ]


def get_layout(view_mode: str) -> Layout:
    """
    Get the appropriate layout for a view mode.

    Args:
        view_mode: View mode (realtime, daily, monthly)

    Returns:
        Layout object for the view mode
    """
    layouts = {
        "realtime": RealtimeLayout(),
        "daily": DailyLayout(),
        "monthly": MonthlyLayout(),
    }

    return layouts.get(view_mode, RealtimeLayout())


def format_header(
    title: str,
    subtitle: str = "",
    width: int = 80,
) -> str:
    """
    Format a header for the display.

    Args:
        title: Main title
        subtitle: Optional subtitle
        width: Display width

    Returns:
        Formatted header string
    """
    lines = [f"[bold magenta]{title}[/]"]

    if subtitle:
        lines.append(f"[dim]{subtitle}[/]")

    return "\n".join(lines)


def format_footer(
    refresh_info: str = "",
    help_info: str = "Press Ctrl+C to exit",
) -> str:
    """
    Format a footer for the display.

    Args:
        refresh_info: Refresh rate or timing info
        help_info: Help text for controls

    Returns:
        Formatted footer string
    """
    parts = []

    if refresh_info:
        parts.append(f"[dim]{refresh_info}[/]")

    if help_info:
        parts.append(f"[dim]{help_info}[/]")

    return " | ".join(parts)
