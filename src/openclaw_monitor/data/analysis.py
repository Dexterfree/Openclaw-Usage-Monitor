"""
Analysis module for OpenCLAW Token Usage Monitor.

This module provides high-level analysis functions for understanding
token usage patterns and trends.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from openclaw_monitor.core.calculations import (
    calculate_burn_rate,
    calculate_model_distribution,
    calculate_p90_burn_rate,
)
from openclaw_monitor.core.models import SessionBlock, UsageEntry
from openclaw_monitor.data.aggregator import (
    AggregatedPeriod,
    AggregatedStats,
    aggregate_by_day,
    aggregate_by_model,
    aggregate_by_month,
    get_total_stats,
)


class UsageAnalysis:
    """
    High-level analysis of token usage data.

    This class provides methods for analyzing usage patterns,
    calculating metrics, and generating insights.
    """

    def __init__(
        self,
        entries: List[UsageEntry],
        timezone_str: str = "UTC",
    ):
        """
        Initialize the usage analysis.

        Args:
            entries: List of UsageEntry objects to analyze
            timezone_str: Timezone for time-based analysis
        """
        self.entries = sorted(entries, key=lambda e: e.timestamp)
        self.timezone_str = timezone_str

        # Cache computed values
        self._total_stats: Optional[AggregatedStats] = None
        self._model_distribution: Optional[Dict[str, int]] = None
        self._daily_periods: Optional[List[AggregatedPeriod]] = None
        self._monthly_periods: Optional[List[AggregatedPeriod]] = None

    @property
    def total_stats(self) -> AggregatedStats:
        """Get total statistics across all entries."""
        if self._total_stats is None:
            self._total_stats = get_total_stats(self.entries)
        return self._total_stats

    @property
    def model_distribution(self) -> Dict[str, int]:
        """Get token distribution by model."""
        if self._model_distribution is None:
            self._model_distribution = calculate_model_distribution(self.entries)
        return self._model_distribution

    @property
    def daily_periods(self) -> List[AggregatedPeriod]:
        """Get aggregated daily statistics."""
        if self._daily_periods is None:
            self._daily_periods = aggregate_by_day(self.entries, self.timezone_str)
        return self._daily_periods

    @property
    def monthly_periods(self) -> List[AggregatedPeriod]:
        """Get aggregated monthly statistics."""
        if self._monthly_periods is None:
            self._monthly_periods = aggregate_by_month(self.entries, self.timezone_str)
        return self._monthly_periods

    @property
    def time_span(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get the time span covered by the entries."""
        if not self.entries:
            return None, None
        return self.entries[0].timestamp, self.entries[-1].timestamp

    @property
    def duration_hours(self) -> float:
        """Get the duration covered by entries in hours."""
        start, end = self.time_span
        if start is None or end is None:
            return 0.0
        return (end - start).total_seconds() / 3600

    def get_burn_rate(
        self,
        window_seconds: int = 60,
    ) -> float:
        """
        Calculate current burn rate.

        Args:
            window_seconds: Time window for rate calculation

        Returns:
            Tokens per minute
        """
        return calculate_burn_rate(self.entries, window_seconds)

    def get_p90_burn_rate(
        self,
        window_minutes: int = 5,
    ) -> float:
        """
        Calculate P90 burn rate.

        Args:
            window_minutes: Time window in minutes

        Returns:
            90th percentile tokens per minute
        """
        return calculate_p90_burn_rate(self.entries, window_minutes)

    def get_model_stats(self) -> Dict[str, AggregatedStats]:
        """
        Get statistics broken down by model.

        Returns:
            Dictionary mapping model names to AggregatedStats
        """
        return aggregate_by_model(self.entries)

    def get_top_models(self, limit: int = 5) -> List[Tuple[str, int]]:
        """
        Get top models by token usage.

        Args:
            limit: Maximum number of models to return

        Returns:
            List of (model_name, token_count) tuples
        """
        sorted_models = sorted(
            self.model_distribution.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_models[:limit]

    def get_entries_in_range(
        self,
        hours_back: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[UsageEntry]:
        """
        Get entries within a time range.

        Args:
            hours_back: Only include entries from this many hours ago
            start_time: Only include entries after this time
            end_time: Only include entries before this time

        Returns:
            Filtered list of UsageEntry objects
        """
        if hours_back:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

        if start_time is None and end_time is None:
            return self.entries

        filtered = []
        for entry in self.entries:
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            filtered.append(entry)

        return filtered

    def get_recent_analysis(
        self,
        hours: int = 24,
    ) -> "UsageAnalysis":
        """
        Get analysis for recent entries only.

        Args:
            hours: Number of hours to look back

        Returns:
            New UsageAnalysis object with filtered entries
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_entries = [e for e in self.entries if e.timestamp >= cutoff]
        return UsageAnalysis(recent_entries, self.timezone_str)

    def compare_periods(
        self,
        period1_hours: int,
        period2_hours: int,
    ) -> Dict[str, Any]:
        """
        Compare two time periods.

        Args:
            period1_hours: First period duration (most recent)
            period2_hours: Second period duration (preceding period1)

        Returns:
            Dictionary with comparison metrics
        """
        now = datetime.now(timezone.utc)

        period1_start = now - timedelta(hours=period1_hours)
        period2_start = now - timedelta(hours=period1_hours + period2_hours)

        period1_entries = [
            e for e in self.entries
            if period1_start <= e.timestamp < now
        ]
        period2_entries = [
            e for e in self.entries
            if period2_start <= e.timestamp < period1_start
        ]

        stats1 = get_total_stats(period1_entries)
        stats2 = get_total_stats(period2_entries)

        return {
            "period1": {
                "hours": period1_hours,
                "stats": stats1.to_dict(),
            },
            "period2": {
                "hours": period2_hours,
                "stats": stats2.to_dict(),
            },
            "change": {
                "total_tokens": stats1.total_tokens - stats2.total_tokens,
                "input_tokens": stats1.input_tokens - stats2.input_tokens,
                "output_tokens": stats1.output_tokens - stats2.output_tokens,
                "count": stats1.count - stats2.count,
            },
            "percentage_change": {
                "total_tokens": _calculate_pct_change(
                    stats2.total_tokens,
                    stats1.total_tokens,
                ),
                "input_tokens": _calculate_pct_change(
                    stats2.input_tokens,
                    stats1.input_tokens,
                ),
                "output_tokens": _calculate_pct_change(
                    stats2.output_tokens,
                    stats1.output_tokens,
                ),
            },
        }

    def get_insights(self) -> Dict[str, Any]:
        """
        Get insights about the usage patterns.

        Returns:
            Dictionary with various insights
        """
        insights = {
            "total_stats": self.total_stats.to_dict(),
            "time_span_hours": round(self.duration_hours, 2),
            "top_models": self.get_top_models(3),
            "daily_periods": len(self.daily_periods),
        }

        # Add recent activity
        recent = self.get_recent_analysis(24)
        insights["last_24h"] = {
            "total_tokens": recent.total_stats.total_tokens,
            "request_count": recent.total_stats.count,
        }

        # Add burn rate info
        if len(self.entries) > 1:
            current_rate = self.get_burn_rate()
            p90_rate = self.get_p90_burn_rate()
            insights["burn_rate"] = {
                "current": round(current_rate, 2),
                "p90": round(p90_rate, 2),
            }

        return insights


def _calculate_pct_change(old: int, new: int) -> float:
    """Calculate percentage change from old to new."""
    if old == 0:
        return 100.0 if new > 0 else 0.0
    return round(((new - old) / old) * 100, 2)


def predict_reset_time(
    current_time: datetime,
    reset_day: int = 1,
    reset_hour: int = 0,
    timezone_str: str = "UTC",
) -> datetime:
    """
    Predict the next reset time based on a recurring schedule.

    Args:
        current_time: Current datetime
        reset_day: Day of month for reset (1-31)
        reset_hour: Hour of day for reset (0-23)
        timezone_str: Timezone for reset calculation

    Returns:
        Next reset datetime
    """
    try:
        import pytz
        tz = pytz.timezone(timezone_str)
    except ImportError:
        tz = timezone.utc

    localized = current_time.astimezone(tz)

    # Create next reset time
    next_reset = localized.replace(
        day=reset_day,
        hour=reset_hour,
        minute=0,
        second=0,
        microsecond=0,
    )

    # If we've passed this month's reset, go to next month
    if next_reset <= localized:
        # Move to next month
        if localized.month == 12:
            next_reset = next_reset.replace(year=localized.year + 1, month=1)
        else:
            next_reset = next_reset.replace(month=localized.month + 1)

    return next_reset


def get_time_until_reset(
    current_time: datetime,
    reset_time: datetime,
) -> timedelta:
    """
    Get time remaining until reset.

    Args:
        current_time: Current datetime
        reset_time: Reset datetime

    Returns:
        Timedelta until reset
    """
    delta = reset_time - current_time
    return delta if delta.total_seconds() > 0 else timedelta(0)
