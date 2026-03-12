"""
Parsers module for OpenCLAW Token Usage Monitor.

This module provides parser classes for converting various log formats
into unified UsageEntry objects.
"""

from openclaw_monitor.data.parsers.base import BaseParser
from openclaw_monitor.data.parsers.openai import OpenAIParser
from openclaw_monitor.data.parsers.claude import ClaudeParser
from openclaw_monitor.data.parsers.generic import GenericParser
from openclaw_monitor.data.parsers.openclaw import OpenCLAWParser

__all__ = [
    "BaseParser",
    "OpenAIParser",
    "ClaudeParser",
    "GenericParser",
    "OpenCLAWParser",
]

# Clawdbot parser is optional - only import if available
try:
    from openclaw_monitor.data.parsers.clawdbot import (
        ClawdbotLogParser,
        parse_clawdbot_directory,
        extract_token_usage_from_logs,
        register_clawdbot_parser,
    )
    __all__.extend([
        "ClawdbotLogParser",
        "parse_clawdbot_directory",
        "extract_token_usage_from_logs",
        "register_clawdbot_parser",
    ])
except ImportError:
    pass
