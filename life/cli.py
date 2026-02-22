import sys

from . import db
from . import commands as _commands
from . import dates as _dates
from . import interventions as _interventions
from . import items as _items
from . import mood as _mood
from . import patterns as _patterns
from . import signal as _signal
from . import tasks as _tasks
from . import habits as _habits
from . import tags as _tags
from .steward import (
    boot,
    close,
    dash,
    improve,
    log,
    observe,
    rm,
)

_ = (
    boot, close, dash, improve, log, observe, rm,
    _commands, _dates, _interventions, _items, _mood, _patterns, _signal, _tasks, _habits, _tags,
)


def main():
    db.init()
    from fncli import dispatch

    user_args = sys.argv[1:]
    if not user_args or user_args == ["-v"] or user_args == ["--verbose"]:
        from .commands import dashboard

        dashboard(verbose="--verbose" in user_args or "-v" in user_args)
        return
    argv = ["life", *user_args]
    code = dispatch(argv)
    sys.exit(code)


if __name__ == "__main__":
    main()
