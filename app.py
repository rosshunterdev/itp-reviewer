import os
import streamlit as st
from src import parsing, review, report, schema
from src import generation, gen_report

st.set_page_config(page_title="ITP Reviewer", layout="wide")
st.title("ITP Reviewer")

if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

tab_generate, tab_review = st.tabs(["Generate ITP", "Review ITP"])


def _safe_parse(f, label):
    try:
        return parsing.parse(f.name, f.getvalue())
    except parsing.UnsupportedFormat as e:
        st.error(f"{label}: {e}")
        return None


# ── Generate tab ──────────────────────────────────────────────────────

with tab_generate:
    st.caption(
        "Generate a draft ITP from a project specification. "
        "Findings are advisory."
    )

    with st.expander("How to use this"):
        st.markdown(
            """
1. **Upload the project specification** — the PDF spec that describes
   the work to be done (e.g. a Masterspec document).
2. **Optionally add supporting documents** — building consent, drawings,
   or an engineer's spec. These give the generator extra context.
3. **Open the preview** to confirm the text came through cleanly.
4. **Click Generate.** The tool reads the spec and produces a draft ITP
   with inspection items, hold/witness points, and acceptance criteria.
5. **Download the report** to review and refine.
6. **Click "Review this draft?"** to run the adversarial QA reviewer on
   the generated ITP and catch any gaps.

⚠️ The generated ITP is a **starting draft** — always review and refine
with your own engineering judgement before use.
"""
        )

    spec_file = st.file_uploader(
        "Project specification (required)",
        type=["pdf", "docx", "xlsx"],
        key="gen_spec",
    )
    support_files = st.file_uploader(
        "Supporting documents (optional — building consent, drawings, engineer's spec)",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        key="gen_support",
    )

    spec_doc = None
    if spec_file:
        spec_doc = _safe_parse(spec_file, "Specification")
        if spec_doc:
            for w in spec_doc.warnings:
                st.warning(f"Specification: {w}")
            with st.expander(
                "Preview parsed specification (check text fidelity)"
            ):
                st.text(spec_doc.preview[:20000])

    support_docs = []
    for sf in support_files:
        sd = _safe_parse(sf, sf.name)
        if sd:
            support_docs.append((sf.name, sd))
            with st.expander(f"Preview: {sf.name}"):
                st.text(sd.preview[:10000])

    if "gen_items" not in st.session_state:
        st.session_state["gen_items"] = None
        st.session_state["gen_hps"] = None

    if st.button("Generate ITP", type="primary", disabled=spec_doc is None):
        try:
            supporting_texts = (
                [(name, sd.text) for name, sd in support_docs]
                if support_docs
                else None
            )
            with st.spinner("Generating ITP from specification…"):
                items, hps = generation.run_generation(
                    spec_doc.text, supporting_texts
                )
            st.session_state["gen_items"] = items
            st.session_state["gen_hps"] = hps
        except Exception as e:
            st.error(
                "Generation could not be completed. Check your "
                "ANTHROPIC_API_KEY and network connection, then try again."
                f"\n\nDetails: {e}"
            )

    if st.session_state.get("gen_items") is not None:
        items = st.session_state["gen_items"]
        hps = st.session_state["gen_hps"]
        if not items:
            st.warning("No ITP items were generated.")
        else:
            st.subheader(f"{len(items)} item(s) generated")

            groups = {}
            for item in items:
                groups.setdefault(item.work_package, []).append(item)

            for wp, wp_items in groups.items():
                st.markdown(f"### {wp} ({len(wp_items)})")
                for item in wp_items:
                    label = f"{item.item_number} — {item.inspection_test}"
                    with st.expander(label):
                        st.markdown(
                            f"**Acceptance Criteria:** {item.acceptance_criteria}"
                        )
                        st.markdown(f"**Reference:** {item.reference}")
                        st.markdown(f"**Frequency:** {item.frequency}")
                        st.markdown(
                            f"**Inspection Point:** {item.inspection_point}"
                        )
                        st.markdown(
                            f"**Contractor Responsibility:** "
                            f"{item.contractor_resp}"
                        )
                        st.markdown(
                            f"**Witness / Release By:** {item.witness_release}"
                        )
                        st.markdown(f"**QA Record:** {item.qa_record}")

            if hps:
                st.markdown("### Hold Point Register")
                for hp in hps:
                    st.markdown(
                        f"- **{hp.hp_number}** (Item {hp.itp_item}): "
                        f"{hp.description}"
                    )

            st.download_button(
                "Download Excel report",
                gen_report.to_xlsx(items, hps),
                file_name="generated_itp.xlsx",
                mime="application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet",
            )
            st.download_button(
                "Download Word report",
                gen_report.to_docx(items, hps),
                file_name="generated_itp.docx",
                mime="application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",
            )
            st.download_button(
                "Download markdown report",
                gen_report.to_markdown(items, hps),
                file_name="generated_itp.md",
                mime="text/markdown",
            )

            # ── Review bridge ─────────────────────────────────────
            st.divider()

            if "gen_review_findings" not in st.session_state:
                st.session_state["gen_review_findings"] = None

            if st.button("Review this draft?"):
                try:
                    itp_text = gen_report.items_to_text(items)
                    with st.spinner("Running adversarial review on generated ITP…"):
                        findings = review.run_review(itp_text)
                    st.session_state["gen_review_findings"] = findings
                except Exception as e:
                    st.error(
                        "Review could not be completed. "
                        f"Details: {e}"
                    )

            if st.session_state.get("gen_review_findings") is not None:
                findings = st.session_state["gen_review_findings"]
                if not findings:
                    st.success("No review findings — the generated ITP looks solid.")
                else:
                    st.subheader(f"{len(findings)} review finding(s)")
                    by_cat = {
                        c: [f for f in findings if f.category == c]
                        for c in schema.CATEGORIES
                    }
                    for cat in schema.CATEGORIES:
                        cat_items = by_cat[cat]
                        if not cat_items:
                            continue
                        st.markdown(
                            f"#### {schema.CATEGORY_LABELS[cat]} "
                            f"({len(cat_items)})"
                        )
                        for f in cat_items:
                            with st.expander(
                                f"{f.location} — {f.observation[:60]}"
                            ):
                                st.markdown(f"**Observation:** {f.observation}")
                                st.markdown(
                                    f"**Why it matters:** {f.why_it_matters}"
                                )
                                st.markdown(
                                    f"**Suggested action:** {f.suggested_action}"
                                )
                    st.download_button(
                        "Download review report (markdown)",
                        report.to_markdown(findings),
                        file_name="generated_itp_review.md",
                        mime="text/markdown",
                        key="gen_review_md",
                    )
                    st.download_button(
                        "Download review report (Word)",
                        report.to_docx(findings),
                        file_name="generated_itp_review.docx",
                        mime="application/vnd.openxmlformats-officedocument"
                        ".wordprocessingml.document",
                        key="gen_review_docx",
                    )


