# ITP Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an ITP generation mode that takes a project specification PDF and produces a structured draft ITP report, with a bridge button to run the existing reviewer on the generated output.

**Architecture:** Single-pass direct-context generation using the same forced-tool-use pattern as the existing reviewer. New generation modules (`gen_schema`, `generation`, `gen_report`) mirror the review modules' structure. The Streamlit UI gets a tab selector to switch between Generate and Review modes.

**Tech Stack:** Python, Anthropic SDK (forced tool use), Streamlit (tabs), python-docx (docx report output)

**Spec:** `docs/superpowers/specs/2026-09-04-itp-generation-design.md`

## Global Constraints

- Model: `claude-sonnet-5` (from `src/config.py`)
- All API calls use forced tool use (`tool_choice` pinned to tool name)
- Advisory phrasing in all user-facing output
- Tests run with `.venv/Scripts/pytest`
- Conventional commits, stage explicit paths

---

### Task 1: Generation Schema

**Files:**
- Create: `src/gen_schema.py`
- Test: `tests/test_gen_schema.py`

**Interfaces:**
- Consumes: nothing (standalone)
- Produces:
  - `ITPItem` dataclass with fields: `item_number: str`, `work_package: str`, `inspection_test: str`, `acceptance_criteria: str`, `reference: str`, `frequency: str`, `inspection_point: str`, `contractor_resp: str`, `witness_release: str`, `qa_record: str`
  - `HoldPoint` dataclass with fields: `hp_number: str`, `itp_item: str`, `description: str`
  - `GENERATE_ITP_TOOL: dict` — forced tool definition with `name = "generate_itp"`
  - `INSPECTION_POINTS: list[str]` — `["H", "W", "S", "R"]`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_gen_schema.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/pytest tests/test_gen_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.gen_schema'`

- [ ] **Step 3: Write the implementation**

Create `src/gen_schema.py`:

```python
from dataclasses import dataclass

INSPECTION_POINTS = ["H", "W", "S", "R"]


@dataclass
class ITPItem:
    item_number: str
    work_package: str
    inspection_test: str
    acceptance_criteria: str
    reference: str
    frequency: str
    inspection_point: str
    contractor_resp: str
    witness_release: str
    qa_record: str


@dataclass
class HoldPoint:
    hp_number: str
    itp_item: str
    description: str


GENERATE_ITP_TOOL = {
    "name": "generate_itp",
    "description": (
        "Generate a complete Inspection Test Plan from the project specification. "
        "Return all ITP items grouped by work package, plus hold point register entries "
        "for every item designated as a hold point (H). Call this exactly once with the "
        "full ITP."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "description": "All ITP inspection/test items, ordered by work package.",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_number": {
                            "type": "string",
                            "description": "Sequential item number, e.g. '1.1', '2.3'.",
                        },
                        "work_package": {
                            "type": "string",
                            "description": "Work package or activity name, e.g. 'Pre-start / document control'.",
                        },
                        "inspection_test": {
                            "type": "string",
                            "description": "What is inspected, tested, or checked.",
                        },
                        "acceptance_criteria": {
                            "type": "string",
                            "description": "Specific, measurable criteria for pass/fail.",
                        },
                        "reference": {
                            "type": "string",
                            "description": "Standards, codes, spec sections, or contract references.",
                        },
                        "frequency": {
                            "type": "string",
                            "description": "When or how often the inspection/test occurs.",
                        },
                        "inspection_point": {
                            "type": "string",
                            "enum": INSPECTION_POINTS,
                            "description": "H = Hold, W = Witness, S = Surveillance, R = Review.",
                        },
                        "contractor_resp": {
                            "type": "string",
                            "description": "Contractor role responsible for this item.",
                        },
                        "witness_release": {
                            "type": "string",
                            "description": "Who witnesses or releases the hold/witness point.",
                        },
                        "qa_record": {
                            "type": "string",
                            "description": "Evidence or documentation required.",
                        },
                    },
                    "required": [
                        "item_number", "work_package", "inspection_test",
                        "acceptance_criteria", "reference", "frequency",
                        "inspection_point", "contractor_resp", "witness_release",
                        "qa_record",
                    ],
                },
            },
            "hold_points": {
                "type": "array",
                "description": "Hold point register entries for every H-designated item.",
                "items": {
                    "type": "object",
                    "properties": {
                        "hp_number": {
                            "type": "string",
                            "description": "Hold point number, e.g. 'HP-01'.",
                        },
                        "itp_item": {
                            "type": "string",
                            "description": "Cross-reference to the ITP item number.",
                        },
                        "description": {
                            "type": "string",
                            "description": "What must be released before work proceeds.",
                        },
                    },
                    "required": ["hp_number", "itp_item", "description"],
                },
            },
        },
        "required": ["items", "hold_points"],
    },
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/pytest tests/test_gen_schema.py -v`
Expected: all 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/gen_schema.py tests/test_gen_schema.py
git commit -m "feat: add generation schema (ITPItem, HoldPoint, tool definition)"
```

---

### Task 2: Generation Module (Prompt + API Call)

**Files:**
- Create: `src/generation.py`
- Modify: `src/config.py`
- Test: `tests/test_generation.py`

**Interfaces:**
- Consumes: `gen_schema.ITPItem`, `gen_schema.HoldPoint`, `gen_schema.GENERATE_ITP_TOOL` from Task 1
- Produces:
  - `generation_system_prompt() -> str`
  - `generation_user_message(spec_text: str, supporting_texts: list[tuple[str, str]] | None = None) -> str` — `supporting_texts` is a list of `(label, text)` pairs, e.g. `[("building consent", "..."), ("drawings", "...")]`
  - `run_generation(spec_text: str, supporting_texts: list[tuple[str, str]] | None = None, client=None) -> tuple[list[gen_schema.ITPItem], list[gen_schema.HoldPoint]]`
  - `GEN_MAX_TOKENS: int` in `config.py` set to `16000`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_generation.py`:

