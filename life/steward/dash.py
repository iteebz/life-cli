from datetime import datetime

from fncli import cli

from ..lib.errors import echo
from . import _rel, get_observations, get_sessions


@cli("life steward")
def dash():
    """Steward dashboard — improvements, patterns, observations, sessions"""
    from ..improvements import get_improvements
    from ..patterns import get_patterns

    improvements = get_improvements()
    if improvements:
        echo("IMPROVEMENTS:")
        for i in improvements:
            echo(f"  [{i.id}] {i.body}")
    else:
        echo("IMPROVEMENTS: none")

    patterns = get_patterns(limit=5)
    if patterns:
        echo("\nRECENT PATTERNS:")
        now = datetime.now()
        for p in patterns:
            s = (now - p.logged_at).total_seconds()
            rel = _rel(s) if s < 86400 * 7 else p.logged_at.strftime("%Y-%m-%d")
            echo(f"  {rel:<10}  {p.body}")

    observations = get_observations(limit=10)
    if observations:
        echo("\nRECENT OBSERVATIONS:")
        now = datetime.now()
        for o in observations:
            rel = _rel((now - o.logged_at).total_seconds())
            tag_str = f" #{o.tag}" if o.tag else ""
            echo(f"  {rel:<10}  {o.body}{tag_str}")

    sessions = get_sessions(limit=5)
    if sessions:
        echo("\nRECENT SESSIONS:")
        now_dt = datetime.now()
        for s in sessions:
            rel = _rel((now_dt - s.logged_at).total_seconds())
            echo(f"  {rel:<10}  {s.summary[:90]}")
