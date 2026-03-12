"""
Model Registry for OpenCLAW Token Usage Monitor.

This module provides universal model identification and classification
for all types of LLM providers (OpenAI, Anthropic, Google, local models, etc.).
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional


class ModelProvider(Enum):
    """
    Enumeration of supported LLM providers.

    These providers are automatically detected from model names
    in usage logs for categorization and display purposes.
    """

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    COHERE = "cohere"
    HUGGING_FACE = "hugging_face"
    LOCAL = "local"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class ModelRegistry:
    """
    Universal model registry for identifying and categorizing LLM models.

    This class provides pattern-based detection of model providers
    from model names, supporting both major cloud providers and
    local open-source models.
    """

    # Model identification patterns
    # Ordered by specificity - more specific patterns first
    MODEL_PATTERNS: Dict[str, ModelProvider] = {
        # OpenAI Models
        "gpt-4": ModelProvider.OPENAI,
        "gpt-3.5": ModelProvider.OPENAI,
        "gpt-4o": ModelProvider.OPENAI,
        "o1-": ModelProvider.OPENAI,
        "o3-": ModelProvider.OPENAI,

        # Anthropic Models
        "claude-3": ModelProvider.ANTHROPIC,
        "claude-opus": ModelProvider.ANTHROPIC,
        "claude-sonnet": ModelProvider.ANTHROPIC,
        "claude-haiku": ModelProvider.ANTHROPIC,

        # Google Models
        "gemini": ModelProvider.GOOGLE,
        "palm": ModelProvider.GOOGLE,

        # Azure OpenAI (specific prefix)
        "azure/": ModelProvider.AZURE,

        # Cohere Models
        "command": ModelProvider.COHERE,
        "embed-": ModelProvider.COHERE,

        # Hugging Face Models
        "hf/": ModelProvider.HUGGING_FACE,
        "huggingface/": ModelProvider.HUGGING_FACE,

        # Local/Open Source Models
        "llama": ModelProvider.LOCAL,
        "mistral": ModelProvider.LOCAL,
        "mixtral": ModelProvider.LOCAL,
        "qwen": ModelProvider.LOCAL,
        "yi-": ModelProvider.LOCAL,
        "deepseek": ModelProvider.LOCAL,
        "phi-": ModelProvider.LOCAL,
        "gemma": ModelProvider.LOCAL,
        "falcon": ModelProvider.LOCAL,
        "mpt-": ModelProvider.LOCAL,
        "dbrx": ModelProvider.LOCAL,
    }

    # Provider display names
    PROVIDER_DISPLAY_NAMES: Dict[ModelProvider, str] = {
        ModelProvider.OPENAI: "OpenAI",
        ModelProvider.ANTHROPIC: "Anthropic",
        ModelProvider.GOOGLE: "Google",
        ModelProvider.AZURE: "Azure",
        ModelProvider.COHERE: "Cohere",
        ModelProvider.HUGGING_FACE: "Hugging Face",
        ModelProvider.LOCAL: "Local",
        ModelProvider.CUSTOM: "Custom",
        ModelProvider.UNKNOWN: "Unknown",
    }

    # Provider icons for UI display
    PROVIDER_ICONS: Dict[ModelProvider, str] = {
        ModelProvider.OPENAI: "🤖",
        ModelProvider.ANTHROPIC: "🧠",
        ModelProvider.GOOGLE: "✨",
        ModelProvider.AZURE: "☁️",
        ModelProvider.COHERE: "🌊",
        ModelProvider.HUGGING_FACE: "🤗",
        ModelProvider.LOCAL: "💻",
        ModelProvider.CUSTOM: "🔧",
        ModelProvider.UNKNOWN: "❓",
    }

    @classmethod
    def identify_provider(cls, model_name: str) -> ModelProvider:
        """
        Identify the LLM provider from a model name.

        Uses pattern matching to determine which provider a model belongs to.
        If no pattern matches, returns CUSTOM for user-defined models.

        Args:
            model_name: The model identifier string

        Returns:
            ModelProvider enum value indicating the detected provider

        Examples:
            >>> ModelRegistry.identify_provider("gpt-4o")
            <ModelProvider.OPENAI: 'openai'>
            >>> ModelRegistry.identify_provider("claude-3-5-sonnet")
            <ModelProvider.ANTHROPIC: 'anthropic'>
            >>> ModelRegistry.identify_provider("llama-3-70b")
            <ModelProvider.LOCAL: 'local'>
            >>> ModelRegistry.identify_provider("my-custom-model")
            <ModelProvider.CUSTOM: 'custom'>
        """
        if not model_name:
            return ModelProvider.UNKNOWN

        model_lower = model_name.lower()

        # Check against known patterns
        for pattern, provider in cls.MODEL_PATTERNS.items():
            if pattern in model_lower:
                return provider

        # Check for common local model hosting patterns
        if any(prefix in model_lower for prefix in ["localhost:", "127.0.0.1", "local/"]):
            return ModelProvider.LOCAL

        return ModelProvider.CUSTOM

    @classmethod
    def get_display_name(cls, model: str) -> str:
        """
        Get a formatted display name for a model.

        The display name includes the provider badge for easy identification.

        Args:
            model: The model identifier string

        Returns:
            Formatted display name with provider badge

        Examples:
            >>> ModelRegistry.get_display_name("gpt-4o")
            '[OpenAI] gpt-4o'
            >>> ModelRegistry.get_display_name("claude-3-5-sonnet")
            '[Anthropic] claude-3-5-sonnet'
        """
        provider = cls.identify_provider(model)
        provider_name = cls.PROVIDER_DISPLAY_NAMES[provider]
        return f"[{provider_name}] {model}"

    @classmethod
    def get_provider_icon(cls, model: str) -> str:
        """
        Get the icon for a model's provider.

        Args:
            model: The model identifier string

        Returns:
            Unicode emoji icon for the provider
        """
        provider = cls.identify_provider(model)
        return cls.PROVIDER_ICONS.get(provider, cls.PROVIDER_ICONS[ModelProvider.UNKNOWN])

    @classmethod
    def get_provider_name(cls, model: str) -> str:
        """
        Get the provider name for a model.

        Args:
            model: The model identifier string

        Returns:
            Human-readable provider name
        """
        provider = cls.identify_provider(model)
        return cls.PROVIDER_DISPLAY_NAMES.get(provider, "Unknown")

    @classmethod
    def get_provider_from_string(cls, provider_str: str) -> ModelProvider:
        """
        Convert a provider string to ModelProvider enum.

        Args:
            provider_str: String representation of provider

        Returns:
            ModelProvider enum value

        Examples:
            >>> ModelRegistry.get_provider_from_string("openai")
            <ModelProvider.OPENAI: 'openai'>
            >>> ModelRegistry.get_provider_from_string("anthropic")
            <ModelProvider.ANTHROPIC: 'anthropic'>
        """
        provider_lower = provider_str.lower().strip().replace("-", "_").replace(" ", "_")

        for provider in ModelProvider:
            if provider.value.lower().replace("_", "") == provider_lower.replace("_", ""):
                return provider

        return ModelProvider.UNKNOWN

    @classmethod
    def is_local_model(cls, model_name: str) -> bool:
        """
        Check if a model is a locally hosted model.

        Args:
            model_name: The model identifier string

        Returns:
            True if the model is detected as local
        """
        provider = cls.identify_provider(model_name)
        return provider == ModelProvider.LOCAL

    @classmethod
    def get_model_family(cls, model_name: str) -> str:
        """
        Get the model family (base model name without version).

        Args:
            model_name: The model identifier string

        Returns:
            Model family name

        Examples:
            >>> ModelRegistry.get_model_family("gpt-4o-2024-05-13")
            'gpt-4o'
            >>> ModelRegistry.get_model_family("claude-3-5-sonnet")
            'claude-3'
        """
        model_lower = model_name.lower()

        # Extract base family name
        for pattern in cls.MODEL_PATTERNS:
            if pattern in model_lower:
                # Handle special cases
                if pattern == "claude-3":
                    return "claude-3"
                if pattern == "gpt-4" and "gpt-4o" not in model_lower:
                    return "gpt-4"
                return pattern.rstrip("-")

        # Fallback: return everything before version numbers
        import re
        family_match = re.match(r"^([a-z-]+)", model_lower)
        if family_match:
            return family_match.group(1)

        return model_name


# Convenience functions for backward compatibility
def identify_provider(model_name: str) -> ModelProvider:
    """Convenience function for provider identification."""
    return ModelRegistry.identify_provider(model_name)


def get_model_display_name(model: str) -> str:
    """Convenience function for getting display name."""
    return ModelRegistry.get_display_name(model)
