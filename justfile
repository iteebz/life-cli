default:
    @just --list

clean:
    @echo "Cleaning life..."
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv
    @find . -type d -name "__pycache__" -exec rm -rf {} +

install:
    @poetry lock
    @poetry install

ci:
    @poetry run ruff format .
    @poetry run ruff check . --fix --unsafe-fixes
    @python -m pytest tests -q
    @poetry build

test:
    @python -m pytest tests

run:
    @poetry run life

format:
    @poetry run ruff format .

lint:
    @poetry run ruff check .

fix:
    @poetry run ruff check . --fix --unsafe-fixes

build:
    @poetry build

commits:
    @git --no-pager log --pretty=format:"%h | %ar | %s"
