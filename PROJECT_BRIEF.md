# Project: Bulletproof ITP (working name, rename if you prefer "itp-reviewer")

## Context

I'm building a tool for a construction industry client. His clients have started running his ITPs (Inspection Test Plans) through their own AI reviewers before accepting them, and sending back a list of things to fix. He wants an AI reviewer on his side that catches the same class of issues before the document goes out, so the back-and-forth shrinks.

This is Phase 1 of a larger vision (the client also wants a persistent "project buddy" assistant later), but Phase 1 is the only validated, real pain point. Build only Phase 1. Everything else is explicitly out of scope, see below.

## Explicit scope

Build a tool that:
1. Takes a draft ITP file (PDF or Word) as input.
2. Optionally takes a project proposal / scope of works file as a second input.
3. Runs an LLM review pass that finds gaps, inconsistencies, and likely points of client pushback.
4. Outputs categorized, structured findings the user can read and act on.
5. Has a simple Streamlit interface: upload file(s), click review, see results, download a report.

## Tech stack

- Python
- Anthropic SDK (`anthropic` package) for the LLM calls. Use the current Claude Sonnet model (as of writing, `claude-sonnet-5`), check for a newer default if one's available when you're actually building.
- Streamlit for the interface (matches how I've built similar tools before).
- Document parsing: start with `pdfplumber` and/or `python-docx` (free, simple, table-aware). ITPs are typically table-heavy (item, hold/witness point, test method, standard reference, acceptance criteria, responsible party), so table structure has to survive parsing. Only reach for a paid parsing service if these prove unreliable against the real sample file, and if you do, log why in DECISIONS.md.

## Input handling

- ITP file: required.
- Proposal file: optional. I don't have a matched proposal yet, only the ITP example. Build the proposal-cross-check as a real feature (it should activate and produce mismatch findings when a proposal is provided), but when no proposal is given, the tool should fall back to a standalone ITP quality review using the checklist below. Both modes need to actually work, I'll test standalone mode first since that's what I can validate today.

## Review logic

System prompt should frame the model as a strict, adversarial QA auditor whose job is to find every gap that would draw scrutiny, not a helpful assistant being asked to "review this document." That framing measurably changes how much gets flagged, don't soften it.

Structure the user message with XML tags separating the inputs clearly, e.g. `<itp>...</itp>` and `<proposal>...</proposal>` if present. This keeps the model from conflating the two documents.

Checklist to check for (standalone mode, and extend for cross-check mode when a proposal is present):
- Are required hold points and witness points explicitly and specifically stated?
- Is acceptance criteria specific and measurable, or vague?
- Are relevant standards/codes referenced at all (the model can't verify a code number is *correct* without a reference document, don't claim it can, just flag when a reference is missing or looks generic)?
- Is a responsible party identified for each check/inspection?
- Internal consistency: contradictions in sequencing, dates, or referenced stages.
- (Cross-check mode only) Does the ITP's inspection/test coverage actually match the methodology and scope described in the proposal? Flag anything proposed that isn't reflected in an inspection point, and vice versa.

Output must be structured, not free text. Use the Anthropic SDK's tool-use (forced tool call / JSON schema) to get reliable structured output, don't rely on asking the model to "return JSON" in prose and parsing it, that's brittle. Each finding should include: section/location reference, category (one of the checklist areas above, or "other"), what was noticed, why it might matter, and a suggested action phrased as advisory, not a directive. E.g. "consider specifying a witness point here" not "this must be fixed." That advisory framing is a deliberate product requirement from the client, not a style nitpick, keep it consistent everywhere the findings surface.

## Output / UI

Streamlit single page: file upload for ITP (required), file upload for proposal (optional), a "Review" button, results displayed grouped by category, and a button to download the findings as a markdown or simple docx report. Keep the UI plain, this is an internal efficiency tool for one user right now, not a product.

## Documentation (important, this is a learning project for me)

Maintain the usual CLAUDE.md, DECISIONS.md, SESSION_LOG.md, and HANDOVER.md files as you build. In DECISIONS.md specifically, explain the reasoning in plain language, not terse commit-style notes, since I'm using this to understand the "why" later, not just the "what." At minimum log the reasoning behind: why direct-context prompting instead of RAG, why tool-use/forced JSON instead of prose parsing, why categorized findings instead of a score, and any parsing library decision.

At the end, in HANDOVER.md, include a clear "known limitations / next steps" section noting: (1) proposal cross-check mode is built but not yet validated against a real matched proposal, and (2) the review checklist is currently based on general ITP/construction QA knowledge, not calibrated against any real example of what the client's own AI reviewer has actually flagged, both should be revisited once that data exists.

## Testing

Test against the one real ITP file I'll provide, in standalone mode. Confirm parsing preserves table structure correctly before trusting the review output, if the parser mangles the tables, the review quality will look fine but be reviewing garbage input, check this explicitly rather than assuming it worked.

## Before you start

If anything above is ambiguous or you're about to make an architectural call I haven't specified, ask me rather than guessing.
