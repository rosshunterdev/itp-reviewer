# SESSION_LOG.md

## Session 4 — 2026-09-07 — Client feedback, merge, deployment decision

**Did:** Addressed three items of client feedback, merged Phase 2 to main,
decided on deployment approach.

Changes made:
- Removed `§` symbol from generation examples and prompt — replaced with
  "Section" throughout (`src/generation.py`)
- Added reference source tagging — generator now tags each reference with
  `(Spec p.XX)`, `(NZ Standard)`, `(External code)`, or `(Contract)` so
  client can trace where each reference came from (`src/generation.py`)
- Added `duplicates_clutter` review category — reviewer now flags repeated
  inspection points, overlapping items, recommends merging
  (`src/prompts.py`, `src/schema.py`, `tests/test_schema.py`)
- Merged `feature/phase-2-generation` into `main` (`--no-ff`)
- Updated HANDOVER.md for next session

**Decided:**
- Deploy on Streamlit Community Cloud (free, fastest path, good enough for
  single-user internal tool). User considered Vercel/Supabase for learning
  but agreed this project is a poor fit — no database, no auth, Python app.
  Vercel/Supabase better suited to a future Next.js project with users and
  stored data. Railway noted as middle-ground if cloud learning is wanted.
- API key ownership still undecided — user's key or client's key. Set a
  usage limit on Anthropic dashboard either way.

**Verified:** 38 tests pass on main after merge. Client feedback changes
not yet tested with a live generation run.

**Not verified:**
- The three client feedback changes need a live test run (generate from
  Waitomo spec, check for no `§`, reference source tags, duplicate detection)

**Git:** 4 session commits on `feature/phase-2-generation`, merged to `main`
with `--no-ff`. 1 post-merge commit (HANDOVER.md). No remote configured.

## Session 3 — 2026-09-04/05 — Phase 2: ITP generation feature

**Did:** Brainstormed, designed, planned, and built ITP generation (Phase 2
feature) end-to-end via subagent-driven development on branch
`feature/phase-2-generation` in a git worktree. The feature reads a project
specification PDF and produces a full draft ITP with inspection items, hold
points, and acceptance criteria. User live-tested with the real 169-page
Waitomo Masterspec and sent the generated Word report to the client for
feedback.

Modules created:
- `src/gen_schema.py` — `ITPItem` (10 fields), `HoldPoint` (3 fields),
  `GENERATE_ITP_TOOL` definition
- `src/generation.py` — system prompt (ITP author persona), XML-tagged user
  message, `run_generation()` with streaming fallback for large specs
- `src/gen_report.py` — `to_markdown()`, `to_docx()`, `items_to_text()`
  (review bridge)
- `src/config.py` — added `GEN_MAX_TOKENS = 32000`
- `app.py` — rewritten with two tabs: "Generate ITP" and "Review ITP"
- Tests: `test_gen_schema.py` (4), `test_generation.py` (7),
  `test_gen_report.py` (8) — total suite 35 passed

**Decided:**
- Single-pass direct-context generation (spec fits in 200k window)
- Separate Generate/Review tabs with "Review this draft?" bridge
- Report output (markdown + docx) now; xlsx deferred until client sends template
- 8 hardcoded few-shot ITP example rows from GT Civil Riverside template
- Streaming fallback: try sync `create()` first, catch streaming-required
  error, retry with `stream()` — keeps mocks simple in tests
- `GEN_MAX_TOKENS = 32000` (16000 truncated on the real spec)

**Broke or found (fixed same session):**
- Worktree doesn't copy gitignored files — had to manually copy
  `.streamlit/secrets.toml` into the worktree
- First generation attempt returned empty — `GEN_MAX_TOKENS` too low (16000),
  increased to 32000 with truncation detection
- Second attempt hit "Streaming is required for operations that may take
  longer than 10 minutes" — added streaming fallback in `run_generation()`
- Streaming fix initially broke tests (`hasattr(mock, "stream")` always
  True) — switched to try/catch approach
- Dead `gen_schema` import in `app.py` — removed

**Verified:** Generation working end-to-end with real 169-page Masterspec
(spec-only, no supporting docs). User downloaded Word report and sent to
client. Full pytest suite: 35 passed, 1 skipped. Review tab not
regression-tested this session (unchanged logic, just wrapped in tab).

**Not verified:**
- Supporting documents feature (user reported it errors — not investigated)
- Review tab regression (logic unchanged, wrapped in tab)
- Client feedback on output quality pending

**Git:** 9 commits on `feature/phase-2-generation` from `main` at `d5e848b`.
Branch not merged. No remote configured.

## Session 2 — 2026-09-03 — Live validation, instructions, merge to main

**Did:** Ran the live end-to-end validation that Session 1 left pending;
added a collapsed "How to use this" instructions expander to `app.py`;
merged `feature/phase-1-build` into `main` (`--no-ff`, branch kept).
Advised the user on client delivery (demo live now; hosting = Phase 2).

**Decided:** Present to the client via a self-driven live demo for now —
do NOT host yet. Hosting deferred to Phase 2, scoped to three
prerequisites: authentication (none exists), the API-key/billing decision
(whose key pays), and a data-privacy line for client ITPs. See DECISIONS.

**Broke or found:** No matched ITP+proposal pair exists in `samples/` — it
holds two ITPs (Riverside WWPS `.xlsx`, Riverside Tauriko `.doc`) and three
construction drawing sets, but no written proposal/scope document. So the
proposal cross-check path stays unvalidated. Also: Streamlit's first-run
email prompt blocked the `!`-runner; fixed permanently with an empty-email
`~/.streamlit/credentials.toml`.

**Verified:** Live standalone review returned 22 categorized, advisory
findings on the real GT_Civil Riverside WWPS `.xlsx` — `claude-sonnet-5`
confirmed valid on the account (Session 1's main unverified assumption,
now resolved). Full pytest suite re-run after the UI edit: `17 passed`
(`.venv/Scripts/python -m pytest`).

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
