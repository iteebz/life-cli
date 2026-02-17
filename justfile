default:
    @just --list

install:
    @uv sync

ci:
    @uv run ruff format .
    @uv run ruff check . --fix
    @uv run ruff check .
    @uv run pyright
    @uv run pytest tests -v

lint:
    @uv run ruff check .

format:
    @uv run ruff format .

fix:
    @uv run ruff check . --fix

test:
    @uv run pytest tests

clean:
    @rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache __pycache__ .venv
    @find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

commits:
    @git --no-pager log --pretty=format:"%h | %ar | %s"

health:
    @uv run python -m life.health
