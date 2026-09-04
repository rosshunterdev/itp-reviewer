from src import gen_report, gen_schema

ITEMS = [
    gen_schema.ITPItem(
        item_number="1.1",
        work_package="Pre-start",
        inspection_test="Approved drawings available",
        acceptance_criteria="Latest revisions on site",
        reference="Contract Docs",
        frequency="Before work",
        inspection_point="H",
        contractor_resp="Site Manager",
        witness_release="Principal's Rep",
        qa_record="Document register",
    ),
    gen_schema.ITPItem(
        item_number="2.1",
        work_package="Demolition",
        inspection_test="Hazardous materials survey",
        acceptance_criteria="Survey complete, no asbestos",
        reference="HSW Act 2015",
        frequency="Before demolition",
        inspection_point="H",
        contractor_resp="H&S Manager",
        witness_release="Engineer",
        qa_record="Survey report",
    ),
    gen_schema.ITPItem(
        item_number="2.2",
        work_package="Demolition",
        inspection_test="Demolition methodology review",
        acceptance_criteria="Methodology approved by engineer",
        reference="Contract spec §2110",
        frequency="Before demolition starts",
        inspection_point="R",
        contractor_resp="Site Manager",
        witness_release="Engineer",
        qa_record="Approved methodology",
    ),
]

HPS = [
    gen_schema.HoldPoint("HP-01", "1.1", "Approved documents before work starts"),
    gen_schema.HoldPoint("HP-02", "2.1", "Hazardous materials clearance"),
]


def test_markdown_groups_by_work_package():
    md = gen_report.to_markdown(ITEMS, HPS)
    assert "## Pre-start" in md
    assert "## Demolition" in md
    assert "1.1" in md
    assert "2.1" in md


def test_markdown_includes_all_columns():
    md = gen_report.to_markdown(ITEMS, HPS)
    assert "Approved drawings available" in md
    assert "Latest revisions on site" in md
    assert "Contract Docs" in md
    assert "Before work" in md
    assert "Site Manager" in md
    assert "Document register" in md


def test_markdown_includes_hold_point_register():
    md = gen_report.to_markdown(ITEMS, HPS)
    assert "Hold Point Register" in md
    assert "HP-01" in md
    assert "HP-02" in md


def test_markdown_empty():
    md = gen_report.to_markdown([], [])
    assert "no items" in md.lower() or "No ITP" in md


def test_markdown_shows_item_count():
    md = gen_report.to_markdown(ITEMS, HPS)
    assert "3" in md


def test_docx_returns_nonempty_bytes():
    data = gen_report.to_docx(ITEMS, HPS)
    assert isinstance(data, (bytes, bytearray)) and len(data) > 0


def test_items_to_text_produces_table():
    text = gen_report.items_to_text(ITEMS)
    assert "1.1" in text
    assert "Pre-start" in text
    assert "Approved drawings available" in text
    assert "2.1" in text


def test_items_to_text_empty():
    text = gen_report.items_to_text([])
    assert text == ""
