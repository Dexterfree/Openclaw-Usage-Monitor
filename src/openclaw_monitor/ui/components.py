"""
UI components for OpenCLAW Token Usage Monitor.

This module provides reusable UI components for displaying
token usage information.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from rich.console import RenderableType
from rich.progress import BarColumn, Progress, TaskID, TextColumn
from rich.text import Text


def format_number(num: int, with_commas: bool = True) -> str:
    """
    Format a number with optional thousands separator.

    Args:
        num: Number to format
        with_commas: Whether to add thousands separator

    Returns:
        Formatted number string
    """
    if with_commas:
        return f"{num:,}"
    return str(num)


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format a percentage value.

    Args:
        value: Percentage value
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


def format_timestamp(
    dt: datetime,
    timezone_str: str = "UTC",
    format: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """
    Format a datetime for display.

    Args:
        dt: Datetime to format
        timezone_str: Target timezone
        format: strftime format string

    Returns:
        Formatted timestamp string
    """
    try:
        import pytz
        tz = pytz.timezone(timezone_str)
    except ImportError:
        tz = timezone.utc

    localized = dt.astimezone(tz)
    return localized.strftime(format)


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds as human-readable.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds / 60)
    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours}h"

    return f"{hours}h {remaining_minutes}m"


def format_time_until(
    target_time: datetime,
    current_time: Optional[datetime] = None,
    timezone_str: str = "UTC",
) -> str:
    """
    Format the time until a target datetime.

    Args:
        target_time: Target datetime
        current_time: Current time (defaults to now)
        timezone_str: Timezone for display

    Returns:
        Formatted time string
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    delta = target_time - current_time
    total_seconds = delta.total_seconds()

    if total_seconds <= 0:
        return "Now"

    duration = format_duration(total_seconds)

    # Also show the actual time
    target_str = format_timestamp(target_time, timezone_str, "%H:%M")

    return f"{duration} ({target_str})"


def create_progress_bar(
    current: int,
    total: int,
    width: int = 20,
    color: str = "cyan",
) -> str:
    """
    Create a text-based progress bar.

    Args:
        current: Current value
        total: Total value
        width: Width of the bar in characters
        color: Color name (for Rich markup)

    Returns:
        Progress bar string with Rich markup
    """
    if total == 0:
        percentage = 100
    else:
        percentage = min(100, int((current / total) * 100))

    filled = int((percentage / 100) * width)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    return f"[{color}]{bar}[/{color}]"


def create_token_usage_bar(
    used: int,
    limit: int,
    width: int = 20,
    theme: Optional[Dict[str, str]] = None,
) -> Tuple[str, str]:
    """
    Create a token usage progress bar with appropriate coloring.

    Args:
        used: Tokens used
        limit: Token limit (0 for unlimited)
        width: Width of the bar in characters
        theme: Theme colors dict

    Returns:
        Tuple of (bar_markup, color_name)
    """
    if limit == 0:
        # Unlimited - show full bar in neutral color
        bar = "█" * width
        return f"[dim]{bar}[/]", "dim"

    percentage = (used / limit) * 100

    # Determine color based on percentage
    if percentage >= 90:
        color = "red"
    elif percentage >= 75:
        color = "yellow"
    else:
        color = "green"

    filled = min(width, int((percentage / 100) * width))
    empty = width - filled

    bar = "█" * filled + "░" * empty
    return f"[{color}]{bar}[/{color}]", color


def format_model_distribution(
    distribution: Dict[str, int],
    total: int,
    width: int = 30,
) -> List[str]:
    """
    Format model distribution as a stacked bar.

    Args:
        distribution: Dict mapping model names to token counts
        total: Total tokens for percentage calculation
        width: Width of the bar in characters

    Returns:
        List of formatted strings
    """
    if not distribution or total == 0:
        return ["No model data"]

    # Colors for different models
    colors = ["blue", "cyan", "green", "yellow", "magenta", "red"]

    lines = []
    sorted_models = sorted(distribution.items(), key=lambda x: x[1], reverse=True)

    for i, (model, count) in enumerate(sorted_models[:5]):  # Top 5 models
        percentage = (count / total) * 100
        bar_width = int((percentage / 100) * width)
        color = colors[i % len(colors)]

        bar = "█" * bar_width
        line = f"[{color}]{bar}[/{color}] {model}: {format_number(count)} ({format_percentage(percentage)})"
        lines.append(line)

    return lines


def format_stat_value(
    label: str,
    value: Any,
    label_color: str = "cyan",
    value_color: str = "white",
) -> str:
    """
    Format a statistic label-value pair.

    Args:
        label: Statistic label
        value: Statistic value
        label_color: Color for label
        value_color: Color for value

    Returns:
        Formatted string with Rich markup
    """
    return f"[{label_color}]{label}:[/] [{value_color}]{value}[/{value_color}]"


def format_prediction_line(
    label: str,
    prediction: Optional[datetime],
    current_time: Optional[datetime] = None,
    timezone_str: str = "UTC",
    label_color: str = "cyan",
) -> str:
    """
    Format a prediction line with time until and target time.

    Args:
        label: Prediction label
        prediction: Predicted datetime (None for unknown)
        current_time: Current time
        timezone_str: Timezone for display
        label_color: Color for label

    Returns:
        Formatted string with Rich markup
    """
    if prediction is None:
        return f"[{label_color}]{label}:[/] [dim]Unknown[/]"

    time_until = format_time_until(prediction, current_time, timezone_str)
    return f"[{label_color}]{label}:[/] {time_until}"


def create_table_header(
    columns: List[str],
    widths: List[int],
) -> str:
    """
    Create a table header row.

    Args:
        columns: List of column names
        widths: List of column widths

    Returns:
        Formatted header row
    """
    parts = []
    for col, width in zip(columns, widths):
        padded = col.ljust(width)
        parts.append(f"[bold cyan]{padded}[/]")

    return " ".join(parts)


def create_table_row(
    values: List[str],
    widths: List[int],
    row_color: str = "white",
) -> str:
    """
    Create a table row.

    Args:
        values: List of cell values
        widths: List of column widths
        row_color: Color for the row

    Returns:
        Formatted row string
    """
    parts = []
    for value, width in zip(values, widths):
        padded = str(value).ljust(width)
        parts.append(f"[{row_color}]{padded}[/]")

    return " ".join(parts)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def get_status_indicator(
    percentage: float,
) -> str:
    """
    Get a status indicator based on percentage.

    Args:
        percentage: Percentage value

    Returns:
        Status indicator string
    """
    if percentage >= 100:
        return "✖"
    if percentage >= 90:
        return "⚠"
    if percentage >= 75:
        return "⚡"
    return "✓"
