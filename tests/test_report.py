from src import report, schema

FINDINGS = [
    schema.Finding("Item 2.1", "acceptance_criteria", "Vague", "Client query", "consider a tolerance"),
    schema.Finding("Item 3.4", "hold_witness", "No hold point", "Risk", "consider adding a hold point"),
]

def test_markdown_groups_by_category_label():
    md = report.to_markdown(FINDINGS)
    assert "Acceptance Criteria" in md
    assert "Hold & Witness Points" in md
    assert "Item 2.1" in md and "consider a tolerance" in md

def test_markdown_empty():
    md = report.to_markdown([])
    assert "no findings" in md.lower()

def test_docx_returns_nonempty_bytes():
    data = report.to_docx(FINDINGS)
    assert isinstance(data, (bytes, bytearray)) and len(data) > 0
