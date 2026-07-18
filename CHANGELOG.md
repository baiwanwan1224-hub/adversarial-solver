# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0-pre] — Unreleased

### Added
- Auto mode detection: standard vs segmented based on model context windows
- Optional Arbiter (3rd model) for Generator-Critic deadlock resolution
- Hard empty-response prevention with automatic fallback model switching
- Provider-specific adapters (M3 system prompt, strict max_tokens, etc.)
- `adversarial-solver info` command to check model context windows
- Context window lookup table for 30+ models
- `adversarial-solver init` now creates `.env` file from template
- Dev dependencies: pytest, pytest-cov, ruff, mypy
- ruff lint + mypy type-check in CI
- Test coverage reporting with 60% threshold

### Changed
- `call_model()` now accepts `fallback_model` parameter
- `adversarial_solve()` mode parameter now defaults to None (auto-detect)
- `EmptyModelError` now carries primary and fallback model info
- `.gitignore` expanded with coverage, mypy, ruff cache patterns

### Fixed
- M3 empty response now triggers fallback instead of giving up
- System prompt adapted for models that don't support it (M3)

## [0.1.0] — 2026-07-18

### Added
- Initial release
- Standard adversarial solve mode (Generator → Critic → Revise loop)
- Segmented mode for long-form HTML content generation
- YAML-based department and rules configuration
- Tone Checker with configurable banned words and internal notes separation
- Multi-provider support via LiteLLM
- CLI (`adversarial-solver solve`, `init`, `check-tone`)
- Python API (`adversarial_solve`, `segmented_adversarial_solve`, `batch_solve`)
- Full audit trail with JSON archiving
- Automatic retry on empty model responses with temperature escalation
