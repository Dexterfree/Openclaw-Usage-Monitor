"""
Clawdbot log parser for OpenCLAW Token Usage Monitor.

This module parses Clawdbot's log format and extracts token usage information.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def parse_clawdbot_log_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single Clawdbot log line (JSONL format).

    Args:
        line: A single log line from Clawdbot log file

    Returns:
        Parsed log entry as dict, or None if parsing fails
    """
    try:
        # Clawdbot logs are JSON objects, possibly double-encoded
        parsed = json.loads(line.strip())

        # Handle double-encoded JSON (some logs have {"0": "...", "1": "...", ...})
        if isinstance(parsed, dict) and "0" in parsed and "1" in parsed:
            # This is a double-encoded log entry
            message = parsed.get("1", "")
            metadata = parsed.get("_meta", {})

            return {
                "timestamp": metadata.get("date", ""),
                "level": metadata.get("logLevelName", "INFO"),
                "subsystem": metadata.get("name", ""),
                "message": message,
                "raw": parsed,
            }

        # Handle standard diagnostic events
        if isinstance(parsed, dict) and "type" in parsed:
            return {
                "timestamp": parsed.get("ts", datetime.now(timezone.utc).timestamp()),
                "type": parsed.get("type"),
                "data": parsed,
                "raw": parsed,
            }

        # Handle regular JSON logs
        if isinstance(parsed, dict):
            time_str = parsed.get("time", "")
            return {
                "timestamp": time_str,
                "level": parsed.get("level", "info"),
                "subsystem": parsed.get("subsystem", ""),
                "message": parsed.get("message", ""),
                "raw": parsed,
            }

        return None

    except json.JSONDecodeError:
        return None
    except Exception as e:
        logger.debug(f"Failed to parse log line: {e}")
        return None


