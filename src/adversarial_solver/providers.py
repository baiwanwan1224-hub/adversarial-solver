"""Provider-specific adapters and context window detection.

Handles:
- Context window lookup for auto mode detection
- Provider-specific quirks (M3 system prompt, Claude token limits, etc.)
"""

from typing import Dict, Optional

# Known context windows (in tokens) — used for auto-detecting segmented vs standard mode
CONTEXT_WINDOWS: Dict[str, int] = {
    # OpenAI
    "gpt-4.1": 128000,
    "gpt-4.1-mini": 128000,
    "gpt-4.1-nano": 128000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 4096,
    # Anthropic
    "claude-sonnet-4-6": 200000,
    "claude-opus-4-6": 200000,
    "claude-haiku-4-5": 200000,
    "claude-3.5-sonnet": 200000,
    "claude-3-opus": 200000,
    "claude-3-haiku": 200000,
    # DeepSeek
    "deepseek-chat": 64000,
    "deepseek-reasoner": 64000,
    # MiniMax (short context — auto-segmented)
    "MiniMax-M3": 8000,
    "MiniMax-M1": 8000,
    # Google
    "gemini-2.5-pro": 1048576,
    "gemini-2.5-flash": 1048576,
    "gemini-2.0-flash": 1048576,
    "gemini-1.5-pro": 1048576,
    # Meta (via Groq/Together)
    "llama-4-maverick": 128000,
    "llama-4-scout": 128000,
    "llama-3.3-70b": 128000,
    "llama-3.2-90b": 128000,
    "llama-3.1-405b": 128000,
    "llama-3.1-70b": 128000,
    "llama-3.1-8b": 128000,
    # Mistral
    "mistral-large": 128000,
    "mistral-medium": 32000,
    "mistral-small": 32000,
    # Qwen
    "qwen-max": 32768,
    "qwen-plus": 131072,
    "qwen-turbo": 131072,
    "qwen3-235b": 131072,
    # xAI / Grok
    "grok-3": 131072,
    "grok-2": 32768,
    # Cohere
    "command-r-plus": 128000,
    "command-r": 128000,
    # AI21
    "jamba-1.5-large": 256000,
    "jamba-1.5-mini": 256000,
}

# Models that cannot handle system prompts well — use user message instead
MODELS_NO_SYSTEM_PROMPT = [
    "MiniMax-M3",  # M3 sometimes ignores system messages
    "MiniMax-M1",
]

# Models with strict max_tokens requirements
MODELS_STRICT_MAX_TOKENS = [
    "MiniMax-M3",  # M3 requires explicit, moderate max_tokens
    "MiniMax-M1",
]


def get_context_window(model: str) -> int:
    """Get context window size for a model.

    Args:
        model: Model identifier (e.g. "openai/gpt-4.1", "MiniMax/M3")

    Returns:
        Context window in tokens. Returns 128000 as safe default if unknown.
    """
    # Strip provider prefix
    model_name = model.split("/")[-1] if "/" in model else model

    # Direct match
    if model_name in CONTEXT_WINDOWS:
        return CONTEXT_WINDOWS[model_name]

    # Fuzzy match: model_name contains key OR key contains model_name
    for key, window in CONTEXT_WINDOWS.items():
        kl = key.lower()
        ml = model_name.lower()
        if kl in ml or ml in kl:
            return window

    # Safe default for unknown models
    return 128000


def needs_system_prompt_adapter(model: str) -> bool:
    """Check if model needs system prompt → user message adapter."""
    model_name = model.split("/")[-1] if "/" in model else model
    return any(m.lower() in model_name.lower() for m in MODELS_NO_SYSTEM_PROMPT)


def needs_strict_max_tokens(model: str) -> bool:
    """Check if model has strict max_tokens requirements."""
    model_name = model.split("/")[-1] if "/" in model else model
    return any(m.lower() in model_name.lower() for m in MODELS_STRICT_MAX_TOKENS)


def build_messages(model: str, system: str, user: str) -> list:
    """Build messages list with provider-specific adaptations.

    For models that don't support system prompts, prepend system content
    to the user message instead.
    """
    if needs_system_prompt_adapter(model):
        return [{"role": "user", "content": f"{system}\n\n---\n\n{user}"}]
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def estimate_output_tokens(task_description: str) -> int:
    """Rough estimate of expected output tokens from task description.

    Heuristic: output is typically 1-2x the task description length,
    with a minimum of 1000 and maximum of 32000.

    Args:
        task_description: The task prompt

    Returns:
        Estimated output tokens
    """
    # Very rough: 1 char ≈ 0.3 tokens for English, 0.5 for CJK
    chars = len(task_description)
    has_cjk = any('\u4e00' <= c <= '\u9fff' for c in task_description)
    ratio = 0.5 if has_cjk else 0.3
    estimated_tokens = int(chars * ratio)

    # Check for long-form indicators
    long_form_keywords = ["report", "article", "essay", "document", "analysis", "review", "报告", "文章", "分析"]
    if any(kw in task_description.lower() for kw in long_form_keywords):
        estimated_tokens = max(estimated_tokens, 8000)

    return max(1000, min(32000, estimated_tokens))


def auto_detect_mode(task_description: str, generator_model: str, critic_model: str) -> str:
    """Auto-detect whether to use standard or segmented mode.

    If either model has a short context window (< 16K) and the estimated
    output approaches that window, use segmented mode.

    Args:
        task_description: The task prompt
        generator_model: Generator model ID
        critic_model: Critic model ID

    Returns:
        "standard" or "segmented"
    """
    gen_window = get_context_window(generator_model)
    crit_window = get_context_window(critic_model)
    min_window = min(gen_window, crit_window)
    estimated = estimate_output_tokens(task_description)

    # If the smallest context window can't comfortably hold the output,
    # auto-switch to segmented mode
    if min_window < 16000:
        return "segmented"

    if estimated * 2 > min_window:
        return "segmented"

    return "standard"
