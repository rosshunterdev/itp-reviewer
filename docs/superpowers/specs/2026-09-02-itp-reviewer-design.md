# ITP Reviewer — Design Spec

Date: 2026-09-02
Status: Approved (design), pre-implementation

## Purpose

Phase 1 of a construction-industry QA tool. A solo internal tool for one
client who prepares ITPs (Inspection Test Plans). His customers now run his
ITPs through their own AI reviewers and send back fix-lists; this tool runs a
comparable adversarial review on his side first, so issues are caught before
the document goes out and the back-and-forth shrinks.

Phase 1 only. The later "project buddy" assistant is explicitly out of scope.

## Scope (in / out)

In:
- Upload a draft ITP (required) and an optional proposal / scope-of-works file.
- Parse to text with table structure preserved.
- One LLM review pass as a strict adversarial QA auditor.
- Structured, categorized findings (not a score, not free text).
- Standalone ITP quality review when no proposal is given; proposal
  cross-check when one is present. Both modes work; standalone is the
  validated priority.
- Download findings as a report (markdown primary, docx optional).

Out: RAG / vector store, persistent assistant, multi-user, auth, hosting,
legacy `.doc` binary parsing (user re-saves as `.docx`).

## Input formats (decided)

Supported: `.xlsx` (openpyxl), `.pdf` (pdfplumber), `.docx` (python-docx).
Not supported: legacy `.doc` (OLE2 binary) — the app returns a friendly
message asking the user to re-save as `.docx`. Rationale: the two real ITP
samples are `.xlsx` and legacy `.doc`; `python-docx` cannot read either, so
the brief's original pdfplumber+python-docx plan covered neither. Excel is
added because the client's actual ITP template is an Excel workbook, and an
Excel grid is the cleanest possible table-preserving input.

## Real ITP structure (grounding)

The client's `.xlsx` template (`GT_Civil_..._ITP_Template.xlsx`) has ~5 sheets:
header/metadata + legend, then the ITP item table with columns:

Item · Work Package/Activity · Inspection/Test/Check · Acceptance Criteria ·
Reference · Frequency/Timing · Inspection Point (H/W/R/S) · GT Civil
Responsibility · Witness/Release By · QA Record/Evidence · Result/Status ·
Comments/NCR Ref.

Checklist mapping: hold/witness → *Inspection Point*; acceptance criteria →
*Acceptance Criteria*; standards → *Reference*; responsible party → *GT Civil
Responsibility* + *Witness/Release By*; internal consistency → across
Item/Frequency/sequencing.

## Architecture

```
app.py               # Streamlit UI only
src/
  parsing.py         # extension dispatch -> normalized table-preserving text + preview
  prompts.py         # adversarial system prompt + XML-tagged user-message builder
  schema.py          # Finding schema / forced tool definition + category enum
  review.py          # Anthropic call, forces the tool, returns findings
  report.py          # findings -> markdown (+ optional docx)
samples/             # provided files moved out of repo root
requirements.txt
.streamlit/secrets.toml   # ANTHROPIC_API_KEY (gitignored)
CLAUDE.md, DECISIONS.md, SESSION_LOG.md, HANDOVER.md
```

Each module has one purpose and a clear interface:
- `parsing.parse(file) -> ParsedDoc{ text: str, preview: str, warnings: list }`
- `prompts.system_prompt() -> str`, `prompts.user_message(itp, proposal?) -> str`
- `schema.REVIEW_TOOL` (tool def) + `Finding` shape + `Category` enum
- `review.run_review(itp_text, proposal_text?) -> list[Finding]`
- `report.to_markdown(findings)`, `report.to_docx(findings) -> bytes`

## Parsing details

- Dispatch by extension. `.xlsx`: iterate all sheets, render each sheet's used
  range as a markdown/pipe table with the sheet name as a header so the 12
  columns survive. `.pdf`: pdfplumber `extract_tables` per page plus surrounding
  text. `.docx`: python-docx paragraphs and tables. `.doc`: friendly error.
- Returns one normalized string plus a `preview` shown in a UI expander so the
  user eyeballs table fidelity BEFORE trusting any review (directly satisfies
  the brief's "confirm parsing didn't mangle the tables" requirement).

## Review details

- System prompt: strict, adversarial QA auditor framing whose job is to find
  every gap that would draw scrutiny — NOT a helpful assistant. Not softened.
- User message: inputs wrapped in `<itp>...</itp>` and, when present,
  `<proposal>...</proposal>` to stop the model conflating documents.
- Forced tool use: a single tool `report_findings` with `tool_choice` forcing
  it. Reliable structured output — no prose-JSON parsing.
- Finding fields: `location`, `category`, `observation`, `why_it_matters`,
  `suggested_action` (advisory phrasing, e.g. "consider specifying a witness
  point here" — a deliberate product requirement, applied everywhere findings
  surface).
- Category enum: `hold_witness`, `acceptance_criteria`, `standards_reference`,
  `responsible_party`, `internal_consistency`, `proposal_mismatch`, `other`.
- Mode switch: proposal present adds a cross-check instruction and enables the
  `proposal_mismatch` category (flag proposed items with no inspection point,
  and inspection points with no basis in the proposal).
- Model: current Claude Sonnet, confirmed against the claude-api skill at build
  time, held as one configurable constant.

## UI (app.py)

Single page: ITP upload (required), proposal upload (optional), parse-preview
expander, Review button, findings grouped by category (expanders/badges),
download-report button. Plain — internal tool for one user.

## Report

`report.to_markdown` groups findings by category. `report.to_docx` optional via
python-docx. Advisory phrasing preserved in output.

## Testing

1. Parse the real `.xlsx`; confirm all 12 columns survive in the preview
   before trusting review output.
2. Run standalone review; confirm findings are sane, categorized, advisory.
3. Proposal cross-check: built but NOT validated (no matched proposal exists).

## Known limitations / next steps (also for HANDOVER.md)

1. Proposal cross-check mode is built but unvalidated against a real matched
   proposal.
2. The checklist is based on general ITP/construction QA knowledge, not
   calibrated against what the client's own AI reviewers have actually flagged.
Both revisit once that data exists.

## Decisions to record in DECISIONS.md (plain-language)

- Why direct-context prompting, not RAG.
- Why forced tool-use / JSON schema, not prose JSON parsing.
- Why categorized findings, not a score.
- Parsing library choices (openpyxl added; legacy `.doc` excluded).
