from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from src.core.config import get_settings


class AIProviderError(Exception):
    """Raised when the configured AI provider can't be initialized (missing API
    key, unknown provider, etc.). Callers map this to a graceful degradation
    response (FR-033) rather than letting it crash the request."""


# Maps AI_PROVIDER -> the Settings field holding its API key. Swapping
# providers is purely a settings change; this is the one place that needs a
# new entry when a new provider is added.
_PROVIDER_API_KEY_FIELDS = {
    "openai": "openai_api_key",
    "google_genai": "google_api_key",
}


@lru_cache
def get_chat_model() -> BaseChatModel:
    """Env-driven chat-model factory (AI_PROVIDER, AI_MODEL). Swapping the
    provider is purely a settings change — no code outside this file needs to
    change, per T067's acceptance criteria."""
    settings = get_settings()

    key_field = _PROVIDER_API_KEY_FIELDS.get(settings.ai_provider)
    api_key = getattr(settings, key_field, None) if key_field else None
    if key_field and not api_key:
        raise AIProviderError(
            f"AI_PROVIDER is '{settings.ai_provider}' but {key_field.upper()} is not set."
        )

    try:
        from langchain.chat_models import init_chat_model

        return init_chat_model(
            settings.ai_model,
            model_provider=settings.ai_provider,
            api_key=api_key,
            temperature=0,
            # The SDK's default retry/backoff (several attempts, growing
            # delays) can turn one rate-limited call into a minute-plus hang
            # before it finally raises. We already degrade gracefully to a
            # 503 (see AIChatService._invoke_graph), so there's no benefit to
            # retrying here — better to fail fast.
            max_retries=1,
        )
    except Exception as exc:
        raise AIProviderError(f"Failed to initialize AI provider: {exc}") from exc


def reset_chat_model_cache() -> None:
    """Test/config-reload hook — clears the cached model so a new one is built
    next call (e.g. after changing settings mid-process in tests)."""
    get_chat_model.cache_clear()
