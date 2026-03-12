"""
Session display formatting for OpenCLAW Token Usage Monitor.

This module provides functions for formatting session-related displays.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from openclaw_monitor.core.models import SessionBlock, UsageEntry
from openclaw_monitor.data.analyzer import SessionSummary
from openclaw_monitor.ui.components import (
    format_duration,
    format_number,
    format_percentage,
    format_stat_value,
    format_timestamp,
)


def format_active_session_screen(
    session: Optional[SessionBlock],
    total_tokens: int,
    token_limit: int,
    burn_rate: float,
    message_count: int,
    model_distribution: Dict[str, int],
    predicted_time: Optional[datetime],
    reset_time: Optional[datetime],
    timezone_str: str = "UTC",
) -> List[str]:
    """
    Format the active session display screen.

    Args:
        session: Current active session block (if any)
        total_tokens: Total tokens used in current period
        token_limit: Token limit for the period
        burn_rate: Current burn rate in tokens/min
        message_count: Total message count
        model_distribution: Token distribution by model
        predicted_time: Predicted time when tokens will run out
        reset_time: Time when token limit resets
        timezone_str: Timezone for display

    Returns:
        List of formatted strings for display
    """
    screen = []

    # Header
    screen.append("[bold magenta]OpenCLAW Token Usage Monitor[/]")
    screen.append("")

    # Token usage section
    percentage = (total_tokens / token_limit * 100) if token_limit > 0 else 0
    if percentage >= 90:
        status_color = "red"
    elif percentage >= 75:
        status_color = "yellow"
    else:
        status_color = "green"

    if token_limit == 0:
        usage_bar = "[dim]░░░░░░░░░░░░░░░░░░[/] [dim]Unlimited[/]"
        percentage_str = "N/A"
    else:
        filled = int((percentage / 100) * 20)
        bar = "█" * filled + "░" * (20 - filled)
        usage_bar = f"[{status_color}]{bar}[/] {format_number(total_tokens)} / {format_number(token_limit)}"
        percentage_str = f"{percentage:.1f}%"

    screen.append(f"📊 [value]Token Usage:[/]          {usage_bar} {percentage_str}")
    screen.append("")

    # Model distribution
    screen.append("🤖 [value]Model Distribution:[/]")

    total = sum(model_distribution.values())
    for model, count in sorted(model_distribution.items(), key=lambda x: x[1], reverse=True)[:3]:
        if total > 0:
            model_pct = (count / total) * 100
            screen.append(f"   {model}: {format_number(count)} ({format_percentage(model_pct)})")

    screen.append("")

    # Burn rate
    screen.append(f"🔥 [value]Burn Rate:[/]              {burn_rate:.1f} [dim]tokens/min[/]")

    # Message count
    screen.append(f"📨 [value]Messages:[/]               {message_count}")

    screen.append("")

    # Time until reset
    if reset_time:
        now = datetime.now(timezone.utc)
        delta = reset_time - now
        if delta.total_seconds() > 0:
            time_str = format_duration(delta.total_seconds())
            reset_str = format_timestamp(reset_time, timezone_str, "%H:%M")
            screen.append(f"⏱️  [value]Time to Reset:[/]          {time_str} ({reset_str})")
        else:
            screen.append(f"⏱️  [value]Time to Reset:[/]          [error]Expired[/]")

    screen.append("")

    # Predictions
    screen.append("🔮 [value]Predictions:[/]")

    if token_limit == 0:
        screen.append("   [dim]Unlimited plan - no prediction needed[/]")
    elif predicted_time:
        pred_delta = predicted_time - datetime.now(timezone.utc)
        if pred_delta.total_seconds() > 0:
            time_until = format_duration(pred_delta.total_seconds())
            pred_time_str = format_timestamp(predicted_time, timezone_str, "%Y-%m-%d %H:%M")
            screen.append(f"   [info]Tokens will run out:[/] {time_until}")
            screen.append(f"   [dim]at {pred_time_str}[/]")
        else:
            screen.append("   [error]Tokens have been exhausted![/]")
    else:
        screen.append("   [dim]Unable to predict - insufficient data[/]")

    screen.append("")

    # Active session info
    if session:
        screen.append("💡 [value]Active Session:[/]")

        if session.start_time:
            start_str = format_timestamp(session.start_time, timezone_str, "%H:%M")
            screen.append(f"   Started: {start_str}")

        if session.duration:
            duration_str = format_duration(session.duration)
            screen.append(f"   Duration: {duration_str}")

        screen.append(f"   Messages: {session.message_count}")
        screen.append(f"   Session Tokens: {format_number(session.token_counts.total_tokens)}")

    screen.append("")

    return screen


def format_session_summary(
    summary: SessionSummary,
    timezone_str: str = "UTC",
) -> str:
    """
    Format a single session summary.

    Args:
        summary: SessionSummary to format
        timezone_str: Timezone for display

    Returns:
        Formatted string
    """
    lines = [
        f"[bold]{summary.model}[/]",
        f"  Time: {format_timestamp(summary.start_time, timezone_str, '%H:%M')} - "
        f"{format_timestamp(summary.end_time, timezone_str, '%H:%M')}",
        f"  Duration: {format_duration(summary.duration_minutes * 60)}",
        f"  Messages: {summary.message_count}",
        f"  Tokens: {format_number(summary.total_tokens)} "
        f"({format_number(summary.input_tokens)} in, {format_number(summary.output_tokens)} out)",
    ]

    return "\n".join(lines)


def create_sessions_table(
    sessions: List[SessionSummary],
    timezone_str: str = "UTC",
) -> Table:
    """
    Create a Rich table for session summaries.

    Args:
        sessions: List of SessionSummary objects
        timezone_str: Timezone for display

    Returns:
        Rich Table object
    """
    table = Table(title="Sessions", show_header=True, header_style="bold cyan")

    table.add_column("Time", style="dim", width=12)
    table.add_column("Model", width=20)
    table.add_column("Duration", width=10)
    table.add_column("Msgs", width=5)
    table.add_column("Tokens", width=12)

    for session in sessions:
        start_str = format_timestamp(session.start_time, timezone_str, "%H:%M")
        duration_str = format_duration(session.duration_minutes * 60)

        table.add_row(
            start_str,
            session.model[:20],
            duration_str,
            str(session.message_count),
            format_number(session.total_tokens),
        )

    return table
