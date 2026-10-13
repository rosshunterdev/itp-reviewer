"""Rule-based quality checks on model output. No API calls.

Used offline by the eval harness and live by app.py on every run.
"""
import re
from difflib import SequenceMatcher

from src.gen_schema import INSPECTION_POINTS
from src.schema import CATEGORIES

# Directive language the system prompt forbids in suggested_action (see CLAUDE.md "Notes").
DIRECTIVE = re.compile(
    r"\b(must|shall|is required to|needs? to be|you need to|have to|has to|"
    r"do not|don't|never|fix this|this is wrong)\b",
    re.IGNORECASE,
)
DUPLICATE_RATIO = 0.9


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(" ."), b.lower().strip(" .")).ratio()


def lint_findings(findings: list[dict]) -> list[str]:
    """Return human-readable problems; empty list means clean."""
    problems = []
    for i, f in enumerate(findings, 1):
        tag = f"#{i} ({f.get('location') or 'no location'})"
        if f.get("category") not in CATEGORIES:
            problems.append(f"{tag}: invalid category '{f.get('category')}'")
        if not (f.get("location") or "").strip():
            problems.append(f"{tag}: empty location")
        action = f.get("suggested_action") or ""
        match = DIRECTIVE.search(action)
        if match:
            problems.append(f"{tag}: directive language '{match.group(0)}' in suggested_action")
    for i in range(len(findings)):
        for j in range(i + 1, len(findings)):
            a, b = findings[i], findings[j]
            if similarity(a.get("observation", ""), b.get("observation", "")) >= DUPLICATE_RATIO:
                problems.append(f"#{i + 1} and #{j + 1}: near-duplicate findings")
    return problems


def lint_hold_points(items: list[dict], hold_points: list[dict]) -> list[str]:
    """Cross-check a generated ITP against its hold point register."""
    problems = []
    points = {}
    seen_numbers = set()
    for it in items:
        num = (it.get("item_number") or "").strip()
        point = (it.get("inspection_point") or "").strip()
        if num in seen_numbers:
            problems.append(f"item {num}: duplicate item number")
        seen_numbers.add(num)
        points[num] = point
        if point not in INSPECTION_POINTS:
            problems.append(f"item {num}: invalid inspection point '{point}'")

    registered = set()
    seen_hp = set()
    for hp in hold_points:
        hp_num = (hp.get("hp_number") or "").strip()
        ref = (hp.get("itp_item") or "").strip()
        if hp_num in seen_hp:
            problems.append(f"{hp_num}: duplicate hold point number")
        seen_hp.add(hp_num)
        registered.add(ref)
        if ref not in points:
            problems.append(f"{hp_num}: references item {ref}, which is not in the ITP")
        elif points[ref] != "H":
            problems.append(
                f"{hp_num}: references item {ref}, which is '{points[ref]}', not H"
            )

    for num, point in points.items():
        if point == "H" and num not in registered:
            problems.append(f"item {num}: is a Hold point but has no register entry")
    return problems
