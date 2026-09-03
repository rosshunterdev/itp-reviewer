# ITP Generation from Specifications — Design Spec

_Phase 2 of ITP Reviewer. Approved in brainstorming session 2026-09-04._

## Problem

The client produces ITPs (Inspection Test Plans) for construction
projects. Today he builds them manually from project specifications — a
slow, repetitive process where the same categories of inspection items
recur across projects. He wants to upload a project spec and get a
structured draft ITP back, in the format he already uses.

## What this adds

A **Generate** mode alongside the existing **Review** mode. The user
uploads a project specification (PDF), optionally with supporting
documents (building consent, drawings), clicks Generate, and receives a
draft ITP as a structured report. A "Review this draft?" button then
feeds the generated ITP into the existing adversarial reviewer without
re-uploading.

## Scope

**In scope:**
- Generate ITP items from a project specification PDF (single-pass, full
  context)
- Structured report output (markdown + docx download) matching the
  12-column ITP format
- "Review this draft?" bridge to the existing reviewer
- Mode selector in the UI (Generate / Review)

**Not in scope (deferred):**
- `.xlsx` export (follow-up after generation quality is validated)
- Auto-apply review fixes (Phase 2b or Phase 3)
- Gap analysis as a standalone mode (the reviewer cross-check covers this)

## Architecture

### Context strategy

Single-pass, direct-context — the same approach as Phase 1's reviewer.
The full spec (~82k tokens for the 169-page Waitomo Masterspec) plus
few-shot ITP examples and system prompt fit within the 200k context
window. No chunking, no RAG.

### Generation pipeline

```
spec PDF  ──►  parsing.parse()  ──►  spec text
                                         │
ITP examples (hardcoded excerpts)        │
                                         ▼
                               generation.run_generation()
                                   │
                                   ├── system prompt (ITP author persona)
                                   ├── user message: <specification> + <itp_examples> + optional <building_consent>/<drawings>
                                   ├── forced tool call: generate_itp
                                   │
                                   ▼
                              list[ITPItem]
                                   │
                                   ▼
                           gen_report.to_markdown()
                           gen_report.to_docx()
```

### Model persona (generation vs review)

The reviewer's system prompt frames the model as an adversarial QA
auditor. The generator needs the opposite: an experienced construction
ITP author who produces thorough, standards-aware inspection plans. Two
different personas, same model.

The generation system prompt instructs the model to:
- Read the specification section by section
- Identify every activity that requires inspection, testing, or
  verification
- Produce ITP items in the 12-column format, grouped by work package
- Assign hold (H), witness (W), surveillance (S), or review (R) points
  based on criticality
- Reference specific standards, codes, and spec section numbers
- Write measurable, specific acceptance criteria (not vague)
- Generate hold point register entries for every H-designated item

### Structured output

Forced tool use, same pattern as Phase 1. The tool schema
(`generate_itp`) returns structured data matching the 12 ITP columns:

```
ITPItem:
  item_number: str          # e.g. "1.1", "2.3"
  work_package: str         # e.g. "Pre-start / document control"
  inspection_test: str      # what is inspected/tested/checked
  acceptance_criteria: str  # measurable pass/fail criteria
  reference: str            # standards, codes, spec sections
  frequency: str            # when/how often
  inspection_point: str     # H / W / S / R
  contractor_resp: str      # who from the contractor side
  witness_release: str      # who witnesses or releases
  qa_record: str            # evidence / documentation required
```

Plus a separate list of hold point register entries:

```
HoldPoint:
  hp_number: str            # e.g. "HP-01"
  itp_item: str             # cross-ref to ITPItem.item_number
  description: str          # what must be released
```

The two remaining ITP columns (Result/Status, Comments/NCR Ref) are
left blank — they are filled in during actual construction, not at
drafting time.

### Few-shot examples

The generation prompt includes 8–12 representative rows from the GT
Civil Riverside WWPS ITP template as examples. These are hardcoded in
the prompt module (not loaded at runtime from the xlsx) because:
- They are curated to show variety (H/W/S/R points, different work
  packages, different standards)
- The prompt needs to be stable and tested, not dependent on an
  external file
- If the client provides better examples later, we update the prompt

### ITP examples source

Selected rows from `samples/GT_Civil_Riverside_WWPS_Civil_ITP_Template.xlsx`
covering:
- Pre-start items (document control, permits) — show H points, general
  references