# ── Review tab ────────────────────────────────────────────────────────

with tab_review:
    st.caption(
        "Adversarial QA review of a draft Inspection Test Plan. "
        "Findings are advisory."
    )

    with st.expander("How to use this"):
        st.markdown(
            """
1. **Upload your draft ITP** — Excel, PDF, or Word. Optionally add the
   matching proposal/scope to cross-check the two against each other.
2. **Open the preview** to confirm the table came through cleanly before
   reviewing.
3. **Click Review.** The tool reads the ITP the way an adversarial QA
   reviewer would and lists things worth a second look.
4. **Each finding** says what it saw, why it matters, and a suggested
   action. Download a report to share or file.

⚠️ Findings are **advisory, not pass/fail** — prompts for a qualified
reviewer to consider. Always apply your own engineering judgement.
"""
        )

    itp_file = st.file_uploader(
        "ITP file (required)",
        type=["xlsx", "pdf", "docx", "doc"],
        key="review_itp",
    )
    proposal_file = st.file_uploader(
        "Proposal / scope of works (optional)",
        type=["xlsx", "pdf", "docx", "doc"],
        key="review_proposal",
    )

    itp_doc = proposal_doc = None
    if itp_file:
        itp_doc = _safe_parse(itp_file, "ITP")
        if itp_doc:
            for w in itp_doc.warnings:
                st.warning(f"ITP: {w}")
            with st.expander(
                "Preview parsed ITP text (check table fidelity before reviewing)"
            ):
                st.text(itp_doc.preview[:20000])

    if proposal_file:
        proposal_doc = _safe_parse(proposal_file, "Proposal")
        if proposal_doc:
            with st.expander("Preview parsed proposal text"):
                st.text(proposal_doc.preview[:20000])

    mode = (
        "Cross-check (ITP vs proposal)" if proposal_doc else "Standalone ITP review"
    )
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
            st.error(
                "The review could not be completed. Check your "
                "ANTHROPIC_API_KEY and network connection, then try again."
                f"\n\nDetails: {e}"
            )

    if st.session_state.get("findings") is not None:
        findings = st.session_state["findings"]
        if not findings:
            st.success("No findings identified.")
        else:
            st.subheader(f"{len(findings)} finding(s)")
            by_cat = {
                c: [f for f in findings if f.category == c]
                for c in schema.CATEGORIES
            }
            for cat in schema.CATEGORIES:
                cat_items = by_cat[cat]
                if not cat_items:
                    continue
                st.markdown(
                    f"### {schema.CATEGORY_LABELS[cat]} ({len(cat_items)})"
                )
                for f in cat_items:
                    with st.expander(
                        f"{f.location} — {f.observation[:60]}"
                    ):
                        st.markdown(f"**Observation:** {f.observation}")
                        st.markdown(f"**Why it matters:** {f.why_it_matters}")
                        st.markdown(
                            f"**Suggested action:** {f.suggested_action}"
                        )
            st.download_button(
                "Download markdown report",
                report.to_markdown(findings),
                file_name="itp_review.md",
                mime="text/markdown",
            )
            st.download_button(
                "Download Word report",
                report.to_docx(findings),
                file_name="itp_review.docx",
                mime="application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document",
            )
