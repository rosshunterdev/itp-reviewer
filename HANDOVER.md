# HANDOVER.md

_As of Session 2 (2026-09-03). See SESSION_LOG.md for what happened._

## Current state

Phase 1 is built, tested, **live-validated, and merged to `main`**. The
standalone review works end-to-end: a real `.xlsx` ITP produced 22
categorized, advisory findings against a real API key, and the
`claude-sonnet-5` model id is confirmed valid on the account. A collapsed
"How to use this" instructions block now sits at the top of the app.

**Verified:** live standalone review (22 findings); full pytest suite `17
passed`. **Not verified:** the proposal cross-check path — see next steps.

## Git state

- On `main`. `feature/phase-1-build` was merged with `--no-ff` (merge
  commit `e69d865`) and kept, not deleted.
- No git remote configured; nothing pushed anywhere.
- Working tree: session-doc edits from this close are the only pending
  changes (commit them as the last step).
- `samples/` and `.streamlit/secrets.toml` are gitignored. `secrets.toml`
  now exists locally with a real key (never committed).

## Next steps (ordered)

Both remaining Phase 1 items are blocked on **external files the user must
source** — there is no more code to write for them right now:

1. **Validate the proposal cross-check.** The path is built and
   unit-tested but has never run on real matched files. Needs one ITP plus
   its corresponding written proposal/scope. `samples/` has no such pair
   (two ITPs + three drawing sets only). Blocked until a real proposal
   file exists.
2. **Calibrate the checklist to the client's real output.** The categories
   were reasoned from general ITP QA knowledge, not from actual fix-lists
   the client's reviewers produce. This is the biggest quality lever before
   sending to the client. Needs one real reviewer fix-list to tune the
   prompt against. Blocked until that exists.

## Phase 2 (when it starts) — hosting

Deliver to the client by live demo for now (decided this session). Hosting
is deferred and scoped to three prerequisites, none of them code-hard:
authentication (none exists yet), the API-key/billing decision (whose key
pays), and a client data-privacy line. Cheapest hands-on route later:
Streamlit Community Cloud + a password, deployed from a private GitHub repo
(none configured yet). Full reasoning in DECISIONS.md.

## Known limitations / notes

- Legacy `.doc` isn't parsed by design — the app asks the user to re-save
  as `.docx` (see DECISIONS.md). The Riverside Tauriko sample is a `.doc`.
- Big sample PDFs are construction drawings, likely image/vector-heavy;
  not useful as proposal-text input even if uploaded.
- `app.py` re-parses uploads on each rerun (no `@st.cache_data`); no
  download button at zero findings. Harmless for single-user Phase 1.

_SDD ledger + per-task reports preserved under
`.superpowers/sdd/2026-09-02-itp-reviewer/`._
