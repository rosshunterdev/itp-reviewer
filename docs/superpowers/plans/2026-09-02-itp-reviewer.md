# ITP Reviewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Streamlit tool that reviews a draft ITP (Inspection Test Plan) as a strict adversarial QA auditor and outputs categorized, advisory findings.

**Architecture:** Single-page Streamlit UI over focused modules — `parsing` (extension dispatch → table-preserving text + preview), `prompts` (adversarial system prompt + XML-tagged user message), `schema` (forced tool-use definition + Finding/Category), `review` (Anthropic call forcing the tool), `report` (findings → markdown/docx). One synchronous LLM call per review, direct-context (no RAG).

**Tech Stack:** Python 3.14, Streamlit, `anthropic` SDK, `openpyxl` (xlsx), `pdfplumber` (pdf), `python-docx` (docx read + docx report), `pytest`.

**Spec:** `docs/superpowers/specs/2026-09-02-itp-reviewer-design.md`

## Global Constraints

- Model constant: `claude-sonnet-5` (current Claude Sonnet). Single configurable constant in `src/config.py`.
- Structured output ONLY via forced tool-use (`tool_choice` forcing the tool). Never parse prose JSON.
- Every `suggested_action` uses advisory phrasing ("consider…", "it may be worth…") — never directive ("must fix"). Product requirement, enforced in prompt AND asserted in tests.
- Adversarial QA-auditor system prompt framing — do not soften.
- Category enum, verbatim values: `hold_witness`, `acceptance_criteria`, `standards_reference`, `responsible_party`, `internal_consistency`, `proposal_mismatch`, `other`.
- Supported inputs: `.xlsx`, `.pdf`, `.docx`. `.doc` → friendly error asking to re-save as `.docx`.
- Inputs to the model wrapped in `<itp>…</itp>` and optional `<proposal>…</proposal>`.
- API key from Streamlit secrets / env `ANTHROPIC_API_KEY`; never hardcode. `samples/` and secrets are gitignored.
- Conventional commits, explicit paths (never `git add -A`). Do not push.

---

### Task 1: Scaffolding, config, dependencies

**Files:**
- Create: `requirements.txt`, `src/__init__.py`, `src/config.py`, `tests/__init__.py`, `tests/test_config.py`

**Interfaces:**
- Produces: `config.MODEL: str`, `config.MAX_TOKENS: int`, `config.SUPPORTED_EXTENSIONS: set[str]`

- [ ] **Step 1: Write `requirements.txt`**

```
streamlit>=1.38
anthropic>=0.40
openpyxl>=3.1
pdfplumber>=0.11
python-docx>=1.1
pytest>=8.0
```

- [ ] **Step 2: Create venv and install**

Run: `python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt`
Expected: installs cleanly. (All subsequent `python`/`pytest` use `.venv/Scripts/`.)

- [ ] **Step 3: Write the failing test** — `tests/test_config.py`

```python
from src import config

def test_model_is_current_sonnet():
    assert config.MODEL == "claude-sonnet-5"

def test_supported_extensions():
    assert config.SUPPORTED_EXTENSIONS == {".xlsx", ".pdf", ".docx"}
```

- [ ] **Step 4: Run test to verify it fails**

Run: `.venv/Scripts/pytest tests/test_config.py -v`
Expected: FAIL (module `src.config` not found).

- [ ] **Step 5: Write `src/config.py`**

```python
MODEL = "claude-sonnet-5"
MAX_TOKENS = 8000
SUPPORTED_EXTENSIONS = {".xlsx", ".pdf", ".docx"}
```

Also create empty `src/__init__.py` and `tests/__init__.py`.

- [ ] **Step 6: Run test to verify it passes**

Run: `.venv/Scripts/pytest tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt src/__init__.py src/config.py tests/__init__.py tests/test_config.py
git commit -m "chore: scaffold config, deps, test harness"
```

---

### Task 2: Schema (Finding + Category + forced tool definition)

**Files:**
- Create: `src/schema.py`, `tests/test_schema.py`

**Interfaces:**
- Produces: `schema.Category` (enum-like), `schema.CATEGORIES: list[str]`, `schema.REVIEW_TOOL: dict` (Anthropic tool def with name `report_findings`), `schema.Finding` dataclass with fields `location, category, observation, why_it_matters, suggested_action`.

- [ ] **Step 1: Write the failing test** — `tests/test_schema.py`

