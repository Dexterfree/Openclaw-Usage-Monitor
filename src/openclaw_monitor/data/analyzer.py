"""
Session analyzer for OpenCLAW Token Usage Monitor.

This module provides functionality for analyzing API usage sessions,
grouping related requests, and calculating session-level metrics.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from openclaw_monitor.core.calculations import calculate_session_blocks
from openclaw_monitor.core.models import SessionBlock, UsageEntry


@dataclass
class SessionSummary:
    """
    Summary of a single session.

    Provides high-level metrics for a session block.
    """

    session_id: str
    model: str
    provider: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    message_count: int
    total_tokens: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    @property
    def tokens_per_minute(self) -> float:
        """Calculate tokens per minute during the session."""
        if self.duration_minutes <= 0:
            return 0.0
        return self.total_tokens / self.duration_minutes

    @property
    def messages_per_minute(self) -> float:
        """Calculate messages per minute during the session."""
        if self.duration_minutes <= 0:
            return 0.0
        return self.message_count / self.duration_minutes

    @property
    def output_ratio(self) -> float:
        """Calculate ratio of output to input tokens."""
        if self.input_tokens == 0:
            return 0.0
        return self.output_tokens / self.input_tokens

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_minutes": round(self.duration_minutes, 2),
            "message_count": self.message_count,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "tokens_per_minute": round(self.tokens_per_minute, 2),
            "messages_per_minute": round(self.messages_per_minute, 2),
            "output_ratio": round(self.output_ratio, 2),
        }


@dataclass
class SessionAnalysis:
    """
    Analysis of sessions within a time window.

    Provides aggregated statistics and insights about sessions.
    """

    sessions: List[SessionSummary] = field(default_factory=list)
    total_sessions: int = 0
    total_tokens: int = 0
    total_duration_minutes: float = 0.0
    total_messages: int = 0
    most_used_model: str = ""
    most_used_provider: str = ""
    average_session_duration: float = 0.0
    average_tokens_per_session: float = 0.0
    average_messages_per_session: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_sessions": self.total_sessions,
            "total_tokens": self.total_tokens,
            "total_duration_minutes": round(self.total_duration_minutes, 2),
            "total_messages": self.total_messages,
            "most_used_model": self.most_used_model,
            "most_used_provider": self.most_used_provider,
            "average_session_duration": round(self.average_session_duration, 2),
            "average_tokens_per_session": round(self.average_tokens_per_session, 2),
            "average_messages_per_session": round(self.average_messages_per_session, 2),
            "sessions": [s.to_dict() for s in self.sessions],
        }


class SessionAnalyzer:
    """
    Analyzer for API usage sessions.

    Groups related API requests into sessions based on time gaps
    and provides session-level analysis.
    """

    def __init__(
        self,
        session_gap_minutes: int = 30,
        session_window_hours: int = 5,
    ):
        """
        Initialize the session analyzer.

        Args:
            session_gap_minutes: Minutes of inactivity before starting a new session
            session_window_hours: Hours to look back for session tracking
        """
        self.session_gap_minutes = session_gap_minutes
        self.session_window_hours = session_window_hours

    def analyze_sessions(
        self,
        entries: List[UsageEntry],
    ) -> SessionAnalysis:
        """
        Analyze sessions from usage entries.

        Args:
            entries: List of UsageEntry objects

        Returns:
            SessionAnalysis object with session summaries
        """
        if not entries:
            return SessionAnalysis()

        # Group into session blocks
        blocks = calculate_session_blocks(
            entries,
            gap_minutes=self.session_gap_minutes,
        )

        # Convert blocks to summaries
        summaries = []
        model_counts: Dict[str, int] = defaultdict(int)
        provider_counts: Dict[str, int] = defaultdict(int)

        for block in blocks:
            summary = self._summarize_block(block)
            summaries.append(summary)
            model_counts[summary.model] += summary.total_tokens
            provider_counts[summary.provider] += summary.total_tokens

        # Calculate overall stats
        total_tokens = sum(s.total_tokens for s in summaries)
        total_duration = sum(s.duration_minutes for s in summaries)
        total_messages = sum(s.message_count for s in summaries)

        most_used_model = max(model_counts.items(), key=lambda x: x[1])[0] if model_counts else ""
        most_used_provider = max(provider_counts.items(), key=lambda x: x[1])[0] if provider_counts else ""

        return SessionAnalysis(
            sessions=summaries,
            total_sessions=len(summaries),
            total_tokens=total_tokens,
            total_duration_minutes=total_duration,
            total_messages=total_messages,
            most_used_model=most_used_model,
            most_used_provider=most_used_provider,
            average_session_duration=total_duration / len(summaries) if summaries else 0.0,
            average_tokens_per_session=total_tokens / len(summaries) if summaries else 0.0,
            average_messages_per_session=total_messages / len(summaries) if summaries else 0.0,
        )

    def get_active_session(
        self,
        entries: List[UsageEntry],
        current_time: Optional[datetime] = None,
    ) -> Optional[SessionBlock]:
        """
        Get the currently active session (if any).

        An active session is one where the last entry is within
        the session gap threshold from now.

        Args:
            entries: List of UsageEntry objects
            current_time: Current time (defaults to now)

        Returns:
            SessionBlock if there's an active session, None otherwise
        """
        if not entries:
            return None

        if current_time is None:
            current_time = datetime.now(timezone.utc)

        # Sort entries by timestamp
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)

        # Get recent entries within window
        cutoff = current_time - timedelta(hours=self.session_window_hours)
        recent_entries = [e for e in sorted_entries if e.timestamp >= cutoff]

        if not recent_entries:
            return None

        # Group into sessions and find the active one
        blocks = calculate_session_blocks(
            recent_entries,
            gap_minutes=self.session_gap_minutes,
        )

        # The last block is the most recent - check if it's active
        if blocks:
            last_block = blocks[-1]
            time_since_last = (current_time - last_block.end_time).total_seconds() / 60

            if time_since_last <= self.session_gap_minutes:
                return last_block

        return None

    def _summarize_block(self, block: SessionBlock) -> SessionSummary:
        """Convert a SessionBlock to a SessionSummary."""
        return SessionSummary(
            session_id=block.session_id,
            model=block.model,
            provider=block.provider,
            start_time=block.start_time or datetime.now(timezone.utc),
            end_time=block.end_time or datetime.now(timezone.utc),
            duration_minutes=block.duration / 60 if block.duration else 0.0,
            message_count=block.message_count,
            total_tokens=block.token_counts.total_tokens,
            input_tokens=block.token_counts.input_tokens,
            output_tokens=block.token_counts.output_tokens,
            cache_read_tokens=block.token_counts.cache_read_tokens,
            cache_creation_tokens=block.token_counts.cache_creation_tokens,
        )

    def get_session_breakdown(
        self,
        entries: List[UsageEntry],
    ) -> Dict[str, Any]:
        """
        Get a detailed breakdown of sessions.

        Args:
            entries: List of UsageEntry objects

        Returns:
            Dictionary with session breakdown information
        """
        analysis = self.analyze_sessions(entries)

        return {
            "analysis": analysis.to_dict(),
            "recent_sessions": [s.to_dict() for s in analysis.sessions[-5:]],
        }
