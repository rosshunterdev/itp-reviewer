import io
from src import schema


def _group(findings):
    grouped = {c: [] for c in schema.CATEGORIES}
    for f in findings:
        grouped.get(f.category, grouped["other"]).append(f)
    return grouped


def to_markdown(findings) -> str:
    if not findings:
        return "# ITP Review\n\nNo findings were identified."
    lines = ["# ITP Review", "", f"{len(findings)} finding(s).", ""]
    grouped = _group(findings)
    for cat in schema.CATEGORIES:
        items = grouped[cat]
        if not items:
            continue
        lines.append(f"## {schema.CATEGORY_LABELS[cat]}")
        lines.append("")
        for f in items:
            lines.append(f"### {f.location}")
            lines.append(f"- **Observation:** {f.observation}")
            lines.append(f"- **Why it matters:** {f.why_it_matters}")
            lines.append(f"- **Suggested action:** {f.suggested_action}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def to_docx(findings) -> bytes:
    import docx
    document = docx.Document()
    document.add_heading("ITP Review", level=0)
    if not findings:
        document.add_paragraph("No findings were identified.")
    else:
        document.add_paragraph(f"{len(findings)} finding(s).")
        grouped = _group(findings)
        for cat in schema.CATEGORIES:
            items = grouped[cat]
            if not items:
                continue
            document.add_heading(schema.CATEGORY_LABELS[cat], level=1)
            for f in items:
                document.add_heading(f.location, level=2)
                document.add_paragraph(f"Observation: {f.observation}")
                document.add_paragraph(f"Why it matters: {f.why_it_matters}")
                document.add_paragraph(f"Suggested action: {f.suggested_action}")
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()
