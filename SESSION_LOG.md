# SESSION_LOG.md

## Session 1 — 2026-09-02 — Phase 1 build

**Did:** Scoped, designed, planned, and built Phase 1 of the ITP Reviewer
end-to-end via TDD across 8 tasks on `feature/phase-1-build`, using
subagent-driven development (fresh implementer per task + task review +
whole-branch final review on Opus).

Modules created:
- `src/config.py` — model constant + supported extensions
- `src/schema.py` — `Finding` shape, category enum, forced tool-use def
- `src/prompts.py` — adversarial system prompt, XML-tagged user message
- `src/parsing.py` — `.xlsx`/`.pdf`/`.docx` dispatch to table-preserving
  text + preview, friendly `.doc` error
- `src/review.py` — Anthropic call, forces tool use, returns findings
- `src/report.py` — findings to markdown / docx
- `app.py` — Streamlit UI: upload, parse preview, review, findings by
  category, session-state-persisted results, report download
- Docs: CLAUDE.md, DECISIONS.md, HANDOVER.md, README.md
- Spec + plan under `docs/superpowers/`

**Decided:** Direct-context over RAG; forced tool-use over prose-JSON;
categorized findings over a score; added `openpyxl` for `.xlsx` (client's
real ITP is Excel), excluded legacy `.doc` (re-save as `.docx`); model
`claude-sonnet-5` as one constant; parse-preview fidelity gate. Two
review-driven design calls: accept `.doc` in the uploader so the friendly
re-save message is delivered in-app, and wrap the review API call so
failures show `st.error` not a traceback. Full reasoning in DECISIONS.md.

**Broke or found (during review, fixed same session):**
- Parsing: PDF "scanned image / no extractable text" warning was
  unreachable (page headers made `text` never empty). Fixed to track real
  content. Also strengthened the xlsx test to assert all 12 real ITP
  column headers survive (was 5).
- UI: results/expanders/downloads rendered only inside the `st.button`
  block, so any rerun (expanding a finding, a download click) dropped the
  results and re-triggered a paid API call. Fixed to persist in
  `st.session_state`.
- Final review (Opus): no error handling around the API call → a
  bad/expired key or model-404 would crash with a raw traceback. Fixed.
  `.doc` friendly message was unreachable because the uploader rejected
  `.doc` first. Fixed by adding `doc` to the uploader types.

**Verified:** Full pytest suite `17 passed` (`.venv/Scripts/python -m
pytest`). Controller-run parse of the real `.xlsx` confirmed all 12 ITP
columns + item rows survive (fidelity gate holds). NOT verified: live
end-to-end review with a real `ANTHROPIC_API_KEY` (needs the user) — and
with it, whether `claude-sonnet-5` is a valid deployable model id.

**Git:** 11 commits on `feature/phase-1-build` (from `main` at `b623665`).
Branch kept as-is at user's choice; not merged, no remote configured.
