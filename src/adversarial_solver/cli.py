"""CLI entry point for adversarial-solver."""

from pathlib import Path

import click

from .core import adversarial_solve, segmented_adversarial_solve
from .tone_checker import tone_check
from .providers import auto_detect_mode, get_context_window


@click.group()
def cli():
    """Adversarial Solver — Dual-LLM adversarial content generation.

    Generator produces. Critic reviews. Generator revises.
    Loop until PASS or escalate for human review.
    """
    pass


@cli.command()
@click.option("--task", "-t", required=True, help="Task description")
@click.option("--dept", "-d", required=True, help="Department ID (from departments.yaml)")
@click.option("--max-rounds", "-r", default=3, help="Maximum adversarial rounds")
@click.option(
    "--mode", "-m", default=None,
    type=click.Choice(["standard", "segmented"]),
    help="Mode: standard / segmented (default: auto-detect)",
)
@click.option("--config", "-c", default=None, help="Path to config directory")
def solve(task: str, dept: str, max_rounds: int, mode: str, config: str):
    """Run adversarial solve on a single task.

    Mode is auto-detected from model context windows unless explicitly set.
    Short-context models (e.g. MiniMax M3 at 8K) auto-trigger segmented mode.

    \b
    Examples:
      adversarial-solver solve -t "Write a product description" -d marketing
      adversarial-solver solve -t "Generate FAQ page" -d legal -m segmented
    """
    if mode == "segmented":
        result = segmented_adversarial_solve(task, dept, max_rounds, config)
    else:
        result = adversarial_solve(task, dept, max_rounds, config, mode)

    print(f"\n\n{'=' * 60}")
    print(f"  Results")
    print(f"{'=' * 60}")
    print(f"  Mode:   {result.get('mode', mode or 'auto')}")
    print(f"  Status: {result['status']}")
    print(f"  Rounds: {result.get('total_rounds', len(result.get('rounds', [])))}")
    if "tone_check" in result:
        tc = result["tone_check"]
        if tc["passed"]:
            print("  Tone Check: PASS")
        else:
            print(f"  Tone Check: FAIL ({len(tc['issues'])} issue(s))")
    print(f"  Output:  {len(result['final'])} chars")
    print(f"{'=' * 60}")


@cli.command()
@click.option("--text", "-t", required=True, help="Text to check")
@click.option("--config", "-c", default=None, help="Path to config directory")
def check_tone(text: str, config: str):
    """Run tone checker on a text string.

    Example:
      adversarial-solver check-tone -t "This product cures everything magically."
    """
    result = tone_check(text, config)
    print(f"\nTone Check: {'PASS' if result['passed'] else 'FAIL'}")
    print(f"Score: {result['score']}/100")
    if result["issues"]:
        print("Issues:")
        for issue in result["issues"]:
            print(f"  - {issue}")


@cli.command()
@click.option("--path", "-p", default="config", help="Where to create config templates")
def init(path: str):
    """Create config templates (departments.yaml, rules.yaml, constitution.md, .env.example).

    Example:
      adversarial-solver init
      adversarial-solver init -p my_project/config
    """
    config_dir = Path(path)
    config_dir.mkdir(parents=True, exist_ok=True)

    # departments.yaml
    dept_file = config_dir / "departments.yaml"
    if not dept_file.exists():
        dept_file.write_text(_DEPT_TEMPLATE, encoding="utf-8")
        print(f"  Created: {dept_file}")

    # rules.yaml
    rules_file = config_dir / "rules.yaml"
    if not rules_file.exists():
        rules_file.write_text(_RULES_TEMPLATE, encoding="utf-8")
        print(f"  Created: {rules_file}")

    # constitution.md
    const_file = config_dir / "constitution.md"
    if not const_file.exists():
        const_file.write_text(_CONSTITUTION_TEMPLATE, encoding="utf-8")
        print(f"  Created: {const_file}")

    # .env
    env_file = config_dir / ".env"
    if not env_file.exists():
        env_file.write_text(_ENV_EXAMPLE, encoding="utf-8")
        print(f"  Created: {env_file} (edit with your API keys)")

    print(f"\n[OK] Config ready: {config_dir.absolute()}")
    print(f"   1. Edit departments.yaml to define your review teams")
    print(f"   2. Edit rules.yaml to set banned words")
    print(f"   3. Edit .env with your API keys")


