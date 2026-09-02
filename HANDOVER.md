# HANDOVER.md

_As of Session 1 (2026-09-02). See SESSION_LOG.md for what happened._

## Current state

Phase 1 is built end-to-end and merge-ready on `feature/phase-1-build`:
parsing (`.xlsx`/`.pdf`/`.docx`, table-preserving, friendly `.doc`
message), adversarial review via forced tool-use, categorized advisory
findings, markdown + docx report downloads, and a Streamlit UI wiring it
together with results persisted across reruns.

**Verified:** full pytest suite `17 passed`; real `.xlsx` parses with all
12 ITP columns intact. **Not verified:** a live review with a real API key
(see next action).

## Git state

- Branch `feature/phase-1-build`, 11 commits, forked from `main` at
  `b623665`. Kept as-is (user's choice) — NOT merged to `main`.
- No git remote configured; nothing pushed.
- Working tree clean.
- `samples/` and `.streamlit/secrets.toml` are gitignored (client files /
  secret). Only `secrets.toml.example` is committed.

## Next action (the one thing to do next)

Run the live validation — a subagent couldn't, it needs a real key:
1. `copy .streamlit\secrets.toml.example .streamlit\secrets.toml`, add your
   `ANTHROPIC_API_KEY`.
2. `.venv\Scripts\streamlit run app.py`
3. Upload `samples\GT_Civil_..._ITP_Template.xlsx`, open the parse-preview
   expander, confirm the table looks right.
4. Click Review (standalone mode); check findings are categorized,
   advisory ("consider…"), and relevant.

**Watch:** the model constant is `claude-sonnet-5` (`src/config.py`). If the
first review errors with model-not-found, that's the id to update — it now
shows as a clean `st.error`, not a crash. This is the main unverified
assumption in the build.

## Known limitations / next steps

1. **Proposal cross-check is built but unvalidated.** The
   `proposal_mismatch` path exists and is unit-tested, but there's no real
   matched proposal to test against yet. Revisit when one exists.
2. **The checklist isn't calibrated to the client's real reviewer output.**
   Categories/gaps were reasoned from general ITP QA knowledge, not from
   actual fix-lists the client's customers have sent back. Tune the prompt
   once that data exists.
3. **Legacy `.doc` isn't parsed.** The uploader accepts it but the app
   returns a friendly "re-save as `.docx`" message. To test the Word path,
   re-save `samples\ITP 1_ Riverside Tauriko PS.doc` as `.docx`.

## Deferred minors (from review — none block use)

- No direct unit test for the PDF empty-content warning path (verified by
  inspection).
- docx report empty-case and grouping paths untested (markdown paths are).
- `app.py` re-parses uploads on each rerun (no `@st.cache_data`); no
  download button when there are zero findings; on-screen category grouping
  lacks the `"other"` fallback the report has (harmless — enum-constrained).

_SDD ledger + per-task reports preserved under
`.superpowers/sdd/2026-09-02-itp-reviewer/` until the branch is merged._
