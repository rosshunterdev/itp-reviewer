"""Checks that run on live model output (see app.py), including failure cases."""
from evals.checks import lint_findings, lint_hold_points


def _item(num="1.1", point="H"):
    return {"item_number": num, "inspection_point": point}


def _hp(num="HP-01", item="1.1"):
    return {"hp_number": num, "itp_item": item}


def test_consistent_register_is_clean():
    items = [_item("1.1", "H"), _item("1.2", "W"), _item("2.1", "H")]
    hps = [_hp("HP-01", "1.1"), _hp("HP-02", "2.1")]
    assert lint_hold_points(items, hps) == []


def test_hold_item_missing_from_register_is_flagged():
    problems = lint_hold_points([_item("1.1", "H"), _item("2.1", "H")], [_hp("HP-01", "1.1")])
    assert problems == ["item 2.1: is a Hold point but has no register entry"]


def test_register_entry_for_unknown_item_is_flagged():
    problems = lint_hold_points([_item("1.1", "H")], [_hp("HP-01", "1.1"), _hp("HP-02", "9.9")])
    assert any("HP-02" in p and "not in the ITP" in p for p in problems)


def test_register_entry_for_non_hold_item_is_flagged():
    problems = lint_hold_points([_item("1.1", "W")], [_hp("HP-01", "1.1")])
    assert any("HP-01" in p and "not H" in p for p in problems)


def test_invalid_inspection_point_and_duplicates_are_flagged():
    items = [_item("1.1", "X"), _item("1.1", "H")]
    hps = [_hp("HP-01", "1.1"), _hp("HP-01", "1.1")]
    problems = lint_hold_points(items, hps)
    assert any("invalid inspection point 'X'" in p for p in problems)
    assert any("duplicate item number" in p for p in problems)
    assert any("duplicate hold point number" in p for p in problems)


def test_missing_fields_do_not_crash():
    # A model response with empty/absent fields should produce problems, not a traceback.
    problems = lint_hold_points([{}], [{}])
    assert problems  # something is flagged


def test_empty_generation_is_clean():
    assert lint_hold_points([], []) == []


def test_lint_findings_flags_malformed_live_finding():
    bad = {"location": "", "category": "not_a_category", "observation": "x",
           "why_it_matters": "y", "suggested_action": "You must fix this"}
    problems = lint_findings([bad])
    assert len(problems) == 3