@cli.command()
@click.option("--model", "-m", required=True, help="Model ID (e.g. openai/gpt-4.1)")
def info(model: str):
    """Show context window info for a model.

    Example:
      adversarial-solver info -m MiniMax/M3
    """
    window = get_context_window(model)
    print(f"\nModel:  {model}")
    print(f"Context window: {window:,} tokens")
    if window < 16000:
        print(f"[WARN] Short context — segmented mode recommended for long outputs")


_ENV_EXAMPLE = """# Adversarial Solver — API Keys
# Fill in the keys for the providers you use.
# Leave unused providers blank.

# DeepSeek
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# OpenAI
OPENAI_API_KEY=sk-your-key

# Anthropic (Claude)
ANTHROPIC_API_KEY=sk-ant-your-key

# MiniMax
MINIMAX_API_KEY=your-key
MINIMAX_API_BASE=https://api.minimaxi.com/v1

# Google Gemini
GEMINI_API_KEY=your-key

# Retry settings
EMPTY_RETRY_MAX=3
"""


_DEPT_TEMPLATE = """# Adversarial Solver — Department Configuration
# Define your departments, models, and review rules here.
#
# Model fields:
#   primary_model   — Generator (produces content)
#   reviewer_model  — Critic (reviews content)
#   arbiter_model   — Arbiter (optional, resolves deadlocks)
#   fallback_model  — Fallback (used if primary/critic return empty)

departments:
  marketing:
    name: "Marketing"
    scope: "Brand content, ad copy, social media, SEO"
    primary_model: "deepseek/deepseek-chat"
    reviewer_model: "deepseek/deepseek-chat"
    arbiter_model: ""
    fallback_model: ""
    tone_checker: true
    reviewer_role: "Review brand tone, banned words, CTA clarity, and compliance"

  legal:
    name: "Legal & Compliance"
    scope: "Privacy policy, terms, regulatory documents"
    primary_model: "deepseek/deepseek-chat"
    reviewer_model: "deepseek/deepseek-chat"
    arbiter_model: ""
    fallback_model: ""
    tone_checker: false
    reviewer_role: "Review legal accuracy, regulatory compliance, liability risks"

  technical:
    name: "Engineering"
    scope: "Code, API docs, technical documentation"
    primary_model: "deepseek/deepseek-chat"
    reviewer_model: "deepseek/deepseek-chat"
    arbiter_model: ""
    fallback_model: ""
    tone_checker: false
    reviewer_role: "Review code correctness, architecture, API design"

  editorial:
    name: "Editorial"
    scope: "Articles, newsletters, long-form content"
    primary_model: "deepseek/deepseek-chat"
    reviewer_model: "deepseek/deepseek-chat"
    arbiter_model: ""
    fallback_model: ""
    tone_checker: true
    reviewer_role: "Review factual accuracy, style consistency, readability"
"""

_RULES_TEMPLATE = """# Adversarial Solver — Tone Checker Rules
# Define banned words and quality checklists here.
# Group words by category for better organization.

banned_words:
  mysticism:
    - "magic"
    - "miracl"
    - "ancient wisdom"
    - "secret formula"
    - "mystical"

  medical:
    - "cure"
    - "treat"
    - "prevent"
    - "heal"
    - "detox"

  exaggeration:
    - "premium"
    - "luxur"
    - "revolutionary"
    - "game-changing"
    - "world-class"
    - "best-ever"

  deprecated:
    - "example-old-slogan"

checklist:
  - "Title <= 60 characters"
  - "Subtitle <= 120 characters"
  - "Paragraph length 50-80 words"
  - "No banned words detected"
  - "No medical claims (unless approved)"
  - "CTA is clear and actionable"
  - "No 'You should' phrasing"
  - "Consistent sentence rhythm"
"""

_CONSTITUTION_TEMPLATE = """# Your Project Constitution

> This is a template. Replace with your own core principles and brand guidelines.
> The Generator model references these rules when producing content.

---

## Core Principles

1. **Accuracy over marketing** — Every claim must be verifiable. No exaggeration.
2. **Clarity over cleverness** — Write to be understood, not to impress.
3. **Respect the reader** — Don't talk down. Don't over-promise.

## Tone Guidelines

- Professional but not corporate
- Warm but not sentimental
- Direct but not aggressive

## Hard Rules

- No false or misleading claims
- No unverified statistics
- No disparagement of competitors
- No fear-based marketing
- Always cite sources for factual claims

## Visual Identity (if applicable)

- Colors: [Define your brand colors]
- Fonts: [Define your brand fonts]
- Image style: [Define your image guidelines]

---

> Edit this file to match your project. The more specific, the better.
"""

if __name__ == "__main__":
    cli()
