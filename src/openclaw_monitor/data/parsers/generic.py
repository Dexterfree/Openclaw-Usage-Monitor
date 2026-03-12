"""
Generic log format parser for OpenCLAW Token Usage Monitor.

This parser provides automatic detection of common token field patterns
and serves as a fallback when specific parsers cannot handle a format.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from openclaw_monitor.data.parsers.base import BaseParser, parse_iso_timestamp, safe_int


class GenericParser(BaseParser):
    """
    Generic parser that auto-detects common token field patterns.

    This parser attempts to identify token-related fields by matching
    against common naming conventions used across various LLM providers
    and logging tools.
    """

    # Common token field name patterns
    COMMON_TOKEN_FIELDS = {
        "input": [
            "input_tokens",
            "prompt_tokens",
            "in_tokens",
            "tokens_in",
            "prompt_length",
            "input_length",
        ],
        "output": [
            "output_tokens",
            "completion_tokens",
            "out_tokens",
            "tokens_out",
            "completion_length",
            "output_length",
        ],
        "cache": [
            "cache_tokens",
            "cached_tokens",
            "cache_read_tokens",
            "cached_prompt_tokens",
        ],
        "cache_creation": [
            "cache_creation_tokens",
            "cache_input_tokens",
            "prompt_cache_written_tokens",
        ],
        "total": [
            "total_tokens",
            "all_tokens",
            "tokens",
        ],
    }

    # Common timestamp field patterns
    TIMESTAMP_PATTERNS = [
        "timestamp",
        "time",
        "created",
        "created_at",
        "date",
        "datetime",
        "request_time",
        "response_time",
    ]

    # Common model field patterns
    MODEL_PATTERNS = [
        "model",
        "model_name",
        "model_id",
        "gpt_model",
        "llm_model",
        "engine",
    ]

    # Provider field patterns
    PROVIDER_PATTERNS = [
        "provider",
        "service",
        "api_provider",
        "llm_provider",
    ]

    # Minimum token value threshold (to avoid false positives)
    MIN_TOKEN_THRESHOLD = 1
    MAX_TOKEN_THRESHOLD = 10_000_000

    def can_parse(self, data: Dict[str, Any]) -> bool:
        """
        Determine if this parser can handle the log entry.

        The generic parser can attempt to parse any dictionary that
        contains token-related fields, making it a good fallback.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            True if token-related fields are detected
        """
        if not isinstance(data, dict):
            return False

        # Try to find any token-related field
        for field_patterns in self.COMMON_TOKEN_FIELDS.values():
            for pattern in field_patterns:
                if pattern in data:
                    value = data[pattern]
                    # Check if it looks like a valid token count
                    if isinstance(value, (int, float)) and self.MIN_TOKEN_THRESHOLD <= value <= self.MAX_TOKEN_THRESHOLD:
                        return True

        # Also check nested structures
        for value in data.values():
            if isinstance(value, dict):
                # Recursively check nested dict
                if self.can_parse(value):
                    return True

        return False

    def extract_tokens(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token counts using common field name patterns.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary with token counts
        """
        tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_creation_tokens": 0,
        }

        def find_nested_value(d: Dict[str, Any], patterns: List[str]) -> Optional[int]:
            """Search for a value using multiple field name patterns."""
            for pattern in patterns:
                if pattern in d:
                    value = safe_int(d[pattern])
                    if value > 0:
                        return value

            # Search in nested dicts
            for value in d.values():
                if isinstance(value, dict):
                    result = find_nested_value(value, patterns)
                    if result is not None:
                        return result

            return None

        # Extract input tokens
        input_value = find_nested_value(data, self.COMMON_TOKEN_FIELDS["input"])
        if input_value is not None:
            tokens["input_tokens"] = input_value

        # Extract output tokens
        output_value = find_nested_value(data, self.COMMON_TOKEN_FIELDS["output"])
        if output_value is not None:
            tokens["output_tokens"] = output_value

        # Extract cache read tokens
        cache_value = find_nested_value(data, self.COMMON_TOKEN_FIELDS["cache"])
        if cache_value is not None:
            tokens["cache_read_tokens"] = cache_value

        # Extract cache creation tokens
        cache_create_value = find_nested_value(data, self.COMMON_TOKEN_FIELDS["cache_creation"])
        if cache_create_value is not None:
            tokens["cache_creation_tokens"] = cache_create_value

        # Try to derive from total if available and individual counts are zero
        if tokens["input_tokens"] == 0 and tokens["output_tokens"] == 0:
            total_value = find_nested_value(data, self.COMMON_TOKEN_FIELDS["total"])
            if total_value:
                # For generic format, we can't reliably split total
                # Put everything in input as a best guess
                tokens["input_tokens"] = total_value

        return tokens

    def extract_model(self, data: Dict[str, Any]) -> str:
        """
        Extract model name using common field patterns.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Model name string
        """
        def find_nested_model(d: Dict[str, Any]) -> Optional[str]:
            """Search for model in nested structure."""
            for pattern in self.MODEL_PATTERNS:
                if pattern in d:
                    value = d[pattern]
                    if isinstance(value, str) and value:
                        return value

            # Search in nested dicts
            for value in d.values():
                if isinstance(value, dict):
                    result = find_nested_model(value)
                    if result:
                        return result

            return None

        model = find_nested_model(data)
        return model if model else "unknown-model"

    def extract_timestamp(self, data: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract timestamp using common field patterns.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            datetime object or None
        """
        def find_nested_timestamp(d: Dict[str, Any]) -> Optional[datetime]:
            """Search for timestamp in nested structure."""
            for pattern in self.TIMESTAMP_PATTERNS:
                if pattern in d:
                    result = parse_iso_timestamp(d[pattern])
                    if result:
                        return result

            # Search in nested dicts
            for value in d.values():
                if isinstance(value, dict):
                    result = find_nested_timestamp(value)
                    if result:
                        return result

            return None

        return find_nested_timestamp(data)

    def extract_provider(self, data: Dict[str, Any]) -> str:
        """
        Extract provider name using common field patterns.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Provider name string
        """
        for pattern in self.PROVIDER_PATTERNS:
            if pattern in data:
                value = data[pattern]
                if isinstance(value, str) and value:
                    return value.lower()

        return ""

    def extract_request_id(self, data: Dict[str, Any]) -> str:
        """
        Extract request ID using common field patterns.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Request ID string
        """
        request_id_patterns = [
            "request_id",
            "id",
            "req_id",
            "requestid",
            "x-request-id",
        ]

        for pattern in request_id_patterns:
            if pattern in data:
                value = data[pattern]
                if isinstance(value, str) and value:
                    return value

        # Check headers
        if "headers" in data and isinstance(data["headers"], dict):
            for key, value in data["headers"].items():
                if "request-id" in key.lower() and isinstance(value, str):
                    return value

        return ""

    def extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract additional metadata from the log entry.

        Captures fields that aren't core to usage tracking but may
        be useful for debugging or analysis.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Fields to exclude from metadata
        exclude_fields = {
            "input_tokens", "prompt_tokens", "in_tokens", "tokens_in",
            "output_tokens", "completion_tokens", "out_tokens", "tokens_out",
            "cache_tokens", "cached_tokens", "cache_read_tokens",
            "cache_creation_tokens", "cache_input_tokens",
            "total_tokens", "all_tokens", "tokens",
            "timestamp", "time", "created", "created_at", "date", "datetime",
            "model", "model_name", "model_id", "gpt_model", "llm_model", "engine",
            "provider", "service", "api_provider", "llm_provider",
            "request_id", "id", "req_id", "requestid",
        }

        # Add any non-excluded fields as metadata
        for key, value in data.items():
            if key.lower() not in exclude_fields:
                # Only include simple types (avoid large nested structures)
                if isinstance(value, (str, int, float, bool)) or value is None:
                    metadata[key] = value

        return metadata
