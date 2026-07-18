"""Tests for adversarial_solver.core."""


def test_import():
    """Verify the package imports correctly."""
    from adversarial_solver import (
        adversarial_solve,
        batch_solve,
        call_model,
        load_rules,
        segmented_adversarial_solve,
        tone_check,
    )
    assert adversarial_solve is not None
    assert segmented_adversarial_solve is not None
    assert batch_solve is not None
    assert tone_check is not None
    assert load_rules is not None
    assert call_model is not None


def test_version():
    """Verify version is defined."""
    from adversarial_solver import __version__
    assert __version__.startswith("0.")
    assert len(__version__.split(".")) >= 2
