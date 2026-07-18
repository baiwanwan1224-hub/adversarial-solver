"""Core adversarial solving logic — standard and segmented modes.

Supports:
- Auto mode detection (standard vs segmented based on model context windows)
- 2-model (Generator + Critic) or 3-model (+ Arbiter) pipeline
- Hard empty-response prevention with fallback models
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import call_model, EmptyModelError, is_empty_response
from .tone_checker import tone_check
from .reviewer import build_reviewer_prompt, is_passed
from .archiver import archive_result
from .utils import load_config, load_department_config
from .providers import auto_detect_mode


def adversarial_solve(
    task: str,
    dept: str,
    max_rounds: int = 3,
    config_path: Optional[str] = None,
    mode: Optional[str] = None,
    _retry_count: int = 0,
) -> Dict:
    """Dual-model (or 3-model) adversarial solve.

    Generator → Critic (→ Arbiter if deadlock) → PASS or PENDING_REVIEW.

    Args:
        task: Task description
        dept: Department ID (must exist in departments.yaml)
        max_rounds: Maximum adversarial review rounds (default 3)
        config_path: Path to config directory (default: ./config/)
        mode: "standard" / "segmented" / None (auto-detect)
        _retry_count: Internal retry counter

    Returns:
        Dict with keys: task, dept, status, final, rounds, tone_check
    """
    config = load_config(config_path)
    dept_config = load_department_config(dept, config_path)

    primary = dept_config.get("primary_model", "deepseek/deepseek-chat")
    reviewer = dept_config.get("reviewer_model", "deepseek/deepseek-chat")
    arbiter = dept_config.get("arbiter_model", "")
    fallback = dept_config.get("fallback_model", "")
    tone_checker_enabled = dept_config.get("tone_checker", False)
    empty_retry_max = config.get("empty_retry_max", 3)

    dept_prompt = _build_generator_prompt(dept_config, config)
    reviewer_prompt = build_reviewer_prompt(dept_config, config)

    # Auto-detect mode based on model context windows
    if mode is None:
        mode = auto_detect_mode(task, primary, reviewer)
        print(f"  Auto-detected mode: {mode}")

    log = {
        "task": task, "dept": dept,
        "primary_model": primary, "reviewer_model": reviewer,
        "arbiter_model": arbiter or None, "fallback_model": fallback or None,
        "mode": mode, "rounds": [], "timestamp": datetime.now().isoformat(),
    }

    print(f"\n{'=' * 60}")
    print(f"  Department: {dept} ({dept_config.get('name', 'Unknown')})")
    print(f"  Generator:  {primary.split('/')[-1]}")
    print(f"  Critic:     {reviewer.split('/')[-1]}")
    if arbiter: print(f"  Arbiter:    {arbiter.split('/')[-1]}")
    print(f"  Mode:       {mode}")
    print(f"{'=' * 60}\n")

    try:
        # ── Round 1: Generator ──
        print(f"[Round 1] {primary.split('/')[-1]} generating...")
        current = call_model(model=primary, system=dept_prompt, user=task, fallback_model=fallback)
        log["rounds"].append({"round": 1, "model": primary, "type": "generate", "output": current})
        print(f"   → {len(current)} chars")

        # ── Rounds 2+: Review → Revise ──
        final_status = "PENDING_REVIEW"
        for round_num in range(2, max_rounds + 2):
            print(f"\n[Round {round_num}] {reviewer.split('/')[-1]} reviewing...")
            review = call_model(
                model=reviewer, system=reviewer_prompt,
                user=f"Task:\n{task}\n\nCurrent output:\n{current}\n\nPlease review.",
                fallback_model=fallback,
            )
            log["rounds"].append({
                "round": round_num, "model": reviewer, "type": "review", "output": review,
            })
            print(f"   → {len(review)} chars")

            if tone_checker_enabled:
                tone_result = tone_check(current, config_path)
                log["tone_check"] = tone_result
                if not tone_result["passed"]:
                    review += f"\n\n[Tone Checker]\n" + "\n".join(tone_result["issues"])
                    print(f"   [WARN]  Tone Checker: {len(tone_result['issues'])} issue(s)")

            if is_passed(review, current):
                print(f"   [OK] PASSED")
                final_status = "PASS"
                break

            # Try Arbiter if configured and Critic+Generator are deadlocked
            if arbiter and round_num >= max_rounds:
                print(f"\n[{round_num}a] Arbiter {arbiter.split('/')[-1]} resolving deadlock...")
                arbiter_prompt = f"""You are the ARBITER. The Generator and Critic disagree after {round_num} rounds.