def extract_token_usage_from_diagnostic(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract token usage from a Clawdbot diagnostic event.

    Args:
        event: Parsed diagnostic event

    Returns:
        Token usage entry compatible with OpenCLAW format, or None
    """
    if not isinstance(event, dict):
        return None

    event_type = event.get("type") or event.get("data", {}).get("type")
    data = event.get("data", event)

    if event_type != "model.usage":
        return None

    try:
        # Extract usage information
        usage = data.get("usage", {})
        context = data.get("context", {})

        # Map Clawdbot format to OpenCLAW format
        entry = {
            "timestamp": datetime.fromtimestamp(
                data.get("ts", datetime.now(timezone.utc).timestamp()),
                tz=timezone.utc
            ).isoformat(),
            "model": data.get("model", "unknown"),
            "provider": data.get("provider", "unknown"),
            "input_tokens": usage.get("input", 0) or usage.get("promptTokens", 0),
            "output_tokens": usage.get("output", 0),
            "cache_read_tokens": usage.get("cacheRead", 0),
            "cache_creation_tokens": usage.get("cacheWrite", 0),
            "request_id": data.get("sessionId", "unknown"),
            "metadata": {
                "session_key": data.get("sessionKey"),
                "channel": data.get("channel"),
                "cost_usd": data.get("costUsd"),
                "duration_ms": data.get("durationMs"),
                "context_limit": context.get("limit"),
                "context_used": context.get("used"),
            }
        }

        return entry

    except Exception as e:
        logger.debug(f"Failed to extract token usage from diagnostic: {e}")
        return None


def load_clawdbot_logs(
    log_path: str,
    hours_back: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Load and parse Clawdbot log files.

    Args:
        log_path: Path to Clawdbot log file or directory
        hours_back: Only load logs from the last N hours (None for all)

    Returns:
        List of parsed log entries
    """
    log_path = Path(log_path)

    # Determine log files to read
    if log_path.is_file():
        log_files = [log_path]
    elif log_path.is_dir():
        # Clawdbot logs are named like clawdbot-YYYY-MM-DD.log
        log_files = sorted(log_path.glob("clawdbot-*.log"), reverse=True)
    else:
        logger.warning(f"Clawdbot log path not found: {log_path}")
        return []

    entries = []
    cutoff_time = None

    if hours_back:
        from datetime import timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    for log_file in log_files:
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    parsed = parse_clawdbot_log_line(line)
                    if parsed:
                        # Check time filter
                        if cutoff_time:
                            try:
                                ts_str = parsed.get("timestamp")
                                if isinstance(ts_str, (int, float)):
                                    ts = datetime.fromtimestamp(ts_str, tz=timezone.utc)
                                elif isinstance(ts_str, str):
                                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                                else:
                                    continue

                                if ts < cutoff_time:
                                    continue
                            except:
                                pass

                        entries.append(parsed)

        except Exception as e:
            logger.error(f"Failed to read log file {log_file}: {e}")

    logger.info(f"Loaded {len(entries)} log entries from Clawdbot logs")
    return entries


def extract_token_usage_from_logs(
    log_path: str,
    hours_back: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Extract token usage entries from Clawdbot logs.

    Args:
        log_path: Path to Clawdbot log file or directory
        hours_back: Only load logs from the last N hours (None for all)

    Returns:
        List of token usage entries in OpenCLAW format
    """
    logs = load_clawdbot_logs(log_path, hours_back)

    token_entries = []
    for log_entry in logs:
        usage = extract_token_usage_from_diagnostic(log_entry)
        if usage:
            token_entries.append(usage)

    logger.info(f"Extracted {len(token_entries)} token usage entries from Clawdbot logs")
    return token_entries


class ClawdbotLogParser:
    """
    Parser for Clawdbot log format.

    This parser can read Clawdbot's JSONL log files and extract
    token usage information from diagnostic events.
    """

    def __init__(self, log_path: str):
        """
        Initialize the Clawdbot log parser.

        Args:
            log_path: Path to Clawdbot log file or directory
        """
        self.log_path = Path(log_path)

    def parse(self, hours_back: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Parse Clawdbot logs and extract token usage.

        Args:
            hours_back: Only parse logs from the last N hours

        Returns:
            List of token usage entries
        """
        return extract_token_usage_from_logs(str(self.log_path), hours_back)

    def get_available_dates(self) -> List[str]:
        """
        Get list of dates with available log files.

        Returns:
            List of date strings (YYYY-MM-DD)
        """
        if self.log_path.is_file():
            # Extract date from filename like clawdbot-2026-03-11.log
            name = self.log_path.stem
            if name.startswith("clawdbot-"):
                date_str = name.replace("clawdbot-", "")
                return [date_str]
            return []

        if self.log_path.is_dir():
            dates = []
            for log_file in self.log_path.glob("clawdbot-*.log"):
                name = log_file.stem
                date_str = name.replace("clawdbot-", "")
                dates.append(date_str)
            return sorted(dates, reverse=True)

        return []


def register_clawdbot_parser():
    """
    Register the Clawdbot parser with the parser registry.

    Call this function to add Clawdbot log parsing support
    to the OpenCLAW Monitor.
    """
    try:
        from openclaw_monitor.data.reader import ParserRegistry

        # Register parser for Clawdbot log files
        ParserRegistry.register_parser(
            name="clawdbot",
            pattern="clawdbot-*.log",
            parser_func=extract_token_usage_from_logs,
            description="Clawdbot JSONL log format with diagnostic events",
        )

        logger.info("Clawdbot log parser registered successfully")

    except ImportError:
        logger.warning("Parser registry not available, skipping registration")


# Convenience function for direct usage
def parse_clawdbot_directory(
    log_dir: str = "C:\\tmp\\clawdbot",
    hours_back: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Parse Clawdbot logs from the default directory.

    Args:
        log_dir: Path to Clawdbot log directory
        hours_back: Only parse logs from the last N hours

    Returns:
        List of token usage entries

    Example:
        >>> entries = parse_clawdbot_directory(hours_back=24)
        >>> for entry in entries:
        ...     print(f"{entry['model']}: {entry['input_tokens']} + {entry['output_tokens']}")
    """
    parser = ClawdbotLogParser(log_dir)
    return parser.parse(hours_back=hours_back)


if __name__ == "__main__":
    # Test the parser
    import sys

    log_path = sys.argv[1] if len(sys.argv) > 1 else "C:\\tmp\\clawdbot"

    print(f"Parsing Clawdbot logs from: {log_path}")

    entries = parse_clawdbot_directory(log_path, hours_back=24)

    print(f"\nFound {len(entries)} token usage entries:\n")

    for entry in entries[:10]:  # Show first 10
        print(f"  Model: {entry['model']}")
        print(f"  Provider: {entry['provider']}")
        print(f"  Tokens: {entry['input_tokens']} + {entry['output_tokens']}")
        if entry.get('cache_read_tokens'):
            print(f"  Cache: {entry['cache_read_tokens']} read, {entry['cache_creation_tokens']} write")
        if entry.get('metadata', {}).get('cost_usd'):
            print(f"  Cost: ${entry['metadata']['cost_usd']:.4f}")
        print()
