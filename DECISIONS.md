# DECISIONS.md

Plain-language reasoning behind the choices in this build, for future-me.
Not a changelog — see git log / SESSION_LOG.md for that.

_Status (as of Session 4): Phase 1 and Phase 2 decisions are all BUILT,
TESTED, and MERGED to main. Client feedback changes (reference tagging,
duplicate detection) are committed but not yet live-tested. Deployment
decision made: Streamlit Community Cloud._

## Phase 1 decisions

### Direct-context prompting, not RAG

An ITP is a single document, at most a few thousand rows of table data.
That fits comfortably inside the model's context window in one shot. RAG
(chunking the document, embedding it, retrieving relevant chunks at query
time) exists to solve a problem this project doesn't have — documents too
large to fit in context, or a corpus to search across. Adding it here
would mean building and maintaining a retrieval pipeline that introduces
its own failure mode (the wrong chunks get retrieved and the review misses
something because it never saw it) for zero benefit. Simpler is correct,
not just easier.

### Forced tool-use, not prose JSON parsing

The alternative was asking the model to reply with a JSON blob in prose
and parsing that with `json.loads`. That's brittle in practice — models
wrap JSON in markdown code fences, add a sentence of preamble before the
JSON starts, or emit a trailing comma that breaks the parser. Forcing a
tool call (`tool_choice` pinned to `report_findings`) means the API itself
guarantees the response matches the declared schema every time. No
regex-stripping fences, no retry-on-parse-failure logic, no silent
partial-parse bugs. It moves the reliability problem from "written
defensively in my code" to "guaranteed by the API contract."

### Categorized findings, not a single score

A single QA score (e.g. "7/10") hides the thing that actually matters:
what to go fix. It also invites disputing the number itself rather than
acting on it. Categorized findings — grouped by `hold_witness`,
`acceptance_criteria`, `standards_reference`, `responsible_party`,
`internal_consistency`, `proposal_mismatch`, `other` — map directly to a
concrete fix action per finding, and line up with the categories the
client's own checklist already thinks in terms of. The output is
immediately actionable instead of needing translation.

### Parsing library choices

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

### Model choice

`claude-sonnet-5`, held as a single constant in `src/config.py`, confirmed
against current model docs at build time. One place to change it if a
newer model should be used later.

### Parse-preview fidelity gate

Before any review runs, the UI shows a preview of the parsed text in an
expander so the user can visually confirm the table structure survived
parsing (e.g. all 12 ITP columns present) before trusting the review
output. Findings are only as good as the text the model actually sees —
this is a manual check against silent parsing damage, not an automated
one, because judging "did this table get mangled" is a task a human eye
is faster and more reliable at than writing a structural validator for.

### Accept `.doc` in the uploader (to deliver the friendly message)

`.doc` still isn't parsed (see "Parsing library choices"), but the
uploader now lists `doc` as an accepted type anyway. Reason: if it isn't
listed, Streamlit rejects the file itself with its own generic message,
and the carefully worded "please re-save as `.docx`" error never reaches
the user. Since the client's real ITP sample _is_ a `.doc`, that friendly
message is exactly the one they'll hit first. Listing `doc` lets the file
through to the parser, which raises the helpful error the UI then shows.
So the app accepts the upload only to give a better rejection.

### Graceful failure around the review API call

The call to the model is wrapped in try/except and surfaces failures as an
`st.error` message rather than letting them crash the app into a raw Python
traceback. The most likely real-world failures — an invalid/expired API
key, a rate limit, a dropped connection, or a model id that doesn't
resolve — all happen at exactly the moment the user is trying the tool for
the first time. A traceback there reads as "broken"; a plain-language
message reads as "here's what to fix." This also keeps any earlier
successful result on screen instead of wiping it on a later failure.

### Deliver by live demo now; defer hosting to Phase 2 (Session 2)

The question was how to get the tool to the client. Decision: present it
by driving it live (screen-share or in person) rather than hosting it and
handing over a URL. Reason: hosting turns three things that don't exist
into hard prerequisites, and none is a code problem —

1. **Auth.** The app has none. A public URL means anyone who finds it can
   run reviews on our API key, i.e. spend our money. A password gate is
   non-negotiable before any public deployment.
2. **API key / billing.** The app uses our Anthropic key. Client hands-on
   use spends our credits until we decide: our key (and bill him) or his
   own key. A business call, not a technical one.
3. **Data privacy.** Client ITPs are sent to Anthropic's API. Fine
   (no training on API data), but it should be stated to the client
   plainly, not discovered.

Phase 1's brief is a single internal user, so a live demo is in-scope and
hosting is genuinely a later phase. When Phase 2 starts, the cheapest
hands-on path is Streamlit Community Cloud (deploys from a private GitHub
repo) with a password added first; a fuller cloud host (Azure Container
Apps / Render) is the alternative if more control is wanted. No remote is
configured yet, so any hosting route starts with pushing to a repo.

## Phase 2 decisions

### Single-pass generation, not multi-pass or chunking (Session 3)

