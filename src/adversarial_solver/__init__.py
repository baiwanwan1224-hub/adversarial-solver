"""Adversarial Solver — Dual-LLM adversarial content generation.

Generator produces. Critic reviews. Generator revises.
Loop until PASS or escalate to human review.

Features:
- 2-model (Gen+Critic) or 3-model (+Arbiter) pipeline
- Auto mode detection (standard vs segmented based on context windows)
- Hard empty-response prevention with fallback models
- Tone Checker with configurable banned words
- Multi-provider via LiteLLM (OpenAI, Anthropic, DeepSeek, MiniMax, etc.)

Version: 0.2.0-pre
"""

__version__ = "0.1.2"
__author__ = "Reforox Contributors"

from .core import adversarial_solve, batch_solve, segmented_adversarial_solve
from .models import EmptyModelError, call_model
from .providers import auto_detect_mode, get_context_window
from .tone_checker import load_rules, tone_check

__all__ = [
    "adversarial_solve",
    "segmented_adversarial_solve",
    "batch_solve",
    "tone_check",
    "load_rules",
    "call_model",
    "EmptyModelError",
    "get_context_window",
    "auto_detect_mode",
]
