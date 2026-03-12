"""
Core data models for OpenCLAW Token Usage Monitor.

This module defines the fundamental data structures used throughout
the application for tracking token usage across various LLM providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TokenCounts:
    """
    Immutable token count aggregation structure.

    This class represents token counts for different categories.
    It is intentionally frozen to ensure data integrity in aggregations.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens across all categories."""
        return sum([
            self.input_tokens,
            self.output_tokens,
            self.cache_creation_tokens,
            self.cache_read_tokens,
        ])

    def __add__(self, other: TokenCounts) -> TokenCounts:
        """Combine two TokenCounts instances."""
        return TokenCounts(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_creation_tokens=self.cache_creation_tokens + other.cache_creation_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
        )

    def __radd__(self, other: int) -> TokenCounts:
        """Support sum() with start value of 0."""
        if other == 0:
            return self
        return self.__add__(other)  # type: ignore

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary representation."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class UsageEntry:
    """
    Represents a single token usage entry from an LLM API call.

    This model captures token usage information from any LLM provider.
    It supports various token types (input, output, cache) and includes
    flexible metadata for provider-specific information.

    Attributes:
        timestamp: When the API call occurred
        input_tokens: Number of input/prompt tokens used
        output_tokens: Number of output/completion tokens used
        cache_creation_tokens: Tokens used for cache creation (if applicable)
        cache_read_tokens: Tokens read from cache (if applicable)
        model: Model identifier (e.g., "gpt-4o", "claude-3-5-sonnet")
        provider: LLM provider name (openai, anthropic, local, etc.)
        request_id: Optional unique identifier for the request
        metadata: Additional provider-specific information
    """

    timestamp: datetime
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    model: str = ""
    provider: str = ""
    request_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens for this entry."""
        return sum([
            self.input_tokens,
            self.output_tokens,
            self.cache_creation_tokens,
            self.cache_read_tokens,
        ])

    @property
    def token_counts(self) -> TokenCounts:
        """Get TokenCounts representation."""
        return TokenCounts(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cache_creation_tokens=self.cache_creation_tokens,
            cache_read_tokens=self.cache_read_tokens,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "provider": self.provider,
            "request_id": self.request_id,
            "metadata": self.metadata,
        }


@dataclass
class SessionBlock:
    """
    Represents a block of consecutive API usage within a session.

    A session block is defined as a period of continuous API usage
    where consecutive requests are within a specified time threshold
    of each other. Blocks are separated by gaps of inactivity.

    Attributes:
        entries: List of UsageEntry objects in this block
        model: Primary model used in this block
        provider: Provider of the LLM used
        session_id: Identifier for the session this block belongs to
    """

    entries: list[UsageEntry] = field(default_factory=list)
    model: str = ""
    provider: str = ""
    session_id: str = ""

    @property
    def start_time(self) -> Optional[datetime]:
        """Get the timestamp of the first entry in the block."""
        if not self.entries:
            return None
        return min(entry.timestamp for entry in self.entries)

    @property
    def end_time(self) -> Optional[datetime]:
        """Get the timestamp of the last entry in the block."""
        if not self.entries:
            return None
        return max(entry.timestamp for entry in self.entries)

    @property
    def duration(self) -> Optional[float]:
        """Get duration of the block in seconds."""
        if self.start_time is None or self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    @property
    def token_counts(self) -> TokenCounts:
        """Get aggregated token counts for this block."""
        return sum((entry.token_counts for entry in self.entries), TokenCounts())

    @property
    def message_count(self) -> int:
        """Get the number of messages (entries) in this block."""
        return len(self.entries)

    def add_entry(self, entry: UsageEntry) -> None:
        """Add an entry to this block."""
        self.entries.append(entry)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration,
            "message_count": self.message_count,
            "token_counts": self.token_counts.to_dict(),
        }


def normalize_model_name(model: str) -> str:
    """
    Normalize model name for consistent grouping and display.

    This function converts model names to a standardized format
    for consistent grouping across different log entries.

    Args:
        model: Raw model name from API logs

    Returns:
        Normalized model name in lowercase

    Examples:
        >>> normalize_model_name("GPT-4o")
        'gpt-4o'
        >>> normalize_model_name("  claude-3-5-sonnet  ")
        'claude-3-5-sonnet'
        >>> normalize_model_name("")
        'unknown'
    """
    if not model:
        return "unknown"
    return model.lower().strip()


def calculate_burn_rate(
    entries: list[UsageEntry],
    window_seconds: int = 60,
) -> float:
    """
    Calculate token burn rate (tokens per minute) over a time window.

    Args:
        entries: List of UsageEntry objects
        window_seconds: Time window in seconds for rate calculation

    Returns:
        Tokens per minute burn rate
    """
    if not entries:
        return 0.0

    # Sort entries by timestamp
    sorted_entries = sorted(entries, key=lambda e: e.timestamp)

    # Get time window
    now = sorted_entries[-1].timestamp
    window_start = now - __import__("datetime").timedelta(seconds=window_seconds)

    # Filter entries within window
    window_entries = [e for e in sorted_entries if e.timestamp >= window_start]

    if not window_entries:
        return 0.0

    # Calculate total tokens in window
    total_tokens = sum(e.total_tokens for e in window_entries)

    # Calculate rate as tokens per minute
    actual_duration = (now - window_entries[0].timestamp).total_seconds()
    if actual_duration <= 0:
        return 0.0

    return (total_tokens / actual_duration) * 60