Task: {task}

Generator's last output: {current[:1500]}...
Critic's feedback: {review[:1500]}...

Decide: PASS (output is acceptable) or FAIL (needs human review). Give a brief reason."""
                arbiter_verdict = call_model(model=arbiter, system="", user=arbiter_prompt, fallback_model=fallback)
                log["rounds"].append({
                    "round": f"{round_num}a", "model": arbiter, "type": "arbiter", "output": arbiter_verdict,
                })
                if is_passed(arbiter_verdict, current):
                    print(f"   [OK] Arbiter: PASSED")
                    final_status = "PASS"
                    break
                else:
                    print(f"   [WARN]  Arbiter: FAILED — escalating to human review")
                    final_status = "PENDING_REVIEW"
                    break

            print(f"   [FAIL] Needs revision")
            round_label = round_num + 1
            print(f"[Round {round_label}] {primary.split('/')[-1]} revising...")
            current = call_model(
                model=primary, system=dept_prompt,
                user=f"Task:\n{task}\n\nYour current output:\n{current}\n\nReview feedback:\n{review}\n\nPlease revise.",
                fallback_model=fallback,
            )
            log["rounds"].append({
                "round": round_label, "model": primary, "type": "revise", "output": current,
            })
            print(f"   → {len(current)} chars")

        log["status"] = final_status
        log["final"] = current
        log["total_rounds"] = len(log["rounds"])
        archive_result(log, dept, final_status, config_path)
        return log

    except EmptyModelError as e:
        _retry_count += 1
        if _retry_count <= empty_retry_max:
            print(f"\n{'=' * 60}")
            print(f"  [RETRY] Empty response! Global retry #{_retry_count}/{empty_retry_max}")
            print(f"     Primary: {e.primary_model} | Fallback: {e.fallback_model}")
            print(f"{'=' * 60}")
            return adversarial_solve(
                task=task, dept=dept, max_rounds=max_rounds,
                config_path=config_path, mode=mode, _retry_count=_retry_count,
            )
        log["status"] = "ERROR_EMPTY_RESPONSE"
        log["error"] = str(e)
        log["final"] = f"[CRITICAL] All models exhausted after {empty_retry_max} global retries.\n{e}"
        print(f"\n  [CRIT] {log['error']}")
        archive_result(log, dept, "PENDING_REVIEW", config_path)
        return log


def segmented_adversarial_solve(
    task: str,
    dept: str,
    max_rounds: int = 3,
    config_path: Optional[str] = None,
) -> Dict:
    """Segmented adversarial solve — for long-form content.

    Phase 1: Outline → Review → Revise
    Phase 2: Generate each section independently
    Phase 3: Assembly + Final review

    Args:
        task: Task description
        dept: Department ID
        max_rounds: Maximum adversarial rounds for outline
        config_path: Path to config directory

    Returns:
        Dict with full execution log
    """
    config = load_config(config_path)
    dept_config = load_department_config(dept, config_path)

    primary = dept_config.get("primary_model", "deepseek/deepseek-chat")
    reviewer = dept_config.get("reviewer_model", "deepseek/deepseek-chat")
    fallback = dept_config.get("fallback_model", "")
    tone_checker_enabled = dept_config.get("tone_checker", False)

    dept_prompt = _build_generator_prompt(dept_config, config)
    reviewer_prompt = build_reviewer_prompt(dept_config, config)

    log = {
        "task": task, "dept": dept,
        "primary_model": primary, "reviewer_model": reviewer,
        "mode": "segmented", "phases": [], "rounds": [],
        "timestamp": datetime.now().isoformat(),
    }

    print(f"\n{'=' * 60}")
    print(f"  Department: {dept} ({dept_config.get('name', 'Unknown')})")
    print(f"  Generator:  {primary.split('/')[-1]}")
    print(f"  Critic:     {reviewer.split('/')[-1]}")
    print(f"  Mode:       segmented (long-form content)")
    print(f"{'=' * 60}\n")

    # ── Phase 1: Outline ──
    print(f"{'─' * 40}")
    print(f"  Phase 1: Outline Generation")
    print(f"{'─' * 40}")

    outline_prompt = f"""Task:
{task}

[WARN] This is a long-form task. To avoid truncation, first output a JSON outline.

Output format (strict JSON, max 3000 chars):
```json
{{
  "css_brief": "CSS design direction (1 sentence)",
  "sections": [
    {{"id": "01", "title": "Section Title", "key_points": ["Point 1 (≤20 chars)", "Point 2"]}}
  ]
}}
```

