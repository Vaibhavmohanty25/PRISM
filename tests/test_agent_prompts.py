from app.agents.prompts import SYSTEM_PROMPT


def test_system_prompt_contains_grounding_rules():
    assert "PRISM tools are the source of truth" in SYSTEM_PROMPT
    assert "Do not invent" in SYSTEM_PROMPT
    assert "Do not independently calculate" in SYSTEM_PROMPT
    assert "not_found" in SYSTEM_PROMPT
    assert "insufficient_data" in SYSTEM_PROMPT
    assert "private chain-of-thought" in SYSTEM_PROMPT