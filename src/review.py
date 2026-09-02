from src import config, prompts, schema


def _get_client():
    import anthropic
    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env


def run_review(itp_text, proposal_text=None, client=None):
    client = client or _get_client()
    resp = client.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=prompts.system_prompt(),
        tools=[schema.REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "report_findings"},
        messages=[{"role": "user", "content": prompts.user_message(itp_text, proposal_text)}],
    )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "report_findings":
            return [
                schema.Finding(
                    location=f.get("location", ""),
                    category=f.get("category", "other"),
                    observation=f.get("observation", ""),
                    why_it_matters=f.get("why_it_matters", ""),
                    suggested_action=f.get("suggested_action", ""),
                )
                for f in block.input.get("findings", [])
            ]
    return []