The real Masterspec is 169 pages / ~443k chars. At ~4 chars per token
that's ~110k tokens — well within the 200k context window with room for
the system prompt, few-shot examples, and the 32k output budget. A single
API call is simpler to build, test, and debug than chunking the spec or
running multiple passes that need merging. If specs grow past ~600 pages
this will need revisiting, but that's unlikely for construction ITPs.

### Streaming fallback for large specs (Session 3)

The Anthropic API requires streaming for requests that may take >10 min.
The 169-page spec hits this. Rather than always streaming (which would
complicate test mocks), `run_generation()` tries sync `create()` first and
catches the streaming-required error by string matching, retrying with
`stream()`. This keeps unit tests simple (mocks use `create()`) while
handling real large specs. The alternative — detecting input size
up-front — would need a tokenizer dependency and a threshold that's
fragile across model versions.

### Separate tabs with review bridge, not a combined workflow (Session 3)

Generate and Review are conceptually different tasks (author vs. critic),
so they live in separate tabs. But the "Review this draft?" button on the
Generate tab bridges them: it converts generated items to text via
`items_to_text()` and feeds that to the existing `run_review()`. This
reuses the Phase 1 review pipeline without duplication and lets the user
get an adversarial check on the generated ITP without switching tabs or
downloading/re-uploading.

### Report output now, xlsx deferred (Session 3)

The client likely wants xlsx output in their GT Civil template format
(5 sheets, 12-column structure). Building that requires the actual
template file, which we don't have yet — asked the client to send one.
Markdown and docx are built now since they can be generated from the
data structure alone without a template. xlsx will be added when the
template arrives.

### GEN_MAX_TOKENS = 32000 (Session 3)

Initially set to 16000 (matching Phase 1's style). The 169-page Masterspec
produces 50+ ITP items, and the model hit `max_tokens` at 16000, returning
a truncated (unusable) response. Doubled to 32000. Added truncation
detection: if `stop_reason == "max_tokens"`, raise an explicit error
rather than silently returning partial results.

### Reference source tagging in generated ITPs (Session 4)

Client feedback: they couldn't tell whether a reference came from the
uploaded spec or from the model's training knowledge. Added prompt
instructions to tag each reference with its source: `(Spec p.XX)` for
items found in the spec (with page number), `(NZ Standard)` for NZ
standards, `(External code)` for council/engineering codes, `(Contract)`
for contract documents. This is a prompt-level solution — the model
approximates page numbers from context position. Not perfectly accurate
but gives the client a starting point to verify.

### Duplicates & clutter review category (Session 4)

Client asked the reviewer to flag double-up points and areas of confusion.
Added `duplicates_clutter` as a dedicated category (8 total now) rather
than lumping these under `internal_consistency` or `other`. Distinct
category means these findings get their own section heading in the output,
making them easy to find and act on.

### Deploy on Streamlit Community Cloud (Session 4)

Evaluated Streamlit Cloud, Railway, Render, Azure App Service, and
self-hosted VPS. Chose Streamlit Cloud because: (a) free, (b) fastest
setup (~15 min), (c) zero infrastructure to manage, (d) the app is a
single-user internal tool so "public but unlisted URL" is fine. The URL
won't appear in any directory — only people with the link can access it.

Trade-offs accepted: no custom domain on free tier, US servers (not NZ/AU),
sleeps after inactivity (~30s cold start). These are acceptable for the
current use case. Migration path to Railway or Azure is straightforward if
auth, custom domain, or data sovereignty becomes a requirement.

User considered Vercel/Supabase for learning cloud development but agreed
this project is a poor fit — it's a Python/Streamlit app with no database,
no auth, no user accounts. Those tools shine for Next.js apps with users
and stored data.

### Password gate, not open access (Session 5)

The Streamlit Cloud URL is public but unlisted. Without protection, anyone
who discovers the URL can trigger API calls on the configured key. Added a
simple shared-password gate: `app.py` reads `PASSWORD` from `st.secrets` and
blocks the entire app behind a login screen. Chose this over per-user auth
because the app has one user (the client). The password lives in Streamlit
Cloud's encrypted secrets, not in code. Gracefully skips when `PASSWORD` is
not set, so local development is unaffected.

### Client-owned API key (Session 5)

User's Anthropic credits running low. Decided the client should create their
own Anthropic account and API key, billed to the client directly. Key is
shared once via onetimesecret.com (self-destructing link), then added to
Streamlit Cloud secrets by the developer. Considered alternatives: (a) adding
a key input field to the app UI — rejected because the client would have to
paste it every session or we'd need persistent storage, and (b) giving the
client Streamlit Cloud dashboard access — rejected because it exposes more
than needed. One-time secure transfer is the simplest path.

### Few-shot examples hardcoded in prompt (Session 3)

Eight representative rows from the GT Civil Riverside ITP template are
embedded directly in the generation system prompt as `ITP_EXAMPLES`. This
gives the model a concrete reference for format, column structure, level
of detail, and the kind of acceptance criteria expected. Hardcoded rather
than loaded from a file because: (a) these rows are stable reference
material, not something that changes between runs; (b) loading from the
real xlsx would need parsing logic just for examples; (c) the examples
serve as documentation of what "good" looks like.