```python
from src import schema

def test_categories_exact():
    assert schema.CATEGORIES == [
        "hold_witness", "acceptance_criteria", "standards_reference",
        "responsible_party", "internal_consistency", "proposal_mismatch", "other",
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/pytest tests/test_schema.py -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Write `src/schema.py`**

```python
from dataclasses import dataclass

CATEGORIES = [
    "hold_witness", "acceptance_criteria", "standards_reference",
    "responsible_party", "internal_consistency", "proposal_mismatch", "other",
]

CATEGORY_LABELS = {
    "hold_witness": "Hold & Witness Points",
    "acceptance_criteria": "Acceptance Criteria",
    "standards_reference": "Standards & References",
    "responsible_party": "Responsible Party",
    "internal_consistency": "Internal Consistency",
    "proposal_mismatch": "Proposal Cross-Check",
    "other": "Other",
}

@dataclass
class Finding:
    location: str
    category: str
    observation: str
    why_it_matters: str
    suggested_action: str

REVIEW_TOOL = {
    "name": "report_findings",
    "description": (
        "Report every QA finding from the adversarial ITP review as structured data. "
        "Call this exactly once with all findings."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "Section/item/cell reference in the ITP, e.g. 'Item 2.1' or 'Acceptance Criteria column'."},
                        "category": {"type": "string", "enum": CATEGORIES},
                        "observation": {"type": "string", "description": "What was noticed."},
                        "why_it_matters": {"type": "string", "description": "Why it might draw client scrutiny."},
                        "suggested_action": {"type": "string", "description": "Advisory suggestion phrased as 'consider…', never a directive."},
                    },
                    "required": ["location", "category", "observation", "why_it_matters", "suggested_action"],
                },
            }
        },
        "required": ["findings"],
    },
}
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/Scripts/pytest tests/test_schema.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/schema.py tests/test_schema.py
git commit -m "feat: add findings schema and forced tool definition"
```

---

### Task 3: Prompts (system prompt + XML user-message builder)

**Files:**
- Create: `src/prompts.py`, `tests/test_prompts.py`

**Interfaces:**
- Produces: `prompts.system_prompt() -> str`, `prompts.user_message(itp_text: str, proposal_text: str | None = None) -> str`

- [ ] **Step 1: Write the failing test** — `tests/test_prompts.py`

```python
from src import prompts

def test_system_prompt_is_adversarial():
    sp = prompts.system_prompt().lower()
    assert "auditor" in sp
    assert "not a helpful assistant" in sp or "not to be helpful" in sp
    # advisory requirement is stated
    assert "advisory" in sp or "consider" in sp

def test_user_message_standalone_has_itp_tags_no_proposal():
    msg = prompts.user_message("ITP CONTENT")
    assert "<itp>" in msg and "ITP CONTENT" in msg and "</itp>" in msg
    assert "<proposal>" not in msg

def test_user_message_cross_check_has_both():
    msg = prompts.user_message("ITP CONTENT", "PROPOSAL CONTENT")
    assert "<itp>" in msg and "<proposal>" in msg and "PROPOSAL CONTENT" in msg
    assert "cross-check" in msg.lower() or "proposal" in msg.lower()
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/Scripts/pytest tests/test_prompts.py -v` — Expected: FAIL.

- [ ] **Step 3: Write `src/prompts.py`**

```python
def system_prompt() -> str:
    return (
        "You are a strict, adversarial QA auditor reviewing a construction "
        "Inspection Test Plan (ITP). You are NOT a helpful assistant being asked "
        "to review a document. Your job is to find every gap, ambiguity, "
        "inconsistency, and omission that a demanding client's own reviewer would "
        "flag and send back. Assume the reader will push back on anything vague.\n\n"
        "Check specifically for:\n"
        "- Hold points and witness points: are they explicitly and specifically stated?\n"
        "- Acceptance criteria: specific and measurable, or vague?\n"
        "- Standards/codes: are relevant references present at all? You cannot verify "
        "a code number is correct without a reference document, so do not claim to — "
        "only flag when a reference is missing or looks generic.\n"
        "- Responsible party: is one identified for each check/inspection?\n"
        "- Internal consistency: contradictions in sequencing, dates, or referenced stages.\n"
        "- When a proposal is supplied: does the ITP's inspection/test coverage match "
        "the methodology and scope in the proposal? Flag anything proposed but not "
        "reflected in an inspection point, and any inspection point with no basis in the proposal.\n\n"
        "Report findings ONLY by calling the report_findings tool. Every suggested_action "
        "must be advisory — phrase as 'consider…' or 'it may be worth…', never as a "
        "directive like 'this must be fixed'. Be thorough; do not soften your review."
    )


