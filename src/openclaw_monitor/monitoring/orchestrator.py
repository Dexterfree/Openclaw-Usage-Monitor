"""
Monitor orchestrator for OpenCLAW Token Usage Monitor.

This module coordinates the monitoring process, managing data loading,
analysis, and display updates.
"""

from __future__ import annotations

import logging
import signal
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from openclaw_monitor.core.models import UsageEntry
from openclaw_monitor.core.settings import MonitorSettings
from openclaw_monitor.core.plans import PlanManager
from openclaw_monitor.data.analyzer import SessionAnalyzer
from openclaw_monitor.data.reader import ParserRegistry, load_usage_entries
from openclaw_monitor.data.analysis import UsageAnalysis
from openclaw_monitor.terminal.themes import get_theme
from openclaw_monitor.ui.display_controller import DisplayController
from rich.console import Console

logger = logging.getLogger(__name__)


class MonitorOrchestrator:
    """
    Main orchestrator for the token usage monitor.

    Coordinates data loading, analysis, and display for realtime
    and report-based monitoring modes.
    """

    def __init__(
        self,
        settings: MonitorSettings,
        console: Optional[Console] = None,
    ):
        """
        Initialize the monitor orchestrator.

        Args:
            settings: Configuration settings
            console: Rich Console for output (created if not provided)
        """
        self.settings = settings
        self.theme = get_theme(settings.color_scheme)
        self.console = console or Console(theme=self.theme.to_rich_theme())

        self.display_controller = DisplayController(
            console=self.console,
            theme=self.theme,
            timezone_str=settings.timezone,
        )

        self.session_analyzer = SessionAnalyzer(
            session_gap_minutes=settings.session_gap_minutes,
            session_window_hours=settings.session_window_hours,
        )

        self.parser_registry = ParserRegistry()

        # State
        self._running = False
        self._entries: List[UsageEntry] = []
        self._token_limit: int = 0

        # Setup signal handlers
        self._setup_signals()

    def _setup_signals(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._running = False

    def start(self) -> None:
        """Start the monitoring process."""
        self._running = True

        # Get token limit from plan
        self._token_limit = PlanManager.get_token_limit(
            self.settings.plan,
            self.settings.custom_limit_tokens,
        )

        # Load initial data
        self._load_data()

        # Display based on view mode
        if self.settings.view == "realtime":
            self._run_realtime()
        elif self.settings.view == "daily":
            self._run_daily()
        elif self.settings.view == "monthly":
            self._run_monthly()
        elif self.settings.view == "detailed":
            self._run_detailed()

    def _load_data(self) -> None:
        """Load usage data from log files."""
        logger.info("Loading usage data...")

        self._entries, _ = load_usage_entries(
            data_path=self.settings.log_path,
            hours_back=None,  # Load all data
            include_raw=False,
            parser_registry=self.parser_registry,
        )

        logger.info(f"Loaded {len(self._entries)} usage entries")

        if not self._entries:
            self.display_controller.display_warning(
                "No usage data found. Check --log-path or create log files."
            )

    def _refresh_data(self) -> None:
        """Refresh usage data (for realtime monitoring)."""
        self._load_data()

    def _run_realtime(self) -> None:
        """Run the realtime monitoring loop."""
        import time

        logger.info("Starting realtime monitoring")

        try:
            while self._running:
                # Refresh data
                self._refresh_data()

                # Display current state
                self.display_controller.display_realtime(
                    entries=self._entries,
                    token_limit=self._token_limit,
                    session_analyzer=self.session_analyzer,
                )

                # Check for warnings
                self._check_warnings()

                # Wait for next refresh
                time.sleep(self.settings.refresh_rate)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            self.display_controller.clear()
            logger.info("Monitoring stopped")

    def _run_daily(self) -> None:
        """Run the daily report view."""
        logger.info("Displaying daily report")

        # Filter for recent data (last 30 days)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent_entries = [e for e in self._entries if e.timestamp >= cutoff]

        self.display_controller.display_daily(
            entries=recent_entries,
            token_limit=self._token_limit,
        )

        # Only wait for input if running interactively
        try:
            input("Press Enter to exit...")
        except (EOFError, OSError):
            pass

    def _run_monthly(self) -> None:
        """Run the monthly report view."""
        logger.info("Displaying monthly report")

        # Filter for recent data (last 12 months)
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        recent_entries = [e for e in self._entries if e.timestamp >= cutoff]

        self.display_controller.display_monthly(
            entries=recent_entries,
            token_limit=self._token_limit,
        )

        # Only wait for input if running interactively
        try:
            input("Press Enter to exit...")
        except (EOFError, OSError):
            pass

    def _run_detailed(self) -> None:
        """Run the detailed breakdown view."""
        logger.info("Displaying detailed breakdown")

        # Use last 7 days of data for detailed view
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        recent_entries = [e for e in self._entries if e.timestamp >= cutoff]

        self.display_controller.display_detailed(
            entries=recent_entries,
            token_limit=self._token_limit,
        )

        # Only wait for input if running interactively
        try:
            input("Press Enter to exit...")
        except (EOFError, OSError):
            # Non-interactive environment, just exit
            pass

    def _check_warnings(self) -> None:
        """Check for usage warnings and display them."""
        if not self._entries:
            return

        analysis = UsageAnalysis(self._entries, self.settings.timezone)
        total_tokens = analysis.total_stats.total_tokens

        if self._token_limit == 0:
            return  # No warnings for unlimited

        percentage = get_percentage_used(total_tokens, self._token_limit)

        if percentage >= self.settings.critical_threshold:
            self.display_controller.display_warning(
                f"Token usage at {percentage:.1f}% - critical threshold!"
            )
        elif percentage >= self.settings.warning_threshold:
            self.display_controller.display_info(
                f"Token usage at {percentage:.1f}% - approaching limit"
            )

    def stop(self) -> None:
        """Stop the monitoring process."""
        self._running = False
