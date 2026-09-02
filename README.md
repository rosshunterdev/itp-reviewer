# ITP Reviewer

A Streamlit tool that runs an adversarial AI QA review on a draft Inspection
Test Plan (ITP) before it goes out to a client — catching the kind of gaps
the client's own AI reviewers tend to flag, so there's less back-and-forth.

Upload an ITP (`.xlsx`, `.pdf`, or `.docx`) and, optionally, a proposal /
scope-of-works file to cross-check against. The tool parses it, runs one
review pass, and returns categorized findings you can download as a report.

Phase 1 only — internal tool, single user, no auth, no persistence.

## Setup

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Edit `.streamlit/secrets.toml` and add your `ANTHROPIC_API_KEY`.

## Run

```bash
.venv\Scripts\streamlit run app.py
```

## Tests

```bash
.venv\Scripts\pytest
```
