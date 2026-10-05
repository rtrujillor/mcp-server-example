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
    """Configuration loaded for the provider selected in .env."""

    provider: str
    model: str
    base_url: str
    api_key: str

    @classmethod
    def from_env(cls) -> ModelSettings:
        selected_provider = os.getenv("MODEL_PROVIDER", "LM").strip().upper()
        provider_aliases = {
            "LM": "lm_studio",
            "LM_STUDIO": "lm_studio",
            "OLLAMA": "ollama",
        }
        if selected_provider not in provider_aliases:
            raise ValueError(
                f"Unsupported MODEL_PROVIDER '{selected_provider}'. Choose LM or OLLAMA."
            )

        provider_name = provider_aliases[selected_provider]
        if provider_name == "lm_studio":
            return cls(
                provider=provider_name,
                model=os.getenv("LM_STUDIO_MODEL", "local-model"),
                base_url=os.getenv(
                    "LM_STUDIO_BASE_URL", "http://localhost:1234/v1"
                ),
                api_key=os.getenv("LM_STUDIO_API_KEY", "lm-studio"),
            )

        return cls(
            provider=provider_name,
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            api_key=os.getenv("OLLAMA_API_KEY", ""),
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
            api_key=settings.api_key,
            temperature=0,
        )


class OllamaProvider(ModelProvider):
    def create_model(self, settings: ModelSettings) -> BaseChatModel:
        client_kwargs = {}
        if settings.api_key:
            client_kwargs["headers"] = {
                "Authorization": f"Bearer {settings.api_key}"
            }
        return ChatOllama(
            model=settings.model,
            base_url=settings.base_url,
            client_kwargs=client_kwargs,
            async_client_kwargs=client_kwargs,
            temperature=0,
        )


_PROVIDERS: dict[str, ModelProvider] = {
    "lm_studio": LMStudioProvider(),
    "ollama": OllamaProvider(),
}


def create_model(settings: ModelSettings) -> BaseChatModel:
    """Create a model through the provider selected in the configuration."""

    return _PROVIDERS[settings.provider].create_model(settings)
