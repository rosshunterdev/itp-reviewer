import re
from src import config, gen_schema


ITP_EXAMPLES = """
Here are representative rows from a real, approved ITP to show the expected format, level of detail, and column structure. Use these as a guide for the quality and specificity of your output:

Item | Work Package / Activity | Inspection / Test / Check | Acceptance Criteria | Reference | Frequency / Timing | Inspection Point | Contractor Responsibility | Witness / Release By | QA Record / Evidence
1.1 | Pre-start / document control | Approved-for-construction drawings, specifications, ITP, methodology and JSA available at workface | Latest approved revisions only; superseded documents removed from workface | Contract Docs; approved drawings; Quality Plan | Before each work package | H | Site Manager / QA | Principal's Rep as applicable | Approved documents / document register
2.1 | Survey and set-out | Verify survey control, datum and benchmark against approved design | Survey control verified; set-out to approved coordinates/levels; NZVD2016 where required | Contract drawings; survey specification | Initial set-out and each structure/pipeline | H | Surveyor | QA / Engineer as required | Set-out sheet / survey file
2.2 | Survey and set-out | Check location, line, level and offsets before excavation / installation | Within drawing/specification tolerances | Approved drawings; TCC IDC | Each structure / pipeline section | W | Surveyor / Site Engineer | Engineer / Council as notified | Pre-install survey record
5.3 | Earthworks / cohesive fill | Compaction / shear vane / air voids testing | Air voids: max 12% single test, average ≤10%; undrained shear strength ≥120 kPa or as specified | Contract §5.3.2 | Min. 1 set / 500 m³ plus random testing as specified | H | IANZ Lab / QA | Geotechnical Engineer | Lab / field test results
8.1 | Concrete works | Pre-pour inspection: excavation/formwork, reinforcement, cover, cast-ins, penetrations | Matches approved structural drawings; reinforcement and cover correct; formwork stable and clean | Contract §9 Reinforced Concrete; NZS 3109; approved drawings | Each pour | H | Site Engineer / QA | Engineer / structural reviewer as required | Pre-pour checklist, photos
9.3 | Gravity pipelines | Line, level and gradient during laying | Pipe laser / survey used; no backfall; within specified line/level tolerances | TCC IDC; Contract §7.4 / §7.8 | Each pipe / reach | W | Surveyor / Site Engineer | Engineer / Council as required | Pipe laying sheet / survey data
10.3 | Pressure / rising main | Hydrostatic pressure test | Test pressure, duration and acceptance criteria comply with Contract / Council requirements | Contract testing specification; TCC IDC | Each test section | H | Contractor / test specialist | Engineer / Council | Pressure test certificate / chart
15.3 | Close-out | Compile QA dossier / handover records | All ITPs closed; hold points released; test results passed; NCRs closed/accepted | Contract Quality Plan / handover requirements | Before Practical Completion | H | QA Manager / Project Manager | Principal's Rep / Engineer | QA dossier / handover index
""".strip()


def generation_system_prompt() -> str:
    return (
        "You are an experienced construction ITP (Inspection Test Plan) author. "
        "Your job is to read a project specification and produce a thorough, "
        "standards-aware ITP that covers every activity requiring inspection, "
        "testing, or verification.\n\n"
        "For each work package or activity in the specification, generate ITP items "
        "with these columns:\n"
        "- Item number (sequential within each work package, e.g. 1.1, 1.2, 2.1)\n"
        "- Work package / activity name\n"
        "- Inspection / test / check — what is inspected or tested\n"
        "- Acceptance criteria — specific, measurable, never vague. Include actual "
        "values, tolerances, or standards thresholds where the spec provides them.\n"
        "- Reference — cite specific standards (e.g. NZS 3109), spec section numbers "
        "(e.g. Contract §7.4), codes, or contract requirements. Never leave blank.\n"
        "- Frequency / timing — when or how often\n"
        "- Inspection point — H (Hold: work stops until released), W (Witness: "
        "notified and may attend), S (Surveillance: routine monitoring), "
        "R (Review: document review only). Assign based on criticality:\n"
        "  - H for safety-critical, structural, concealment, or compliance milestones\n"
        "  - W for quality-significant items that benefit from third-party observation\n"
        "  - S for routine ongoing monitoring\n"
        "  - R for document/certification checks\n"
        "- Contractor responsibility — the role responsible\n"
        "- Witness / release by — who witnesses or releases\n"
        "- QA record / evidence — what documentation is produced\n\n"
        "Also generate a hold point register entry for every item designated H.\n\n"
        "Be thorough — cover pre-start, each trade/discipline in the spec, testing, "
        "and close-out. Do not skip sections of the specification. Do not invent "
        "standards that are not referenced in the specification or examples. "
        "Report the full ITP by calling the generate_itp tool exactly once."
    )


def generation_user_message(
    spec_text: str,
    supporting_texts: list[tuple[str, str]] | None = None,
) -> str:
    parts = [
        "Generate a complete ITP from the following project specification. "
        "Use the example ITP rows below as a guide for format, level of detail, "
        "and the kind of acceptance criteria expected.",
        f"<itp_examples>\n{ITP_EXAMPLES}\n</itp_examples>",
        f"<specification>\n{spec_text}\n</specification>",
    ]
    if supporting_texts:
        for label, text in supporting_texts:
            tag = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
            parts.append(f"<{tag}>\n{text}\n</{tag}>")
    return "\n\n".join(parts)


def _get_client():
    import anthropic
    return anthropic.Anthropic()


def run_generation(
    spec_text: str,
    supporting_texts: list[tuple[str, str]] | None = None,
    client=None,
) -> tuple[list[gen_schema.ITPItem], list[gen_schema.HoldPoint]]:
    client = client or _get_client()
    resp = client.messages.create(
        model=config.MODEL,
        max_tokens=config.GEN_MAX_TOKENS,
        system=generation_system_prompt(),
        tools=[gen_schema.GENERATE_ITP_TOOL],
        tool_choice={"type": "tool", "name": "generate_itp"},
        messages=[
            {
                "role": "user",
                "content": generation_user_message(spec_text, supporting_texts),
            }
        ],
    )
    if resp.stop_reason == "max_tokens":
        raise RuntimeError(
            "The model ran out of output space before finishing the ITP. "
            "This usually means the specification is very large. "
            "Try uploading just the specification without supporting documents."
        )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "generate_itp":
            items = [
                gen_schema.ITPItem(
                    item_number=it.get("item_number", ""),
                    work_package=it.get("work_package", ""),
                    inspection_test=it.get("inspection_test", ""),
                    acceptance_criteria=it.get("acceptance_criteria", ""),
                    reference=it.get("reference", ""),
                    frequency=it.get("frequency", ""),
                    inspection_point=it.get("inspection_point", "H"),
                    contractor_resp=it.get("contractor_resp", ""),
                    witness_release=it.get("witness_release", ""),
                    qa_record=it.get("qa_record", ""),
                )
                for it in block.input.get("items", [])
            ]
            hold_points = [
                gen_schema.HoldPoint(
                    hp_number=hp.get("hp_number", ""),
                    itp_item=hp.get("itp_item", ""),
                    description=hp.get("description", ""),
                )
                for hp in block.input.get("hold_points", [])
            ]
            return items, hold_points
    return [], []
