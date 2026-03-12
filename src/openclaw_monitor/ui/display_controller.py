"""
Display controller for OpenCLAW Token Usage Monitor.

This module controls the overall display and rendering of
token usage information.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table

from openclaw_monitor.core.models import SessionBlock, UsageEntry
from openclaw_monitor.core.plans import (
    get_percentage_used,
    get_tokens_remaining,
)
from openclaw_monitor.data.aggregator import (
    AggregatedPeriod,
    get_total_stats,
    aggregate_by_hour,
    get_model_breakdown_details,
    get_provider_breakdown_details,
    get_token_type_breakdown,
)
from openclaw_monitor.data.analyzer import SessionAnalyzer
from openclaw_monitor.data.analysis import UsageAnalysis
from openclaw_monitor.terminal.themes import Theme, get_theme
from openclaw_monitor.ui.components import (
    format_duration,
    format_number,
    format_time_until,
    format_timestamp,
)
from openclaw_monitor.ui.progress_bars import (
    create_model_distribution_bar,
    create_usage_progress_bar,
)
from openclaw_monitor.ui.session_display import format_active_session_screen
from openclaw_monitor.ui.table_views import (
    create_daily_table,
    create_model_breakdown_table,
    create_monthly_table,
    create_summary_table,
    create_hourly_table,
    create_detailed_model_table,
    create_provider_table,
    create_token_type_table,
)

logger = logging.getLogger(__name__)


class DisplayController:
    """
    Main controller for displaying token usage information.

    Handles rendering for different view modes (realtime, daily, monthly).
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        theme: Optional[Theme] = None,
        timezone_str: str = "UTC",
    ):
        """
        Initialize the display controller.

        Args:
            console: Rich Console for output
            theme: Color theme for display
            timezone_str: Timezone for timestamp display
        """
        self.console = console or Console()
        self.theme = theme or get_theme()
        self.timezone_str = timezone_str

    def display_realtime(
        self,
        entries: List[UsageEntry],
        token_limit: int,
        session_analyzer: SessionAnalyzer,
    ) -> None:
        """
        Display realtime monitoring view.

        Args:
            entries: List of UsageEntry objects
            token_limit: Token limit for the period
            session_analyzer: SessionAnalyzer for session tracking
        """
        analysis = UsageAnalysis(entries, self.timezone_str)
        active_session = session_analyzer.get_active_session(entries)

        # Calculate metrics
        total_stats = analysis.total_stats
        burn_rate = analysis.get_burn_rate()
        model_dist = analysis.model_distribution

        # Predictions
        predicted_time = None
        if token_limit > 0 and burn_rate > 0:
            remaining = token_limit - total_stats.total_tokens
            if remaining > 0:
                minutes_until = remaining / burn_rate
                predicted_time = datetime.now(timezone.utc) + __import__(
                    "datetime"
                ).timedelta(minutes=minutes_until)

        # Format display
        screen = format_active_session_screen(
            session=active_session,
            total_tokens=total_stats.total_tokens,
            token_limit=token_limit,
            burn_rate=burn_rate,
            message_count=total_stats.count,
            model_distribution=model_dist,
            predicted_time=predicted_time,
            reset_time=None,  # Could be passed in if needed
            timezone_str=self.timezone_str,
        )

        self.console.clear()
        self.console.print("\n".join(screen))

    def display_daily(
        self,
        entries: List[UsageEntry],
        token_limit: int,
    ) -> None:
        """
        Display daily report view.

        Args:
            entries: List of UsageEntry objects
            token_limit: Token limit for the period
        """
        analysis = UsageAnalysis(entries, self.timezone_str)

        # Create summary
        summary_data = {
            "total_tokens": analysis.total_stats.total_tokens,
            "input_tokens": analysis.total_stats.input_tokens,
            "output_tokens": analysis.total_stats.output_tokens,
            "cache_percentage": analysis.total_stats.cache_percentage,
            "count": analysis.total_stats.count,
        }

        period_info = {
            "name": "Daily Report",
            "duration_hours": analysis.duration_hours,
        }

        # Create tables
        summary_table = create_summary_table(summary_data, period_info, self.timezone_str)
        daily_table = create_daily_table(analysis.daily_periods, self.timezone_str)

        # Display
        self.console.clear()
        self.console.print(summary_table)
        self.console.print()
        self.console.print(daily_table)

    def display_monthly(
        self,
        entries: List[UsageEntry],
        token_limit: int,
    ) -> None:
        """
        Display monthly report view.

        Args:
            entries: List of UsageEntry objects
            token_limit: Token limit for the period
        """
        analysis = UsageAnalysis(entries, self.timezone_str)

        # Create summary
        summary_data = {
            "total_tokens": analysis.total_stats.total_tokens,
            "input_tokens": analysis.total_stats.input_tokens,
            "output_tokens": analysis.total_stats.output_tokens,
            "cache_percentage": analysis.total_stats.cache_percentage,
            "count": analysis.total_stats.count,
        }

        period_info = {
            "name": "Monthly Report",
            "duration_hours": analysis.duration_hours,
        }

        # Create tables
        summary_table = create_summary_table(summary_data, period_info, self.timezone_str)
        monthly_table = create_monthly_table(analysis.monthly_periods, self.timezone_str)

        # Display
        self.console.clear()
        self.console.print(summary_table)
        self.console.print()
        self.console.print(monthly_table)

    def display_detailed(
        self,
        entries: List[UsageEntry],
        token_limit: int,
    ) -> None:
        """
        Display detailed breakdown view.

        Shows:
        - Hourly usage breakdown
        - Detailed model breakdown
        - Provider breakdown
        - Token type breakdown

        Args:
            entries: List of UsageEntry objects
            token_limit: Token limit for the period
        """
        analysis = UsageAnalysis(entries, self.timezone_str)
        total_tokens = analysis.total_stats.total_tokens

        # Create summary
        summary_data = {
            "total_tokens": total_tokens,
            "input_tokens": analysis.total_stats.input_tokens,
            "output_tokens": analysis.total_stats.output_tokens,
            "cache_percentage": analysis.total_stats.cache_percentage,
            "count": analysis.total_stats.count,
        }

        period_info = {
            "name": "Detailed Breakdown",
            "duration_hours": analysis.duration_hours,
        }

        # Get detailed breakdowns
        hourly_periods = aggregate_by_hour(entries, self.timezone_str)
        model_breakdown = get_model_breakdown_details(entries)
        provider_breakdown = get_provider_breakdown_details(entries)
        token_breakdown = get_token_type_breakdown(entries)

        # Create tables
        summary_table = create_summary_table(summary_data, period_info, self.timezone_str)
        hourly_table = create_hourly_table(hourly_periods[-24:], self.timezone_str)  # Last 24 hours
        model_table = create_detailed_model_table(model_breakdown, total_tokens)
        provider_table = create_provider_table(provider_breakdown, total_tokens)
        token_type_table = create_token_type_table(token_breakdown, total_tokens)

        # Display
        self.console.clear()
        self.console.print(summary_table)
        self.console.print()
        self.console.print(hourly_table)
        self.console.print()
        self.console.print(model_table)
        self.console.print()
        self.console.print(provider_table)
        self.console.print()
        self.console.print(token_type_table)

    def display_error(self, message: str) -> None:
        """
        Display an error message.

        Args:
            message: Error message to display
        """
        self.console.print(f"[{self.theme.error}]Error:[/] {message}")

    def display_warning(self, message: str) -> None:
        """
        Display a warning message.

        Args:
            message: Warning message to display
        """
        self.console.print(f"[{self.theme.warning}]Warning:[/] {message}")

    def display_info(self, message: str) -> None:
        """
        Display an info message.

        Args:
            message: Info message to display
        """
        self.console.print(f"[{self.theme.info}]{message}[/]")

    def clear(self) -> None:
        """Clear the console display."""
        self.console.clear()


def create_live_display(
    display_controller: DisplayController,
    refresh_rate: int = 5,
) -> Live:
    """
    Create a Live display context manager for realtime updates.

    Args:
        display_controller: DisplayController instance
        refresh_rate: Refresh rate in seconds

    Returns:
        Rich Live object
    """
    return Live(
        console=display_controller.console,
        refresh_per_second=1 / refresh_rate,
    )
