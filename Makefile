.PHONY: dev lint format test build clean check-all dev-web build-web lint-web format-web docs-reference docs docs-links

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
	rm -rf dist/ build/ *.egg-info src/*.egg-info web/dist/

check-all: lint test

# ---- web (MCP Apps UI bundles) ----

# Local design workbench with hot reload. Open http://localhost:5174/
# after this prints the dev server URL.
dev-web:
	cd web && npm install
	cd web && npm run dev

# Rebuild the React entries via Vite and emit
# src/bibliocommons_mcp/_ui_bundles.py. Run after editing anything
# under web/ before committing.
build-web:
	cd web && npm install
	cd web && npm run build:bundles

lint-web:
	cd web && npm run lint
	cd web && npm run typecheck

format-web:
	cd web && npm run format

# ---- docs site (Mintlify, docs-mintlify/) ----

# Regenerate the CLI + MCP tool reference from source. Run + commit after
# changing the CLI or any MCP tool, or CI ("Docs Reference Freshness") fails.
docs-reference:
	python scripts/gen_cli_reference.py
	python scripts/gen_mcp_reference.py

# Local docs preview at http://localhost:3000
docs:
	cd docs-mintlify && npx mint@latest dev

# Validate internal links + nav
docs-links:
	cd docs-mintlify && npx mint@latest broken-links