def user_message(itp_text: str, proposal_text: str | None = None) -> str:
    parts = [
        "Review the following ITP as an adversarial QA auditor and report all findings "
        "via the report_findings tool.",
    ]
    if proposal_text:
        parts.append(
            "A project proposal / scope of works is also provided. Perform a cross-check: "
            "flag coverage in the proposal that is missing from the ITP and vice versa, "
            "using the proposal_mismatch category."
        )
    parts.append(f"<itp>\n{itp_text}\n</itp>")
    if proposal_text:
        parts.append(f"<proposal>\n{proposal_text}\n</proposal>")
    return "\n\n".join(parts)
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/Scripts/pytest tests/test_prompts.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/prompts.py tests/test_prompts.py
git commit -m "feat: add adversarial system prompt and XML user-message builder"
```

---

### Task 4: Parsing — xlsx first (highest-fidelity, real sample), then pdf/docx/doc

**Files:**
- Create: `src/parsing.py`, `tests/test_parsing.py`

**Interfaces:**
- Consumes: `config.SUPPORTED_EXTENSIONS`
- Produces: `parsing.ParsedDoc` dataclass `{text: str, preview: str, warnings: list[str]}`; `parsing.parse(filename: str, data: bytes) -> ParsedDoc`; raises `parsing.UnsupportedFormat(message)` for `.doc` and unknown extensions.

- [ ] **Step 1: Write the failing test** — `tests/test_parsing.py`

```python
import pathlib
import pytest
from src import parsing

SAMPLE_XLSX = pathlib.Path("samples/GT_Civil_Riverside_WWPS_Civil_ITP_Template.xlsx")

def test_doc_rejected_with_friendly_message():
    with pytest.raises(parsing.UnsupportedFormat) as e:
        parsing.parse("old.doc", b"\xd0\xcf\x11\xe0")
    assert "re-save" in str(e.value).lower() and "docx" in str(e.value).lower()

def test_unknown_extension_rejected():
    with pytest.raises(parsing.UnsupportedFormat):
        parsing.parse("x.txt", b"hi")

@pytest.mark.skipif(not SAMPLE_XLSX.exists(), reason="sample not present")
def test_xlsx_preserves_itp_columns():
    pd = parsing.parse(SAMPLE_XLSX.name, SAMPLE_XLSX.read_bytes())
    # All 12 ITP table column headers must survive parsing.
    for col in ["Acceptance Criteria", "Inspection Point", "Reference",
                "Witness / Release By", "QA Record / Evidence"]:
        assert col in pd.text, f"missing column: {col}"
    # A known data cell survives too (item numbering).
    assert "1.1" in pd.text
    assert pd.preview  # non-empty preview for UI
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/Scripts/pytest tests/test_parsing.py -v` — Expected: FAIL (module not found).

- [ ] **Step 3: Write `src/parsing.py`**

```python
import io
import os
from dataclasses import dataclass, field


class UnsupportedFormat(Exception):
    pass


@dataclass
class ParsedDoc:
    text: str
    preview: str
    warnings: list[str] = field(default_factory=list)


def parse(filename: str, data: bytes) -> ParsedDoc:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".doc":
        raise UnsupportedFormat(
            "Legacy .doc files aren't supported. Please open it in Word and "
            "re-save as .docx, then upload again."
        )
    if ext == ".xlsx":
        return _parse_xlsx(data)
    if ext == ".pdf":
        return _parse_pdf(data)
    if ext == ".docx":
        return _parse_docx(data)
    raise UnsupportedFormat(
        f"Unsupported file type '{ext}'. Supported: .xlsx, .pdf, .docx."
    )


def _row_to_line(cells) -> str:
    vals = ["" if c is None else str(c).strip() for c in cells]
    if not any(vals):
        return ""
    return " | ".join(vals)


def _parse_xlsx(data: bytes) -> ParsedDoc:
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True, read_only=True)
    lines = []
    for ws in wb.worksheets:
        lines.append(f"### Sheet: {ws.title}")
        for row in ws.iter_rows(values_only=True):
            line = _row_to_line(row)
            if line:
                lines.append(line)
        lines.append("")
    text = "\n".join(lines).strip()
    return ParsedDoc(text=text, preview=text)


