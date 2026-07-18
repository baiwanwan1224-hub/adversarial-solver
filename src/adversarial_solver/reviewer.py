"""Reviewer prompt builder and pass/fail judgment logic."""



def build_reviewer_prompt(dept_config: dict, config: dict) -> str:
    """Build the critic/reviewer system prompt.

    Args:
        dept_config: Department config from departments.yaml
        config: Global config from config loader

    Returns:
        System prompt string for the reviewer model
    """
    dept_name = dept_config.get("name", "Unknown")
    reviewer_role = dept_config.get("reviewer_role", "Review content quality and compliance")
    scope = dept_config.get("scope", "General content")

    return f"""You are the CRITIC for department: {dept_name}.

# Your Role: Reviewer (not Writer)
Your job is to review the Generator's output against the department's standards.
Do NOT rewrite the content. Only identify issues.

# Review Scope
{scope}

# Review Focus
{reviewer_role}

# Output Format
- If the output has SIGNIFICANT issues: list up to 3 key problems, with specific suggestions
- If the output is acceptable or has only minor issues: say "通过" or "PASS"
- Do not fabricate issues
- Do not rewrite the content

# Review Criteria
1. Does it meet the task requirements?
2. Are there any factual errors or unsupported claims?
3. Is the tone appropriate for this department?
4. Are there any compliance or quality issues?
"""


def is_passed(review: str, current_output: str = "") -> bool:
    """Determine if a review verdict is PASS or FAIL.

    Args:
        review: Reviewer's output text
        current_output: The content being reviewed (validated for minimum length)

    Returns:
        True if review indicates pass
    """
    # Guard: empty/error generator output
    if not current_output or not current_output.strip():
        return False
    if current_output.strip().startswith("[ERROR]"):
        return False
    if len(current_output.strip()) < 30:
        return False

    # Guard: reviewer error
    if "[ERROR]" in review:
        return False
    if not review or len(review.strip()) < 5:
        return False

    pass_signals = ["通过", "PASS", "无问题", "审核通过", "Approved", "OK"]
    fail_signals = [
        "问题：", "Issue:", "不通过", "需要修改", "建议修改",
        "存在以下问题", "⚠️", "❌", "改进", "调整",
    ]

    has_pass = any(sig in review for sig in pass_signals)
    has_fail = any(sig in review for sig in fail_signals)

    if has_fail and not has_pass:
        return False
    if has_pass and not has_fail:  # noqa: SIM103
        return True
    # Conservative: ambiguous → fail
    return False
