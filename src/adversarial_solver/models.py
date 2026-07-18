"""Multi-provider LLM call with retry, fallback, and empty-response handling.

HARD GUARANTEE: call_model() NEVER returns empty string.
If primary model fails (empty/error after all retries), falls back to fallback_model.
If fallback also fails, raises EmptyModelError with full diagnostic info.
"""

from litellm import completion

from .providers import build_messages, needs_strict_max_tokens


class EmptyModelError(Exception):
    """Raised when ALL models (primary + fallback) return empty responses."""
    def __init__(self, message: str, primary: str = "", fallback: str = ""):
        super().__init__(message)
        self.primary_model = primary
        self.fallback_model = fallback


def is_empty_response(content: str, min_chars: int = 20) -> bool:
    """Check if model response is effectively empty."""
    if not content or not content.strip():
        return True
    if content.strip().startswith("[ERROR]"):
        return True
    if len(content.strip()) < min_chars:
        return True
    return False


def _call_single(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    max_retries: int = 5,
) -> str:
    """Internal: call a single model with retries. May raise EmptyModelError.

    Returns:
        Model response text
    Raises:
        EmptyModelError: if model returns empty after all retries
    """
    messages = build_messages(model, system, user)

    # Adjust max_tokens for models with strict limits
    if needs_strict_max_tokens(model):
        max_tokens = min(max_tokens, 4000)

    for attempt in range(max_retries + 1):
        try:
            response = completion(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content = response.choices[0].message.content or ""
            content = content.strip()

            if is_empty_response(content):
                model_tag = model.split("/")[-1]
                if attempt < max_retries:
                    print(f"   [WARN]  {model_tag} empty, retry {attempt+1}/{max_retries}...")
                    temperature = min(temperature + 0.15, 1.2)
                    continue
                else:
                    raise EmptyModelError(
                        f"{model} returned empty after {max_retries + 1} attempts",
                        primary=model,
                    )

            return content

        except EmptyModelError:
            raise
        except Exception as e:
            model_tag = model.split("/")[-1]
            if attempt < max_retries:
                print(f"   [WARN]  {model_tag} error, retry {attempt+1}/{max_retries}: {e}")
                continue
            raise EmptyModelError(
                f"{model} call failed after {max_retries + 1} attempts: {e}",
                primary=model,
            )

    raise EmptyModelError(f"{model}: unexpected retry exhaustion", primary=model)


def call_model(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    max_retries: int = 5,
    fallback_model: str = "",
) -> str:
    """Call a LiteLLM-supported model with retry AND fallback.

    HARD GUARANTEE: Never returns empty string.

    Flow:
    1. Try primary model with retries
    2. On empty/failure → try fallback_model (if configured)
    3. On fallback failure → raise EmptyModelError with full diagnostic

    Args:
        model: Primary model ID (e.g. "openai/gpt-4.1")
        system: System prompt
        user: User message (appended with activation suffix to prevent empty)
        max_tokens: Max output tokens
        temperature: Sampling temperature
        max_retries: Max retries per model
        fallback_model: Fallback model ID (empty = no fallback)

    Returns:
        Model response text (GUARANTEED non-empty)
    """
    # Activation suffix — prevents models from returning empty
    activation = "\n\n请输出内容。不要返回空值。Please output your response now."
    user_with_activation = f"{user}{activation}"

    # Try primary model
    try:
        return _call_single(model, system, user_with_activation, max_tokens, temperature, max_retries)
    except EmptyModelError as e:
        if not fallback_model:
            raise
        print(f"   [RETRY] Primary model failed. Switching to fallback: {fallback_model.split('/')[-1]}")
        try:
            result = _call_single(
                fallback_model, system, user_with_activation,
                max_tokens, temperature, max_retries,
            )
            print(f"   [OK] Fallback succeeded")
            return result
        except EmptyModelError:
            raise EmptyModelError(
                f"ALL models exhausted.\n  Primary: {model}\n  Fallback: {fallback_model}\n"
                f"  Task may be too complex or models are unavailable.",
                primary=model,
                fallback=fallback_model,
            )
