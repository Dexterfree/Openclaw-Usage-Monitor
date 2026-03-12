"""
Aggregator module for OpenCLAW Token Usage Monitor.

This module provides functionality to aggregate usage data by
different time periods (daily, monthly, etc.).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Set, Tuple

from openclaw_monitor.core.models import TokenCounts, UsageEntry


@dataclass(frozen=True)
class AggregatedStats:
    """
    Immutable aggregated statistics for a group of entries.

    All token counts are summed across all entries in the group.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    count: int = 0

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens across all categories."""
        return sum([
            self.input_tokens,
            self.output_tokens,
            self.cache_creation_tokens,
            self.cache_read_tokens,
        ])

    @property
    def cache_percentage(self) -> float:
        """Calculate percentage of tokens that were from cache."""
        total_cache = self.cache_creation_tokens + self.cache_read_tokens
        if self.total_tokens == 0:
            return 0.0
        return (total_cache / self.total_tokens) * 100

    @property
    def output_ratio(self) -> float:
        """Calculate ratio of output to input tokens."""
        if self.input_tokens == 0:
            return 0.0
        return self.output_tokens / self.input_tokens

    def __add__(self, other: "AggregatedStats") -> "AggregatedStats":
        """Combine two AggregatedStats instances."""
        return AggregatedStats(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_creation_tokens=self.cache_creation_tokens + other.cache_creation_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
            count=self.count + other.count,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "total_tokens": self.total_tokens,
            "count": self.count,
            "cache_percentage": round(self.cache_percentage, 2),
            "output_ratio": round(self.output_ratio, 2),
        }


@dataclass
class AggregatedPeriod:
    """
    Aggregated statistics for a specific time period.

    Contains both overall stats and breakdowns by model.
    """

    period_key: str
    stats: AggregatedStats
    models_used: Set[str] = field(default_factory=set)
    model_breakdowns: Dict[str, AggregatedStats] = field(default_factory=dict)

    def add_entry(self, entry: UsageEntry) -> None:
        """Add an entry to this period aggregation."""
        model = entry.model or "unknown"
        self.models_used.add(model)

        # Add to overall stats
        self.stats = AggregatedStats(
            input_tokens=self.stats.input_tokens + entry.input_tokens,
            output_tokens=self.stats.output_tokens + entry.output_tokens,
            cache_creation_tokens=self.stats.cache_creation_tokens + entry.cache_creation_tokens,
            cache_read_tokens=self.stats.cache_read_tokens + entry.cache_read_tokens,
            count=self.stats.count + 1,
        )

        # Add to model breakdown
        if model not in self.model_breakdowns:
            self.model_breakdowns[model] = AggregatedStats()

        self.model_breakdowns[model] = AggregatedStats(
            input_tokens=self.model_breakdowns[model].input_tokens + entry.input_tokens,
            output_tokens=self.model_breakdowns[model].output_tokens + entry.output_tokens,
            cache_creation_tokens=self.model_breakdowns[model].cache_creation_tokens + entry.cache_creation_tokens,
            cache_read_tokens=self.model_breakdowns[model].cache_read_tokens + entry.cache_read_tokens,
            count=self.model_breakdowns[model].count + 1,
        )

    def to_dict(self, period_type: str) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            period_type: self.period_key,
            "stats": self.stats.to_dict(),
            "models_used": sorted(list(self.models_used)),
            "model_breakdowns": {
                model: stats.to_dict()
                for model, stats in self.model_breakdowns.items()
            },
        }


def aggregate_by_day(
    entries: List[UsageEntry],
    timezone_str: str = "UTC",
) -> List[AggregatedPeriod]:
    """
    Aggregate usage entries by day.

    Args:
        entries: List of UsageEntry objects
        timezone_str: Timezone to use for day grouping

    Returns:
        List of AggregatedPeriod objects, one per day
    """
    if not entries:
        return []

    try:
        import pytz
        tz_obj = pytz.timezone(timezone_str)
    except ImportError:
        tz_obj = timezone.utc

    # Group entries by day
    daily_groups: Dict[str, List[UsageEntry]] = defaultdict(list)

    for entry in entries:
        localized = entry.timestamp.astimezone(tz_obj)
        day_key = localized.date().isoformat()
        daily_groups[day_key].append(entry)

    # Create aggregated periods
    periods = []
    for day_key, day_entries in sorted(daily_groups.items()):
        stats = AggregatedStats(
            input_tokens=sum(e.input_tokens for e in day_entries),
            output_tokens=sum(e.output_tokens for e in day_entries),
            cache_creation_tokens=sum(e.cache_creation_tokens for e in day_entries),
            cache_read_tokens=sum(e.cache_read_tokens for e in day_entries),
            count=len(day_entries),
        )

        models_used = {e.model or "unknown" for e in day_entries}

        # Model breakdowns
        model_breakdowns: Dict[str, AggregatedStats] = {}
        for model in models_used:
            model_entries = [e for e in day_entries if (e.model or "unknown") == model]
            model_breakdowns[model] = AggregatedStats(
                input_tokens=sum(e.input_tokens for e in model_entries),
                output_tokens=sum(e.output_tokens for e in model_entries),
                cache_creation_tokens=sum(e.cache_creation_tokens for e in model_entries),
                cache_read_tokens=sum(e.cache_read_tokens for e in model_entries),
                count=len(model_entries),
            )

        periods.append(AggregatedPeriod(
            period_key=day_key,
            stats=stats,
            models_used=models_used,
            model_breakdowns=model_breakdowns,
        ))

    return periods


def aggregate_by_month(
    entries: List[UsageEntry],
    timezone_str: str = "UTC",
) -> List[AggregatedPeriod]:
    """
    Aggregate usage entries by month.

    Args:
        entries: List of UsageEntry objects
        timezone_str: Timezone to use for month grouping

    Returns:
        List of AggregatedPeriod objects, one per month
    """
    if not entries:
        return []

    try:
        import pytz
        tz_obj = pytz.timezone(timezone_str)
    except ImportError:
        tz_obj = timezone.utc

    # Group entries by month
    monthly_groups: Dict[str, List[UsageEntry]] = defaultdict(list)

    for entry in entries:
        localized = entry.timestamp.astimezone(tz_obj)
        month_key = localized.strftime("%Y-%m")
        monthly_groups[month_key].append(entry)

    # Create aggregated periods
    periods = []
    for month_key, month_entries in sorted(monthly_groups.items()):
        stats = AggregatedStats(
            input_tokens=sum(e.input_tokens for e in month_entries),
            output_tokens=sum(e.output_tokens for e in month_entries),
            cache_creation_tokens=sum(e.cache_creation_tokens for e in month_entries),
            cache_read_tokens=sum(e.cache_read_tokens for e in month_entries),
            count=len(month_entries),
        )

        models_used = {e.model or "unknown" for e in month_entries}

        # Model breakdowns
        model_breakdowns: Dict[str, AggregatedStats] = {}
        for model in models_used:
            model_entries = [e for e in month_entries if (e.model or "unknown") == model]
            model_breakdowns[model] = AggregatedStats(
                input_tokens=sum(e.input_tokens for e in model_entries),
                output_tokens=sum(e.output_tokens for e in model_entries),
                cache_creation_tokens=sum(e.cache_creation_tokens for e in model_entries),
                cache_read_tokens=sum(e.cache_read_tokens for e in model_entries),
                count=len(model_entries),
            )

        periods.append(AggregatedPeriod(
            period_key=month_key,
            stats=stats,
            models_used=models_used,
            model_breakdowns=model_breakdowns,
        ))

    return periods


def aggregate_by_model(
    entries: List[UsageEntry],
) -> Dict[str, AggregatedStats]:
    """
    Aggregate usage entries by model.

    Args:
        entries: List of UsageEntry objects

    Returns:
        Dictionary mapping model names to AggregatedStats
    """
    model_groups: Dict[str, List[UsageEntry]] = defaultdict(list)

    for entry in entries:
        model = entry.model or "unknown"
        model_groups[model].append(entry)

    return {
        model: AggregatedStats(
            input_tokens=sum(e.input_tokens for e in model_entries),
            output_tokens=sum(e.output_tokens for e in model_entries),
            cache_creation_tokens=sum(e.cache_creation_tokens for e in model_entries),
            cache_read_tokens=sum(e.cache_read_tokens for e in model_entries),
            count=len(model_entries),
        )
        for model, model_entries in model_groups.items()
    }


def aggregate_by_provider(
    entries: List[UsageEntry],
) -> Dict[str, AggregatedStats]:
    """
    Aggregate usage entries by provider.

    Args:
        entries: List of UsageEntry objects

    Returns:
        Dictionary mapping provider names to AggregatedStats
    """
    provider_groups: Dict[str, List[UsageEntry]] = defaultdict(list)

    for entry in entries:
        provider = entry.provider or "unknown"
        provider_groups[provider].append(entry)

    return {
        provider: AggregatedStats(
            input_tokens=sum(e.input_tokens for e in provider_entries),
            output_tokens=sum(e.output_tokens for e in provider_entries),
            cache_creation_tokens=sum(e.cache_creation_tokens for e in provider_entries),
            cache_read_tokens=sum(e.cache_read_tokens for e in provider_entries),
            count=len(provider_entries),
        )
        for provider, provider_entries in provider_groups.items()
    }


def get_total_stats(
    entries: List[UsageEntry],
) -> AggregatedStats:
    """
    Get total aggregated statistics across all entries.

    Args:
        entries: List of UsageEntry objects

    Returns:
        AggregatedStats for all entries
    """
    if not entries:
        return AggregatedStats()

    return AggregatedStats(
        input_tokens=sum(e.input_tokens for e in entries),
        output_tokens=sum(e.output_tokens for e in entries),
        cache_creation_tokens=sum(e.cache_creation_tokens for e in entries),
        cache_read_tokens=sum(e.cache_read_tokens for e in entries),
        count=len(entries),
    )


def get_top_models(
    entries: List[UsageEntry],
    limit: int = 5,
) -> List[Tuple[str, int]]:
    """
    Get the top models by token usage.

    Args:
        entries: List of UsageEntry objects
        limit: Maximum number of models to return

    Returns:
        List of (model_name, token_count) tuples sorted by count descending
    """
    model_totals = aggregate_by_model(entries)

    sorted_models = sorted(
        model_totals.items(),
        key=lambda x: x[1].total_tokens,
        reverse=True,
    )

    return [(model, stats.total_tokens) for model, stats in sorted_models[:limit]]


def get_top_providers(
    entries: List[UsageEntry],
    limit: int = 5,
) -> List[Tuple[str, int]]:
    """
    Get the top providers by token usage.

    Args:
        entries: List of UsageEntry objects
        limit: Maximum number of providers to return

    Returns:
        List of (provider_name, token_count) tuples sorted by count descending
    """
    provider_totals = aggregate_by_provider(entries)

    sorted_providers = sorted(
        provider_totals.items(),
        key=lambda x: x[1].total_tokens,
        reverse=True,
    )

    return [(provider, stats.total_tokens) for provider, stats in sorted_providers[:limit]]


def calculate_daily_average(
    periods: List[AggregatedPeriod],
) -> AggregatedStats:
    """
    Calculate daily average statistics from a list of periods.

    Args:
        periods: List of AggregatedPeriod objects

    Returns:
        AggregatedStats with average values
    """
    if not periods:
        return AggregatedStats()

    count = len(periods)
    total_input = sum(p.stats.input_tokens for p in periods)
    total_output = sum(p.stats.output_tokens for p in periods)
    total_cache_create = sum(p.stats.cache_creation_tokens for p in periods)
    total_cache_read = sum(p.stats.cache_read_tokens for p in periods)
    total_requests = sum(p.stats.count for p in periods)

    return AggregatedStats(
        input_tokens=total_input // count,
        output_tokens=total_output // count,
        cache_creation_tokens=total_cache_create // count,
        cache_read_tokens=total_cache_read // count,
        count=total_requests // count if count > 0 else 0,
    )
