"""
Calculations module for OpenCLAW Token Usage Monitor.

This module provides functions for calculating burn rates, predictions,
and other token usage metrics.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from openclaw_monitor.core.models import SessionBlock, UsageEntry


def calculate_burn_rate(
    entries: List[UsageEntry],
    window_seconds: int = 60,
) -> float:
    """
    Calculate token burn rate (tokens per minute) over a sliding time window.

    Args:
        entries: List of UsageEntry objects (should be sorted by timestamp)
        window_seconds: Time window in seconds for rate calculation

    Returns:
        Tokens per minute burn rate
    """
    if not entries:
        return 0.0

    if window_seconds <= 0:
        return 0.0

    # Get the most recent timestamp
    now = entries[-1].timestamp
    window_start = now - timedelta(seconds=window_seconds)

    # Filter entries within the window
    window_entries = [e for e in entries if e.timestamp >= window_start]

    if not window_entries:
        return 0.0

    # Calculate total tokens in window
    total_tokens = sum(e.total_tokens for e in window_entries)

    # Calculate actual duration within window
    actual_duration_seconds = (now - window_entries[0].timestamp).total_seconds()

    if actual_duration_seconds <= 0:
        return 0.0

    # Return tokens per minute
    return (total_tokens / actual_duration_seconds) * 60


def calculate_p90_burn_rate(
    entries: List[UsageEntry],
    window_minutes: int = 5,
    sample_interval_seconds: int = 30,
) -> float:
    """
    Calculate the 90th percentile burn rate over multiple samples.

    This provides a more stable burn rate metric by taking the P90
    of multiple rate calculations, smoothing out temporary spikes.

    Args:
        entries: List of UsageEntry objects
        window_minutes: Time window to analyze
        sample_interval_seconds: Interval between rate samples

    Returns:
        90th percentile burn rate in tokens per minute
    """
    if not entries:
        return 0.0

    window_seconds = window_minutes * 60
    samples: List[float] = []

    # Take samples at regular intervals
    for i in range(0, window_seconds, sample_interval_seconds):
        cutoff_time = entries[-1].timestamp - timedelta(seconds=i)
        window_entries = [e for e in entries if e.timestamp >= cutoff_time]

        if window_entries:
            duration = (entries[-1].timestamp - window_entries[0].timestamp).total_seconds()
            if duration > 0:
                total_tokens = sum(e.total_tokens for e in window_entries)
                rate = (total_tokens / duration) * 60
                samples.append(rate)

    if not samples:
        return 0.0

    # Calculate P90
    samples.sort()
    p90_index = math.floor(len(samples) * 0.9)
    return samples[p90_index] if samples else 0.0


def predict_time_until_limit(
    current_usage: int,
    token_limit: int,
    burn_rate: float,
) -> Optional[datetime]:
    """
    Predict when tokens will run out based on current burn rate.

    Args:
        current_usage: Current token usage count
        token_limit: Token limit (0 for unlimited)
        burn_rate: Current burn rate in tokens per minute

    Returns:
        Predicted datetime when limit will be reached, or None if
        unlimited or burn rate is zero
    """
    if token_limit == 0:
        return None

    if burn_rate <= 0:
        return None

    remaining = token_limit - current_usage
    if remaining <= 0:
        return datetime.now(timezone.utc)

    minutes_until_limit = remaining / burn_rate

    return datetime.now(timezone.utc) + timedelta(minutes=minutes_until_limit)


def predict_time_until_limit_p90(
    current_usage: int,
    token_limit: int,
    p90_burn_rate: float,
) -> Optional[datetime]:
    """
    Predict when tokens will run out using P90 burn rate.

    This provides a more conservative (later) prediction than
    using the current burn rate.

    Args:
        current_usage: Current token usage count
        token_limit: Token limit (0 for unlimited)
        p90_burn_rate: P90 burn rate in tokens per minute

    Returns:
        Predicted datetime when limit will be reached, or None if
        unlimited or burn rate is zero
    """
    return predict_time_until_limit(
        current_usage,
        token_limit,
        p90_burn_rate,
    )


def calculate_session_blocks(
    entries: List[UsageEntry],
    gap_minutes: int = 30,
) -> List[SessionBlock]:
    """
    Group entries into session blocks based on time gaps.

    A session block is a sequence of entries where consecutive
    entries are within gap_minutes of each other.

    Args:
        entries: List of UsageEntry objects (should be sorted)
        gap_minutes: Maximum gap in minutes before starting a new block

    Returns:
        List of SessionBlock objects
    """
    if not entries:
        return []

    # Sort entries by timestamp
    sorted_entries = sorted(entries, key=lambda e: e.timestamp)

    blocks: List[SessionBlock] = []
    current_block: List[UsageEntry] = [sorted_entries[0]]
    current_model = sorted_entries[0].model or "unknown"
    current_provider = sorted_entries[0].provider or ""

    for entry in sorted_entries[1:]:
        time_gap = (entry.timestamp - current_block[-1].timestamp).total_seconds() / 60

        if time_gap <= gap_minutes:
            # Continue current block
            current_block.append(entry)
            # Update model/provider if newer entries have them
            if entry.model:
                current_model = entry.model
            if entry.provider:
                current_provider = entry.provider
        else:
            # Start new block
            # Finalize current block
            block = SessionBlock(
                entries=current_block,
                model=current_model,
                provider=current_provider,
                session_id=f"session_{len(blocks)}",
            )
            blocks.append(block)

            # Start new block
            current_block = [entry]
            current_model = entry.model or "unknown"
            current_provider = entry.provider or ""

    # Don't forget the last block
    if current_block:
        block = SessionBlock(
            entries=current_block,
            model=current_model,
            provider=current_provider,
            session_id=f"session_{len(blocks)}",
        )
        blocks.append(block)

    return blocks


def calculate_model_distribution(
    entries: List[UsageEntry],
) -> Dict[str, int]:
    """
    Calculate token distribution across different models.

    Args:
        entries: List of UsageEntry objects

    Returns:
        Dictionary mapping model names to token counts
    """
    distribution: Dict[str, int] = defaultdict(int)

    for entry in entries:
        model = entry.model or "unknown"
        distribution[model] += entry.total_tokens

    return dict(distribution)


def calculate_provider_distribution(
    entries: List[UsageEntry],
) -> Dict[str, int]:
    """
    Calculate token distribution across different providers.

    Args:
        entries: List of UsageEntry objects

    Returns:
        Dictionary mapping provider names to token counts
    """
    distribution: Dict[str, int] = defaultdict(int)

    for entry in entries:
        provider = entry.provider or "unknown"
        distribution[provider] += entry.total_tokens

    return dict(distribution)


def calculate_cache_hit_rate(entries: List[UsageEntry]) -> Tuple[int, int, float]:
    """
    Calculate cache hit rate metrics.

    Args:
        entries: List of UsageEntry objects

    Returns:
        Tuple of (cache_read_tokens, cache_creation_tokens, hit_rate)
        where hit_rate is cache_read / total_cache_tokens
    """
    cache_read = sum(e.cache_read_tokens for e in entries)
    cache_creation = sum(e.cache_creation_tokens for e in entries)

    total_cache = cache_read + cache_creation
    hit_rate = (cache_read / total_cache * 100) if total_cache > 0 else 0.0

    return cache_read, cache_creation, hit_rate


def calculate_average_tokens_per_request(entries: List[UsageEntry]) -> Dict[str, float]:
    """
    Calculate average token usage per request.

    Args:
        entries: List of UsageEntry objects

    Returns:
        Dictionary with average values for input, output, and total tokens
    """
    if not entries:
        return {"input": 0.0, "output": 0.0, "total": 0.0}

    count = len(entries)
    total_input = sum(e.input_tokens for e in entries)
    total_output = sum(e.output_tokens for e in entries)
    total_all = sum(e.total_tokens for e in entries)

    return {
        "input": total_input / count,
        "output": total_output / count,
        "total": total_all / count,
    }


def calculate_peak_usage(
    entries: List[UsageEntry],
    bucket_minutes: int = 5,
) -> List[Tuple[datetime, int]]:
    """
    Calculate peak usage periods by bucketing entries into time windows.

    Args:
        entries: List of UsageEntry objects
        bucket_minutes: Size of each time bucket in minutes

    Returns:
        List of (datetime, token_count) tuples sorted by count descending
    """
    if not entries:
        return []

    # Create time buckets
    buckets: Dict[datetime, int] = defaultdict(int)

    for entry in entries:
        # Round down to nearest bucket
        timestamp = entry.timestamp
        bucket_time = timestamp.replace(
            second=0,
            microsecond=0,
        )
        bucket_time = bucket_time - timedelta(
            minutes=(bucket_time.minute % bucket_minutes)
        )
        buckets[bucket_time] += entry.total_tokens

    # Sort by token count descending
    sorted_buckets = sorted(
        buckets.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return sorted_buckets[:10]  # Return top 10 peaks


def calculate_hourly_pattern(
    entries: List[UsageEntry],
    timezone_str: str = "UTC",
) -> Dict[int, int]:
    """
    Calculate token usage pattern by hour of day.

    Args:
        entries: List of UsageEntry objects
        timezone_str: Timezone to use for hour calculation

    Returns:
        Dictionary mapping hour (0-23) to token count
    """
    try:
        from datetime import timezone as tz
        import pytz
        tz_obj = pytz.timezone(timezone_str)
    except ImportError:
        tz_obj = timezone.utc

    hourly_totals: Dict[int, int] = defaultdict(int)

    for entry in entries:
        # Convert to target timezone
        localized = entry.timestamp.astimezone(tz_obj)
        hour = localized.hour
        hourly_totals[hour] += entry.total_tokens

    return dict(hourly_totals)


def calculate_daily_trend(
    entries: List[UsageEntry],
    days: int = 7,
) -> List[Tuple[str, int]]:
    """
    Calculate daily token usage trend.

    Args:
        entries: List of UsageEntry objects
        days: Number of days to analyze

    Returns:
        List of (date_string, token_count) tuples
    """
    if not entries:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # Group by date
    daily_totals: Dict[str, int] = defaultdict(int)

    for entry in entries:
        if entry.timestamp < cutoff:
            continue
        date_str = entry.timestamp.date().isoformat()
        daily_totals[date_str] += entry.total_tokens

    # Sort by date
    sorted_daily = sorted(daily_totals.items())

    return sorted_daily


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds as a human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2h 30m", "45s")
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


def get_tokens_at_time(
    entries: List[UsageEntry],
    target_time: datetime,
) -> int:
    """
    Get total tokens used up to a specific time.

    Args:
        entries: List of UsageEntry objects (should be sorted)
        target_time: Cutoff time

    Returns:
        Total tokens used before or at target_time
    """
    total = 0
    for entry in entries:
        if entry.timestamp <= target_time:
            total += entry.total_tokens
        else:
            break
    return total