```python
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
```

- [ ] **Step 2: Add GEN_MAX_TOKENS to config**

Add to the end of `src/config.py`:

```python
GEN_MAX_TOKENS = 16000
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/Scripts/pytest tests/test_generation.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.generation'`

- [ ] **Step 4: Write the implementation**

Create `src/generation.py`:

```python
import re
from src import config, gen_schema


ITP_EXAMPLES = """
Here are representative rows from a real, approved ITP to show the expected format, level of detail, and column structure. Use these as a guide for the quality and specificity of your output:

Item | Work Package / Activity | Inspection / Test / Check | Acceptance Criteria | Reference | Frequency / Timing | Inspection Point | Contractor Responsibility | Witness / Release By | QA Record / Evidence
1.1 | Pre-start / document control | Approved-for-construction drawings, specifications, ITP, methodology and JSA available at workface | Latest approved revisions only; superseded documents removed from workface | Contract Docs; approved drawings; Quality Plan | Before each work package | H | Site Manager / QA | Principal's Rep as applicable | Approved documents / document register
2.1 | Survey and set-out | Verify survey control, datum and benchmark against approved design | Survey control verified; set-out to approved coordinates/levels; NZVD2016 where required | Contract drawings; survey specification | Initial set-out and each structure/pipeline | H | Surveyor | QA / Engineer as required | Set-out sheet / survey file
2.2 | Survey and set-out | Check location, line, level and offsets before excavation / installation | Within drawing/specification tolerances | Approved drawings; TCC IDC | Each structure / pipeline section | W | Surveyor / Site Engineer | Engineer / Council as notified | Pre-install survey record
5.3 | Earthworks / cohesive fill | Compaction / shear vane / air voids testing | Air voids: max 12% single test, average ≤10%; undrained shear strength ≥120 kPa or as specified | Contract §5.3.2 | Min. 1 set / 500 m³ plus random testing as specified | H | IANZ Lab / QA | Geotechnical Engineer | Lab / field test results
8.1 | Concrete works | Pre-pour inspection: excavation/formwork, reinforcement, cover, cast-ins, penetrations | Matches approved structural drawings; reinforcement and cover correct; formwork stable and clean | Contract §9 Reinforced Concrete; NZS 3109; approved drawings | Each pour | H | Site Engineer / QA | Engineer / structural reviewer as required | Pre-pour checklist, photos
9.3 | Gravity pipelines | Line, level and gradient during laying | Pipe laser / survey used; no backfall; within specified line/level tolerances | TCC IDC; Contract §7.4 / §7.8 | Each pipe / reach | W | Surveyor / Site Engineer | Engineer / Council as required | Pipe laying sheet / survey data
10.3 | Pressure / rising main | Hydrostatic pressure test | Test pressure, duration and acceptance criteria comply with Contract / Council requirements | Contract testing specification; TCC IDC | Each test section | H | Contractor / test specialist | Engineer / Council | Pressure test certificate / chart
15.3 | Close-out | Compile QA dossier / handover records | All ITPs closed; hold points released; test results passed; NCRs closed/accepted | Contract Quality Plan / handover requirements | Before Practical Completion | H | QA Manager / Project Manager | Principal's Rep / Engineer | QA dossier / handover index
""".strip()


def generation_system_prompt() -> str:
    return (
        "You are an experienced construction ITP (Inspection Test Plan) author. "
        "Your job is to read a project specification and produce a thorough, "
        "standards-aware ITP that covers every activity requiring inspection, "
        "testing, or verification.\n\n"
        "For each work package or activity in the specification, generate ITP items "
        "with these columns:\n"
        "- Item number (sequential within each work package, e.g. 1.1, 1.2, 2.1)\n"
        "- Work package / activity name\n"
        "- Inspection / test / check — what is inspected or tested\n"
        "- Acceptance criteria — specific, measurable, never vague. Include actual "
        "values, tolerances, or standards thresholds where the spec provides them.\n"
        "- Reference — cite specific standards (e.g. NZS 3109), spec section numbers "
        "(e.g. Contract §7.4), codes, or contract requirements. Never leave blank.\n"
        "- Frequency / timing — when or how often\n"
        "- Inspection point — H (Hold: work stops until released), W (Witness: "
        "notified and may attend), S (Surveillance: routine monitoring), "
        "R (Review: document review only). Assign based on criticality:\n"
        "  - H for safety-critical, structural, concealment, or compliance milestones\n"
        "  - W for quality-significant items that benefit from third-party observation\n"
        "  - S for routine ongoing monitoring\n"
        "  - R for document/certification checks\n"
        "- Contractor responsibility — the role responsible\n"
        "- Witness / release by — who witnesses or releases\n"
        "- QA record / evidence — what documentation is produced\n\n"
        "Also generate a hold point register entry for every item designated H.\n\n"
        "Be thorough — cover pre-start, each trade/discipline in the spec, testing, "
        "and close-out. Do not skip sections of the specification. Do not invent "
        "standards that are not referenced in the specification or examples. "
        "Report the full ITP by calling the generate_itp tool exactly once."
    )


def generation_user_message(
    spec_text: str,
    supporting_texts: list[tuple[str, str]] | None = None,
) -> str:
    parts = [
        "Generate a complete ITP from the following project specification. "
        "Use the example ITP rows below as a guide for format, level of detail, "
        "and the kind of acceptance criteria expected.",
        f"<itp_examples>\n{ITP_EXAMPLES}\n</itp_examples>",
        f"<specification>\n{spec_text}\n</specification>",
    ]
    if supporting_texts:
        for label, text in supporting_texts:
            tag = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
            parts.append(f"<{tag}>\n{text}\n</{tag}>")
    return "\n\n".join(parts)


def _get_client():
    import anthropic
    return anthropic.Anthropic()


def run_generation(
    spec_text: str,
    supporting_texts: list[tuple[str, str]] | None = None,
    client=None,
) -> tuple[list[gen_schema.ITPItem], list[gen_schema.HoldPoint]]:
    client = client or _get_client()
    resp = client.messages.create(
        model=config.MODEL,
        max_tokens=config.GEN_MAX_TOKENS,
        system=generation_system_prompt(),
        tools=[gen_schema.GENERATE_ITP_TOOL],
        tool_choice={"type": "tool", "name": "generate_itp"},
        messages=[
            {
                "role": "user",
                "content": generation_user_message(spec_text, supporting_texts),
            }
        ],
    )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "generate_itp":
            items = [
                gen_schema.ITPItem(
                    item_number=it.get("item_number", ""),
                    work_package=it.get("work_package", ""),
                    inspection_test=it.get("inspection_test", ""),
                    acceptance_criteria=it.get("acceptance_criteria", ""),
                    reference=it.get("reference", ""),
                    frequency=it.get("frequency", ""),
                    inspection_point=it.get("inspection_point", "H"),
                    contractor_resp=it.get("contractor_resp", ""),
                    witness_release=it.get("witness_release", ""),
                    qa_record=it.get("qa_record", ""),
                )
                for it in block.input.get("items", [])
            ]
            hold_points = [
                gen_schema.HoldPoint(
                    hp_number=hp.get("hp_number", ""),
                    itp_item=hp.get("itp_item", ""),
                    description=hp.get("description", ""),
                )
                for hp in block.input.get("hold_points", [])
            ]
            return items, hold_points
    return [], []
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/Scripts/pytest tests/test_generation.py -v`
Expected: all 7 tests PASS

