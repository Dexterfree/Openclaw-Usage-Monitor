"""
Claude API log format parser for OpenCLAW Token Usage Monitor.

This parser handles Claude API log formats from Anthropic including:
- Claude API response format
- Claude Code usage logs
- Third-party tools that log Claude API calls
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from openclaw_monitor.data.parsers.base import BaseParser, parse_iso_timestamp, safe_int


class ClaudeParser(BaseParser):
    """
    Parser for Claude API log formats.

    Handles the standard Anthropic Claude API format where tokens are
    reported with input_tokens, output_tokens, and cache_read_tokens
    for prompt caching.
    """

    # Known field mappings for Claude format variations
    FIELD_MAPS = {
        "input_tokens": [
            "input_tokens",
            "prompt_tokens",
            "usage.input_tokens",
            "message.usage.input_tokens",
        ],
        "output_tokens": [
            "output_tokens",
            "completion_tokens",
            "usage.output_tokens",
            "message.usage.output_tokens",
        ],
        "cache_creation_tokens": [
            "cache_creation_tokens",
            "cache_input_tokens",
            "usage.cache_creation_tokens",
        ],
        "cache_read_tokens": [
            "cache_read_tokens",
            "cached_tokens",
            "usage.cache_read_tokens",
        ],
    }

    # Model field name variations
    MODEL_FIELDS = [
        "model",
        "usage.model",
        "message.model",
        "request.model",
    ]

    # Timestamp field variations
    TIMESTAMP_FIELDS = [
        "created_at",
        "timestamp",
        "date",
        "stop_reason",
        "usage.created_at",
    ]

    # Provider identifiers in the data
    PROVIDER_INDICATORS = [
        "anthropic",
        "claude",
        "claude-api",
    ]

    # Claude model identifiers
    CLAUDE_MODEL_PATTERNS = [
        "claude-3",
        "claude-opus",
        "claude-sonnet",
        "claude-haiku",
    ]

    def can_parse(self, data: Dict[str, Any]) -> bool:
        """
        Determine if this is a Claude format log entry.

        Checks for Claude-specific field names and patterns.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            True if this appears to be a Claude format log
        """
        if not isinstance(data, dict):
            return False

        # Check for provider indicator
        data_str = str(data).lower()

        # Check model name
        if "model" in data:
            model = str(data.get("model", "")).lower()
            if any(pattern in model for pattern in self.CLAUDE_MODEL_PATTERNS):
                return True

        # Check for provider string
        if any(indicator in data_str for indicator in self.PROVIDER_INDICATORS):
            return True

        # Check for Claude-specific token fields
        claude_token_fields = ["cache_read_tokens", "cache_creation_tokens"]
        has_claude_tokens = any(field in data for field in claude_token_fields)

        if has_claude_tokens:
            return True

        # Check for nested usage object
        if "usage" in data and isinstance(data["usage"], dict):
            usage = data["usage"]
            # Claude has cache tokens
            if any(field in usage for field in claude_token_fields):
                return True

        # Check for message.usage structure (Claude API format)
        if "message" in data and isinstance(data["message"], dict):
            if "usage" in data["message"]:
                return True

        return False

    def extract_tokens(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token counts from Claude format log.

        Handles both flat and nested (usage.*) structures.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary with token counts
        """
        tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_tokens": 0,
            "cache_read_tokens": 0,
        }

        # Helper to get value from nested path
        def get_value(d: Dict[str, Any], path: str) -> Any:
            parts = path.split(".")
            current = d
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
            return current

        # Extract each token type
        for token_type, field_names in self.FIELD_MAPS.items():
            for field_name in field_names:
                value = get_value(data, field_name)
                if value is not None:
                    tokens[token_type] = safe_int(value)
                    break

        return tokens

    def extract_model(self, data: Dict[str, Any]) -> str:
        """
        Extract model name from Claude format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Model name string
        """
        # Check known model field locations
        for field in self.MODEL_FIELDS:
            parts = field.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
            else:
                if isinstance(current, str):
                    return current

        # Check for stop_reason which indicates Claude response
        if "stop_reason" in data or ("message" in data and "stop_reason" in data.get("message", {})):
            # It's a Claude API response but no model specified
            return "claude-3-5-sonnet"  # Common default

        return "claude-model"

    def extract_timestamp(self, data: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract timestamp from Claude format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            datetime object or None
        """
        # Check known timestamp field locations
        for field in self.TIMESTAMP_FIELDS:
            parts = field.split(".")
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    break
            else:
                if current is not None:
                    result = parse_iso_timestamp(current)
                    if result:
                        return result

        return None

    def extract_provider(self, data: Dict[str, Any]) -> str:
        """
        Extract provider name from Claude format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Provider name string
        """
        return "anthropic"

    def extract_request_id(self, data: Dict[str, Any]) -> str:
        """
        Extract request ID from Claude format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Request ID string
        """
        # Claude uses 'request_id' or 'id' field
        if "request_id" in data:
            return str(data["request_id"])

        if "id" in data and isinstance(data["id"], str):
            return data["id"]

        # Check for request_id in nested message
        if "message" in data and isinstance(data["message"], dict):
            if "id" in data["message"]:
                return str(data["message"]["id"])

        # Check for x-request-id header
        if "headers" in data and isinstance(data["headers"], dict):
            if "x-request-id" in data["headers"]:
                return str(data["headers"]["x-request-id"])

        return ""

    def extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract additional metadata from Claude format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Extract stop_reason if available
        if "stop_reason" in data:
            metadata["stop_reason"] = data["stop_reason"]

        # Check for stop_reason in message object
        if "message" in data and isinstance(data["message"], dict):
            if "stop_reason" in data["message"]:
                metadata["stop_reason"] = data["message"]["stop_reason"]

        # Extract usage summary
        if "usage" in data and isinstance(data["usage"], dict):
            metadata["usage_summary"] = {
                k: v for k, v in data["usage"].items()
                if k != "model"
            }

        # Check for message.usage
        if "message" in data and isinstance(data["message"], dict):
            if "usage" in data["message"]:
                metadata["message_usage"] = data["message"]["usage"]

        return metadata
