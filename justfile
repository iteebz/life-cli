default:
    @just --list

install:
    @uv sync

ci:
    #!/bin/bash
    if just _ci > .ci.log 2>&1; then
        echo "CI passed"
    else
        cat .ci.log
        exit 1
    fi

_ci:
    #!/bin/bash
    set -e
    uv run ruff format .
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff check .
    uv run pytest tests -x -qq

lint:
    @uv run ruff check .

fmt:
    @uv run ruff format .

fix:
    @uv run ruff check . --fix --unsafe-fixes

test:
    @uv run pytest tests

clean:
    @rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache __pycache__ .venv
    @find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

commits:
    @git --no-pager log --pretty=format:"%h | %ar | %s"