- [ ] **Step 6: Run full suite to check nothing broke**

Run: `.venv/Scripts/pytest -v`
Expected: all existing tests still PASS plus 7 new

- [ ] **Step 7: Commit**

```bash
git add src/config.py src/generation.py tests/test_generation.py
git commit -m "feat: add ITP generation module (prompt, API call, parsing)"
```

---

### Task 3: Generation Report

**Files:**
- Create: `src/gen_report.py`
- Test: `tests/test_gen_report.py`

**Interfaces:**
- Consumes: `gen_schema.ITPItem`, `gen_schema.HoldPoint` from Task 1
- Produces:
  - `to_markdown(items: list[gen_schema.ITPItem], hold_points: list[gen_schema.HoldPoint]) -> str`
  - `to_docx(items: list[gen_schema.ITPItem], hold_points: list[gen_schema.HoldPoint]) -> bytes`
  - `items_to_text(items: list[gen_schema.ITPItem]) -> str` — plain-text table representation used by the "Review this draft?" bridge

- [ ] **Step 1: Write the failing tests**

Create `tests/test_gen_report.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/pytest tests/test_gen_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.gen_report'`

- [ ] **Step 3: Write the implementation**

Create `src/gen_report.py`:

```python
import io
from collections import OrderedDict
from src import gen_schema


COLUMNS = [
    ("Item", "item_number"),
    ("Work Package / Activity", "work_package"),
    ("Inspection / Test / Check", "inspection_test"),
    ("Acceptance Criteria", "acceptance_criteria"),
    ("Reference", "reference"),
    ("Frequency / Timing", "frequency"),
    ("Inspection Point", "inspection_point"),
    ("Contractor Responsibility", "contractor_resp"),
    ("Witness / Release By", "witness_release"),
    ("QA Record / Evidence", "qa_record"),
]


def _group_by_work_package(
    items: list[gen_schema.ITPItem],
) -> OrderedDict[str, list[gen_schema.ITPItem]]:
    groups: OrderedDict[str, list[gen_schema.ITPItem]] = OrderedDict()
    for item in items:
        groups.setdefault(item.work_package, []).append(item)
    return groups


def items_to_text(items: list[gen_schema.ITPItem]) -> str:
    if not items:
        return ""
    header = " | ".join(label for label, _ in COLUMNS)
    lines = [header]
    for item in items:
        row = " | ".join(getattr(item, field) for _, field in COLUMNS)
        lines.append(row)
    return "\n".join(lines)


def to_markdown(
    items: list[gen_schema.ITPItem],
    hold_points: list[gen_schema.HoldPoint],
) -> str:
    if not items:
        return "# Generated ITP\n\nNo ITP items were generated.\n"
    lines = [
        "# Generated ITP",
        "",
        f"{len(items)} item(s) across "
        f"{len(_group_by_work_package(items))} work package(s).",
        "",
    ]
    groups = _group_by_work_package(items)
    for wp, wp_items in groups.items():
        lines.append(f"## {wp}")
        lines.append("")
        for item in wp_items:
            lines.append(f"### {item.item_number} — {item.inspection_test}")
            lines.append(f"- **Acceptance Criteria:** {item.acceptance_criteria}")
            lines.append(f"- **Reference:** {item.reference}")
            lines.append(f"- **Frequency:** {item.frequency}")
            lines.append(f"- **Inspection Point:** {item.inspection_point}")
            lines.append(f"- **Contractor Responsibility:** {item.contractor_resp}")
            lines.append(f"- **Witness / Release By:** {item.witness_release}")
            lines.append(f"- **QA Record:** {item.qa_record}")
            lines.append("")
    if hold_points:
        lines.append("## Hold Point Register")
        lines.append("")
        for hp in hold_points:
            lines.append(
                f"- **{hp.hp_number}** (Item {hp.itp_item}): {hp.description}"
            )
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def to_docx(
    items: list[gen_schema.ITPItem],
    hold_points: list[gen_schema.HoldPoint],
) -> bytes:
    import docx

    document = docx.Document()
    document.add_heading("Generated ITP", level=0)
    if not items:
        document.add_paragraph("No ITP items were generated.")
    else:
        document.add_paragraph(
            f"{len(items)} item(s) across "
            f"{len(_group_by_work_package(items))} work package(s)."
        )
        groups = _group_by_work_package(items)
        for wp, wp_items in groups.items():
            document.add_heading(wp, level=1)
            for item in wp_items:
                document.add_heading(
                    f"{item.item_number} — {item.inspection_test}", level=2
                )
                document.add_paragraph(
                    f"Acceptance Criteria: {item.acceptance_criteria}"
                )
                document.add_paragraph(f"Reference: {item.reference}")
                document.add_paragraph(f"Frequency: {item.frequency}")
                document.add_paragraph(f"Inspection Point: {item.inspection_point}")
                document.add_paragraph(
                    f"Contractor Responsibility: {item.contractor_resp}"
                )
                document.add_paragraph(
                    f"Witness / Release By: {item.witness_release}"
                )
                document.add_paragraph(f"QA Record: {item.qa_record}")
        if hold_points:
            document.add_heading("Hold Point Register", level=1)
            for hp in hold_points:
                document.add_paragraph(
                    f"{hp.hp_number} (Item {hp.itp_item}): {hp.description}"
                )
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/pytest tests/test_gen_report.py -v`
Expected: all 8 tests PASS

