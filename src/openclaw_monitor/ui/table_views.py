"""
Table views for OpenCLAW Token Usage Monitor.

This module provides table formatting for daily and monthly reports.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

from openclaw_monitor.data.aggregator import AggregatedPeriod
from openclaw_monitor.ui.components import format_number, format_percentage


def create_daily_table(
    periods: List[AggregatedPeriod],
    timezone_str: str = "UTC",
) -> Table:
    """
    Create a table showing daily token usage.

    Args:
        periods: List of daily AggregatedPeriod objects
        timezone_str: Timezone for display

    Returns:
        Rich Table object
    """
    table = Table(
        title="Daily Token Usage",
        show_header=True,
        header_style="bold cyan",
        border_style="dim cyan",
    )

    table.add_column("Date", style="white", width=12)
    table.add_column("Total Tokens", justify="right", style="white", width=14)
    table.add_column("Input", justify="right", style="dim", width=12)
    table.add_column("Output", justify="right", style="dim", width=12)
    table.add_column("Cache %", justify="right", style="cyan", width=10)
    table.add_column("Requests", justify="right", style="dim", width=10)
    table.add_column("Top Models", style="yellow", width=30)

    for period in periods:
        # Get top models for this day
        model_items = sorted(
            period.model_breakdowns.items(),
            key=lambda x: x[1].total_tokens,
            reverse=True,
        )[:2]

        top_models = ", ".join([m for m, _ in model_items])

        cache_pct = format_percentage(period.stats.cache_percentage)

        table.add_row(
            period.period_key,
            format_number(period.stats.total_tokens),
            format_number(period.stats.input_tokens),
            format_number(period.stats.output_tokens),
            cache_pct,
            str(period.stats.count),
            top_models,
        )

    return table


def create_monthly_table(
    periods: List[AggregatedPeriod],
    timezone_str: str = "UTC",
) -> Table:
    """
    Create a table showing monthly token usage.

    Args:
        periods: List of monthly AggregatedPeriod objects
        timezone_str: Timezone for display

    Returns:
        Rich Table object
    """
    table = Table(
        title="Monthly Token Usage",
        show_header=True,
        header_style="bold cyan",
        border_style="dim cyan",
    )

    table.add_column("Month", style="white", width=10)
    table.add_column("Total Tokens", justify="right", style="white", width=14)
    table.add_column("Input", justify="right", style="dim", width=12)
    table.add_column("Output", justify="right", style="dim", width=12)
    table.add_column("Cache %", justify="right", style="cyan", width=10)
    table.add_column("Requests", justify="right", style="dim", width=10)
    table.add_column("Top Models", style="yellow", width=30)

    for period in periods:
        # Get top models for this month
        model_items = sorted(
            period.model_breakdowns.items(),
            key=lambda x: x[1].total_tokens,
            reverse=True,
        )[:2]

        top_models = ", ".join([m for m, _ in model_items])

        cache_pct = format_percentage(period.stats.cache_percentage)

        table.add_row(
            period.period_key,
            format_number(period.stats.total_tokens),
            format_number(period.stats.input_tokens),
            format_number(period.stats.output_tokens),
            cache_pct,
            str(period.stats.count),
            top_models,
        )

    return table


def create_summary_table(
    total_stats: Dict[str, Any],
    period_info: Dict[str, Any],
    timezone_str: str = "UTC",
) -> Table:
    """
    Create a summary table for the overall statistics.

    Args:
        total_stats: Dictionary of total statistics
        period_info: Dictionary with period information
        timezone_str: Timezone for display

    Returns:
        Rich Table object
    """
    table = Table(
        title="Summary",
        show_header=False,
        border_style="dim cyan",
    )

    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Value", style="white")

    # Add rows
    table.add_row("Period", period_info.get("name", "Unknown"))
    table.add_row("Total Tokens", format_number(total_stats.get("total_tokens", 0)))
    table.add_row("Input Tokens", format_number(total_stats.get("input_tokens", 0)))
    table.add_row("Output Tokens", format_number(total_stats.get("output_tokens", 0)))

    cache_pct = format_percentage(
        total_stats.get("cache_percentage", 0)
    )
    table.add_row("Cache Percentage", cache_pct)

    table.add_row("Total Requests", str(total_stats.get("count", 0)))

    if period_info.get("duration_hours"):
        duration = f"{period_info['duration_hours']:.1f} hours"
        table.add_row("Duration", duration)

    return table


def create_model_breakdown_table(
    model_stats: Dict[str, Dict[str, int]],
    total_tokens: int,
) -> Table:
    """
    Create a table showing breakdown by model.

    Args:
        model_stats: Dictionary mapping model names to stats
        total_tokens: Total tokens for percentage calculation

    Returns:
        Rich Table object
    """
    table = Table(
        title="Model Breakdown",
        show_header=True,
        header_style="bold cyan",
        border_style="dim cyan",
    )

    table.add_column("Model", style="yellow", width=30)
    table.add_column("Tokens", justify="right", style="white", width=14)
    table.add_column("%", justify="right", style="cyan", width=8)
    table.add_column("Input", justify="right", style="dim", width=12)
    table.add_column("Output", justify="right", style="dim", width=12)
    table.add_column("Requests", justify="right", style="dim", width=10)

    # Sort by token count descending
    sorted_models = sorted(
        model_stats.items(),
        key=lambda x: x[1].get("total_tokens", 0),
        reverse=True,
    )

    for model, stats in sorted_models:
        tokens = stats.get("total_tokens", 0)
        percentage = (tokens / total_tokens * 100) if total_tokens > 0 else 0

        table.add_row(
            model,
            format_number(tokens),
            format_percentage(percentage),
            format_number(stats.get("input_tokens", 0)),
            format_number(stats.get("output_tokens", 0)),
            str(stats.get("count", 0)),
        )

    return table
