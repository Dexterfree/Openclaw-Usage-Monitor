"""
Plans and token limits for OpenCLAW Token Usage Monitor.

This module defines the available plans and their associated token limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class TokenLimit:
    """
    Immutable configuration for token limits.

    Attributes:
        name: Display name for the plan
        token_limit: Maximum number of tokens allowed
        description: Human-readable description of the plan
    """

    name: str
    token_limit: int
    description: str = ""

    @property
    def is_unlimited(self) -> bool:
        """Check if this plan has unlimited tokens."""
        return self.token_limit == 0


# Predefined token limit plans
TOKEN_PLANS: Dict[str, TokenLimit] = {
    "small": TokenLimit(
        name="Small",
        token_limit=100_000,
        description="Small project with up to 100k tokens",
    ),
    "medium": TokenLimit(
        name="Medium",
        token_limit=1_000_000,
        description="Medium project with up to 1M tokens",
    ),
    "large": TokenLimit(
        name="Large",
        token_limit=10_000_000,
        description="Large project with up to 10M tokens",
    ),
    "unlimited": TokenLimit(
        name="Unlimited",
        token_limit=0,
        description="No token limit",
    ),
}


class PlanManager:
    """
    Manager for token limit plans.

    Provides methods to query and validate token limits
    for different plan types.
    """

    @staticmethod
    def get_token_limit(
        plan: str,
        custom_limit: Optional[int] = None,
    ) -> int:
        """
        Get the token limit for a given plan.

        Args:
            plan: Plan name ('small', 'medium', 'large', 'unlimited', 'custom')
            custom_limit: Custom token limit (required when plan='custom')

        Returns:
            Token limit as an integer (0 for unlimited)

        Raises:
            ValueError: If plan is 'custom' but no custom_limit provided

        Examples:
            >>> PlanManager.get_token_limit("small")
            100000
            >>> PlanManager.get_token_limit("unlimited")
            0
            >>> PlanManager.get_token_limit("custom", custom_limit=500_000)
            500000
        """
        if plan == "custom":
            if custom_limit is None:
                raise ValueError("custom_limit must be provided for 'custom' plan")
            return max(0, custom_limit)

        if plan in TOKEN_PLANS:
            return TOKEN_PLANS[plan].token_limit

        # Default to medium for unknown plans
        return TOKEN_PLANS["medium"].token_limit

    @staticmethod
    def get_plan(plan: str) -> Optional[TokenLimit]:
        """
        Get the TokenLimit configuration for a plan.

        Args:
            plan: Plan name

        Returns:
            TokenLimit object or None if plan not found
        """
        return TOKEN_PLANS.get(plan)

    @staticmethod
    def get_all_plans() -> Dict[str, TokenLimit]:
        """
        Get all available token limit plans.

        Returns:
            Dictionary mapping plan names to TokenLimit objects
        """
        return TOKEN_PLANS.copy()

    @staticmethod
    def is_valid_plan(plan: str) -> bool:
        """
        Check if a plan name is valid.

        Args:
            plan: Plan name to check

        Returns:
            True if the plan exists
        """
        return plan in TOKEN_PLANS or plan == "custom"

    @staticmethod
    def get_plan_description(plan: str) -> str:
        """
        Get the description for a plan.

        Args:
            plan: Plan name

        Returns:
            Plan description string
        """
        if plan in TOKEN_PLANS:
            return TOKEN_PLANS[plan].description
        if plan == "custom":
            return "Custom token limit"
        return "Unknown plan"


def get_percentage_used(used: int, limit: int) -> float:
    """
    Calculate the percentage of tokens used.

    Args:
        used: Number of tokens used
        limit: Token limit (0 for unlimited)

    Returns:
        Percentage as a float (0.0 to 100.0+)
        Returns 0.0 if limit is 0 (unlimited)
    """
    if limit == 0:
        return 0.0
    return (used / limit) * 100.0


def get_tokens_remaining(used: int, limit: int) -> int:
    """
    Calculate the remaining tokens.

    Args:
        used: Number of tokens used
        limit: Token limit (0 for unlimited)

    Returns:
        Number of tokens remaining
        Returns -1 if limit is 0 (unlimited)
    """
    if limit == 0:
        return -1  # Indicates unlimited
    return max(0, limit - used)


def is_near_limit(used: int, limit: int, threshold: float = 90.0) -> bool:
    """
    Check if token usage is near the limit.

    Args:
        used: Number of tokens used
        limit: Token limit (0 for unlimited)
        threshold: Percentage threshold for "near" (default: 90%)

    Returns:
        True if usage is at or above threshold
        False if limit is unlimited (0)
    """
    if limit == 0:
        return False
    return get_percentage_used(used, limit) >= threshold


def is_over_limit(used: int, limit: int) -> bool:
    """
    Check if token usage has exceeded the limit.

    Args:
        used: Number of tokens used
        limit: Token limit (0 for unlimited)

    Returns:
        True if usage exceeds limit
        False if limit is unlimited (0)
    """
    if limit == 0:
        return False
    return used > limit
