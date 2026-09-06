# HANDOVER.md

_As of Session 4 (2026-09-07). See SESSION_LOG.md for what happened._

## Current state

Phase 2 ITP generation feature is **merged to `main`**. 38 tests pass.
Client has seen a live demo and provided feedback (all three items
addressed this session). App is feature-complete and ready for deployment.

## Git state

- Branch: `main` (up to date, feature branch merged)
- Worktree: `.claude/worktrees/feature+phase-2-generation` still exists (can be cleaned up)
- Working tree: clean (untracked: `.claude/`, `docs/new-download/`)
- No git remote configured; nothing pushed
- `.streamlit/secrets.toml` gitignored, contains `ANTHROPIC_API_KEY`

## What was done this session

1. **Removed `§` symbol** from generation examples and prompt — replaced
   with "Section" throughout (`src/generation.py`)
2. **Added reference source tagging** — generator now tags each reference
   with `(Spec p.XX)`, `(NZ Standard)`, `(External code)`, or `(Contract)`
   so the client can trace where each reference came from
3. **Added duplicate/clutter detection** — new `duplicates_clutter` category
   in the reviewer (`src/prompts.py`, `src/schema.py`) that flags repeated
   inspection points, overlapping items, and recommends merging
4. **Merged `feature/phase-2-generation` to `main`** with `--no-ff`

## What needs doing next (ordered by priority)

### 1. Deploy to Streamlit Community Cloud (immediate)

Decision made: deploy on Streamlit Cloud so the client can use it themselves.

Steps:
1. Push repo to GitHub (private repo)
2. Go to share.streamlit.io, connect the GitHub repo
3. Set `ANTHROPIC_API_KEY` as a secret in the Streamlit Cloud dashboard
4. Set main file to `app.py`
5. Share the URL with the client

Considerations:
- **API key ownership** — decide whether the user's key or the client's key
  is used. Set a usage limit on the Anthropic dashboard either way.
- App URL is public but unlisted (no directory). Fine for single-user internal
  tool. If auth is needed later, migrate to Railway or Azure.
- Free tier sleeps after inactivity — first load after sleep takes ~30s.

### 2. Test the three client feedback changes

The client feedback changes (no `§`, reference source tags, duplicate
detection) were committed but not yet tested with a live generation run.
Run the app, upload the Waitomo spec, generate, and verify:
- No `§` symbols appear anywhere
- References show source tags like `(Spec p.47)`, `(NZ Standard)`
- "Review this draft?" catches duplicates under the new category

### 3. Future: gap analysis and auto-fix

Two other features the client requested from the Phase 1 demo. Gap
analysis (compare spec vs ITP to find missing coverage) and auto-apply
review fixes. Not started. See memory file `phase-2-client-direction.md`.

## Known limitations

- Legacy `.doc` isn't parsed — app asks user to re-save as `.docx`
- No auth, no hosting yet — local only until deployment
- Few-shot examples are hardcoded from one GT Civil ITP template
- `app.py` re-parses uploads on each Streamlit rerun (no caching)

## Architecture quick reference

- `app.py` — two tabs: Generate ITP, Review ITP
- `src/generation.py` — generation prompt + API call (streaming fallback)
- `src/gen_schema.py` — ITPItem, HoldPoint, GENERATE_ITP_TOOL
- `src/gen_report.py` — markdown, docx, xlsx output + items_to_text bridge
- `src/prompts.py` — adversarial reviewer prompt (now with duplicate detection)
- `src/schema.py` — Finding, CATEGORIES (now 8 including duplicates_clutter)
- `src/review.py` — reviewer API call
- `src/report.py` — review findings to markdown/docx
- `src/config.py` — MODEL, MAX_TOKENS, GEN_MAX_TOKENS

_Design spec: `docs/superpowers/specs/2026-09-04-itp-generation-design.md`_
_Implementation plan: `docs/superpowers/plans/2026-09-04-itp-generation.md`_
