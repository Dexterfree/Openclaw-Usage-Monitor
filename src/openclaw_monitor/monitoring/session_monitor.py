"""
Session monitor for OpenCLAW Token Usage Monitor.

This module tracks and analyzes API usage sessions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from openclaw_monitor.core.models import SessionBlock, UsageEntry
from openclaw_monitor.data.analyzer import SessionAnalyzer

logger = logging.getLogger(__name__)


class SessionMonitor:
    """
    Monitors and tracks API usage sessions.

    Provides real-time session tracking with configurable
    gap detection for session boundaries.
    """

    def __init__(
        self,
        session_gap_minutes: int = 30,
        session_window_hours: int = 5,
    ):
        """
        Initialize the session monitor.

        Args:
            session_gap_minutes: Minutes of inactivity before new session
            session_window_hours: Hours to look back for session tracking
        """
        self.session_gap_minutes = session_gap_minutes
        self.session_window_hours = session_window_hours

        self._analyzer = SessionAnalyzer(
            session_gap_minutes=session_gap_minutes,
            session_window_hours=session_window_hours,
        )

    def get_active_session(
        self,
        entries: List[UsageEntry],
        current_time: Optional[datetime] = None,
    ) -> Optional[SessionBlock]:
        """
        Get the currently active session.

        Args:
            entries: List of UsageEntry objects
            current_time: Current time (defaults to now)

        Returns:
            SessionBlock if active session exists, None otherwise
        """
        return self._analyzer.get_active_session(entries, current_time)

    def is_session_active(
        self,
        entries: List[UsageEntry],
        current_time: Optional[datetime] = None,
    ) -> bool:
        """
        Check if there's an active session.

        Args:
            entries: List of UsageEntry objects
            current_time: Current time (defaults to now)

        Returns:
            True if there's an active session
        """
        return self.get_active_session(entries, current_time) is not None

    def get_time_since_last_activity(
        self,
        entries: List[UsageEntry],
        current_time: Optional[datetime] = None,
    ) -> Optional[float]:
        """
        Get time since the last API activity.

        Args:
            entries: List of UsageEntry objects
            current_time: Current time (defaults to now)

        Returns:
            Minutes since last activity, or None if no entries
        """
        if not entries:
            return None

        if current_time is None:
            current_time = datetime.now(timezone.utc)

        last_entry = max(entries, key=lambda e: e.timestamp)
        delta = current_time - last_entry.timestamp

        return delta.total_seconds() / 60

    def should_create_new_session(
        self,
        entries: List[UsageEntry],
        current_time: Optional[datetime] = None,
    ) -> bool:
        """
        Check if activity gap indicates a new session should start.

        Args:
            entries: List of UsageEntry objects
            current_time: Current time (defaults to now)

        Returns:
            True if gap exceeds threshold
        """
        time_since = self.get_time_since_last_activity(entries, current_time)

        if time_since is None:
            return True

        return time_since > self.session_gap_minutes