Requirements:
1. 5-8 sections covering all task dimensions
2. key_points: brief (≤20 chars each)
3. Only output JSON, no extra text
4. JSON ≤ 3000 chars"""

    outline = call_model(model=primary, system=dept_prompt, user=outline_prompt,
                         max_tokens=8000, fallback_model=fallback)
    log["rounds"].append({"round": 1, "model": primary, "type": "outline", "output": outline})
    print(f"   → Outline {len(outline)} chars")

    sections = _parse_outline(outline)
    if len(sections) < 4:
        outline_review = call_model(
            model=reviewer, system=reviewer_prompt,
            user=f"Task:\n{task}\n\nOutline:\n{outline}\n\nReview structure only.",
            max_tokens=1500, fallback_model=fallback,
        )
        log["rounds"].append({"round": 2, "model": reviewer, "type": "outline_review", "output": outline_review})
        if not is_passed(outline_review, outline):
            outline = call_model(
                model=primary, system=dept_prompt,
                user=f"{outline_prompt}\n\nReview:\n{outline_review}\n\nRevise:",
                max_tokens=4000, fallback_model=fallback,
            )
            log["rounds"].append({"round": 3, "model": primary, "type": "outline_revise", "output": outline})
        sections = _parse_outline(outline)

    if not sections:
        log["status"] = "ERROR_PARSE_OUTLINE"
        log["final"] = "[ERROR] Failed to parse outline JSON"
        archive_result(log, dept, "PENDING_REVIEW", config_path)
        return log

    print(f"   [OK] {len(sections)} sections parsed")

    # ── Phase 2: Generate sections ──
    print(f"\n{'─' * 40}")
    print(f"  Phase 2: Section Generation ({len(sections)} sections)")
    print(f"{'─' * 40}")

    sections_html = []
    for i, sec in enumerate(sections):
        sec_id = sec.get("id", f"{i+1:02d}")
        sec_title = sec.get("title", "Untitled")
        section_prompt = f"""Task:
{task}

Section {i+1}/{len(sections)}: [{sec_id}] {sec_title}
Output ONLY the HTML body content for this section. 300+ chars."""

        print(f"\n   [{sec_id}] {sec_title}...")
        sec_content = call_model(model=primary, system=dept_prompt,
                                 user=section_prompt, max_tokens=6000, fallback_model=fallback)
        sections_html.append(sec_content)
        log["rounds"].append({
            "round": 4 + i, "model": primary, "type": f"section_{sec_id}",
            "section_title": sec_title, "output": sec_content,
        })
        print(f"      → {len(sec_content)} chars")

    # ── Phase 3: Assembly + Final Review ──
    print(f"\n{'─' * 40}")
    print(f"  Phase 3: Assembly + Final Review")
    print(f"{'─' * 40}")

    all_sections = "\n".join(
        f'<!-- {s.get("id","")}: {s.get("title","")} -->\n<div class="container">\n{html}\n</div>'
        for s, html in zip(sections, sections_html)
    )

    css_prompt = f"Generate <style> CSS for a {len(sections)}-section HTML report. Minimalist, clean typography. Output ONLY <style>...</style>."
    css_html = call_model(model=primary, system=dept_prompt, user=css_prompt,
                          max_tokens=8000, fallback_model=fallback)
    css_clean = _clean_css(css_html)

    final_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Generated Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Montserrat:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>{css_clean}</style>
</head>
<body>
{all_sections}
<footer style="text-align:center;padding:40px;color:#999;font-size:11px;">
  Generated with Adversarial Solver · {datetime.now().strftime('%Y-%m-%d')}
</footer>
</body>
</html>"""

    log["rounds"].append({"round": 5 + len(sections), "model": "system", "type": "assembly", "output": final_html})
    print(f"   → HTML {len(final_html)} chars")

    review_sample = final_html[:2000] + "\n...\n" + final_html[-2000:]
    final_review = call_model(
        model=reviewer, system=reviewer_prompt,
        user=f"Task:\n{task}\n\n{len(sections)} sections, {len(final_html)} chars.\nSample:\n{review_sample}\n\nFinal review:",
        max_tokens=2000, fallback_model=fallback,
    )
    log["rounds"].append({"round": 6 + len(sections), "model": reviewer, "type": "final_review", "output": final_review})

    if tone_checker_enabled:
        tone_result = tone_check(final_html, config_path)
        log["tone_check"] = tone_result
        if not tone_result["passed"]:
            final_review += f"\n\n[Tone Checker]\n" + "\n".join(tone_result["issues"])

    final_status = "PASS" if is_passed(final_review, final_html) else "PENDING_REVIEW"
    log["status"] = final_status
    log["final"] = final_html
    log["total_rounds"] = len(log["rounds"])

    print(f"\n   {'[OK] PASSED' if final_status == 'PASS' else '[WARN]  PENDING_REVIEW'}")
    archive_result(log, dept, final_status, config_path)
    return log


