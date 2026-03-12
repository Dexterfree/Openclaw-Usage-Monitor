"""
OpenAI API log format parser for OpenCLAW Token Usage Monitor.

This parser handles various OpenAI API log formats including:
- Official OpenAI API response format
- Azure OpenAI format
- Third-party tools that log OpenAI API calls
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from openclaw_monitor.data.parsers.base import BaseParser, parse_iso_timestamp, safe_int


class OpenAIParser(BaseParser):
    """
    Parser for OpenAI API log formats.

    Handles the standard OpenAI API response format where tokens are
    reported as 'prompt_tokens', 'completion_tokens', and optionally
    'cached_tokens' for prompt caching.
    """

    # Known field mappings for OpenAI format variations
    FIELD_MAPS = {
        "input_tokens": ["prompt_tokens", "input_tokens", "usage.prompt_tokens", "usage.input_tokens"],
        "output_tokens": ["completion_tokens", "output_tokens", "usage.completion_tokens", "usage.output_tokens"],
        "cache_read_tokens": ["cached_tokens", "cache_read_tokens", "usage.cached_tokens"],
        "total_tokens": ["total_tokens", "usage.total_tokens"],
    }

    # Model field name variations
    MODEL_FIELDS = ["model", "usage.model", "request.model", "gpt_model"]

    # Timestamp field variations
    TIMESTAMP_FIELDS = ["created", "timestamp", "date", "request_date", "usage.created"]

    # Provider identifiers in the data
    PROVIDER_INDICATORS = ["openai", "openai-api", "azure-openai"]

    def can_parse(self, data: Dict[str, Any]) -> bool:
        """
        Determine if this is an OpenAI format log entry.

        Checks for OpenAI-specific field names and patterns.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            True if this appears to be an OpenAI format log
        """
        if not isinstance(data, dict):
            return False

        # Check for provider indicator
        data_str = str(data).lower()
        if any(indicator in data_str for indicator in self.PROVIDER_INDICATORS):
            return True

        # Check for OpenAI-specific token fields
        openai_token_fields = ["prompt_tokens", "completion_tokens", "cached_tokens"]
        has_openai_tokens = any(field in data for field in openai_token_fields)

        if has_openai_tokens:
            return True

        # Check for nested usage object
        if "usage" in data and isinstance(data["usage"], dict):
            usage = data["usage"]
            if any(field in usage for field in openai_token_fields):
                return True

        return False

    def extract_tokens(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token counts from OpenAI format log.

        Handles both flat and nested (usage.*) structures.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary with token counts
        """
        tokens = {
            "input_tokens": 0,
            "output_tokens": 0,
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
            if token_type == "total_tokens":
                continue

            for field_name in field_names:
                value = get_value(data, field_name)
                if value is not None:
                    tokens[token_type] = safe_int(value)
                    break

        # Try to derive from total_tokens if needed
        total_tokens = 0
        for field_name in self.FIELD_MAPS["total_tokens"]:
            value = get_value(data, field_name)
            if value is not None:
                total_tokens = safe_int(value)
                break

        # If we have total but missing individual counts, try to derive
        if total_tokens > 0:
            input_tokens = tokens["input_tokens"]
            output_tokens = tokens["output_tokens"]
            cache_tokens = tokens["cache_read_tokens"]

            known_total = input_tokens + output_tokens + cache_tokens

            if known_total < total_tokens and input_tokens == 0:
                # Assume uncached prompt tokens
                tokens["input_tokens"] = total_tokens - output_tokens - cache_tokens

        return tokens

    def extract_model(self, data: Dict[str, Any]) -> str:
        """
        Extract model name from OpenAI format log.

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

        # Try to infer from content
        if "choices" in data and isinstance(data["choices"], list):
            if data["choices"] and "message" in data["choices"][0]:
                # This is a chat completion response
                return "openai-chat"

        return "openai-model"

    def extract_timestamp(self, data: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract timestamp from OpenAI format log.

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

        # Try Unix timestamp (created field often contains this)
        if "created" in data:
            try:
                return datetime.fromtimestamp(safe_int(data["created"]))
            except (ValueError, OSError):
                pass

        return None

    def extract_provider(self, data: Dict[str, Any]) -> str:
        """
        Extract provider name from OpenAI format log.

        Detects between OpenAI and Azure OpenAI.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Provider name string
        """
        # Check for Azure indicators
        data_str = str(data).lower()
        if "azure" in data_str:
            return "azure"

        # Check deployment_id (Azure specific)
        if "deployment_id" in data or "deployment" in data:
            return "azure"

        return "openai"

    def extract_request_id(self, data: Dict[str, Any]) -> str:
        """
        Extract request ID from OpenAI format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Request ID string
        """
        # OpenAI uses 'id' field
        if "id" in data and isinstance(data["id"], str):
            return data["id"]

        # Check for request_id
        if "request_id" in data:
            return str(data["request_id"])

        # Check for x-request-id header
        if "headers" in data and isinstance(data["headers"], dict):
            if "x-request-id" in data["headers"]:
                return str(data["headers"]["x-request-id"])

        return ""

    def extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract additional metadata from OpenAI format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary of metadata
        """
        metadata = {}

        # Extract organization if present
        if "organization" in data:
            metadata["organization"] = data["organization"]

        # Extract usage summary
        if "usage" in data and isinstance(data["usage"], dict):
            metadata["usage_summary"] = {
                k: v for k, v in data["usage"].items()
                if k != "model"  # Avoid duplicating model field
            }

        # Extract finish reason if available
        if "choices" in data and isinstance(data["choices"], list):
            if data["choices"] and "finish_reason" in data["choices"][0]:
                metadata["finish_reason"] = data["choices"][0]["finish_reason"]

        return metadata
