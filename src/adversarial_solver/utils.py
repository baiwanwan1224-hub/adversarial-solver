"""Utility functions — config loading and helpers."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_config(config_path: str | None = None) -> dict:
    """Load global config. Optionally loads .env if present.

    Args:
        config_path: Path to config directory (default: ./config/)

    Returns:
        Dict with merged configuration
    """
    if config_path is None:
        config_path = "config"

    config_dir = Path(config_path)
    env_file = config_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    return {
        "config_dir": str(config_dir),
        "constitution_path": str(config_dir / "constitution.md"),
        "empty_retry_max": int(os.getenv("EMPTY_RETRY_MAX", "3")),
    }


def load_department_config(dept: str, config_path: str | None = None) -> dict:
    """Load department-specific config from config/departments.yaml.

    Args:
        dept: Department ID (e.g. "marketing", "legal")
        config_path: Path to config directory

    Returns:
        Dict with department config (name, scope, models, tone_checker, reviewer_role)

    Raises:
        ValueError: If department not found in config
    """
    if config_path is None:
        config_path = "config"

    yaml_file = Path(config_path) / "departments.yaml"
    if not yaml_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {yaml_file}\n"
            f"Run 'adversarial-solver init' to create a template."
        )

    with open(yaml_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    departments = data.get("departments", {})
    if dept not in departments:
        available = ", ".join(departments.keys())
        raise ValueError(
            f"Department '{dept}' not found in config.\n"
            f"Available departments: {available}"
        )

    dept_config = departments[dept]

    # Merge with defaults
    return {
        "name": dept_config.get("name", dept),
        "scope": dept_config.get("scope", "General"),
        "primary_model": dept_config.get("primary_model", "deepseek/deepseek-chat"),
        "reviewer_model": dept_config.get("reviewer_model", "deepseek/deepseek-chat"),
        "tone_checker": dept_config.get("tone_checker", False),
        "reviewer_role": dept_config.get("reviewer_role", "Review content quality"),
    }
