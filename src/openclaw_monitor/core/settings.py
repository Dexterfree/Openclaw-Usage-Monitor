"""
Settings configuration for OpenCLAW Token Usage Monitor.

This module defines the configuration settings using Pydantic
for type-safe configuration management.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class ViewMode(str, Enum):
    """Available viewing modes for the monitor."""

    REALTIME = "realtime"
    DAILY = "daily"
    MONTHLY = "monthly"
    DETAILED = "detailed"


class TokenPlan(str, Enum):
    """Predefined token limit plans."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    UNLIMITED = "unlimited"
    CUSTOM = "custom"


class MonitorSettings(BaseModel):
    """
    Core monitoring settings.

    These settings control the behavior of the token usage monitor
    including view mode, token limits, and refresh rates.
    """

    # View configuration
    view: Literal["realtime", "daily", "monthly", "detailed"] = Field(
        default="realtime",
        description="View mode for displaying usage data",
    )

    # Plan configuration
    plan: Literal["small", "medium", "large", "unlimited", "custom"] = Field(
        default="medium",
        description="Token limit plan to use",
    )

    custom_limit_tokens: Optional[int] = Field(
        default=None,
        description="Custom token limit (required when plan=custom)",
    )

    # Data configuration
    log_path: Optional[str] = Field(
        default=None,
        description="Path to log file or directory containing logs",
    )

    # Refresh configuration
    refresh_rate: int = Field(
        default=5,
        ge=1,
        le=300,
        description="Refresh rate in seconds for realtime view",
    )

    # Timezone configuration
    timezone: str = Field(
        default="UTC",
        description="Timezone for displaying timestamps",
    )

    # Session configuration
    session_gap_minutes: int = Field(
        default=30,
        ge=1,
        description="Minutes of inactivity before starting a new session",
    )

    session_window_hours: int = Field(
        default=5,
        ge=1,
        description="Hours to look back for session tracking",
    )

    # Warning thresholds
    warning_threshold: float = Field(
        default=75.0,
        ge=0.0,
        le=100.0,
        description="Percentage threshold for showing warnings",
    )

    critical_threshold: float = Field(
        default=90.0,
        ge=0.0,
        le=100.0,
        description="Percentage threshold for showing critical warnings",
    )

    # UI configuration
    color_scheme: Literal["auto", "light", "dark"] = Field(
        default="auto",
        description="Color scheme for UI",
    )

    @field_validator("custom_limit_tokens")
    @classmethod
    def validate_custom_limit(cls, v: Optional[int], info) -> Optional[int]:
        """Validate that custom_limit is provided when plan=custom."""
        if info.data.get("plan") == "custom" and v is None:
            raise ValueError("custom_limit_tokens must be provided when plan='custom'")
        if v is not None and v < 0:
            raise ValueError("custom_limit_tokens must be non-negative")
        return v

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone string."""
        try:
            import pytz
            pytz.timezone(v)
        except (ImportError, pytz.exceptions.UnknownTimeZoneError):
            # Try IANA timezone without pytz
            import zoneinfo
            try:
                zoneinfo.ZoneInfo(v)
            except (ImportError, zoneinfo.ZoneInfoNotFoundError):
                # Allow UTC to pass through
                if v.upper() != "UTC":
                    raise ValueError(f"Unknown timezone: {v}")
        return v

    def get_token_limit(self) -> int:
        """Get the token limit based on the current plan."""
        from openclaw_monitor.core.plans import PlanManager
        return PlanManager.get_token_limit(
            self.plan,
            self.custom_limit_tokens,
        )


class AppConfig(BaseSettings):
    """
    Application-level configuration.

    This includes environment variables and global settings
    that apply across all view modes.
    """

    # Environment prefix
    class Config:
        env_prefix = "OPENCLAW_"

    # Log level
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    # Data directory
    data_dir: str = Field(
        default="~/.openclaw",
        description="Directory for storing OpenCLAW data",
    )

    # Enable/disable features
    enable_notifications: bool = Field(
        default=True,
        description="Enable desktop notifications",
    )

    enable_predictions: bool = Field(
        default=True,
        description="Enable token usage predictions",
    )

    # Terminal settings
    terminal_width: Optional[int] = Field(
        default=None,
        description="Override terminal width detection",
    )


# Global settings instance
_settings_cache: Optional[MonitorSettings] = None
_app_config_cache: Optional[AppConfig] = None


def get_settings(**overrides) -> MonitorSettings:
    """
    Get the current monitor settings.

    Args:
        **overrides: Optional setting overrides

    Returns:
        MonitorSettings instance
    """
    global _settings_cache

    if _settings_cache is None or overrides:
        settings = MonitorSettings(**overrides)
        if not overrides:
            _settings_cache = settings
        return settings

    return _settings_cache


def get_app_config() -> AppConfig:
    """
    Get the application configuration.

    Returns:
        AppConfig instance loaded from environment variables
    """
    global _app_config_cache

    if _app_config_cache is None:
        _app_config_cache = AppConfig()

    return _app_config_cache


def reset_settings() -> None:
    """Reset cached settings (useful for testing)."""
    global _settings_cache, _app_config_cache
    _settings_cache = None
    _app_config_cache = None
