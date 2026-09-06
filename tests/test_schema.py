from src import schema

def test_categories_exact():
    assert schema.CATEGORIES == [
        "hold_witness", "acceptance_criteria", "standards_reference",
        "responsible_party", "internal_consistency", "duplicates_clutter",
        "proposal_mismatch", "other",
    ]

def test_tool_shape():
    tool = schema.REVIEW_TOOL
    assert tool["name"] == "report_findings"
    props = tool["input_schema"]["properties"]
    assert "findings" in props
    finding_props = props["findings"]["items"]["properties"]
    assert set(finding_props) == {
        "location", "category", "observation", "why_it_matters", "suggested_action"
    }
    assert finding_props["category"]["enum"] == schema.CATEGORIES

def test_finding_dataclass():
    f = schema.Finding("Item 1.1", "hold_witness", "obs", "why", "consider X")
    assert f.category == "hold_witness"
