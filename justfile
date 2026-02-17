default:
    @just ls

ls:
    #!/bin/bash
    echo -e "\033[37minstall.\033[0m  sync dependencies"
    echo -e "\033[37mlint.\033[0m  format, lint, typecheck"
    echo -e "\033[37mci.\033[0m  format, lint, typecheck, test"
    echo -e "\033[37mtest.\033[0m  run tests"
    echo -e "\033[37mbuild.\033[0m  build package"
    echo -e "\033[37mclean.\033[0m  remove build artifacts"
    echo -e "\033[37mcommits.\033[0m  recent commit log"
    echo -e "\033[37mhealth.\033[0m  system health check"

install:
    @uv sync

lint:
    #!/bin/bash
    set -e
    uv run ruff format .
    uv run ruff check . --fix
    uv run pyright

ci:
    #!/bin/bash
    set -e
    just lint
    uv run pytest tests --tb=short

test:
    @uv run pytest tests

build:
    @uv build

clean:
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv
    @find . -type d -name "__pycache__" -exec rm -rf {} +

commits:
    @git --no-pager log --pretty=format:"%h | %ar | %s"

health:
    @uv run python -m life.health
