"""Model-provider abstraction for the LangChain client example."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI


@dataclass(frozen=True)
class ModelSettings:
    """Provider-neutral model configuration."""

    provider: str
    model: str
    base_url: str

    @classmethod
    def from_env(
        cls,
        *,
        provider: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> ModelSettings:
        provider_name = (provider or os.getenv("MODEL_PROVIDER", "lm_studio")).lower()

        defaults = {
            "lm_studio": (
                os.getenv("LM_STUDIO_MODEL", "local-model"),
                os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"),
            ),
            "ollama": (
                os.getenv("OLLAMA_MODEL", "llama3.1"),
                os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ),
        }
        if provider_name not in defaults:
            supported = ", ".join(defaults)
            raise ValueError(
                f"Unsupported MODEL_PROVIDER '{provider_name}'. Choose one of: {supported}"
            )

        default_model, default_base_url = defaults[provider_name]
        return cls(
            provider=provider_name,
            model=model or os.getenv("MODEL_NAME", default_model),
            base_url=base_url or os.getenv("MODEL_BASE_URL", default_base_url),
        )


class ModelProvider(ABC):
    """Creates a LangChain chat model without exposing provider details."""

    @abstractmethod
    def create_model(self, settings: ModelSettings) -> BaseChatModel:
        """Build the configured chat model."""


class LMStudioProvider(ModelProvider):
    def create_model(self, settings: ModelSettings) -> BaseChatModel:
        return ChatOpenAI(
            model=settings.model,
            base_url=settings.base_url,
            api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
            temperature=0,
        )


class OllamaProvider(ModelProvider):
    def create_model(self, settings: ModelSettings) -> BaseChatModel:
        return ChatOllama(
            model=settings.model,
            base_url=settings.base_url,
            temperature=0,
        )


_PROVIDERS: dict[str, ModelProvider] = {
    "lm_studio": LMStudioProvider(),
    "ollama": OllamaProvider(),
}


def create_model(settings: ModelSettings) -> BaseChatModel:
    """Create a model through the provider selected in the configuration."""

    return _PROVIDERS[settings.provider].create_model(settings)
