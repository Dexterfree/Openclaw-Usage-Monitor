"""
Base parser interface for OpenCLAW Token Usage Monitor.

This module defines the abstract base class that all specific parsers
must implement, ensuring a consistent interface for parsing different
log formats.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from openclaw_monitor.core.models import UsageEntry


class BaseParser(ABC):
    """
    Abstract base class for all log format parsers.

    Each parser must implement methods to detect if it can parse a given
    log entry and extract the required information to create a UsageEntry.
    """

    @abstractmethod
    def can_parse(self, data: Dict[str, Any]) -> bool:
        """
        Determine if this parser can handle the given log data.

        This method should check for format-specific markers or fields
        that uniquely identify this log format.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            True if this parser can handle the data format
        """
        pass

    @abstractmethod
    def extract_tokens(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token information from the log entry.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary with token counts containing any of:
            - input_tokens
            - output_tokens
            - cache_creation_tokens
            - cache_read_tokens
        """
        pass

    @abstractmethod
    def extract_model(self, data: Dict[str, Any]) -> str:
        """
        Extract the model identifier from the log entry.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Model name string
        """
        pass

    @abstractmethod
    def extract_timestamp(self, data: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract the timestamp from the log entry.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            datetime object or None if not available
        """
        pass

    def extract_provider(self, data: Dict[str, Any]) -> str:
        """
        Extract the provider name from the log entry.

        Default implementation returns empty string. Override if the
        log format explicitly includes provider information.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Provider name string
        """
        return ""

    def extract_request_id(self, data: Dict[str, Any]) -> str:
        """
        Extract the request ID from the log entry.

        Default implementation returns empty string. Override if the
        log format includes request identifiers.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Request ID string
        """
        return ""

    def extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract additional metadata from the log entry.

        Default implementation returns empty dict. Override to capture
        provider-specific information.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary of metadata
        """
        return {}

    def to_usage_entry(self, data: Dict[str, Any]) -> Optional[UsageEntry]:
        """
        Convert raw log data to a UsageEntry object.

        This method orchestrates the extraction of all required fields
        and creates a UsageEntry instance.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            UsageEntry object or None if parsing fails
        """
        try:
            model = self.extract_model(data)
            timestamp = self.extract_timestamp(data)

            if timestamp is None:
                timestamp = datetime.now()

            tokens = self.extract_tokens(data)

            return UsageEntry(
                timestamp=timestamp,
                input_tokens=tokens.get("input_tokens", 0),
                output_tokens=tokens.get("output_tokens", 0),
                cache_creation_tokens=tokens.get("cache_creation_tokens", 0),
                cache_read_tokens=tokens.get("cache_read_tokens", 0),
                model=model,
                provider=self.extract_provider(data),
                request_id=self.extract_request_id(data),
                metadata=self.extract_metadata(data),
            )
        except Exception as e:
            # Log parsing error but don't raise - allow other parsers to try
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"{self.__class__.__name__} failed to parse entry: {e}")
            return None


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to an integer.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_iso_timestamp(value: Any) -> Optional[datetime]:
    """
    Parse an ISO 8601 timestamp string to datetime.

    Handles various timestamp formats including:
    - ISO 8601 with/without timezone
    - Unix timestamps
    - Common string formats

    Args:
        value: Timestamp value to parse

    Returns:
        datetime object or None if parsing fails
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        # Unix timestamp
        try:
            return datetime.fromtimestamp(value)
        except (ValueError, OSError):
            return None

    if not isinstance(value, str):
        return None

    # Try ISO format first
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Try common formats
    from dateutil import parser
    try:
        return parser.parse(value)
    except (ValueError, ImportError):
        pass

    return None
