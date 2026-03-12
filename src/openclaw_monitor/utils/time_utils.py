"""
Time utility functions for OpenCLAW Token Usage Monitor.

This module provides helper functions for time-related operations.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional


def format_duration(
    seconds: float,
    style: str = "short",
) -> str:
    """
    Format a duration in seconds as a human-readable string.

    Args:
        seconds: Duration in seconds
        style: Format style ("short", "long", "compact")

    Returns:
        Formatted duration string

    Examples:
        >>> format_duration(90)
        '1m 30s'
        >>> format_duration(3661, style="long")
        '1 hour, 1 minute, 1 second'
    """
    if seconds < 0:
        return "0s"

    if style == "compact":
        if seconds < 60:
            return f"{int(seconds)}s"
        minutes = int(seconds / 60)
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        return f"{hours}h"

    # Calculate components
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if style == "long":
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if secs > 0 or not parts:
            parts.append(f"{secs} second{'s' if secs != 1 else ''}")
        return ", ".join(parts)

    # Short style (default)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_timestamp(
    dt: datetime,
    timezone_str: str = "UTC",
    format: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    """
    Format a datetime for display in a specific timezone.

    Args:
        dt: Datetime to format
        timezone_str: Target timezone name
        format: strftime format string

    Returns:
        Formatted timestamp string
    """
    tz = get_timezone(timezone_str)
    localized = dt.astimezone(tz)
    return localized.strftime(format)


def get_timezone(timezone_str: str = "UTC"):
    """
    Get a timezone object from a string.

    Args:
        timezone_str: Timezone name (e.g., "UTC", "America/New_York")

    Returns:
        Timezone object
    """
    try:
        import pytz
        return pytz.timezone(timezone_str)
    except ImportError:
        pass

    try:
        import zoneinfo
        return zoneinfo.ZoneInfo(timezone_str)
    except ImportError:
        pass

    # Fallback to UTC
    return timezone.utc


def get_time_until(
    target: datetime,
    current: Optional[datetime] = None,
) -> timedelta:
    """
    Get the time delta until a target datetime.

    Args:
        target: Target datetime
        current: Current time (defaults to now)

    Returns:
        Timedelta until target
    """
    if current is None:
        current = datetime.now(timezone.utc)

    delta = target - current
    return delta if delta.total_seconds() > 0 else timedelta(0)


def get_days_in_month(year: int, month: int) -> int:
    """
    Get the number of days in a month.

    Args:
        year: Year
        month: Month (1-12)

    Returns:
        Number of days in the month
    """
    if month == 12:
        return 31

    # First day of next month minus first day of this month
    return (
        datetime(year, month + 1, 1) - datetime(year, month, 1)
    ).days


def get_month_start(
    dt: Optional[datetime] = None,
    timezone_str: str = "UTC",
) -> datetime:
    """
    Get the start of the month for a given datetime.

    Args:
        dt: Reference datetime (defaults to now)
        timezone_str: Timezone for the result

    Returns:
        Datetime at start of month
    """
    if dt is None:
        dt = datetime.now(get_timezone(timezone_str))

    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_month_end(
    dt: Optional[datetime] = None,
    timezone_str: str = "UTC",
) -> datetime:
    """
    Get the end of the month for a given datetime.

    Args:
        dt: Reference datetime (defaults to now)
        timezone_str: Timezone for the result

    Returns:
        Datetime at end of month
    """
    if dt is None:
        dt = datetime.now(get_timezone(timezone_str))

    # Go to first day of next month, then subtract one microsecond
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)

    return next_month.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    ) - timedelta(microseconds=1)


def get_day_start(
    dt: Optional[datetime] = None,
    timezone_str: str = "UTC",
) -> datetime:
    """
    Get the start of the day for a given datetime.

    Args:
        dt: Reference datetime (defaults to now)
        timezone_str: Timezone for the result

    Returns:
        Datetime at start of day
    """
    if dt is None:
        dt = datetime.now(get_timezone(timezone_str))

    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end(
    dt: Optional[datetime] = None,
    timezone_str: str = "UTC",
) -> datetime:
    """
    Get the end of the day for a given datetime.

    Args:
        dt: Reference datetime (defaults to now)
        timezone_str: Timezone for the result

    Returns:
        Datetime at end of day
    """
    if dt is None:
        dt = datetime.now(get_timezone(timezone_str))

    return dt.replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )
