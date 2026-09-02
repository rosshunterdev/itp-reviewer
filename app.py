import os
import streamlit as st
from src import parsing, review, report, schema

st.set_page_config(page_title="ITP Reviewer", layout="wide")
st.title("ITP Reviewer")
st.caption("Adversarial QA review of a draft Inspection Test Plan. Findings are advisory.")

with st.expander("How to use this"):
    st.markdown(
        """
1. **Upload your draft ITP** — Excel, PDF, or Word. Optionally add the matching
   proposal/scope to cross-check the two against each other.
2. **Open the preview** to confirm the table came through cleanly before reviewing.
3. **Click Review.** The tool reads the ITP the way an adversarial QA reviewer
   would and lists things worth a second look.
4. **Each finding** says what it saw, why it matters, and a suggested action.
   Download a report to share or file.

⚠️ Findings are **advisory, not pass/fail** — prompts for a qualified reviewer to
consider. Always apply your own engineering judgement.
"""
    )

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

itp_file = st.file_uploader("ITP file (required)", type=["xlsx", "pdf", "docx", "doc"])
proposal_file = st.file_uploader("Proposal / scope of works (optional)", type=["xlsx", "pdf", "docx", "doc"])


def _safe_parse(f, label):
    try:
        return parsing.parse(f.name, f.getvalue())
    except parsing.UnsupportedFormat as e:
        st.error(f"{label}: {e}")
        return None


itp_doc = proposal_doc = None
if itp_file:
    itp_doc = _safe_parse(itp_file, "ITP")
    if itp_doc:
        for w in itp_doc.warnings:
            st.warning(f"ITP: {w}")
        with st.expander("Preview parsed ITP text (check table fidelity before reviewing)"):
            st.text(itp_doc.preview[:20000])

if proposal_file:
    proposal_doc = _safe_parse(proposal_file, "Proposal")
    if proposal_doc:
        with st.expander("Preview parsed proposal text"):
            st.text(proposal_doc.preview[:20000])

mode = "Cross-check (ITP vs proposal)" if proposal_doc else "Standalone ITP review"
st.info(f"Mode: {mode}")

if "findings" not in st.session_state:
    st.session_state["findings"] = None

if st.button("Review", type="primary", disabled=itp_doc is None):
    try:
        with st.spinner("Running adversarial review…"):
            findings = review.run_review(
                itp_doc.text,
                proposal_doc.text if proposal_doc else None,
            )
        st.session_state["findings"] = findings
    except Exception as e:
        st.error(f"The review could not be completed. Check your ANTHROPIC_API_KEY and network connection, then try again.\n\nDetails: {e}")

if st.session_state.get("findings") is not None:
    findings = st.session_state["findings"]
    if not findings:
        st.success("No findings identified.")
    else:
        st.subheader(f"{len(findings)} finding(s)")
        by_cat = {c: [f for f in findings if f.category == c] for c in schema.CATEGORIES}
        for cat in schema.CATEGORIES:
            items = by_cat[cat]
            if not items:
                continue
            st.markdown(f"### {schema.CATEGORY_LABELS[cat]} ({len(items)})")
            for f in items:
                with st.expander(f"{f.location} — {f.observation[:60]}"):
                    st.markdown(f"**Observation:** {f.observation}")
                    st.markdown(f"**Why it matters:** {f.why_it_matters}")
                    st.markdown(f"**Suggested action:** {f.suggested_action}")
        st.download_button("Download markdown report", report.to_markdown(findings),
                           file_name="itp_review.md", mime="text/markdown")
        st.download_button("Download Word report", report.to_docx(findings),
                           file_name="itp_review.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
