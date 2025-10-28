from typer.testing import CliRunner

from life.api import add_item, add_tag, get_checks, get_pending_items, get_tags
from life.cli import app
from life.ops.toggle import toggle_done

runner = CliRunner()


def test_done_command(tmp_life_dir):
    item_id = add_item("task to complete")
    result = runner.invoke(app, ["done", str(item_id)])
    assert result.exit_code == 0
    assert "Task: 'task to complete' marked as complete." in result.stdout


def test_done_undo_command(tmp_life_dir):
    item_id = add_item("task")
    runner.invoke(app, ["done", str(item_id)])
    result = runner.invoke(app, ["done", str(item_id)])
    assert result.exit_code == 0

    assert "Task: 'task' marked as pending." in result.stdout


def test_done_command_multi_word_fuzzy_match(tmp_life_dir):
    add_item("wedding band")
    result = runner.invoke(app, ["done", "wedding band"])
    assert result.exit_code == 0
    assert "Task: 'wedding band' marked as complete." in result.stdout


def test_focus_command(tmp_life_dir):
    item_id = add_item("task")
    result = runner.invoke(app, ["focus", str(item_id)])
    assert result.exit_code == 0


def test_tag_command_add(tmp_life_dir):
    item_id = add_item("task")
    result = runner.invoke(app, ["tag", "work", str(item_id)])
    assert result.exit_code == 0


def test_tag_command_list(tmp_life_dir):
    add_item("task 1", tags=["work"])
    add_item("task 2", tags=["work"])
    result = runner.invoke(app, ["tag", "work"])
    assert result.exit_code == 0
    assert "WORK" in result.stdout


def test_rename_command(tmp_life_dir):
    add_item("task to rename")
    result = runner.invoke(app, ["rename", "task", "renamed task"])
    assert result.exit_code == 0
    assert "Updated: 'task to rename' → 'renamed task'" in result.stdout
    pending_items = get_pending_items()
    assert any(item.content == "renamed task" for item in pending_items)
    assert not any(item.content == "task to rename" for item in pending_items)


def test_due_command(tmp_life_dir):
    item_id = add_item("task")
    result = runner.invoke(app, ["due", "2025-12-25", str(item_id)])
    assert result.exit_code == 0


def test_rm_command(tmp_life_dir):
    item_id = add_item("task to remove")
    result = runner.invoke(app, ["rm", str(item_id)])
    assert result.exit_code == 0
    pending = get_pending_items()
    assert not any(item.id == item_id for item in pending)


def test_rm_command_cascades_delete(tmp_life_dir):
    item_id = add_item("item for cascade delete", item_type="habit", tags=["habit"])
    toggle_done(str(item_id))
    add_tag(item_id, "testtag")

    # Verify tag and check exist before deletion
    assert len(get_tags(item_id)) > 0
    assert len(get_checks(item_id)) > 0

    result = runner.invoke(app, ["rm", str(item_id)])
    assert result.exit_code == 0

    # Verify tag and check are deleted after item deletion
    assert len(get_tags(item_id)) == 0
    assert len(get_checks(item_id)) == 0


def test_task_command(tmp_life_dir):
    result = runner.invoke(app, ["task", "new task"])
    assert result.exit_code == 0
    items = get_pending_items()
    assert any(item.content == "new task" for item in items)


def test_task_command_with_focus(tmp_life_dir):
    result = runner.invoke(app, ["task", "-f", "urgent task"])
    assert result.exit_code == 0
    items = get_pending_items()
    assert any(item.content == "urgent task" for item in items)


def test_task_command_with_due(tmp_life_dir):
    result = runner.invoke(app, ["task", "-d", "2025-12-25", "task with due"])
    assert result.exit_code == 0


def test_task_command_multi_word_content(tmp_life_dir):
    result = runner.invoke(app, ["task", "renew license"])
    assert result.exit_code == 0
    items = get_pending_items()
    assert any(item.content == "renew license" for item in items)


def test_habit_command(tmp_life_dir):
    result = runner.invoke(app, ["habit", "morning routine"])
    assert result.exit_code == 0


def test_chore_command(tmp_life_dir):
    result = runner.invoke(app, ["chore", "clean dishes"])
    assert result.exit_code == 0


def test_profile_command(tmp_life_dir):
    result = runner.invoke(app, ["profile"])
    assert result.exit_code == 0


def test_context_command(tmp_life_dir):
    result = runner.invoke(app, ["context"])
    assert result.exit_code == 0


def test_backup_command(tmp_life_dir):
    result = runner.invoke(app, ["backup"])
    assert result.exit_code == 0


def test_main_no_command_renders_dashboard(tmp_life_dir):
    add_item("task 1")
    add_item("task 2")
    result = runner.invoke(app, [])
    assert result.exit_code == 0


def test_rename_command_same_content(tmp_life_dir):
    add_item("existing content")
    result = runner.invoke(app, ["rename", "existing", "existing content"])
    assert result.exit_code == 1
    assert "Error: Cannot rename 'existing content' to itself." in result.stdout


def test_rename_command_empty_to_content(tmp_life_dir):
    add_item("some content")
    result = runner.invoke(app, ["rename", "some", ""])
    assert result.exit_code == 1
    assert "Error: 'to' content cannot be empty." in result.stdout


def test_rename_command_no_match(tmp_life_dir):
    add_item("unique item")
    result = runner.invoke(app, ["rename", "nonexistent", "new content"])
    assert result.exit_code == 1
    assert "No fuzzy match found for: 'nonexistent'" in result.stdout
    pending_items = get_pending_items()
    assert any(item.content == "unique item" for item in pending_items)
    assert not any(item.content == "new content" for item in pending_items)


def test_add_check_fails_for_regular_task(tmp_life_dir):
    item_id = add_item("regular task")
    result = runner.invoke(app, ["check", str(item_id)])
    assert result.exit_code == 1
    assert "Checks can only be added to repeating items." in result.stdout


def test_add_check_fails_if_habit_completed(tmp_life_dir):
    habit_id = add_item("completed habit", item_type="habit", tags=["habit"])
    # First, check the habit
    runner.invoke(app, ["done", str(habit_id)])
    # Then, try to check it again, which should result in 'Already checked'
    result = runner.invoke(app, ["done", str(habit_id)])
    assert result.exit_code == 0
    assert "Habit: 'completed habit' already checked for today." in result.stdout


def test_add_check_succeeds_for_habit(tmp_life_dir):
    habit_id = add_item("new habit", item_type="habit", tags=["habit"])
    result = runner.invoke(app, ["done", str(habit_id)])
    assert result.exit_code == 0
    assert "Habit: 'new habit' checked for today." in result.stdout
    checks = get_checks(habit_id)
    assert len(checks) == 1
