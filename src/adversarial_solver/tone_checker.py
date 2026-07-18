"""Tone Checker — hard-filter banned words in generated content.

Rules are defined in config/rules.yaml.
"""

from pathlib import Path

try:
    import yaml
    _has_yaml = True
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]
    _has_yaml = False


def load_rules(config_path: str | None = None) -> dict:
    """Load tone checker rules from config/rules.yaml.

    Returns:
        Dict with 'banned_words' (list) and 'checklist' (list of rules)
    """
    if config_path is None:
        config_path = "config"
    rules_file = Path(config_path) / "rules.yaml"

    if not rules_file.exists() or not _has_yaml:
        return {"banned_words": [], "checklist": []}

    with open(rules_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Flatten grouped banned words
    banned = []
    raw_banned = data.get("banned_words", {})
    if isinstance(raw_banned, dict):
        for _category, words in raw_banned.items():
            if isinstance(words, list):
                banned.extend(words)
    elif isinstance(raw_banned, list):
        banned = raw_banned

    return {
        "banned_words": banned,
        "checklist": data.get("checklist", []),
    }


def tone_check(text: str, config_path: str | None = None) -> dict:
    """Run tone check on generated text.

    Separates "internal notes" from "public content" before checking.

    Args:
        text: Full text to check
        config_path: Path to config directory

    Returns:
        Dict with keys: passed (bool), issues (list), score (int)
    """
    rules = load_rules(config_path)
    banned_words = rules.get("banned_words", [])

    # Separate internal notes from public content
    public_text = text
    for sep in ["===INTERNAL===", "---INTERNAL---", "[INTERNAL]", "INTERNAL NOTES"]:
        if sep in text:
            public_text = text.split(sep)[0]
            break

    public_lower = public_text.lower()
    issues = []

    for word in banned_words:
        if word.lower() in public_lower:
            issues.append(f"Banned word: {word}")

    # Basic length checks
    lines = [ln.strip() for ln in public_text.split("\n") if ln.strip()]
    if lines and len(lines[0]) > 80:
        issues.append(f"First line may be too long: {len(lines[0])} chars (suggest ≤60)")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "score": max(0, 100 - len(issues) * 15),
        "checked_chars": len(public_text),
        "skipped_chars": len(text) - len(public_text),
    }
