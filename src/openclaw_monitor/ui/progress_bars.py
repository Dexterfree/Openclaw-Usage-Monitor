"""
Progress bars for OpenCLAW Token Usage Monitor.

This module provides progress bar components for displaying
token usage and other metrics.
"""

from __future__ import annotations

from typing import Optional, Tuple

from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn
from rich.console import Console
from rich.text import Text


def create_usage_progress_bar(
    used: int,
    limit: int,
    label: str = "",
    width: int = 40,
    console: Optional[Console] = None,
) -> str:
    """
    Create a token usage progress bar.

    Args:
        used: Current token usage
        limit: Token limit (0 for unlimited)
        label: Optional label for the bar
        width: Width of the progress bar
        console: Console for rendering

    Returns:
        Formatted progress bar string
    """
    if limit == 0:
        # Unlimited - show a full bar with different style
        bar = "█" * width
        percentage = 100.0
        color = "dim"
    else:
        percentage = min(100, (used / limit) * 100)

        # Determine color based on percentage
        if percentage >= 90:
            color = "red"
        elif percentage >= 75:
            color = "yellow"
        else:
            color = "green"

        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)

    # Format the usage text
    if limit == 0:
        usage_text = f"{used:,} / ∞"
    else:
        usage_text = f"{used:,} / {limit:,}"

    label_part = f"{label}: " if label else ""

    return f"[{color}]{bar}[/] {label_part}[white]{usage_text}[/] ([{color}]{percentage:.1f}%[/])"


def create_multi_bar_display(
    values: list[tuple[str, int, int]],
    width: int = 30,
) -> list[str]:
    """
    Create multiple progress bars for display.

    Args:
        values: List of (label, used, limit) tuples
        width: Width of each bar

    Returns:
        List of formatted bar strings
    """
    lines = []

    for label, used, limit in values:
        bar = create_usage_progress_bar(used, limit, label, width)
        lines.append(bar)

    return lines


def create_model_distribution_bar(
    distribution: dict[str, int],
    total: int,
    width: int = 40,
) -> list[str]:
    """
    Create a stacked bar showing model distribution.

    Args:
        distribution: Dict mapping model names to token counts
        total: Total tokens
        width: Width of the stacked bar

    Returns:
        List of formatted strings showing the distribution
    """
    if not distribution or total == 0:
        return ["[dim]No model data[/]"]

    colors = ["blue", "cyan", "green", "yellow", "magenta", "red"]
    lines = []

    sorted_models = sorted(distribution.items(), key=lambda x: x[1], reverse=True)

    # Create the stacked bar
    stacked_parts = []
    remaining = width

    for i, (model, count) in enumerate(sorted_models):
        if remaining <= 0:
            break

        percentage = (count / total) * 100
        bar_width = max(1, min(remaining, int((percentage / 100) * width)))
        color = colors[i % len(colors)]

        stacked_parts.append(f"[{color}]{"█" * bar_width}[/]")
        remaining -= bar_width

    stacked_bar = "".join(stacked_parts)

    # Create legend lines
    legend_lines = []
    for i, (model, count) in enumerate(sorted_models[:5]):
        percentage = (count / total) * 100
        color = colors[i % len(colors)]
        legend_lines.append(
            f"  [{color}]■[/{color}] {model}: {count:,} ({percentage:.1f}%)"
        )

    # Combine stacked bar with legend
    lines.append(stacked_bar)
    lines.extend(legend_lines)

    return lines


def create_time_until_bar(
    current: int,
    limit: int,
    reset_time_str: str,
    width: int = 30,
) -> str:
    """
    Create a bar showing time until reset with current usage.

    Args:
        current: Current token usage
        limit: Token limit
        reset_time_str: String showing time until reset
        width: Width of the bar

    Returns:
        Formatted bar string
    """
    if limit == 0:
        return f"[dim]{'░' * width}[/] ∞ until reset"

    percentage = min(100, (current / limit) * 100)

    if percentage >= 90:
        color = "red"
    elif percentage >= 75:
        color = "yellow"
    else:
        color = "green"

    filled = int((percentage / 100) * width)
    bar = "█" * filled + "░" * (width - filled)

    return f"[{color}]{bar}[/] {reset_time_str} until reset"


def get_bar_color(percentage: float) -> str:
    """
    Get the appropriate color for a percentage value.

    Args:
        percentage: Percentage value (0-100+)

    Returns:
        Color name for Rich markup
    """
    if percentage >= 100:
        return "bright_red"
    if percentage >= 90:
        return "red"
    if percentage >= 75:
        return "yellow"
    if percentage >= 50:
        return "cyan"
    return "green"


def create_simple_bar(
    value: int,
    maximum: int,
    width: int = 20,
    color: str = "cyan",
) -> str:
    """
    Create a simple progress bar.

    Args:
        value: Current value
        maximum: Maximum value
        width: Bar width
        color: Bar color

    Returns:
        Formatted bar string
    """
    if maximum == 0:
        percentage = 100
    else:
        percentage = min(100, (value / maximum) * 100)

    filled = int((percentage / 100) * width)
    bar = "█" * filled + "░" * (width - filled)

    return f"[{color}]{bar}[/]"
