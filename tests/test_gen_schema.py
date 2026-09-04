from src import gen_schema


def test_itp_item_dataclass():
    item = gen_schema.ITPItem(
        item_number="1.1",
        work_package="Pre-start / document control",
        inspection_test="Approved-for-construction drawings available",
        acceptance_criteria="Latest approved revisions only",
        reference="Contract Docs; Quality Plan",
        frequency="Before each work package",
        inspection_point="H",
        contractor_resp="Site Manager / QA",
        witness_release="Principal's Rep",
        qa_record="Approved documents register",
    )
    assert item.item_number == "1.1"
    assert item.inspection_point == "H"


def test_hold_point_dataclass():
    hp = gen_schema.HoldPoint(
        hp_number="HP-01",
        itp_item="1.1",
        description="Approved documents before work package starts",
    )
    assert hp.hp_number == "HP-01"
    assert hp.itp_item == "1.1"


def test_inspection_points():
    assert gen_schema.INSPECTION_POINTS == ["H", "W", "S", "R"]


def test_tool_shape():
    tool = gen_schema.GENERATE_ITP_TOOL
    assert tool["name"] == "generate_itp"
    props = tool["input_schema"]["properties"]
    assert "items" in props
    assert "hold_points" in props
    item_props = props["items"]["items"]["properties"]
    assert set(item_props) == {
        "item_number", "work_package", "inspection_test",
        "acceptance_criteria", "reference", "frequency",
        "inspection_point", "contractor_resp", "witness_release",
        "qa_record",
    }
    assert item_props["inspection_point"]["enum"] == ["H", "W", "S", "R"]
    hp_props = props["hold_points"]["items"]["properties"]
    assert set(hp_props) == {"hp_number", "itp_item", "description"}