- [ ] **Step 5: Run full suite**

Run: `.venv/Scripts/pytest -v`
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/gen_report.py tests/test_gen_report.py
git commit -m "feat: add generation report module (markdown, docx, text bridge)"
```

---

### Task 4: Streamlit UI — Generate Mode + Review Bridge

**Files:**
- Modify: `app.py`

**Interfaces:**
- Consumes:
  - `generation.run_generation(spec_text, supporting_texts, client) -> tuple[list[ITPItem], list[HoldPoint]]` from Task 2
  - `gen_report.to_markdown(items, hold_points) -> str` from Task 3
  - `gen_report.to_docx(items, hold_points) -> bytes` from Task 3
  - `gen_report.items_to_text(items) -> str` from Task 3
  - `review.run_review(itp_text, proposal_text, client) -> list[Finding]` (existing)
  - `report.to_markdown(findings) -> str` (existing)
  - `report.to_docx(findings) -> bytes` (existing)
  - `parsing.parse(filename, data) -> ParsedDoc` (existing)
  - `schema.CATEGORIES`, `schema.CATEGORY_LABELS` (existing)
- Produces: updated Streamlit UI with Generate / Review tabs

- [ ] **Step 1: Read the current `app.py` to confirm its state**

Read `app.py` before modifying.

- [ ] **Step 2: Rewrite `app.py` with tab-based UI**

Replace the full contents of `app.py` with the following. The Review tab preserves all existing behaviour exactly. The Generate tab adds the new flow.

```python
import os
import streamlit as st
from src import parsing, review, report, schema
from src import generation, gen_report, gen_schema

