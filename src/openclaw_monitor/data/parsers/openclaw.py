"""
OpenCLAW platform log format parser for OpenCLAW Token Usage Monitor.

This parser handles the OpenCLAW platform's specific log format,
which is optimized for the monitoring tool's internal data structure.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from openclaw_monitor.data.parsers.base import BaseParser, parse_iso_timestamp, safe_int


class OpenCLAWParser(BaseParser):
    """
    Parser for OpenCLAW platform log format.

    The OpenCLAW format is the native format for this monitoring tool,
    designed for easy parsing and comprehensive token tracking.
    """

    # Field names in OpenCLAW format (direct mapping)
    FIELD_NAMES = {
        "input_tokens": ["input_tokens"],
        "output_tokens": ["output_tokens"],
        "cache_creation_tokens": ["cache_creation_tokens"],
        "cache_read_tokens": ["cache_read_tokens"],
    }

    # Identifier fields
    SOURCE_FIELD = "source"
    MODEL_FIELD = "model"
    PROVIDER_FIELD = "provider"
    TIMESTAMP_FIELD = "timestamp"
    REQUEST_ID_FIELD = "request_id"
    METADATA_FIELD = "metadata"

    # OpenCLAW format identifier
    OPENCLAW_SOURCE_MARKER = "openclaw"

    def can_parse(self, data: Dict[str, Any]) -> bool:
        """
        Determine if this is an OpenCLAW format log entry.

        Checks for the 'source' field with 'openclaw' value or
        the characteristic flat structure of OpenCLAW logs.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            True if this appears to be an OpenCLAW format log
        """
        if not isinstance(data, dict):
            return False

        # Check for explicit source marker
        if self.SOURCE_FIELD in data:
            source = str(data[self.SOURCE_FIELD]).lower()
            if self.OPENCLAW_SOURCE_MARKER in source:
                return True

        # Check for OpenCLAW characteristic structure
        # OpenCLAW logs have direct field mappings
        has_input_tokens = any(
            field in data for field in self.FIELD_NAMES["input_tokens"]
        )
        has_output_tokens = any(
            field in data for field in self.FIELD_NAMES["output_tokens"]
        )
        has_timestamp = self.TIMESTAMP_FIELD in data

        # If it has the characteristic structure with timestamp, it's likely OpenCLAW
        if has_input_tokens and has_output_tokens and has_timestamp:
            return True

        return False

    def extract_tokens(self, data: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token counts from OpenCLAW format log.

        OpenCLAW format uses direct field names.

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

        # Direct field mapping
        for token_type, field_names in self.FIELD_NAMES.items():
            for field_name in field_names:
                if field_name in data:
                    tokens[token_type] = safe_int(data[field_name])
                    break

        return tokens

    def extract_model(self, data: Dict[str, Any]) -> str:
        """
        Extract model name from OpenCLAW format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Model name string
        """
        if self.MODEL_FIELD in data:
            model = data[self.MODEL_FIELD]
            if isinstance(model, str):
                return model

        return "openclaw-model"

    def extract_timestamp(self, data: Dict[str, Any]) -> Optional[datetime]:
        """
        Extract timestamp from OpenCLAW format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            datetime object or None
        """
        if self.TIMESTAMP_FIELD in data:
            return parse_iso_timestamp(data[self.TIMESTAMP_FIELD])

        return None

    def extract_provider(self, data: Dict[str, Any]) -> str:
        """
        Extract provider name from OpenCLAW format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Provider name string
        """
        if self.PROVIDER_FIELD in data:
            provider = data[self.PROVIDER_FIELD]
            if isinstance(provider, str):
                return provider

        # Try to infer from model name
        model = self.extract_model(data)
        if model:
            from openclaw_monitor.core.model_registry import ModelRegistry
            return ModelRegistry.identify_provider(model).value

        return ""

    def extract_request_id(self, data: Dict[str, Any]) -> str:
        """
        Extract request ID from OpenCLAW format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Request ID string
        """
        if self.REQUEST_ID_FIELD in data:
            req_id = data[self.REQUEST_ID_FIELD]
            if isinstance(req_id, str):
                return req_id

        return ""

    def extract_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract additional metadata from OpenCLAW format log.

        Args:
            data: Raw log entry as a dictionary

        Returns:
            Dictionary of metadata
        """
        # If there's an explicit metadata field, return it
        if self.METADATA_FIELD in data:
            metadata = data[self.METADATA_FIELD]
            if isinstance(metadata, dict):
                return metadata

        # Otherwise, collect non-core fields as metadata
        metadata = {}
        core_fields = {
            self.SOURCE_FIELD, self.MODEL_FIELD, self.PROVIDER_FIELD,
            self.TIMESTAMP_FIELD, self.REQUEST_ID_FIELD, self.METADATA_FIELD,
            *self.FIELD_NAMES["input_tokens"],
            *self.FIELD_NAMES["output_tokens"],
            *self.FIELD_NAMES["cache_creation_tokens"],
            *self.FIELD_NAMES["cache_read_tokens"],
        }

        for key, value in data.items():
            if key not in core_fields:
                metadata[key] = value

        return metadata
