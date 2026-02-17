from datetime import date, datetime, timedelta

from typer.testing import CliRunner

from life import db
from life.cli import app


def test_status_shows_feedback_metrics(tmp_life_dir):
    runner = CliRunner()
    runner.invoke(app, ["task", "call bank", "-t", "finance", "-d", "today"])
    runner.invoke(app, ["task", "wedding vids", "-t", "jaynice"])

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "FEEDBACK LOOPS (7d):" in result.stdout
    assert "admin_closure_rate:" in result.stdout
    assert "jaynice_followthrough_rate:" in result.stdout
    assert "avoidance_half_life_days:" in result.stdout


def test_status_flags_relationship_and_stuck_task(tmp_life_dir):
    runner = CliRunner()
    runner.invoke(app, ["task", "wedding vids", "-t", "jaynice"])
    runner.invoke(app, ["task", "call bank", "-t", "finance"])

    today = date.today()
    with db.get_db() as conn:
        conn.execute(
            "UPDATE tasks SET created = ? WHERE content = ?",
            ((today - timedelta(days=4)).isoformat(), "call bank"),
        )

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "flags:" in result.stdout
    assert "relationship_escalation" in result.stdout
    assert "stuck_task_protocol" in result.stdout


def test_status_admin_closure_rate_counts_recent_overdue_closures(tmp_life_dir):
    runner = CliRunner()
    today = date.today()
    runner.invoke(app, ["task", "invoice jeff", "-t", "finance", "-d", "today"])
    runner.invoke(app, ["done", "invoice jeff"])

    yesterday = datetime.combine(today - timedelta(days=1), datetime.min.time())
    with db.get_db() as conn:
        conn.execute(
            "UPDATE tasks SET due_date = ?, created = ?, completed_at = ? WHERE content = ?",
            (
                (today - timedelta(days=1)).isoformat(),
                yesterday.isoformat(),
                datetime.combine(today, datetime.min.time()).isoformat(),
                "invoice jeff",
            ),
        )

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    assert "admin_closure_rate: 100% (1/1)" in result.stdout