st.set_page_config(page_title="ITP Reviewer", layout="wide")
st.title("ITP Reviewer")

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

tab_generate, tab_review = st.tabs(["Generate ITP", "Review ITP"])


def _safe_parse(f, label):
    try:
        return parsing.parse(f.name, f.getvalue())
    except parsing.UnsupportedFormat as e:
        st.error(f"{label}: {e}")
        return None


# ── Generate tab ──────────────────────────────────────────────────────

with tab_generate:
    st.caption(
        "Generate a draft ITP from a project specification. "
        "Findings are advisory."
    )

    with st.expander("How to use this"):
        st.markdown(
            """
1. **Upload the project specification** — the PDF spec that describes
   the work to be done (e.g. a Masterspec document).
2. **Optionally add supporting documents** — building consent, drawings,
   or an engineer's spec. These give the generator extra context.
3. **Open the preview** to confirm the text came through cleanly.
4. **Click Generate.** The tool reads the spec and produces a draft ITP
   with inspection items, hold/witness points, and acceptance criteria.
5. **Download the report** to review and refine.
6. **Click "Review this draft?"** to run the adversarial QA reviewer on
   the generated ITP and catch any gaps.

⚠️ The generated ITP is a **starting draft** — always review and refine
with your own engineering judgement before use.
"""
        )

    spec_file = st.file_uploader(
        "Project specification (required)",
        type=["pdf", "docx", "xlsx"],
        key="gen_spec",
    )
    support_files = st.file_uploader(
        "Supporting documents (optional — building consent, drawings, engineer's spec)",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        key="gen_support",
    )

    spec_doc = None
    if spec_file:
        spec_doc = _safe_parse(spec_file, "Specification")
        if spec_doc:
            for w in spec_doc.warnings:
                st.warning(f"Specification: {w}")
            with st.expander(
                "Preview parsed specification (check text fidelity)"
            ):
                st.text(spec_doc.preview[:20000])

    support_docs = []
    for sf in support_files:
        sd = _safe_parse(sf, sf.name)
        if sd:
            support_docs.append((sf.name, sd))
            with st.expander(f"Preview: {sf.name}"):
                st.text(sd.preview[:10000])

    if "gen_items" not in st.session_state:
        st.session_state["gen_items"] = None
        st.session_state["gen_hps"] = None

    if st.button("Generate ITP", type="primary", disabled=spec_doc is None):
        try:
            supporting_texts = (
                [(name, sd.text) for name, sd in support_docs]
                if support_docs
                else None
            )
            with st.spinner("Generating ITP from specification…"):
                items, hps = generation.run_generation(
                    spec_doc.text, supporting_texts
                )
            st.session_state["gen_items"] = items
            st.session_state["gen_hps"] = hps
        except Exception as e:
            st.error(
                "Generation could not be completed. Check your "
                "ANTHROPIC_API_KEY and network connection, then try again."
                f"\n\nDetails: {e}"
            )

    if st.session_state.get("gen_items") is not None:
        items = st.session_state["gen_items"]
        hps = st.session_state["gen_hps"]
        if not items:
            st.warning("No ITP items were generated.")
        else:
            st.subheader(f"{len(items)} item(s) generated")

            groups = {}
            for item in items:
                groups.setdefault(item.work_package, []).append(item)

            for wp, wp_items in groups.items():
                st.markdown(f"### {wp} ({len(wp_items)})")
                for item in wp_items:
                    label = f"{item.item_number} — {item.inspection_test}"
                    with st.expander(label):
                        st.markdown(
                            f"**Acceptance Criteria:** {item.acceptance_criteria}"
                        )
                        st.markdown(f"**Reference:** {item.reference}")
                        st.markdown(f"**Frequency:** {item.frequency}")
                        st.markdown(
                            f"**Inspection Point:** {item.inspection_point}"
                        )
                        st.markdown(
                            f"**Contractor Responsibility:** "
                            f"{item.contractor_resp}"
                        )
                        st.markdown(
                            f"**Witness / Release By:** {item.witness_release}"
                        )
                        st.markdown(f"**QA Record:** {item.qa_record}")

            if hps:
                st.markdown("### Hold Point Register")
                for hp in hps:
                    st.markdown(
                        f"- **{hp.hp_number}** (Item {hp.itp_item}): "
                        f"{hp.description}"
                    )

            st.download_button(
                "Download markdown report",
                gen_report.to_markdown(items, hps),
                file_name="generated_itp.md",
                mime="text/markdown",
            )
            st.download_button(
                "Download Word report",
                gen_report.to_docx(items, hps),
                file_name="generated_itp.docx",
                mime="application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",
            )

            # ── Review bridge ─────────────────────────────────────
            st.divider()

            if "gen_review_findings" not in st.session_state:
                st.session_state["gen_review_findings"] = None

            if st.button("Review this draft?"):
                try:
                    itp_text = gen_report.items_to_text(items)
                    with st.spinner("Running adversarial review on generated ITP…"):
                        findings = review.run_review(itp_text)
                    st.session_state["gen_review_findings"] = findings
                except Exception as e:
                    st.error(
                        "Review could not be completed. "
                        f"Details: {e}"
                    )

            if st.session_state.get("gen_review_findings") is not None:
                findings = st.session_state["gen_review_findings"]
                if not findings:
                    st.success("No review findings — the generated ITP looks solid.")
                else:
                    st.subheader(f"{len(findings)} review finding(s)")
                    by_cat = {
                        c: [f for f in findings if f.category == c]
                        for c in schema.CATEGORIES
                    }
                    for cat in schema.CATEGORIES:
                        cat_items = by_cat[cat]
                        if not cat_items:
                            continue
                        st.markdown(
                            f"#### {schema.CATEGORY_LABELS[cat]} "
                            f"({len(cat_items)})"
                        )
                        for f in cat_items:
                            with st.expander(
                                f"{f.location} — {f.observation[:60]}"
                            ):
                                st.markdown(f"**Observation:** {f.observation}")
                                st.markdown(
                                    f"**Why it matters:** {f.why_it_matters}"
                                )
                                st.markdown(
                                    f"**Suggested action:** {f.suggested_action}"
                                )
                    st.download_button(
                        "Download review report (markdown)",
                        report.to_markdown(findings),
                        file_name="generated_itp_review.md",
                        mime="text/markdown",
                        key="gen_review_md",
                    )
                    st.download_button(
                        "Download review report (Word)",
                        report.to_docx(findings),
                        file_name="generated_itp_review.docx",
                        mime="application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document",
                        key="gen_review_docx",
                    )


