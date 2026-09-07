# HANDOVER.md

_As of Session 5 (2026-09-07). See SESSION_LOG.md for what happened._

## Current state

App is **live on Streamlit Community Cloud** at https://itp-reviewer.streamlit.app/.
Password-protected. Waiting on client to send their Anthropic API key
(instructions sent, awaiting response).

## Git state

- Branch: `main` (up to date with `origin/main`)
- Remote: `origin` → `github.com/rosshunterdev/itp-reviewer` (private)
- Working tree: clean (untracked: `.claude/`, `docs/new-download/`)
- `.streamlit/secrets.toml` gitignored, contains local `ANTHROPIC_API_KEY`

## What was done this session

1. **Created GitHub repo** — private, at `rosshunterdev/itp-reviewer`, pushed
   all commits to `origin/main`
2. **Removed `pytest` from `requirements.txt`** — not needed in production
3. **Added password gate** — `app.py` reads `PASSWORD` from `st.secrets`,
   blocks the app behind a login screen when set, skips gracefully for local dev
4. **Deployed to Streamlit Community Cloud** — user deployed manually at
   https://itp-reviewer.streamlit.app/
5. **Decided: client provides their own API key** — user's Anthropic credits
   running low. Client instructed to create an Anthropic account, generate a
   key, and share it via onetimesecret.com (self-destructing link)

## What needs doing next (ordered by priority)

### 1. Add client's API key to Streamlit Cloud secrets (blocked — waiting on client)

Client has been sent instructions to:
- Create an Anthropic account at console.anthropic.com
- Generate an API key
- Share it via onetimesecret.com

Once received, add to Streamlit Cloud: Manage app → Settings → Secrets:
```
ANTHROPIC_API_KEY = "the-client-key"
PASSWORD = "the-password"
```

### 2. Test the three client feedback changes (live)

The client feedback changes from Session 4 (no `§`, reference source tags,
duplicate detection) were committed but never tested with a live generation run.
Run the app on Streamlit Cloud, upload the Waitomo spec, generate, and verify:
- No `§` symbols appear anywhere
- References show source tags like `(Spec p.47)`, `(NZ Standard)`
- "Review this draft?" catches duplicates under the new category

### 3. New client documents

`docs/new-download/` contains 4 new PDFs (untracked, not investigated):
- Waitomo Whakatane FC Drawings
- Building Consent (Form 5)
- Specifications (final set)
- important-page-1.pdf

May be relevant for testing generation or as supporting documents.

### 4. Cleanup

- `.claude/worktrees/feature+phase-2-generation` worktree can be deleted
- `.claude/` directory is untracked — decide whether to commit or gitignore

### 5. Future: gap analysis and auto-fix

Two other features the client requested from the Phase 1 demo. Not started.
See memory file `phase-2-client-direction.md`.

## Known limitations

- Legacy `.doc` isn't parsed — app asks user to re-save as `.docx`
- Password gate is simple shared password, not per-user auth
- Few-shot examples are hardcoded from one GT Civil ITP template
- `app.py` re-parses uploads on each Streamlit rerun (no caching)
- Free tier sleeps after inactivity (~30s cold start)

## Architecture quick reference

- `app.py` — password gate + two tabs: Generate ITP, Review ITP
- `src/generation.py` — generation prompt + API call (streaming fallback)
- `src/gen_schema.py` — ITPItem, HoldPoint, GENERATE_ITP_TOOL
- `src/gen_report.py` — markdown, docx, xlsx output + items_to_text bridge
- `src/prompts.py` — adversarial reviewer prompt (with duplicate detection)
- `src/schema.py` — Finding, CATEGORIES (8 including duplicates_clutter)
- `src/review.py` — reviewer API call
- `src/report.py` — review findings to markdown/docx
- `src/config.py` — MODEL, MAX_TOKENS, GEN_MAX_TOKENS

_Design spec: `docs/superpowers/specs/2026-09-04-itp-generation-design.md`_
_Implementation plan: `docs/superpowers/plans/2026-09-04-itp-generation.md`_
