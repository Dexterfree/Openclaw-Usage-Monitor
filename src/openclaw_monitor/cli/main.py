"""
Main CLI entry point for OpenCLAW Token Usage Monitor.

This module provides the command-line interface for the monitor.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List, Optional

from openclaw_monitor.core.settings import MonitorSettings, get_app_config, reset_settings
from openclaw_monitor.monitoring.orchestrator import MonitorOrchestrator
from openclaw_monitor._version import __version__
from rich.console import Console
import sys
import io


def create_parser() -> argparse.ArgumentParser:
    """
    Create the command-line argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="openclaw-monitor",
        description="Universal token usage monitoring for all LLM providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Realtime monitoring with medium plan
  openclaw-monitor --view realtime --plan medium

  # Daily report with custom log path
  openclaw-monitor --view daily --log-path ./logs

  # Monthly report with custom token limit
  openclaw-monitor --view monthly --plan custom --custom-limit-tokens 5000000

  # Realtime monitoring with 10 second refresh
  openclaw-monitor --view realtime --refresh-rate 10 --timezone America/New_York
        """,
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # View mode
    parser.add_argument(
        "--view",
        choices=["realtime", "daily", "monthly", "detailed"],
        default="realtime",
        help="View mode for displaying usage data (default: realtime)",
    )

    # Plan configuration
    parser.add_argument(
        "--plan",
        choices=["small", "medium", "large", "unlimited", "custom"],
        default="medium",
        help="Token limit plan (default: medium)",
    )

    parser.add_argument(
        "--custom-limit-tokens",
        type=int,
        default=None,
        metavar="N",
        help="Custom token limit (required when --plan=custom)",
    )

    # Data configuration
    parser.add_argument(
        "--log-path",
        type=str,
        default=None,
        metavar="PATH",
        help="Path to log file or directory containing usage logs",
    )

    # Refresh configuration
    parser.add_argument(
        "--refresh-rate",
        type=int,
        default=5,
        metavar="SECONDS",
        help="Refresh rate in seconds for realtime view (default: 5, range: 1-300)",
    )

    # Timezone configuration
    parser.add_argument(
        "--timezone",
        type=str,
        default="UTC",
        metavar="TZ",
        help="Timezone for displaying timestamps (default: UTC)",
    )

    # Session configuration
    parser.add_argument(
        "--session-gap-minutes",
        type=int,
        default=30,
        metavar="MINUTES",
        help="Minutes of inactivity before starting a new session (default: 30)",
    )

    parser.add_argument(
        "--session-window-hours",
        type=int,
        default=5,
        metavar="HOURS",
        help="Hours to look back for session tracking (default: 5)",
    )

    # Warning thresholds
    parser.add_argument(
        "--warning-threshold",
        type=float,
        default=75.0,
        metavar="PERCENT",
        help="Percentage threshold for showing warnings (default: 75.0)",
    )

    parser.add_argument(
        "--critical-threshold",
        type=float,
        default=90.0,
        metavar="PERCENT",
        help="Percentage threshold for showing critical warnings (default: 90.0)",
    )

    # UI configuration
    parser.add_argument(
        "--color-scheme",
        choices=["auto", "light", "dark"],
        default="auto",
        help="Color scheme for UI (default: auto)",
    )

    # Debug options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    return parser


def setup_logging(debug: bool = False, verbose: bool = False) -> None:
    """
    Setup logging configuration.

    Args:
        debug: Enable debug level logging
        verbose: Enable verbose output
    """
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_console() -> Console:
    """
    Create a Rich Console with proper UTF-8 encoding for Windows.

    Returns:
        Configured Console instance
    """
    # On Windows, configure UTF-8 encoding for emoji support
    if sys.platform == "win32":
        try:
            # Try to set console to UTF-8 mode
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            # Fallback: wrap stdout in a UTF-8 text wrapper
            if hasattr(sys.stdout, "buffer"):
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, encoding="utf-8", errors="replace", newline=None
                )
            if hasattr(sys.stderr, "buffer"):
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, encoding="utf-8", errors="replace", newline=None
                )

    return Console(
        force_terminal=True,
        legacy_windows=False,  # Disable legacy Windows rendering
    )


def validate_args(args: argparse.Namespace) -> List[str]:
    """
    Validate command-line arguments.

    Args:
        args: Parsed arguments

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Validate custom limit
    if args.plan == "custom" and args.custom_limit_tokens is None:
        errors.append(
            "--custom-limit-tokens is required when --plan=custom"
        )

    # Validate refresh rate
    if not (1 <= args.refresh_rate <= 300):
        errors.append(
            "--refresh-rate must be between 1 and 300"
        )

    # Validate thresholds
    if not (0 <= args.warning_threshold <= 100):
        errors.append(
            "--warning-threshold must be between 0 and 100"
        )

    if not (0 <= args.critical_threshold <= 100):
        errors.append(
            "--critical-threshold must be between 0 and 100"
        )

    if args.warning_threshold >= args.critical_threshold:
        errors.append(
            "--warning-threshold must be less than --critical-threshold"
        )

    return errors


def create_settings_from_args(args: argparse.Namespace) -> MonitorSettings:
    """
    Create MonitorSettings from parsed arguments.

    Args:
        args: Parsed arguments

    Returns:
        MonitorSettings object
    """
    return MonitorSettings(
        view=args.view,
        plan=args.plan,
        custom_limit_tokens=args.custom_limit_tokens,
        log_path=args.log_path,
        refresh_rate=args.refresh_rate,
        timezone=args.timezone,
        session_gap_minutes=args.session_gap_minutes,
        session_window_hours=args.session_window_hours,
        warning_threshold=args.warning_threshold,
        critical_threshold=args.critical_threshold,
        color_scheme=args.color_scheme,
    )


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(debug=args.debug, verbose=args.verbose)

    # Create console with proper UTF-8 encoding
    console = create_console()

    # Validate arguments
    errors = validate_args(args)
    if errors:
        for error in errors:
            console.print(f"[red]Error:[/] {error}")
        return 1

    # Create settings
    try:
        settings = create_settings_from_args(args)
    except Exception as e:
        console.print(f"[red]Configuration Error:[/] {e}")
        return 1

    # Create and run monitor
    try:
        orchestrator = MonitorOrchestrator(
            settings=settings,
            console=console,
        )
        orchestrator.start()
        return 0
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted by user[/]")
        return 0
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        if args.debug:
            import traceback
            console.print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
