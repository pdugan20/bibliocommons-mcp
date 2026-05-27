# Contributing

## Setup

```bash
git clone https://github.com/pdugan20/bibliocommons-mcp.git
cd bibliocommons-mcp
make dev
```

This installs the package with dev/test dependencies and sets up pre-commit hooks.

You'll also need a `~/.config/bibliocommons-mcp/config.toml` to run the server
locally (see `config.example.toml`). Tests run from VCR cassettes by default, so
no config is needed to run the test suite — but local development against a real
library account does need one.

## Running Tests

```bash
make test
```

Tests are recorded HTTP cassettes (via `vcrpy`) under `tests/cassettes/`. They
replay deterministically in CI with no network access.

To re-record cassettes (for example, after a real-world API change):

```bash
BIBLIOCOMMONS_RECORD_CASSETTES=1 make test
```

You'll need a working `config.toml` for re-recording. Cassettes are
sanitized — see `tests/conftest.py` for the redaction rules. Always inspect
recorded cassettes before committing to ensure no card number, PIN, or
session token leaks in.

## Linting and Formatting

```bash
make lint                            # check only
make format                          # auto-fix
make check-all                       # lint + tests
```

We use [ruff](https://docs.astral.sh/ruff/) for both linting and formatting.

## Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/).
Commitlint enforces this via a pre-commit hook, and `release-please` uses the
commit history to determine version bumps.

### Format

```text
<type>: <description>
```

### Types

- **feat** — new feature or tool (minor version bump)
- **fix** — bug fix (patch version bump)
- **docs** — documentation changes (no version bump)
- **chore** — maintenance, dependencies, CI (no version bump)
- **refactor** — code changes that don't add features or fix bugs
- **test** — adding or updating tests
- **style** — formatting, linting fixes

### Examples

```text
feat: add list_loans tool
fix: correct branchId field name in physical hold body
docs: explain how to find your BiblioCommons subdomain
chore: bump httpx pin to 0.29
test: add VCR cassettes for search pagination
```

### Rules

- Use lowercase for the subject line
- Keep the header under 100 characters
- No period at the end of the subject

Breaking changes go in the commit body or footer as `BREAKING CHANGE: ...`,
which triggers a major version bump.

## Building

```bash
make build
```

## Releasing

See [docs/releasing.md](docs/releasing.md). Releases are automated via
`release-please` — you don't run `make release` locally for this project.