- Survey/set-out — show W points, specific tolerances
- Earthworks — show compaction testing, lab references, measurable criteria
- Concrete works — show NZS 3109/3104 references, pre-pour checklists
- Pipeline works — show pressure testing, manufacturer requirements
- Close-out — show as-built and QA dossier items

### MAX_TOKENS

Generation output is longer than review findings. A 40-item ITP with
hold point register could be 4000–6000 tokens of structured output.
`MAX_TOKENS` for generation calls set to 16000 (double the review
default of 8000) to give headroom for larger specs that produce more
items.

## File changes

### New files

| File | Purpose |
|------|---------|
| `src/gen_schema.py` | `ITPItem` and `HoldPoint` dataclasses, `GENERATE_ITP_TOOL` definition |
| `src/generation.py` | Generation system prompt, user message builder, `run_generation()` API call |
| `src/gen_report.py` | `to_markdown()` and `to_docx()` for generated ITP output |
| `tests/test_gen_schema.py` | Schema and tool definition tests |
| `tests/test_generation.py` | Generation with mocked API response |
| `tests/test_gen_report.py` | Report formatting tests |

### Modified files

| File | Change |
|------|--------|
| `app.py` | Add mode selector (tabs: Generate / Review). Generate tab: spec upload, optional supporting docs, Generate button, ITP output display, report downloads, "Review this draft?" bridge button. Review tab: existing UI unchanged. |
| `src/config.py` | Add `GEN_MAX_TOKENS = 16000`. Existing `MAX_TOKENS` unchanged. |

### Unchanged files

| File | Why unchanged |
|------|--------------|
| `src/parsing.py` | Spec PDFs parse fine with existing logic (confirmed). |
| `src/prompts.py` | Review prompts stay as-is. Generation prompts live in `src/generation.py` to keep concerns separate. |
| `src/schema.py` | Review schema unchanged. Generation schema is a different shape in a separate file. |
| `src/review.py` | Called as-is by the "Review this draft?" bridge. |
| `src/report.py` | Review reports unchanged. Generation reports are a different format in a separate file. |

## UI flow

### Mode selector

Two tabs at the top: **Generate ITP** and **Review ITP**.

The Review tab contains the existing UI exactly as-is (upload ITP,
optional proposal, preview, review button, findings, downloads).

### Generate tab

1. **Upload project specification** (required) — PDF. Parsed and
   previewed in an expander, same fidelity-gate pattern as the
   reviewer.
2. **Upload supporting documents** (optional) — building consent,
   drawings, engineer's spec. Each parsed and previewed separately.
3. **Generate button** — calls `run_generation()`, stores result in
   `session_state`.
4. **Output display** — ITP items grouped by work package, each item
   showing all 12 columns. Hold point register displayed separately.
5. **Download buttons** — markdown report, docx report.
6. **"Review this draft?" button** — converts the generated ITP items
   to a text representation, passes it to `review.run_review()`, and
   displays findings below using the existing findings UI.

### "Review this draft?" bridge

The generated ITP items are formatted as a text table (matching how a
real ITP would look after parsing) and passed to the existing
`run_review()` function as the `itp_text` argument. No changes to the
review pipeline — it sees what looks like a parsed ITP document.

## Testing

### Unit tests
- `test_gen_schema.py` — ITPItem/HoldPoint construction, tool schema
  has required fields, inspection_point values are valid
- `test_gen_report.py` — markdown output has headers and all columns,
  docx output is valid, empty items handled, hold point register
  included
- `test_generation.py` — mocked API response parsed into ITPItem list,
  hold points extracted, error handling matches review pattern

### Live validation
- Run generation against the Waitomo Masterspec with a real API key
- Confirm output covers the spec's work sections (demolition,
  groundwork, carpentry, planting)
- Verify the "Review this draft?" bridge produces review findings on
  the generated ITP
- Compare generated items against the GT Civil template for format
  consistency

## Risks and mitigations

| Risk | Mitigation |
|------|-----------|
| 82k token spec + examples + system prompt might be tight | Measured at ~82k; with examples (~2k) and system prompt (~1k), total input is ~85k of 200k. Comfortable margin. |
| Generated ITP may miss sections of the spec | Few-shot examples cover all major work package types. Live validation will check coverage. |
| Quality of acceptance criteria may be generic | Prompt instructs specific, measurable criteria with worked examples. Reviewer bridge catches vagueness. |
| Client expects xlsx output immediately | Decision already made: report first, xlsx later. Communicated. |
