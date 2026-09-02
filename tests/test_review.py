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