# ── Review tab ────────────────────────────────────────────────────────

with tab_review:
    st.caption(
        "Adversarial QA review of a draft Inspection Test Plan. "
        "Findings are advisory."
    )

    with st.expander("How to use this"):
        st.markdown(
            """
1. **Upload your draft ITP** — Excel, PDF, or Word. Optionally add the
   matching proposal/scope to cross-check the two against each other.
2. **Open the preview** to confirm the table came through cleanly before
   reviewing.
3. **Click Review.** The tool reads the ITP the way an adversarial QA
   reviewer would and lists things worth a second look.
4. **Each finding** says what it saw, why it matters, and a suggested
   action. Download a report to share or file.

⚠️ Findings are **advisory, not pass/fail** — prompts for a qualified
reviewer to consider. Always apply your own engineering judgement.
"""
        )

    itp_file = st.file_uploader(
        "ITP file (required)",
        type=["xlsx", "pdf", "docx", "doc"],
        key="review_itp",
    )
    proposal_file = st.file_uploader(
        "Proposal / scope of works (optional)",
        type=["xlsx", "pdf", "docx", "doc"],
        key="review_proposal",
    )

    itp_doc = proposal_doc = None
    if itp_file:
        itp_doc = _safe_parse(itp_file, "ITP")
        if itp_doc:
            for w in itp_doc.warnings:
                st.warning(f"ITP: {w}")
            with st.expander(
                "Preview parsed ITP text (check table fidelity before reviewing)"
            ):
                st.text(itp_doc.preview[:20000])

    if proposal_file:
        proposal_doc = _safe_parse(proposal_file, "Proposal")
        if proposal_doc:
            with st.expander("Preview parsed proposal text"):
                st.text(proposal_doc.preview[:20000])

    mode = (
        "Cross-check (ITP vs proposal)" if proposal_doc else "Standalone ITP review"
    )
    st.info(f"Mode: {mode}")

    if "findings" not in st.session_state:
        st.session_state["findings"] = None

    if st.button("Review", type="primary", disabled=itp_doc is None):
        try:
            with st.spinner("Running adversarial review…"):
                findings = review.run_review(
                    itp_doc.text,
                    proposal_doc.text if proposal_doc else None,
                )
            st.session_state["findings"] = findings
        except Exception as e:
            st.error(
                "The review could not be completed. Check your "
                "ANTHROPIC_API_KEY and network connection, then try again."
                f"\n\nDetails: {e}"
            )

    if st.session_state.get("findings") is not None:
        findings = st.session_state["findings"]
        if not findings:
            st.success("No findings identified.")
        else:
            st.subheader(f"{len(findings)} finding(s)")
            by_cat = {
                c: [f for f in findings if f.category == c]
                for c in schema.CATEGORIES
            }
            for cat in schema.CATEGORIES:
                cat_items = by_cat[cat]
                if not cat_items:
                    continue
                st.markdown(
                    f"### {schema.CATEGORY_LABELS[cat]} ({len(cat_items)})"
                )
                for f in cat_items:
                    with st.expander(
                        f"{f.location} — {f.observation[:60]}"
                    ):
                        st.markdown(f"**Observation:** {f.observation}")
                        st.markdown(f"**Why it matters:** {f.why_it_matters}")
                        st.markdown(
                            f"**Suggested action:** {f.suggested_action}"
                        )
            st.download_button(
                "Download markdown report",
                report.to_markdown(findings),
                file_name="itp_review.md",
                mime="text/markdown",
            )
            st.download_button(
                "Download Word report",
                report.to_docx(findings),
                file_name="itp_review.docx",
                mime="application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",
            )
