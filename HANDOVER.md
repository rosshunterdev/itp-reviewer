# HANDOVER.md

## Current state

Phase 1 is built end-to-end via TDD: parsing (`.xlsx`/`.pdf`/`.docx`),
adversarial review with forced tool-use, categorized findings, markdown
and docx report downloads, and a Streamlit UI wiring it all together.
Full pytest suite passes. Not yet run live against the real API by the
user.

## Known limitations / next steps

1. **Proposal cross-check mode is built but not yet validated.** The
   `proposal_mismatch` category and the cross-check prompt path exist and
   are exercised by unit tests, but there is no real matched
   proposal/scope-of-works document to test against yet — only the ITP
   samples exist. Revisit once a real proposal file is available:
   run it through and sanity-check the findings the same way standalone
   review was checked.
2. **The review checklist is based on general ITP/construction QA
   knowledge, not calibrated against the client's own AI reviewer
   output.** The categories and what counts as a gap (missing witness
   point, vague acceptance criteria, etc.) were reasoned from first
   principles, not from a set of actual fix-lists the client's customers
   have sent back. Revisit and tune the prompt once real reviewer
   feedback exists to compare against.
3. **Legacy `.doc` files are not supported.** If the user has an old
   binary `.doc` ITP, the app returns a friendly error — re-save it as
   `.docx` in Word first. See DECISIONS.md for why this wasn't built.
4. **Live end-to-end review still needs manual validation.** The build
   was verified with unit/mocked tests. Nobody has yet run a real ITP
   through the app with a real `ANTHROPIC_API_KEY` and checked the actual
   findings for sanity, tone (advisory, not directive), and usefulness.
   That's the next concrete step before treating this as production-ready
   for real use.

## Next action

Add a real `ANTHROPIC_API_KEY` to `.streamlit/secrets.toml`, run
`.venv/Scripts/streamlit run app.py`, upload a real ITP sample, and read
the findings end to end.
