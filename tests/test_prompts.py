from src import prompts

def test_system_prompt_is_adversarial():
    sp = prompts.system_prompt().lower()
    assert "auditor" in sp
    assert "not a helpful assistant" in sp or "not to be helpful" in sp
    # advisory requirement is stated
    assert "advisory" in sp or "consider" in sp

def test_user_message_standalone_has_itp_tags_no_proposal():
    msg = prompts.user_message("ITP CONTENT")
    assert "<itp>" in msg and "ITP CONTENT" in msg and "</itp>" in msg
    assert "<proposal>" not in msg

def test_user_message_cross_check_has_both():
    msg = prompts.user_message("ITP CONTENT", "PROPOSAL CONTENT")
    assert "<itp>" in msg and "<proposal>" in msg and "PROPOSAL CONTENT" in msg
    assert "cross-check" in msg.lower() or "proposal" in msg.lower()
