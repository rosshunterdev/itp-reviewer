from src import config, prompts, schema


class ReviewError(Exception):
    """Base for failures where the model's response can't be trusted."""


class TruncatedResponse(ReviewError):
    """The model hit max_tokens before it finished its answer."""


class MalformedResponse(ReviewError):
    """The response had no usable tool call, or its shape was wrong."""


def explain_error(e: Exception) -> str:
    """Say what kind of failure this was: truncation, bad response, or API/network."""
    import anthropic

    if isinstance(e, TruncatedResponse):
        return f"Output was cut off. {e}"
    if isinstance(e, MalformedResponse):
        return f"The model's response could not be read. {e} Try again."
    if isinstance(e, anthropic.AuthenticationError):
        return "The API key was rejected. Check ANTHROPIC_API_KEY."
    if isinstance(e, anthropic.RateLimitError):
        return "The API rate limit was hit. Wait a minute and try again."
    if isinstance(e, anthropic.APIConnectionError):
        return "Could not reach the API (network or timeout). Try again."
    if isinstance(e, anthropic.APIStatusError):
        return f"The API returned an error (HTTP {e.status_code}). Try again shortly."
    return f"Unexpected error ({type(e).__name__}): {e}"


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
    if resp.stop_reason == "max_tokens":
        raise TruncatedResponse(
            "The model ran out of output space before finishing the review, so "
            "the findings would be incomplete. Try a smaller ITP."
        )
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "report_findings":
            raw = block.input.get("findings") if isinstance(block.input, dict) else None
            if not isinstance(raw, list):
                raise MalformedResponse(
                    "The model's response did not contain a findings list."
                )
            if not all(isinstance(f, dict) for f in raw):
                raise MalformedResponse(
                    "The model returned a finding that was not a structured record."
                )
            return [
                schema.Finding(
                    location=f.get("location", ""),
                    category=f.get("category", "other"),
                    observation=f.get("observation", ""),
                    why_it_matters=f.get("why_it_matters", ""),
                    suggested_action=f.get("suggested_action", ""),
                )
                for f in raw
            ]
    raise MalformedResponse(
        "The model did not return a review (no report_findings call in the response)."
    )
