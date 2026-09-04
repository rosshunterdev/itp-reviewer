import io
from collections import OrderedDict
from src import gen_schema


COLUMNS = [
    ("Item", "item_number"),
    ("Work Package / Activity", "work_package"),
    ("Inspection / Test / Check", "inspection_test"),
    ("Acceptance Criteria", "acceptance_criteria"),
    ("Reference", "reference"),
    ("Frequency / Timing", "frequency"),
    ("Inspection Point", "inspection_point"),
    ("Contractor Responsibility", "contractor_resp"),
    ("Witness / Release By", "witness_release"),
    ("QA Record / Evidence", "qa_record"),
]


def _group_by_work_package(
    items: list[gen_schema.ITPItem],
) -> OrderedDict[str, list[gen_schema.ITPItem]]:
    groups: OrderedDict[str, list[gen_schema.ITPItem]] = OrderedDict()
    for item in items:
        groups.setdefault(item.work_package, []).append(item)
    return groups


def items_to_text(items: list[gen_schema.ITPItem]) -> str:
    if not items:
        return ""
    header = " | ".join(label for label, _ in COLUMNS)
    lines = [header]
    for item in items:
        row = " | ".join(getattr(item, field) for _, field in COLUMNS)
        lines.append(row)
    return "\n".join(lines)


def to_markdown(
    items: list[gen_schema.ITPItem],
    hold_points: list[gen_schema.HoldPoint],
) -> str:
    if not items:
        return "# Generated ITP\n\nNo ITP items were generated.\n"
    lines = [
        "# Generated ITP",
        "",
        f"{len(items)} item(s) across "
        f"{len(_group_by_work_package(items))} work package(s).",
        "",
    ]
    groups = _group_by_work_package(items)
    for wp, wp_items in groups.items():
        lines.append(f"## {wp}")
        lines.append("")
        for item in wp_items:
            lines.append(f"### {item.item_number} — {item.inspection_test}")
            lines.append(f"- **Acceptance Criteria:** {item.acceptance_criteria}")
            lines.append(f"- **Reference:** {item.reference}")
            lines.append(f"- **Frequency:** {item.frequency}")
            lines.append(f"- **Inspection Point:** {item.inspection_point}")
            lines.append(f"- **Contractor Responsibility:** {item.contractor_resp}")
            lines.append(f"- **Witness / Release By:** {item.witness_release}")
            lines.append(f"- **QA Record:** {item.qa_record}")
            lines.append("")
    if hold_points:
        lines.append("## Hold Point Register")
        lines.append("")
        for hp in hold_points:
            lines.append(
                f"- **{hp.hp_number}** (Item {hp.itp_item}): {hp.description}"
            )
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def to_docx(
    items: list[gen_schema.ITPItem],
    hold_points: list[gen_schema.HoldPoint],
) -> bytes:
    import docx

    document = docx.Document()
    document.add_heading("Generated ITP", level=0)
    if not items:
        document.add_paragraph("No ITP items were generated.")
    else:
        document.add_paragraph(
            f"{len(items)} item(s) across "
            f"{len(_group_by_work_package(items))} work package(s)."
        )
        groups = _group_by_work_package(items)
        for wp, wp_items in groups.items():
            document.add_heading(wp, level=1)
            for item in wp_items:
                document.add_heading(
                    f"{item.item_number} — {item.inspection_test}", level=2
                )
                document.add_paragraph(
                    f"Acceptance Criteria: {item.acceptance_criteria}"
                )
                document.add_paragraph(f"Reference: {item.reference}")
                document.add_paragraph(f"Frequency: {item.frequency}")
                document.add_paragraph(f"Inspection Point: {item.inspection_point}")
                document.add_paragraph(
                    f"Contractor Responsibility: {item.contractor_resp}"
                )
                document.add_paragraph(
                    f"Witness / Release By: {item.witness_release}"
                )
                document.add_paragraph(f"QA Record: {item.qa_record}")
        if hold_points:
            document.add_heading("Hold Point Register", level=1)
            for hp in hold_points:
                document.add_paragraph(
                    f"{hp.hp_number} (Item {hp.itp_item}): {hp.description}"
                )
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()
