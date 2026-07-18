"""Tests for adversarial_solver.core."""


def test_version():
    """Verify version is defined and follows semver format."""
    from adversarial_solver import __version__
    assert isinstance(__version__, str)
    assert __version__.startswith("0.")
    assert len(__version__.split(".")) >= 2


def test_import_core():
    """Verify core functions are importable."""
    from adversarial_solver import (
        adversarial_solve,
        batch_solve,
        segmented_adversarial_solve,
    )
    assert callable(adversarial_solve)
    assert callable(segmented_adversarial_solve)
    assert callable(batch_solve)


def test_import_models():
    """Verify model utilities are importable."""
    from adversarial_solver import call_model, EmptyModelError
    assert callable(call_model)
    assert issubclass(EmptyModelError, Exception)


def test_import_providers():
    """Verify provider utilities are importable."""
    from adversarial_solver import get_context_window, auto_detect_mode
    assert callable(get_context_window)
    assert callable(auto_detect_mode)
