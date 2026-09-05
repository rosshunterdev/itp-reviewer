# HANDOVER.md

_As of Session 3 (2026-09-05). See SESSION_LOG.md for what happened._

## Current state

Phase 2 ITP generation feature is **built and live-tested** on branch
`feature/phase-2-generation` (git worktree at
`.claude/worktrees/feature+phase-2-generation`). The user generated a
full draft ITP from the real 169-page Waitomo Masterspec and sent the
Word report to the client for feedback. **Not yet merged to `main`.**

Full pytest suite: **35 passed, 1 skipped** (xlsx sample file check).

## Git state

- Branch: `feature/phase-2-generation` (9 commits ahead of `main`)
- Worktree: `.claude/worktrees/feature+phase-2-generation`
- Working tree: clean
- No git remote configured; nothing pushed
- `.streamlit/secrets.toml` must be copied into the worktree manually
  (gitignored, not inherited)

## What's on the branch

New files:
- `src/gen_schema.py` — ITPItem (10 fields), HoldPoint, GENERATE_ITP_TOOL
- `src/generation.py` — generation prompt, API call with streaming fallback
- `src/gen_report.py` — markdown, docx, and text-bridge output
- Tests: `test_gen_schema.py`, `test_generation.py`, `test_gen_report.py`

Modified:
- `src/config.py` — added `GEN_MAX_TOKENS = 32000`
- `app.py` — rewritten with two tabs (Generate ITP / Review ITP)

Key design: streaming fallback in `run_generation()` — tries sync
`create()` first, catches streaming-required errors for large specs
(>10 min), retries with `stream()`. This keeps test mocks simple.

## What needs doing next (ordered by priority)

### 1. Fix supporting documents error (bug)
The user reported an error when adding supporting documents alongside the
spec. Not investigated yet. Likely a parsing issue with one of the uploaded
files, or the combined input exceeding token limits. Reproduce by uploading
the Masterspec plus any PDF from `samples/` as a supporting doc.

### 2. Wait for client feedback
The user sent the generated Word report to the client. Waiting on:
- Does the level of detail match what they'd normally put in an ITP?
- Does the client want a specific template/format? (asked them to send one)
- The Cosgroves engineer spec — without it, the generator only covers
  architectural items, missing civil/structural (earthworks, drainage, etc.)

### 3. Regression-test the Review tab
The review tab logic is unchanged from Phase 1 but is now wrapped in a
Streamlit tab. Should be tested live to confirm nothing broke. Upload
the GT Civil `.xlsx` and verify 22-ish findings still appear.

### 4. Merge to main
Once items 1 and 3 are done, merge `feature/phase-2-generation` into
`main` with `--no-ff`. Use the `finishing-a-development-branch` skill.

### 5. Future: xlsx output format
The client likely wants the ITP in their existing xlsx template format
(GT Civil template has 5 sheets, 12-column structure). Deferred until
they send an empty template. Currently outputs markdown and docx only.

### 6. Future: gap analysis and auto-fix
Two other features the client requested from the Phase 1 demo. Gap
analysis (compare spec vs ITP to find missing coverage) and auto-apply
review fixes. Not started. See memory file `phase-2-client-direction.md`.

## Known limitations

- Legacy `.doc` isn't parsed — app asks user to re-save as `.docx`
- Supporting documents feature untested/potentially broken (see item 1)
- No auth, no hosting — delivered via live demo only
- Few-shot examples are hardcoded from one GT Civil ITP template
- `app.py` re-parses uploads on each Streamlit rerun (no caching)

_SDD ledger + per-task reports preserved under
`.superpowers/sdd/2026-09-04-itp-generation/`._
_Design spec: `docs/superpowers/specs/2026-09-04-itp-generation-design.md`_
_Implementation plan: `docs/superpowers/plans/2026-09-04-itp-generation.md`_
