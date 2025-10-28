from life.ops.personas.base import build_prompt
from life.ops.personas.kim import kim
from life.ops.personas.pepper import pepper
from life.ops.personas.roast import roast


def test_build_prompt_assembles_sections():
    prompt = build_prompt("Identity", "Section1", "Section2")
    assert "Identity" in prompt
    assert "Section1" in prompt
    assert "Section2" in prompt
    assert "CLI OPERATIONS" in prompt
    assert "GUIDANCE" in prompt


def test_roast_identity_and_patterns():
    prompt = roast()
    assert any(x in prompt.lower() for x in ("roast", "roaster"))
    assert "PATTERNS" in prompt or "pattern" in prompt.lower()
    assert "life task" in prompt or "CLI OPERATIONS" in prompt


def test_pepper_identity():
    prompt = pepper()
    assert "pepper" in prompt.lower() or "PEPPER" in prompt
    assert len(prompt) > 100


def test_kim_identity():
    prompt = kim()
    assert "kim" in prompt.lower() or "KIM" in prompt
    assert len(prompt) > 100


def test_personas_distinct_prompts():
    r, p, k = roast(), pepper(), kim()
    assert r != p and p != k and r != k
