from dataclasses import dataclass

CATEGORIES = [
    "hold_witness", "acceptance_criteria", "standards_reference",
    "responsible_party", "internal_consistency", "proposal_mismatch", "other",
]

CATEGORY_LABELS = {
    "hold_witness": "Hold & Witness Points",
    "acceptance_criteria": "Acceptance Criteria",
    "standards_reference": "Standards & References",
    "responsible_party": "Responsible Party",
    "internal_consistency": "Internal Consistency",
    "proposal_mismatch": "Proposal Cross-Check",
    "other": "Other",
}

@dataclass
class Finding:
    location: str
    category: str
    observation: str
    why_it_matters: str
    suggested_action: str

REVIEW_TOOL = {
    "name": "report_findings",
    "description": (
        "Report every QA finding from the adversarial ITP review as structured data. "
        "Call this exactly once with all findings."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "Section/item/cell reference in the ITP, e.g. 'Item 2.1' or 'Acceptance Criteria column'."},
                        "category": {"type": "string", "enum": CATEGORIES},
                        "observation": {"type": "string", "description": "What was noticed."},
                        "why_it_matters": {"type": "string", "description": "Why it might draw client scrutiny."},
                        "suggested_action": {"type": "string", "description": "Advisory suggestion phrased as 'consider…', never a directive."},
                    },
                    "required": ["location", "category", "observation", "why_it_matters", "suggested_action"],
                },
            }
        },
        "required": ["findings"],
    },
}
