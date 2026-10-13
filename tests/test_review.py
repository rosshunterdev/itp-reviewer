from unittest.mock import MagicMock
from src import review, schema


def _fake_client_returning(findings):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "report_findings"
    block.input = {"findings": findings}
    resp = MagicMock()
    resp.content = [block]
    client = MagicMock()
    client.messages.create.return_value = resp
    return client


def test_run_review_parses_tool_output():
    client = _fake_client_returning([
        {"location": "Item 2.1", "category": "acceptance_criteria",
         "observation": "Vague criteria", "why_it_matters": "Client will query",
         "suggested_action": "consider specifying a tolerance"}
    ])
    findings = review.run_review("itp text", client=client)
    assert len(findings) == 1
    assert isinstance(findings[0], schema.Finding)
    assert findings[0].category == "acceptance_criteria"


def test_run_review_forces_tool_and_passes_system():
    client = _fake_client_returning([])
    review.run_review("itp text", client=client)
    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["tool_choice"] == {"type": "tool", "name": "report_findings"}
    assert kwargs["tools"] == [schema.REVIEW_TOOL]
    assert "auditor" in kwargs["system"].lower()


def test_run_review_includes_proposal_when_given():
    client = _fake_client_returning([])
    review.run_review("itp", "proposal text", client=client)
    kwargs = client.messages.create.call_args.kwargs
    sent = kwargs["messages"][0]["content"]
    assert "<proposal>" in sent and "proposal text" in sent


# ── failure cases ─────────────────────────────────────────────────────

import anthropic
import pytest


def _client_with(content, stop_reason="tool_use"):
    resp = MagicMock()
    resp.content = content
    resp.stop_reason = stop_reason
    client = MagicMock()
    client.messages.create.return_value = resp
    return client


def _tool_block(input_):
    block = MagicMock()
    block.type = "tool_use"
    block.name = "report_findings"
    block.input = input_
    return block


def test_run_review_raises_on_truncated_response():
    # Truncated tool input can look like a valid partial list; must not be trusted.
    client = _client_with(
        [_tool_block({"findings": [{"location": "Item 1"}]})], stop_reason="max_tokens"
    )
    with pytest.raises(review.TruncatedResponse):
        review.run_review("itp", client=client)


def test_run_review_raises_on_empty_response():
    with pytest.raises(review.MalformedResponse):
        review.run_review("itp", client=_client_with([]))


def test_run_review_raises_when_only_other_tool_called():
    other = _tool_block({"findings": []})
    other.name = "something_else"
    with pytest.raises(review.MalformedResponse):
        review.run_review("itp", client=_client_with([other]))


def test_run_review_raises_when_findings_missing_or_wrong_type():
    for bad in ({}, {"findings": "none"}, {"findings": None}):
        with pytest.raises(review.MalformedResponse):
            review.run_review("itp", client=_client_with([_tool_block(bad)]))


def test_run_review_raises_when_a_finding_is_not_a_record():
    client = _client_with([_tool_block({"findings": ["just a string"]})])
    with pytest.raises(review.MalformedResponse):
        review.run_review("itp", client=client)


def test_run_review_valid_empty_findings_is_not_an_error():
    assert review.run_review("itp", client=_client_with([_tool_block({"findings": []})])) == []


def test_explain_error_distinguishes_failure_kinds():
    # MagicMock stands in for the HTTP request/response; avoids depending on
    # which HTTP library the installed SDK version uses.
    req = MagicMock()
    resp_401 = MagicMock(status_code=401)
    resp_500 = MagicMock(status_code=500)

    msgs = {
        "truncated": review.explain_error(review.TruncatedResponse("too long")),
        "malformed": review.explain_error(review.MalformedResponse("no list")),
        "network": review.explain_error(anthropic.APIConnectionError(request=req)),
        "auth": review.explain_error(
            anthropic.AuthenticationError("bad", response=resp_401, body=None)
        ),
        "status": review.explain_error(
            anthropic.InternalServerError("boom", response=resp_500, body=None)
        ),
        "other": review.explain_error(ValueError("oops")),
    }
    assert "cut off" in msgs["truncated"]
    assert "could not be read" in msgs["malformed"]
    assert "network" in msgs["network"].lower()
    assert "key" in msgs["auth"].lower()
    assert "500" in msgs["status"]
    assert "ValueError" in msgs["other"]
    assert len(set(msgs.values())) == len(msgs)