def batch_solve(tasks: List[Dict], config_path: Optional[str] = None) -> Dict:
    """Batch process multiple tasks.

    Args:
        tasks: [{"task": "...", "dept": "marketing", "max_rounds": 3}, ...]
        config_path: Path to config directory

    Returns:
        Summary dict with total/passed/pending counts
    """
    results = []
    for i, t in enumerate(tasks, 1):
        print(f"\n\n{'=' * 60}")
        print(f"  Batch {i}/{len(tasks)}")
        print(f"{'=' * 60}")
        result = adversarial_solve(
            task=t["task"], dept=t["dept"],
            max_rounds=t.get("max_rounds", 3), config_path=config_path,
            mode=t.get("mode"),
        )
        results.append(result)

    summary = {
        "total": len(results),
        "passed": sum(1 for r in results if r["status"] == "PASS"),
        "pending_review": sum(1 for r in results if r["status"] == "PENDING_REVIEW"),
        "results": results,
    }
    print(f"\n{'=' * 60}")
    print(f"  Batch Complete: {summary['passed']}/{summary['total']} passed")
    return summary


def _build_generator_prompt(dept_config: Dict, config: Dict) -> str:
    """Build generator system prompt from config."""
    constitution_path = config.get("constitution_path", "config/constitution.md")
    constitution_text = ""
    try:
        constitution_text = Path(constitution_path).read_text(encoding="utf-8")
        if len(constitution_text) > 3000:
            constitution_text = constitution_text[:3000] + "\n\n[...truncated for context window]"
    except FileNotFoundError:
        pass

    return f"""You are the Generator for: {dept_config.get('name', 'Unknown')}.

Scope: {dept_config.get('scope', 'General content generation')}

# Guidelines
{constitution_text}

# Principles
1. Follow guidelines strictly
2. When uncertain, prioritize core principles
3. Flag cross-department issues explicitly
4. Output structured content (headings / bullets / tables)
"""


def _parse_outline(outline_text: str) -> List[Dict]:
    """Parse sections JSON with truncation resilience. 5 fallback methods."""
    # Method 1: ```json ``` code block
    json_match = re.search(r'```json\s*([\s\S]*?)\s*(?:```|$)', outline_text)
    if json_match:
        try:
            return json.loads(json_match.group(1)).get("sections", [])
        except json.JSONDecodeError:
            pass

    # Method 2: bare JSON
    try:
        start = outline_text.find('{'); end = outline_text.rfind('}')
        if start >= 0 and end > start:
            return json.loads(outline_text[start:end+1]).get("sections", [])
    except json.JSONDecodeError:
        pass

    # Method 3: "sections" array
    sec_match = re.search(r'"sections"\s*:\s*(\[[\s\S]*?\])', outline_text)
    if sec_match:
        try:
            return json.loads(sec_match.group(1))
        except json.JSONDecodeError:
            pass

    # Method 4: individual section objects (truncation resilience)
    sec_objs = re.findall(
        r'\{\s*"id"\s*:\s*"([^"]+)"\s*,\s*"title"\s*:\s*"([^"]+)"\s*,\s*"key_points"\s*:\s*(\[[^\]]*\])',
        outline_text,
    )
    if sec_objs:
        sections = []
        for sid, title, kp_str in sec_objs:
            try:
                key_points = json.loads(kp_str)
            except json.JSONDecodeError:
                key_points = [kp_str]
            sections.append({"id": sid, "title": title, "key_points": key_points})
        if sections:
            print(f"   [WARN]  JSON parse failed — rescued {len(sections)} sections")
            return sections

    # Method 5: loose "id"/"title" pairs
    loose = re.findall(r'"id"\s*:\s*"(\d+)"\s*,\s*"title"\s*:\s*"([^"]+)"', outline_text)
    if loose:
        return [{"id": sid, "title": title, "key_points": []} for sid, title in loose]

    return []


def _clean_css(css_html: str) -> str:
    """Extract clean CSS from model output."""
    md_match = re.search(r'```(?:css)?\s*([\s\S]*?)\s*```', css_html)
    if md_match:
        css_html = md_match.group(1)
    style_match = re.search(r'<style[^>]*>([\s\S]*)</style>', css_html, re.IGNORECASE)
    if style_match:
        css_html = style_match.group(1)
    return css_html.strip()
