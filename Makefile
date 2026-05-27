.PHONY: dev lint format test build clean check-all

dev:
	pip install -e '.[dev]'
	pre-commit install --hook-type pre-commit --hook-type commit-msg

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff check --fix src/ tests/
	ruff format src/ tests/

test:
	python -m pytest tests/ -v

build: clean
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info

check-all: lint test
