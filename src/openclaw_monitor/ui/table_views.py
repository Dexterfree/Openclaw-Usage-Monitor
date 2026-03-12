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


def create_hourly_table(
    periods: List[AggregatedPeriod],
    timezone_str: str = "UTC",
) -> Table:
    """
    Create a table showing hourly token usage.

    Args:
        periods: List of hourly AggregatedPeriod objects
        timezone_str: Timezone for display

    Returns:
        Rich Table object
    """
    table = Table(
        title="Hourly Token Usage",
        show_header=True,
        header_style="bold cyan",
        border_style="dim cyan",
    )

    table.add_column("Time", style="white", width=16)
    table.add_column("Total", justify="right", style="white", width=12)
    table.add_column("Input", justify="right", style="green", width=10)
    table.add_column("Output", justify="right", style="blue", width=10)
    table.add_column("Cache R", justify="right", style="cyan", width=10)
    table.add_column("Cache W", justify="right", style="magenta", width=10)
    table.add_column("Reqs", justify="right", style="dim", width=6)
    table.add_column("Models", style="yellow", width=25)

    for period in periods:
        # Get top models for this hour
        model_items = sorted(
            period.model_breakdowns.items(),
            key=lambda x: x[1].total_tokens,
            reverse=True,
        )[:2]

        top_models = ", ".join([m for m, _ in model_items]) if model_items else "-"

        table.add_row(
            period.period_key,
            format_number(period.stats.total_tokens),
            format_number(period.stats.input_tokens),
            format_number(period.stats.output_tokens),
            format_number(period.stats.cache_read_tokens),
            format_number(period.stats.cache_creation_tokens),
            str(period.stats.count),
            top_models,
        )

    return table


def create_detailed_model_table(
    model_breakdown: List[tuple],
    total_tokens: int,
) -> Table:
    """
    Create a detailed table showing model breakdown with all metrics.

    Args:
        model_breakdown: List of (model, stats, percentage) tuples
        total_tokens: Total tokens for percentage calculation

    Returns:
        Rich Table object
    """
    table = Table(
        title="Model Detailed Breakdown",
        show_header=True,
        header_style="bold cyan",
        border_style="dim cyan",
    )

    table.add_column("Model", style="yellow", width=30)
    table.add_column("Total", justify="right", style="white", width=14)
    table.add_column("%", justify="right", style="cyan", width=8)
    table.add_column("Input", justify="right", style="green", width=12)
    table.add_column("Output", justify="right", style="blue", width=12)
    table.add_column("Cache R", justify="right", style="cyan", width=10)
    table.add_column("Cache W", justify="right", style="magenta", width=10)
    table.add_column("Reqs", justify="right", style="dim", width=8)
    table.add_column("I/O Ratio", justify="right", style="white", width=10)

    for model, stats, percentage in model_breakdown:
        io_ratio = stats.output_ratio if stats.input_tokens > 0 else 0

        table.add_row(
            model,
            format_number(stats.total_tokens),
            format_percentage(percentage),
            format_number(stats.input_tokens),
            format_number(stats.output_tokens),
            format_number(stats.cache_read_tokens),
            format_number(stats.cache_creation_tokens),
            str(stats.count),
            f"{io_ratio:.2f}",
        )

    return table


def create_provider_table(
    provider_breakdown: List[tuple],
    total_tokens: int,
) -> Table:
    """
    Create a table showing breakdown by provider.

    Args:
        provider_breakdown: List of (provider, stats, percentage) tuples
        total_tokens: Total tokens for percentage calculation

    Returns:
        Rich Table object
    """
    table = Table(
        title="Provider Breakdown",
        show_header=True,
        header_style="bold cyan",
        border_style="dim cyan",
    )

    table.add_column("Provider", style="yellow", width=20)
    table.add_column("Total", justify="right", style="white", width=14)
    table.add_column("%", justify="right", style="cyan", width=8)
    table.add_column("Input", justify="right", style="green", width=12)
    table.add_column("Output", justify="right", style="blue", width=12)
    table.add_column("Cache", justify="right", style="cyan", width=12)
    table.add_column("Reqs", justify="right", style="dim", width=8)

    for provider, stats, percentage in provider_breakdown:
        table.add_row(
            provider,
            format_number(stats.total_tokens),
            format_percentage(percentage),
            format_number(stats.input_tokens),
            format_number(stats.output_tokens),
            format_number(stats.cache_read_tokens + stats.cache_creation_tokens),
            str(stats.count),
        )

    return table


def create_token_type_table(
    token_breakdown: Dict[str, int],
    total_tokens: int,
) -> Table:
    """
    Create a table showing breakdown by token type.

    Args:
        token_breakdown: Dictionary with token type counts
        total_tokens: Total tokens for percentage calculation

    Returns:
        Rich Table object
    """
    table = Table(
        title="Token Type Breakdown",
        show_header=True,
        header_style="bold cyan",
        border_style="dim cyan",
    )

    table.add_column("Token Type", style="cyan", width=20)
    table.add_column("Count", justify="right", style="white", width=16)
    table.add_column("Percentage", justify="right", style="yellow", width=12)
    table.add_column("Description", style="dim", width=40)

    token_types = [
        ("Input Tokens", token_breakdown.get("input_tokens", 0), "Tokens sent to the LLM"),
        ("Output Tokens", token_breakdown.get("output_tokens", 0), "Tokens generated by the LLM"),
        ("Cache Read", token_breakdown.get("cache_read_tokens", 0), "Tokens read from prompt cache"),
        ("Cache Write", token_breakdown.get("cache_creation_tokens", 0), "Tokens written to prompt cache"),
    ]

    for name, count, description in token_types:
        percentage = (count / total_tokens * 100) if total_tokens > 0 else 0

        # Color coding
        style_map = {
            "Input Tokens": "green",
            "Output Tokens": "blue",
            "Cache Read": "cyan",
            "Cache Write": "magenta",
        }
        style = style_map.get(name, "white")

        table.add_row(
            f"[{style}]{name}[/{style}]",
            format_number(count),
            format_percentage(percentage),
            description,
        )

    return table
