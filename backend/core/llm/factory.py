"""Build an :class:`LLMBackend` from settings, environment, or explicit args.

Precedence is: explicit argument > environment variable > settings default.
Failures here are configuration mistakes, so the messages say exactly which
variable to set.
"""

from __future__ import annotations

import os
from typing import Optional

from backend.core.llm.anthropic_backend import AnthropicBackend
from backend.core.llm.base import LLMBackend, LLMError
from backend.core.llm.openai_backend import OpenAIBackend

ANTHROPIC_ALIASES = {"anthropic", "claude"}
OPENAI_ALIASES = {"openai", "openai_compat", "ollama", "gemini", "deepseek", "proxy"}

DEFAULT_BASE_URLS = {
    "ollama": "http://localhost:11434/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "deepseek": "https://api.deepseek.com/v1",
}

DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-4o-mini",
    "openai_compat": "gpt-4o-mini",
    "ollama": "qwen2.5-coder:7b",
    "gemini": "gemini-2.0-flash",
    "deepseek": "deepseek-chat",
}


def _settings():
    """Load app settings, tolerating an environment with no .env at all."""
    try:
        from backend.config import get_settings  # noqa: PLC0415 - optional at import time

        return get_settings()
    except Exception:  # noqa: BLE001 - config is a convenience, not a requirement
        return None


def _pick(*candidates: Optional[str]) -> str:
    for value in candidates:
        if value:
            return str(value)
    return ""


def create_llm_backend(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    *,
    timeout: float = 600.0,
) -> LLMBackend:
    settings = _settings()
    get = lambda name, default="": getattr(settings, name, default) if settings else default  # noqa: E731

    target = _pick(
        provider,
        os.getenv("JARVIS_LLM_PROVIDER"),
        os.getenv("LLM_PROVIDER"),
        get("llm_provider"),
        "anthropic",
    ).strip().lower()

    resolved_model = _pick(
        model, os.getenv("JARVIS_MODEL"), get("agent_model"), DEFAULT_MODELS.get(target, "")
    )

    if target in ANTHROPIC_ALIASES:
        key = _pick(api_key, os.getenv("ANTHROPIC_API_KEY"), get("anthropic_api_key"))
        url = _pick(base_url, os.getenv("ANTHROPIC_BASE_URL"), get("anthropic_base_url"))

        if not key:
            raise LLMError(
                "ANTHROPIC_API_KEY is not set. Put a real Anthropic key "
                "(it starts with 'sk-ant-') in your .env, or switch backends with "
                "JARVIS_LLM_PROVIDER=openai_compat."
            )
        if not key.startswith("sk-ant-") and not url:
            # The key shipped in this repo's .env is an agentrouter.org proxy
            # key, which the Anthropic SDK cannot authenticate against.
            raise LLMError(
                "ANTHROPIC_API_KEY does not look like an Anthropic key (expected a "
                "'sk-ant-' prefix). If it belongs to a proxy, set "
                "JARVIS_LLM_PROVIDER=openai_compat and OPENAI_BASE_URL to that "
                "proxy's /v1 endpoint instead."
            )

        return AnthropicBackend(
            api_key=key,
            model=resolved_model or DEFAULT_MODELS["anthropic"],
            base_url=url or None,
            timeout=timeout,
        )

    if target in OPENAI_ALIASES:
        key = _pick(
            api_key,
            os.getenv("OPENAI_API_KEY"),
            os.getenv("GOOGLE_API_KEY") if target == "gemini" else "",
            get("openai_api_key"),
            get("google_api_key") if target == "gemini" else "",
            # Ollama is unauthenticated but the SDK insists on a non-empty key.
            "ollama" if target == "ollama" else "",
        )
        url = _pick(
            base_url,
            os.getenv("OPENAI_BASE_URL"),
            get("openai_base_url"),
            DEFAULT_BASE_URLS.get(target, ""),
        )

        if not key:
            raise LLMError(
                f"No API key for provider '{target}'. Set OPENAI_API_KEY in your .env "
                "(or OPENAI_BASE_URL if you are pointing at a local/self-hosted endpoint)."
            )

        return OpenAIBackend(
            api_key=key,
            model=resolved_model or DEFAULT_MODELS["openai_compat"],
            base_url=url or None,
            timeout=timeout,
        )

    known = ", ".join(sorted(ANTHROPIC_ALIASES | OPENAI_ALIASES))
    raise LLMError(f"Unknown LLM provider '{target}'. Supported: {known}.")
