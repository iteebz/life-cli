default:
    @just --list

install:
    @poetry install

test:
    @poetry run python -m pytest tests -v

format:
    @poetry run ruff format .

lint:
    @poetry run ruff check .

fix:
    @poetry run ruff check . --fix --unsafe-fixes

build:
    @poetry build

ci: format fix test build
