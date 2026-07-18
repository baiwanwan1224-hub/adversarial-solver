# Adversarial Solver

> Dual-LLM adversarial content generation — Generator produces, Critic reviews, loop until PASS.

## Why?

Writing content is easy. Writing *correct* content is hard.

Adversarial Solver makes two (or three) LLMs keep each other in check:
- **Generator** produces the content
- **Critic** reviews it against your rules
- If it fails, the Generator revises
- Loop until the Critic (or **Arbiter**) says "PASS"

The result: content that has been through a quality-control pipeline *before* it reaches human eyes.

## Key Features

- **Dual-Model Adversarial Loop** — Generator → Critic → Revise → PASS
- **Optional Arbiter** — 3rd model breaks Generator-Critic deadlocks
- **Auto Mode Detection** — Short-context models (e.g. MiniMax M3 at 8K) auto-trigger segmented mode; long-context models stay in standard mode
- **Hard Empty-Response Prevention** — Built-in retry + temperature escalation + automatic fallback model switching
- **Tone Checker** — Hard-filter banned words with configurable YAML rules
- **Segmented Mode** — Long-form content split into outline → sections → assembly
- **Config-Driven** — YAML departments and rules; no code changes needed
- **Multi-Provider** — Any LiteLLM-supported model (OpenAI, Anthropic, DeepSeek, MiniMax, Gemini, local models)
- **Full Audit Trail** — Every round logged; results archived as JSON

## Quick Start

```bash
# Install
pip install adversarial-solver

# Create config templates
adversarial-solver init

# Edit config/departments.yaml and config/rules.yaml
# Add your API keys to config/.env

# Run your first adversarial solve (mode auto-detected)
adversarial-solver solve -t "Write a product description." -d marketing
```

## How It Works

```
Task → Generator (v1) → Critic reviews
                ↑            ↓
                │      PASS? ─── Yes → Output
                │         │
                └─ Revise ← No
                │         │
                │   Deadlocked? → Arbiter (optional) → Final verdict
                │
           [Empty response? → Retry → Fallback model]
```

### Auto Mode Detection

The solver automatically detects whether to use **standard** or **segmented** mode based on model context windows:

| Scenario | Detection | Behavior |
|----------|-----------|----------|
| Both models 128K+ context | → standard | Single-pass generation |
| One model ≤16K context (e.g. M3) | → segmented | Auto-split into outline + sections |
| Manual override | `-m standard` or `-m segmented` | User choice respected |

Run `adversarial-solver info -m MiniMax/M3` to check a model's context window.

## Configuration

### departments.yaml — Define your review teams

```yaml
departments:
  marketing:
    name: "Marketing"
    primary_model: "openai/gpt-4.1"           # Generator
    reviewer_model: "anthropic/claude-sonnet-4-6"  # Critic
    arbiter_model: ""                          # Optional 3rd model
    fallback_model: ""                         # Fallback on empty response
    tone_checker: true
```

### rules.yaml — Define your banned words

```yaml
banned_words:
  medical:
    - "cure"
    - "treat"
    - "heal"
  exaggeration:
    - "premium"
    - "luxury"
    - "revolutionary"
```

### constitution.md — Define your principles

Write your brand guidelines, core principles, and hard rules. The Generator references this for every task.

## CLI Reference

```bash
# Single task (mode auto-detected)
adversarial-solver solve -t "Write a landing page headline." -d marketing

# Force segmented mode
adversarial-solver solve -t "Generate a 50-page report." -d editorial -m segmented

# Tone check on existing text
adversarial-solver check-tone -t "This product cures everything."

# Check model context window
adversarial-solver info -m MiniMax/M3

# Create config templates
adversarial-solver init -p my_project/config
```

## Python API

```python
from adversarial_solver import adversarial_solve

result = adversarial_solve(
    task="Write a product description.",
    dept="marketing",
    max_rounds=3,
    config_path="my_config",  # optional
    mode=None,                # None = auto-detect
)

print(result["final"])          # The approved output
print(result["status"])         # "PASS" or "PENDING_REVIEW"
print(result["total_rounds"])   # How many review rounds it took
print(result.get("tone_check")) # Tone checker results (if enabled)
```

### Batch Processing

```python
from adversarial_solver import batch_solve

results = batch_solve([
    {"task": "Write a homepage headline.", "dept": "marketing"},
    {"task": "Write a privacy policy summary.", "dept": "legal"},
])
print(f"{results['passed']}/{results['total']} passed")
```

## Real-World Use Cases

| Use Case | Department | Typical Mode |
|----------|-----------|-------------|
| Brand copy & ads | marketing | standard |
| Legal/regulatory docs | legal | standard |
| Code review | engineering | standard |
| Blog posts | editorial | standard |
| Competitive analysis (50+ pages) | editorial | auto-segmented |
| Strategy documents | marketing | auto-segmented |

## FAQ

**Q: Do I need two different models?**
A: No. Same model works — the Critic gets a different system prompt that makes it behave as a reviewer.

**Q: When do I need the Arbiter (3rd model)?**
A: When Generator and Critic disagree for multiple rounds and you want an automatic tie-breaker. Most cases, 2 models are enough.

**Q: What happens if a model returns empty?**
A: The solver retries with temperature escalation. If still empty, it switches to `fallback_model` (if configured). If fallback also fails, the task is archived for human review.

**Q: How does auto mode detection work?**
A: The solver checks both models' context windows (via built-in lookup table). If either model has ≤16K context, it auto-switches to segmented mode. You can always override with `-m standard`.

**Q: What if my model isn't in the context window lookup table?**
A: Unknown models default to 128K (safe for most modern LLMs). You can submit a PR to add your model to `providers.py`.

**Q: Can I use local models?**
A: Yes — via LiteLLM's support for Ollama, vLLM, and other local providers.

**Q: Does the tone checker work with non-English text?**
A: Yes. Banned words are case-insensitive substring matches. Add any language words to `rules.yaml`.

## Requirements

- Python 3.10+
- API key for at least one LLM provider (see [LiteLLM docs](https://docs.litellm.ai/docs/providers))

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
