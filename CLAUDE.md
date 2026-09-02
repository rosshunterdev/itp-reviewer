# CLAUDE.md — ITP Reviewer

Project-specific guidance. Read alongside the global `~/.claude/CLAUDE.md`.

## What this is

A Streamlit tool that runs an adversarial AI QA review on a construction
ITP (Inspection Test Plan), producing categorized findings instead of a
score. Phase 1, single internal user. See `PROJECT_BRIEF.md` and
`docs/superpowers/specs/2026-09-02-itp-reviewer-design.md` for the full
design.

## Run it

```bash
.venv/Scripts/streamlit run app.py
```

## Run tests

```bash
.venv/Scripts/pytest
```

## Module map

- `app.py` — Streamlit UI only. Upload, parse-preview expander, Review
  button, findings grouped by category, download-report button.
- `src/config.py` — model name (`MODEL`), `MAX_TOKENS`, supported file
  extensions. **The model constant lives here** — change it in one place.
- `src/parsing.py` — extension dispatch (`.xlsx` / `.pdf` / `.docx`) to a
  normalized, table-preserving text string plus a UI preview. `.doc`
  (legacy binary) returns a friendly error — see DECISIONS.md.
- `src/prompts.py` — adversarial system prompt + XML-tagged user-message
  builder (`<itp>...</itp>`, optional `<proposal>...</proposal>`).
- `src/schema.py` — `Finding` shape, category enum, forced tool-use
  definition (`REVIEW_TOOL`).
- `src/review.py` — calls the Anthropic API, forces the tool, returns
  `list[Finding]`.
- `src/report.py` — findings to markdown (`to_markdown`) and optional
  docx (`to_docx`).

## Secrets

`ANTHROPIC_API_KEY` lives in `.streamlit/secrets.toml`, which is
gitignored. `.streamlit/secrets.toml.example` shows the expected shape —
copy it and fill in your key, never commit the real file.

## Samples

`samples/` holds real client ITP/proposal files used for local testing.
Gitignored — never commit anything from this folder.

## Notes

- No RAG, no persistence, no auth — see `DECISIONS.md` for why.
- Advisory phrasing ("consider specifying...") is enforced in the prompt
  and expected in all findings output — don't let report changes drift
  into directive language.
