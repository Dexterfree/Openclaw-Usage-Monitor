"""
Data reader module for OpenCLAW Token Usage Monitor.

This module provides functionality to read and parse log files
containing LLM usage data in various formats.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openclaw_monitor.core.models import UsageEntry
from openclaw_monitor.data.parsers.base import BaseParser
from openclaw_monitor.data.parsers.claude import ClaudeParser
from openclaw_monitor.data.parsers.generic import GenericParser
from openclaw_monitor.data.parsers.openai import OpenAIParser
from openclaw_monitor.data.parsers.openclaw import OpenCLAWParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Registry for managing multiple log format parsers.

    Parsers are tried in order - the first parser that can handle
    a log entry format will be used to parse it.
    """

    def __init__(self) -> None:
        """Initialize the parser registry with all available parsers."""
        self.parsers: List[BaseParser] = [
            OpenCLAWParser(),  # Try OpenCLAW format first (most specific)
            OpenAIParser(),    # Then OpenAI format
            ClaudeParser(),    # Then Claude format
            GenericParser(),   # Generic as fallback
        ]

    def parse_entry(
        self,
        raw_data: Dict[str, Any],
    ) -> Optional[UsageEntry]:
        """
        Attempt to parse a log entry using registered parsers.

        Args:
            raw_data: Raw log entry as a dictionary

        Returns:
            UsageEntry object if parsing succeeds, None otherwise
        """
        for parser in self.parsers:
            if parser.can_parse(raw_data):
                try:
                    entry = parser.to_usage_entry(raw_data)
                    if entry and entry.total_tokens > 0:
                        return entry
                except Exception as e:
                    logger.debug(f"Parser {parser.__class__.__name__} failed: {e}")
                    continue

        logger.debug(f"No parser could handle entry: {list(raw_data.keys())[:5]}...")
        return None

    def register_parser(self, parser: BaseParser, position: Optional[int] = None) -> None:
        """
        Register a custom parser.

        Args:
            parser: Parser instance to register
            position: Optional position in parser list (default: append)
        """
        if position is not None:
            self.parsers.insert(position, parser)
        else:
            self.parsers.append(parser)


def find_log_files(
    data_path: Optional[str] = None,
    hours_back: Optional[int] = None,
) -> List[Path]:
    """
    Find log files in the specified path.

    Searches for JSON and JSONL files that may contain usage data.

    Args:
        data_path: Directory to search or specific file path
        hours_back: Only consider files modified within this many hours

    Returns:
        List of Path objects for found log files
    """
    log_files: List[Path] = []

    if data_path:
        path = Path(data_path)
        if path.is_file():
            return [path]
        search_paths = [path]
    else:
        # Default search paths
        search_paths = [
            Path.cwd(),
            Path.cwd() / "logs",
            Path.home() / ".openclaw" / "logs",
        ]

    cutoff_time = None
    if hours_back:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    for search_path in search_paths:
        if not search_path.exists():
            continue

        # Find all JSON/JSONL files
        for pattern in ["*.json", "*.jsonl", "*.ndjson"]:
            for file_path in search_path.rglob(pattern):
                # Skip hidden files
                if file_path.name.startswith("."):
                    continue

                # Check modification time if hours_back specified
                if cutoff_time:
                    try:
                        mtime = datetime.fromtimestamp(
                            file_path.stat().st_mtime,
                            tz=timezone.utc,
                        )
                        if mtime < cutoff_time:
                            continue
                    except OSError:
                        pass

                log_files.append(file_path)

    # Remove duplicates and sort
    log_files = sorted(set(log_files))
    return log_files


def load_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load entries from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of parsed JSON dictionaries
    """
    entries: List[Dict[str, Any]] = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict):
                        entries.append(entry)
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse line {line_num} in {file_path}: {e}")

    except (OSError, IOError) as e:
        logger.warning(f"Failed to read file {file_path}: {e}")

    return entries


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load entries from a JSON file.

    Handles both array format and single object format.

    Args:
        file_path: Path to the JSON file

    Returns:
        List of parsed JSON dictionaries
    """
    entries: List[Dict[str, Any]] = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        entries.append(item)
            elif isinstance(data, dict):
                # Check if this dict has entries as a nested list
                for key in ["entries", "logs", "requests", "data", "items"]:
                    if key in data and isinstance(data[key], list):
                        for item in data[key]:
                            if isinstance(item, dict):
                                entries.append(item)
                        break
                else:
                    # Treat the dict itself as a single entry
                    entries.append(data)

    except (OSError, IOError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to read file {file_path}: {e}")

    return entries


def load_usage_entries(
    data_path: Optional[str] = None,
    hours_back: Optional[int] = None,
    include_raw: bool = False,
    parser_registry: Optional[ParserRegistry] = None,
) -> Tuple[List[UsageEntry], Optional[List[Dict[str, Any]]]]:
    """
    Load and parse usage entries from log files.

    This is the main entry point for loading token usage data.
    It searches for log files, reads them, and parses the entries
    using the parser registry.

    Args:
        data_path: Directory to search or specific file path
        hours_back: Only consider data from this many hours ago
        include_raw: Include raw JSON data in return value
        parser_registry: Custom parser registry (uses default if None)

    Returns:
        Tuple of (parsed UsageEntry list, optional raw data list)
    """
    if parser_registry is None:
        parser_registry = ParserRegistry()

    # Find log files
    log_files = find_log_files(data_path, hours_back)

    if not log_files:
        logger.info("No log files found")
        return [], None if not include_raw else []

    # Load and parse entries
    usage_entries: List[UsageEntry] = []
    raw_data: List[Dict[str, Any]] = [] if include_raw else None

    for file_path in log_files:
        logger.debug(f"Reading file: {file_path}")

        # Determine file type and load
        if file_path.suffix in [".jsonl", ".ndjson"]:
            file_entries = load_jsonl_file(file_path)
        else:
            file_entries = load_json_file(file_path)

        # Parse entries
        for raw_entry in file_entries:
            if include_raw and raw_data is not None:
                raw_data.append(raw_entry)

            usage_entry = parser_registry.parse_entry(raw_entry)
            if usage_entry:
                usage_entries.append(usage_entry)

    # Sort by timestamp
    usage_entries.sort(key=lambda e: e.timestamp)

    logger.info(f"Loaded {len(usage_entries)} usage entries from {len(log_files)} file(s)")

    return usage_entries, raw_data


def filter_entries_by_time(
    entries: List[UsageEntry],
    hours_back: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[UsageEntry]:
    """
    Filter usage entries by time range.

    Args:
        entries: List of UsageEntry objects
        hours_back: Only include entries from this many hours ago
        start_time: Only include entries after this time
        end_time: Only include entries before this time

    Returns:
        Filtered list of UsageEntry objects
    """
    if not entries:
        return entries

    now = datetime.now(timezone.utc)

    if hours_back:
        start_time = now - timedelta(hours=hours_back)

    if start_time is None and end_time is None:
        return entries

    filtered = []
    for entry in entries:
        if start_time and entry.timestamp < start_time:
            continue
        if end_time and entry.timestamp > end_time:
            continue
        filtered.append(entry)

    return filtered
