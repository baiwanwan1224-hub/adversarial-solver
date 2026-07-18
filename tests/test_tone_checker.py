"""Tests for adversarial_solver.tone_checker."""

import tempfile
from pathlib import Path

from adversarial_solver.tone_checker import load_rules, tone_check


def test_tone_check_no_rules():
    """Tone check with no config should return clean."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = tone_check("Hello world", tmpdir)
        assert result["passed"] is True
        assert result["score"] == 100


def test_tone_check_banned_word():
    """Tone check should detect banned words."""
    # Create temp rules file
    rules_dir = Path(tempfile.mkdtemp())
    rules_file = rules_dir / "rules.yaml"
    rules_file.write_text(
        "banned_words:\n  test:\n    - badword\n",
        encoding="utf-8",
    )

    result = tone_check("This contains badword in the text.", str(rules_dir))
    assert result["passed"] is False
    assert len(result["issues"]) == 1
    assert "badword" in result["issues"][0]


def test_tone_check_internal_notes():
    """Banned words in internal notes should not trigger."""
    rules_dir = Path(tempfile.mkdtemp())
    rules_file = rules_dir / "rules.yaml"
    rules_file.write_text(
        "banned_words:\n  test:\n    - badword\n",
        encoding="utf-8",
    )

    result = tone_check(
        "Clean public text.\n===INTERNAL===\nThis has badword in internal notes.",
        str(rules_dir),
    )
    assert result["passed"] is True


def test_load_rules_empty():
    """Load rules from non-existent path returns empty."""
    result = load_rules("/nonexistent/path")
    assert result["banned_words"] == []
    assert result["checklist"] == []