```

- [ ] **Step 3: Run full test suite**

Run: `.venv/Scripts/pytest -v`
Expected: all tests PASS (app.py isn't unit-tested directly — the modules it calls are)

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: add Generate ITP tab with review bridge"
```

---

### Task 5: Live Validation

**Files:** none created or modified — this is a manual validation task

**Interfaces:**
- Consumes: everything from Tasks 1–4

- [ ] **Step 1: Start the app**

Run: `.venv/Scripts/streamlit run app.py`

- [ ] **Step 2: Test the Generate tab — upload the Waitomo spec**

Upload `docs/new-download/BC250324_-SPECIFICATIONS_-_FINAL_SET..pdf` as the project specification. Optionally upload the building consent PDF as a supporting document.

Verify:
- Spec preview shows clean text with section numbers
- Generate button is enabled

- [ ] **Step 3: Run generation**

Click Generate ITP. Wait for completion (~30–60 seconds).

Verify:
- ITP items are displayed, grouped by work package
- Items cover the spec's sections (demolition, groundwork, carpentry, planting)
- Acceptance criteria are specific, not vague
- Standards references match what's in the spec
- Hold point register is populated
- Download buttons produce valid markdown and docx files

- [ ] **Step 4: Test the review bridge**

Click "Review this draft?" on the generated ITP.

Verify:
- Review findings appear below the generated ITP
- Findings are categorized and advisory
- Both review download buttons work

- [ ] **Step 5: Test the Review tab still works**

Switch to the Review tab. Upload an existing ITP (e.g. `GT_Civil_Riverside_WWPS_Civil_ITP_Template.xlsx`). Click Review.

Verify:
- Existing review functionality works exactly as before
- No regressions

- [ ] **Step 6: Commit any fixes**

If any fixes were needed, commit them:

```bash
git add <fixed files>
git commit -m "fix: <description of what was fixed during validation>"
```

- [ ] **Step 7: Update session docs**

Update `SESSION_LOG.md`, `HANDOVER.md`, and `DECISIONS.md` with:
- What was built this session
- Decisions made (single-pass, report-first, tab-based UI)
- Validation results
- Next steps (xlsx export, auto-apply fixes)

```bash
git add SESSION_LOG.md HANDOVER.md DECISIONS.md
git commit -m "docs: session 3 close-out (generation feature, validation)"
```
