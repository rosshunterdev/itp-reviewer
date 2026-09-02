# SESSION_LOG.md

## 2026-09-02 — Phase 1 build

Built Phase 1 of the ITP Reviewer end-to-end via TDD across 8 tasks, on
`feature/phase-1-build`.

**Modules created:**
- `src/config.py` — model constant + supported extensions
- `src/schema.py` — `Finding` shape, category enum, forced tool-use def
- `src/prompts.py` — adversarial system prompt, XML-tagged user message
- `src/parsing.py` — `.xlsx`/`.pdf`/`.docx` dispatch to table-preserving
  text + preview, friendly `.doc` error
- `src/review.py` — Anthropic call, forces tool use, returns findings
- `src/report.py` — findings to markdown / docx
- `app.py` — Streamlit UI: upload, parse preview, review, findings by
  category, report download

**Key decisions** (full reasoning in DECISIONS.md):
- Direct-context prompting instead of RAG — document is small enough,
  RAG adds failure modes for no benefit.
- Forced tool-use instead of prose-JSON parsing — guaranteed valid
  structure, no brittle string parsing.
- Categorized findings instead of a single score — maps to fix actions.
- Added `openpyxl` for `.xlsx` (the client's real ITP template format);
  excluded legacy `.doc` (OLE2 binary, no reliable read path without
  external tooling) — user re-saves as `.docx`.

**Current state:** working Streamlit app, full pytest suite passing.
Proposal cross-check mode is built but unvalidated (no real matched
proposal exists yet). Review checklist is based on general ITP/QA
knowledge, not calibrated against the client's actual AI reviewer
feedback. Live end-to-end review with a real API key still needs the
user's manual validation — that's the next step, not yet done this
session.
