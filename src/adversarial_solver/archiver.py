"""Result archiving — save execution logs as JSON."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def archive_result(
    log: Dict,
    dept: str,
    status: str,
    config_path: Optional[str] = None,
) -> Path:
    """Archive an adversarial solve execution log to outputs/ directory.

    Args:
        log: Full execution log dict
        dept: Department ID
        status: "PASS" or "PENDING_REVIEW"
        config_path: Path to config directory (for resolving outputs/ location)

    Returns:
        Path to the archived file
    """
    if config_path:
        outputs_dir = Path(config_path).parent / "outputs"
    else:
        outputs_dir = Path("outputs")

    target_dir = outputs_dir / dept if status == "PASS" else outputs_dir / "_pending_review"
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = target_dir / f"{timestamp}.json"
    output_file.write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[ARCHIVE] Archived: {output_file}")
    return output_file
