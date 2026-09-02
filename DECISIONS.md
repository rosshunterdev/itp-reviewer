# DECISIONS.md

Plain-language reasoning behind the choices in this build, for future-me.
Not a changelog — see git log / SESSION_LOG.md for that.

_Status (as of Session 1): every decision below is BUILT and covered by
the passing test suite. None is yet VERIFIED against a live API review —
that check is still pending the user's hands-on run._

## Direct-context prompting, not RAG

An ITP is a single document, at most a few thousand rows of table data.
That fits comfortably inside the model's context window in one shot. RAG
(chunking the document, embedding it, retrieving relevant chunks at query
time) exists to solve a problem this project doesn't have — documents too
large to fit in context, or a corpus to search across. Adding it here
would mean building and maintaining a retrieval pipeline that introduces
its own failure mode (the wrong chunks get retrieved and the review misses
something because it never saw it) for zero benefit. Simpler is correct,
not just easier.

## Forced tool-use, not prose JSON parsing

The alternative was asking the model to reply with a JSON blob in prose
and parsing that with `json.loads`. That's brittle in practice — models
wrap JSON in markdown code fences, add a sentence of preamble before the
JSON starts, or emit a trailing comma that breaks the parser. Forcing a
tool call (`tool_choice` pinned to `report_findings`) means the API itself
guarantees the response matches the declared schema every time. No
regex-stripping fences, no retry-on-parse-failure logic, no silent
partial-parse bugs. It moves the reliability problem from "written
defensively in my code" to "guaranteed by the API contract."

## Categorized findings, not a single score

A single QA score (e.g. "7/10") hides the thing that actually matters:
what to go fix. It also invites disputing the number itself rather than
acting on it. Categorized findings — grouped by `hold_witness`,
`acceptance_criteria`, `standards_reference`, `responsible_party`,
`internal_consistency`, `proposal_mismatch`, `other` — map directly to a
concrete fix action per finding, and line up with the categories the
client's own checklist already thinks in terms of. The output is
immediately actionable instead of needing translation.

## Parsing library choices

The original brief assumed pdfplumber (PDF) and python-docx (`.docx`)
would cover the real samples. They didn't: one real sample is `.xlsx`,
the other is a legacy binary `.doc`. `openpyxl` was added because the
client's actual ITP template is an Excel workbook — and an Excel grid is,
if anything, the cleanest possible table-preserving input, since rows and
columns are already structured data rather than something to reconstruct
from a rendered table. Legacy `.doc` (the old OLE2 binary Word format,
not the modern `.docx` zip/XML format) was excluded because python-docx
can only read `.docx`; reading `.doc` reliably needs external conversion
tooling (e.g. a LibreOffice/Word install to convert it first), which is
disproportionate infrastructure for a one-user internal tool. The app
returns a friendly error asking the user to re-save the file as `.docx`
instead — a five-second fix on their end versus a new dependency on ours.

## Model choice

`claude-sonnet-5`, held as a single constant in `src/config.py`, confirmed
against current model docs at build time. One place to change it if a
newer model should be used later.

## Parse-preview fidelity gate

Before any review runs, the UI shows a preview of the parsed text in an
expander so the user can visually confirm the table structure survived
parsing (e.g. all 12 ITP columns present) before trusting the review
output. Findings are only as good as the text the model actually sees —
this is a manual check against silent parsing damage, not an automated
one, because judging "did this table get mangled" is a task a human eye
is faster and more reliable at than writing a structural validator for.

## Accept `.doc` in the uploader (to deliver the friendly message)

`.doc` still isn't parsed (see "Parsing library choices"), but the
uploader now lists `doc` as an accepted type anyway. Reason: if it isn't
listed, Streamlit rejects the file itself with its own generic message,
and the carefully worded "please re-save as `.docx`" error never reaches
the user. Since the client's real ITP sample _is_ a `.doc`, that friendly
message is exactly the one they'll hit first. Listing `doc` lets the file
through to the parser, which raises the helpful error the UI then shows.
So the app accepts the upload only to give a better rejection.

## Graceful failure around the review API call

The call to the model is wrapped in try/except and surfaces failures as an
`st.error` message rather than letting them crash the app into a raw Python
traceback. The most likely real-world failures — an invalid/expired API
key, a rate limit, a dropped connection, or a model id that doesn't
resolve — all happen at exactly the moment the user is trying the tool for
the first time. A traceback there reads as "broken"; a plain-language
message reads as "here's what to fix." This also keeps any earlier
successful result on screen instead of wiping it on a later failure.
