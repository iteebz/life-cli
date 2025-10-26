from life.core.item import add_chore, add_habit, add_task


def test_task_format_includes_content(tmp_life_dir):
    result = add_task("build feature")
    assert "Added:" in result
    assert "build feature" in result


def test_task_format_includes_focus_label(tmp_life_dir):
    result = add_task("urgent", focus=True)
    assert "FOCUS" in result


def test_task_format_includes_due_date(tmp_life_dir):
    result = add_task("deadline", due="2025-12-31")
    assert "due 2025-12-31" in result


def test_task_format_includes_all_tags(tmp_life_dir):
    result = add_task("task", tags=["work", "urgent"])
    assert "#work" in result and "#urgent" in result


def test_task_format_done_uses_checkmark(tmp_life_dir):
    result = add_task("quick", done=True)
    assert "✓" in result
    assert "Added:" not in result


def test_habit_format_labels_as_habit(tmp_life_dir):
    result = add_habit("meditate")
    assert "Added habit:" in result


def test_chore_format_labels_as_chore(tmp_life_dir):
    result = add_chore("dishes")
    assert "Added chore:" in result
