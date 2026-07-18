"""Tests for adversarial_solver.models."""

from adversarial_solver.models import is_empty_response


def test_is_empty_none():
    assert is_empty_response("") is True
    assert is_empty_response("   ") is True


def test_is_empty_short():
    assert is_empty_response("Hi") is True
    assert is_empty_response("Short text") is True


def test_is_empty_error():
    assert is_empty_response("[ERROR] Something went wrong") is True


def test_is_not_empty():
    assert is_empty_response("This is a proper response that is long enough.") is False