def _parse_pdf(data: bytes) -> ParsedDoc:
    import pdfplumber
    lines, warnings = [], []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            lines.append(f"### Page {i}")
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    line = _row_to_line(row)
                    if line:
                        lines.append(line)
            page_text = page.extract_text() or ""
            if page_text.strip():
                lines.append(page_text.strip())
            lines.append("")
    text = "\n".join(lines).strip()
    if not text:
        warnings.append("No extractable text found — the PDF may be scanned images.")
    return ParsedDoc(text=text, preview=text, warnings=warnings)


def _parse_docx(data: bytes) -> ParsedDoc:
    import docx
    document = docx.Document(io.BytesIO(data))
    lines = []
    for para in document.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())
    for t_i, table in enumerate(document.tables, 1):
        lines.append(f"### Table {t_i}")
        for row in table.rows:
            line = _row_to_line([c.text for c in row.cells])
            if line:
                lines.append(line)
    text = "\n".join(lines).strip()
    return ParsedDoc(text=text, preview=text)
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/Scripts/pytest tests/test_parsing.py -v` — Expected: PASS (xlsx test confirms the 12-column table survives — the core fidelity gate).

- [ ] **Step 5: Commit**

```bash
git add src/parsing.py tests/test_parsing.py
git commit -m "feat: add format-dispatch parsing with table-preserving output"
```

---

### Task 5: Review orchestration (Anthropic forced tool-use, mocked)

**Files:**
- Create: `src/review.py`, `tests/test_review.py`

**Interfaces:**
- Consumes: `config.MODEL`, `config.MAX_TOKENS`, `schema.REVIEW_TOOL`, `schema.Finding`, `prompts.system_prompt`, `prompts.user_message`
- Produces: `review.run_review(itp_text: str, proposal_text: str | None = None, client=None) -> list[schema.Finding]`

- [ ] **Step 1: Write the failing test** — `tests/test_review.py` (mock the Anthropic client; no network)

```python
from unittest.mock import MagicMock
from src import review, schema


def _fake_client_returning(findings):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "report_findings"
    block.input = {"findings": findings}
    resp = MagicMock()
    resp.content = [block]
    client = MagicMock()
    client.messages.create.return_value = resp
    return client


def test_run_review_parses_tool_output():
    client = _fake_client_returning([
        {"location": "Item 2.1", "category": "acceptance_criteria",
         "observation": "Vague criteria", "why_it_matters": "Client will query",
         "suggested_action": "consider specifying a tolerance"}
    ])
    findings = review.run_review("itp text", client=client)
    assert len(findings) == 1
    assert isinstance(findings[0], schema.Finding)
    assert findings[0].category == "acceptance_criteria"


def test_run_review_forces_tool_and_passes_system():
    client = _fake_client_returning([])
    review.run_review("itp text", client=client)
    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "tool", "name": "report_findings"}
    assert kwargs["tools"] == [schema.REVIEW_TOOL]
    assert "auditor" in kwargs["system"].lower()


def test_run_review_includes_proposal_when_given():
    client = _fake_client_returning([])
    review.run_review("itp", "proposal text", client=client)
    kwargs = client.messages.create.call_args.kwargs
    sent = kwargs["messages"][0]["content"]
    assert "<proposal>" in sent and "proposal text" in sent
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/Scripts/pytest tests/test_review.py -v` — Expected: FAIL.

- [ ] **Step 3: Write `src/review.py`**

```python
from src import config, prompts, schema


def _get_client():
    import anthropic
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def run_review(itp_text, proposal_text=None, client=None):
    client = client or _get_client()
    resp = client.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=prompts.system_prompt(),
        tools=[schema.REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "report_findings"},
        messages=[{"role": "user", "content": prompts.user_message(itp_text, proposal_text)}],
    )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "report_findings":
            return [
                schema.Finding(
                    location=f.get("location", ""),
                    category=f.get("category", "other"),
                    observation=f.get("observation", ""),
                    why_it_matters=f.get("why_it_matters", ""),
                    suggested_action=f.get("suggested_action", ""),
                )
                for f in block.input.get("findings", [])
            ]
    return []
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/Scripts/pytest tests/test_review.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/review.py tests/test_review.py
git commit -m "feat: add review orchestration with forced tool-use"
```

---

### Task 6: Report generation (markdown + docx)

**Files:**
- Create: `src/report.py`, `tests/test_report.py`

**Interfaces:**
- Consumes: `schema.Finding`, `schema.CATEGORY_LABELS`, `schema.CATEGORIES`
- Produces: `report.to_markdown(findings: list[schema.Finding]) -> str`; `report.to_docx(findings: list[schema.Finding]) -> bytes`

- [ ] **Step 1: Write the failing test** — `tests/test_report.py`

```python
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
```

- [ ] **Step 2: Run test to verify it fails** — Run: `.venv/Scripts/pytest tests/test_report.py -v` — Expected: FAIL.

- [ ] **Step 3: Write `src/report.py`**

```python
import io
from src import schema


