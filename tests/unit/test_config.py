from life.config import (
    add_countdown,
    get_context,
    get_countdowns,
    get_default_persona,
    get_or_set_context,
    get_or_set_profile,
    get_profile,
    list_backups,
    remove_countdown,
    set_context,
    set_default_persona,
    set_profile,
)


def test_set_profile(tmp_life_dir):
    set_profile("Senior IC. ADHD. Direct.")
    prof = get_profile()
    assert "Senior IC" in prof


def test_get_profile_empty(tmp_life_dir):
    prof = get_profile()
    assert prof == ""


def test_get_or_set_profile_get(tmp_life_dir):
    set_profile("Test Profile")
    result = get_or_set_profile()
    assert "Test Profile" in result


def test_get_or_set_profile_set(tmp_life_dir):
    result = get_or_set_profile("New Profile")
    assert "New Profile" in result
    assert get_profile() == "New Profile"


def test_get_or_set_profile_empty(tmp_life_dir):
    result = get_or_set_profile()
    assert "none" in result.lower()


def test_set_context(tmp_life_dir):
    set_context("Sprint deadline Friday")
    ctx = get_context()
    assert "Sprint deadline Friday" in ctx


def test_get_context_default(tmp_life_dir):
    ctx = get_context()
    assert "No context set" in ctx


def test_get_or_set_context_get(tmp_life_dir):
    set_context("Current Status")
    result = get_or_set_context()
    assert "Current Status" in result


def test_get_or_set_context_set(tmp_life_dir):
    result = get_or_set_context("New Context")
    assert "New Context" in result
    assert get_context() == "New Context"


def test_default_persona_not_set(tmp_life_dir):
    persona = get_default_persona()
    assert persona is None


def test_set_default_persona(tmp_life_dir):
    set_default_persona("roast")
    persona = get_default_persona()
    assert persona == "roast"


def test_set_default_persona_different(tmp_life_dir):
    set_default_persona("kim")
    persona = get_default_persona()
    assert persona == "kim"


def test_countdown_add(tmp_life_dir):
    add_countdown("wedding", "2025-06-01", "💍")
    countdowns = get_countdowns()
    assert len(countdowns) == 1
    assert countdowns[0]["name"] == "wedding"
    assert countdowns[0]["date"] == "2025-06-01"


def test_countdown_add_default_emoji(tmp_life_dir):
    add_countdown("deadline", "2025-12-31")
    countdowns = get_countdowns()
    assert countdowns[0]["emoji"] == "📌"


def test_countdown_remove(tmp_life_dir):
    add_countdown("wedding", "2025-06-01")
    add_countdown("deadline", "2025-12-31")
    remove_countdown("wedding")
    countdowns = get_countdowns()
    assert len(countdowns) == 1
    assert countdowns[0]["name"] == "deadline"


def test_countdown_remove_nonexistent(tmp_life_dir):
    add_countdown("wedding", "2025-06-01")
    remove_countdown("nonexistent")
    countdowns = get_countdowns()
    assert len(countdowns) == 1


def test_countdowns_empty(tmp_life_dir):
    countdowns = get_countdowns()
    assert countdowns == []


def test_list_backups_empty(tmp_life_dir):
    backups = list_backups()
    assert backups == []
