from unittest.mock import MagicMock
from src import generation, gen_schema, config


def _fake_client_returning(items, hold_points):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "generate_itp"
    block.input = {"items": items, "hold_points": hold_points}
    resp = MagicMock()
    resp.content = [block]
    client = MagicMock()
    client.messages.create.return_value = resp
    return client


SAMPLE_ITEMS = [
    {
        "item_number": "1.1",
        "work_package": "Pre-start",
        "inspection_test": "Approved drawings available",
        "acceptance_criteria": "Latest revisions on site",
        "reference": "Contract Docs",
        "frequency": "Before work",
        "inspection_point": "H",
        "contractor_resp": "Site Manager",
        "witness_release": "Principal's Rep",
        "qa_record": "Document register",
    },
    {
        "item_number": "2.1",
        "work_package": "Demolition",
        "inspection_test": "Hazardous materials survey",
        "acceptance_criteria": "Survey complete, no asbestos",
        "reference": "HSW Act 2015",
        "frequency": "Before demolition",
        "inspection_point": "H",
        "contractor_resp": "H&S Manager",
        "witness_release": "Engineer",
        "qa_record": "Survey report",
    },
]

SAMPLE_HPS = [
    {
        "hp_number": "HP-01",
        "itp_item": "1.1",
        "description": "Approved documents before work starts",
    },
    {
        "hp_number": "HP-02",
        "itp_item": "2.1",
        "description": "Hazardous materials clearance before demolition",
    },
]


def test_run_generation_parses_tool_output():
    client = _fake_client_returning(SAMPLE_ITEMS, SAMPLE_HPS)
    items, hps = generation.run_generation("spec text", client=client)
    assert len(items) == 2
    assert isinstance(items[0], gen_schema.ITPItem)
    assert items[0].item_number == "1.1"
    assert items[1].work_package == "Demolition"
    assert len(hps) == 2
    assert isinstance(hps[0], gen_schema.HoldPoint)
    assert hps[0].hp_number == "HP-01"


def test_run_generation_forces_tool():
    client = _fake_client_returning(SAMPLE_ITEMS, SAMPLE_HPS)
    generation.run_generation("spec text", client=client)
    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "tool", "name": "generate_itp"}
    assert kwargs["tools"] == [gen_schema.GENERATE_ITP_TOOL]
    assert kwargs["max_tokens"] == config.GEN_MAX_TOKENS


def test_run_generation_system_prompt_is_author_persona():
    client = _fake_client_returning([], [])
    generation.run_generation("spec text", client=client)
    kwargs = client.messages.create.call_args.kwargs
    system = kwargs["system"].lower()
    assert "itp" in system
    assert "author" in system or "writer" in system or "prepare" in system
    assert "adversarial" not in system


def test_run_generation_includes_spec_in_xml_tags():
    client = _fake_client_returning([], [])
    generation.run_generation("my spec content", client=client)
    kwargs = client.messages.create.call_args.kwargs
    msg = kwargs["messages"][0]["content"]
    assert "<specification>" in msg
    assert "my spec content" in msg
    assert "</specification>" in msg


def test_run_generation_includes_supporting_texts():
    client = _fake_client_returning([], [])
    generation.run_generation(
        "spec",
        supporting_texts=[("building consent", "consent text here")],
        client=client,
    )
    kwargs = client.messages.create.call_args.kwargs
    msg = kwargs["messages"][0]["content"]
    assert "<building_consent>" in msg
    assert "consent text here" in msg


def test_run_generation_no_supporting_texts():
    client = _fake_client_returning([], [])
    generation.run_generation("spec", supporting_texts=None, client=client)
    kwargs = client.messages.create.call_args.kwargs
    msg = kwargs["messages"][0]["content"]
    assert "<specification>" in msg
    assert "<building_consent>" not in msg


def test_run_generation_returns_empty_on_no_tool_block():
    resp = MagicMock()
    resp.content = []
    client = MagicMock()
    client.messages.create.return_value = resp
    items, hps = generation.run_generation("spec", client=client)
    assert items == []
    assert hps == []
