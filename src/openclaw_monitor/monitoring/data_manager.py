"""
Data manager for OpenCLAW Token Usage Monitor.

This module handles data loading, caching, and refresh operations.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from openclaw_monitor.core.models import UsageEntry
from openclaw_monitor.data.reader import ParserRegistry, load_usage_entries

logger = logging.getLogger(__name__)


class DataManager:
    """
    Manages loading and caching of usage data.

    Provides thread-safe data access with automatic refresh
    capabilities for realtime monitoring.
    """

    def __init__(
        self,
        log_path: Optional[str] = None,
        parser_registry: Optional[ParserRegistry] = None,
    ):
        """
        Initialize the data manager.

        Args:
            log_path: Path to log file or directory
            parser_registry: Custom parser registry
        """
        self.log_path = log_path
        self.parser_registry = parser_registry or ParserRegistry()

        self._entries: List[UsageEntry] = []
        self._raw_data: Optional[List[dict]] = None
        self._last_load_time: Optional[float] = None
        self._lock = threading.RLock()

    def load(
        self,
        hours_back: Optional[int] = None,
        force_refresh: bool = False,
    ) -> List[UsageEntry]:
        """
        Load usage entries from log files.

        Args:
            hours_back: Only load data from this many hours ago
            force_refresh: Force reload even if recently loaded

        Returns:
            List of UsageEntry objects
        """
        with self._lock:
            current_time = time.time()

            # Check if we can use cached data
            if (
                not force_refresh
                and self._entries
                and self._last_load_time
                and (current_time - self._last_load_time) < 5  # 5 second cache
            ):
                return self._entries

            # Load fresh data
            self._entries, self._raw_data = load_usage_entries(
                data_path=self.log_path,
                hours_back=hours_back,
                include_raw=False,
                parser_registry=self.parser_registry,
            )

            self._last_load_time = current_time

            return self._entries

    def get_entries(
        self,
        hours_back: Optional[int] = None,
    ) -> List[UsageEntry]:
        """
        Get cached entries, optionally filtering by time.

        Args:
            hours_back: Only include entries from this many hours ago

        Returns:
            Filtered list of UsageEntry objects
        """
        with self._lock:
            if not self._entries:
                return []

            if hours_back is None:
                return self._entries.copy()

            cutoff = datetime.now(timezone.utc) - __import__(
                "datetime"
            ).timedelta(hours=hours_back)
            return [e for e in self._entries if e.timestamp >= cutoff]

    def refresh(self) -> int:
        """
        Refresh the cached data.

        Returns:
            Number of entries loaded
        """
        with self._lock:
            self.load(force_refresh=True)
            return len(self._entries)

    def get_entry_count(self) -> int:
        """
        Get the number of cached entries.

        Returns:
            Number of entries
        """
        with self._lock:
            return len(self._entries)

    def clear_cache(self) -> None:
        """Clear the cached data."""
        with self._lock:
            self._entries.clear()
            self._raw_data = None
            self._last_load_time = None
