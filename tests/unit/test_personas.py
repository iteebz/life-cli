import pytest

from life.personas import (
    get_default_persona_name,
    get_persona,
    manage_personas,
    set_default_persona_name,
)


def test_get_persona_roast(tmp_life_dir):
    result = get_persona("roast")
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_persona_pepper(tmp_life_dir):
    result = get_persona("pepper")
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_persona_kim(tmp_life_dir):
    result = get_persona("kim")
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_persona_default_is_roast(tmp_life_dir):
    result = get_persona()
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_persona_invalid(tmp_life_dir):
    with pytest.raises(ValueError):
        get_persona("invalid_persona")


def test_manage_personas_list(tmp_life_dir):
    result = manage_personas()
    assert "roast" in result.lower()
    assert "pepper" in result.lower()
    assert "kim" in result.lower()


def test_manage_personas_show_roast(tmp_life_dir):
    result = manage_personas(name="roast")
    assert isinstance(result, str)
    assert len(result) > 0


def test_manage_personas_show_pepper(tmp_life_dir):
    result = manage_personas(name="pepper")
    assert isinstance(result, str)
    assert len(result) > 0


def test_manage_personas_show_kim(tmp_life_dir):
    result = manage_personas(name="kim")
    assert isinstance(result, str)
    assert len(result) > 0


def test_manage_personas_kitsuragi_alias(tmp_life_dir):
    result = manage_personas(name="kitsuragi")
    assert isinstance(result, str)
    assert len(result) > 0


def test_manage_personas_invalid(tmp_life_dir):
    with pytest.raises(ValueError):
        manage_personas(name="invalid")


def test_set_default_persona(tmp_life_dir):
    set_default_persona_name("pepper")
    assert get_default_persona_name() == "pepper"


def test_set_default_persona_kim(tmp_life_dir):
    set_default_persona_name("kim")
    assert get_default_persona_name() == "kim"


def test_default_persona_persists(tmp_life_dir):
    set_default_persona_name("roast")
    name = get_default_persona_name()
    assert name == "roast"


def test_manage_personas_set_default(tmp_life_dir):
    result = manage_personas(name="pepper", set_default=True)
    assert "pepper" in result.lower()
    assert get_default_persona_name() == "pepper"


def test_manage_personas_show_prompt_contains_persona(tmp_life_dir):
    result = manage_personas(name="roast", show_prompt=True)
    assert isinstance(result, str)
    assert len(result) > 100


def test_manage_personas_show_prompt_contains_profile_section(tmp_life_dir):
    result = manage_personas(name="roast", show_prompt=True)
    assert "PROFILE:" in result


def test_manage_personas_show_prompt_contains_context_section(tmp_life_dir):
    result = manage_personas(name="roast", show_prompt=True)
    assert "CONTEXT:" in result


def test_manage_personas_show_prompt_contains_life_state(tmp_life_dir):
    result = manage_personas(name="roast", show_prompt=True)
    assert "CURRENT LIFE STATE:" in result
