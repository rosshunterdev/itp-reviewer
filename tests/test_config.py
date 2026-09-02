from src import config

def test_model_is_current_sonnet():
    assert config.MODEL == "claude-sonnet-5"

def test_supported_extensions():
    assert config.SUPPORTED_EXTENSIONS == {".xlsx", ".pdf", ".docx"}