def _group(findings):
    grouped = {c: [] for c in schema.CATEGORIES}
    for f in findings:
        grouped.get(f.category, grouped["other"]).append(f)
    return grouped


def to_markdown(findings) -> str:
    if not findings:
        return "# ITP Review\n\nNo findings were identified."
    lines = ["# ITP Review", "", f"{len(findings)} finding(s).", ""]
    grouped = _group(findings)
    for cat in schema.CATEGORIES:
        items = grouped[cat]
        if not items:
            continue
        lines.append(f"## {schema.CATEGORY_LABELS[cat]}")
        lines.append("")
        for f in items:
            lines.append(f"### {f.location}")
            lines.append(f"- **Observation:** {f.observation}")
            lines.append(f"- **Why it matters:** {f.why_it_matters}")
            lines.append(f"- **Suggested action:** {f.suggested_action}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def to_docx(findings) -> bytes:
    import docx
    document = docx.Document()
    document.add_heading("ITP Review", level=0)
    if not findings:
        document.add_paragraph("No findings were identified.")
    else:
        document.add_paragraph(f"{len(findings)} finding(s).")
        grouped = _group(findings)
        for cat in schema.CATEGORIES:
            items = grouped[cat]
            if not items:
                continue
            document.add_heading(schema.CATEGORY_LABELS[cat], level=1)
            for f in items:
                document.add_heading(f.location, level=2)
                document.add_paragraph(f"Observation: {f.observation}")
                document.add_paragraph(f"Why it matters: {f.why_it_matters}")
                document.add_paragraph(f"Suggested action: {f.suggested_action}")
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()
```

- [ ] **Step 4: Run test to verify it passes** — Run: `.venv/Scripts/pytest tests/test_report.py -v` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/report.py tests/test_report.py
git commit -m "feat: add markdown and docx report generation"
```

---

### Task 7: Streamlit UI (manual verification)

**Files:**
- Create: `app.py`, `.streamlit/secrets.toml.example`

**Interfaces:**
- Consumes: `parsing.parse`, `parsing.UnsupportedFormat`, `review.run_review`, `report.to_markdown`, `report.to_docx`, `schema.CATEGORY_LABELS`, `schema.CATEGORIES`

- [ ] **Step 1: Write `.streamlit/secrets.toml.example`**

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

- [ ] **Step 2: Write `app.py`**

```python
import os
import streamlit as st
from src import parsing, review, report, schema

st.set_page_config(page_title="ITP Reviewer", layout="wide")
st.title("ITP Reviewer")
st.caption("Adversarial QA review of a draft Inspection Test Plan. Findings are advisory.")

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

itp_file = st.file_uploader("ITP file (required)", type=["xlsx", "pdf", "docx"])
proposal_file = st.file_uploader("Proposal / scope of works (optional)", type=["xlsx", "pdf", "docx"])


def _safe_parse(f, label):
    try:
        return parsing.parse(f.name, f.getvalue())
    except parsing.UnsupportedFormat as e:
        st.error(f"{label}: {e}")
        return None


itp_doc = proposal_doc = None
if itp_file:
    itp_doc = _safe_parse(itp_file, "ITP")
    if itp_doc:
        for w in itp_doc.warnings:
            st.warning(f"ITP: {w}")
        with st.expander("Preview parsed ITP text (check table fidelity before reviewing)"):
            st.text(itp_doc.preview[:20000])

if proposal_file:
    proposal_doc = _safe_parse(proposal_file, "Proposal")
    if proposal_doc:
        with st.expander("Preview parsed proposal text"):
            st.text(proposal_doc.preview[:20000])

mode = "Cross-check (ITP vs proposal)" if proposal_doc else "Standalone ITP review"
st.info(f"Mode: {mode}")

if st.button("Review", type="primary", disabled=itp_doc is None):
    with st.spinner("Running adversarial review…"):
        findings = review.run_review(
            itp_doc.text,
            proposal_doc.text if proposal_doc else None,
        )
    if not findings:
        st.success("No findings identified.")
    else:
        st.subheader(f"{len(findings)} finding(s)")
        by_cat = {c: [f for f in findings if f.category == c] for c in schema.CATEGORIES}
        for cat in schema.CATEGORIES:
            items = by_cat[cat]
            if not items:
                continue
            st.markdown(f"### {schema.CATEGORY_LABELS[cat]} ({len(items)})")
            for f in items:
                with st.expander(f"{f.location} — {f.observation[:60]}"):
                    st.markdown(f"**Observation:** {f.observation}")
                    st.markdown(f"**Why it matters:** {f.why_it_matters}")
                    st.markdown(f"**Suggested action:** {f.suggested_action}")
        st.download_button("Download markdown report", report.to_markdown(findings),
                           file_name="itp_review.md", mime="text/markdown")
        st.download_button("Download Word report", report.to_docx(findings),
                           file_name="itp_review.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
```

- [ ] **Step 3: Manual verification — parsing fidelity gate**

Run: `.venv/Scripts/streamlit run app.py`
Upload `samples/GT_Civil_Riverside_WWPS_Civil_ITP_Template.xlsx`. Open the preview expander. Confirm all 12 ITP columns and item rows (1.1, 2.1, …) are present and readably aligned. **If the table is mangled, stop and fix parsing before trusting review output** (spec testing requirement).

- [ ] **Step 4: Manual verification — end-to-end review**

With a valid `ANTHROPIC_API_KEY` in `.streamlit/secrets.toml`, click Review in standalone mode. Confirm: findings appear grouped by category; each has location/observation/why/action; every suggested_action is advisory ("consider…"), never directive; both downloads produce a file.

- [ ] **Step 5: Commit**

```bash
git add app.py .streamlit/secrets.toml.example
git commit -m "feat: add Streamlit UI with parse preview and report downloads"
```

---

### Task 8: Project documentation

**Files:**
- Create: `CLAUDE.md`, `DECISIONS.md`, `SESSION_LOG.md`, `HANDOVER.md`, `README.md`

- [ ] **Step 1: Write `DECISIONS.md`** with plain-language reasoning (required by brief) for: (a) direct-context prompting instead of RAG — the whole ITP fits comfortably in context, RAG adds retrieval infrastructure and failure modes for no benefit at this size; (b) forced tool-use instead of prose JSON — guarantees a valid structured shape, no brittle string-parsing; (c) categorized findings instead of a score — a single number hides what to act on and invites arguing the number, categories map directly to fix actions; (d) parsing libraries — openpyxl added because the real ITP template is Excel; legacy `.doc` excluded because it's OLE2 binary that python-docx can't read and reliable conversion needs external tooling; user re-saves as `.docx`.

- [ ] **Step 2: Write `CLAUDE.md`** — project-specific: how to run (`.venv/Scripts/streamlit run app.py`), run tests (`.venv/Scripts/pytest`), module map, model constant location, secrets handling, samples are gitignored.

- [ ] **Step 3: Write `HANDOVER.md`** — include the "known limitations / next steps" section verbatim from the spec: (1) proposal cross-check built but unvalidated against a real matched proposal; (2) checklist based on general ITP/construction QA knowledge, not calibrated against the client's own AI reviewer output — both revisit when that data exists.

- [ ] **Step 4: Write `SESSION_LOG.md`** and `README.md` (short: what it is, setup, run).

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md DECISIONS.md SESSION_LOG.md HANDOVER.md README.md
git commit -m "docs: add project docs, decisions, and handover"
```

---

## Self-Review

**Spec coverage:** inputs xlsx/pdf/docx + .doc friendly error (T4) ✓; table-preserving parse + preview fidelity gate (T4, T7) ✓; adversarial system prompt (T3) ✓; XML-tagged inputs (T3) ✓; forced tool-use structured findings with the 5 fields (T2, T5) ✓; category enum incl. proposal_mismatch (T2) ✓; standalone + cross-check modes (T3, T5) ✓; advisory phrasing enforced (T2/T3 prompt, T7 manual check) ✓; findings grouped by category in UI + markdown + docx download (T6, T7) ✓; model constant confirmed current (T1) ✓; four doc files + required DECISIONS rationales + HANDOVER limitations (T8) ✓.

**Placeholder scan:** no TBD/TODO; all code and tests are concrete.

**Type consistency:** `ParsedDoc.text/preview/warnings`, `Finding(location, category, observation, why_it_matters, suggested_action)`, `run_review(itp_text, proposal_text=None, client=None)`, `to_markdown`/`to_docx`, `CATEGORIES`/`CATEGORY_LABELS` used consistently across tasks.
