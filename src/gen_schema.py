from dataclasses import dataclass

INSPECTION_POINTS = ["H", "W", "S", "R"]


@dataclass
class ITPItem:
    item_number: str
    work_package: str
    inspection_test: str
    acceptance_criteria: str
    reference: str
    frequency: str
    inspection_point: str
    contractor_resp: str
    witness_release: str
    qa_record: str


@dataclass
class HoldPoint:
    hp_number: str
    itp_item: str
    description: str


GENERATE_ITP_TOOL = {
    "name": "generate_itp",
    "description": (
        "Generate a complete Inspection Test Plan from the project specification. "
        "Return all ITP items grouped by work package, plus hold point register entries "
        "for every item designated as a hold point (H). Call this exactly once with the "
        "full ITP."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "description": "All ITP inspection/test items, ordered by work package.",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_number": {
                            "type": "string",
                            "description": "Sequential item number, e.g. '1.1', '2.3'.",
                        },
                        "work_package": {
                            "type": "string",
                            "description": "Work package or activity name, e.g. 'Pre-start / document control'.",
                        },
                        "inspection_test": {
                            "type": "string",
                            "description": "What is inspected, tested, or checked.",
                        },
                        "acceptance_criteria": {
                            "type": "string",
                            "description": "Specific, measurable criteria for pass/fail.",
                        },
                        "reference": {
                            "type": "string",
                            "description": "Standards, codes, spec sections, or contract references.",
                        },
                        "frequency": {
                            "type": "string",
                            "description": "When or how often the inspection/test occurs.",
                        },
                        "inspection_point": {
                            "type": "string",
                            "enum": INSPECTION_POINTS,
                            "description": "H = Hold, W = Witness, S = Surveillance, R = Review.",
                        },
                        "contractor_resp": {
                            "type": "string",
                            "description": "Contractor role responsible for this item.",
                        },
                        "witness_release": {
                            "type": "string",
                            "description": "Who witnesses or releases the hold/witness point.",
                        },
                        "qa_record": {
                            "type": "string",
                            "description": "Evidence or documentation required.",
                        },
                    },
                    "required": [
                        "item_number", "work_package", "inspection_test",
                        "acceptance_criteria", "reference", "frequency",
                        "inspection_point", "contractor_resp", "witness_release",
                        "qa_record",
                    ],
                },
            },
            "hold_points": {
                "type": "array",
                "description": "Hold point register entries for every H-designated item.",
                "items": {
                    "type": "object",
                    "properties": {
                        "hp_number": {
                            "type": "string",
                            "description": "Hold point number, e.g. 'HP-01'.",
                        },
                        "itp_item": {
                            "type": "string",
                            "description": "Cross-reference to the ITP item number.",
                        },
                        "description": {
                            "type": "string",
                            "description": "What must be released before work proceeds.",
                        },
                    },
                    "required": ["hp_number", "itp_item", "description"],
                },
            },
        },
        "required": ["items", "hold_points"],
    },
}
