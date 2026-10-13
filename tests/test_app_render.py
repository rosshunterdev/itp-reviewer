"""Render the real Streamlit app headlessly and check what the user sees."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src import report, schema

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _findings():
    return [
        schema.Finding("Item 1", "made_up_category", "odd category", "w", "consider x"),
        schema.Finding("Item 2", "hold_witness", "normal", "w", "consider y"),
        schema.Finding("Item 3", "acceptance_criteria", "vague", "w", "consider z"),
    ]


def test_group_findings_puts_unknown_category_under_other():
    grouped = report.group_findings(_findings())
    assert [f.location for f in grouped["other"]] == ["Item 1"]
    assert sum(len(v) for v in grouped.values()) == 3


def test_ui_count_matches_rendered_findings():
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["findings"] = _findings()
    at.run()
    assert not at.exception
    shown = int(at.subheader[0].value.split()[0])
    # every finding is rendered inside an expander labelled "<location> — <obs>"
    rendered = [e for e in at.expander if e.label.startswith("Item ")]
    assert shown == 3
    assert len(rendered) == shown
    assert any("Other" in m.value for m in at.markdown if m.value.startswith("###"))
