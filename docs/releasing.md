# Releasing

Releases are automated via [release-please](https://github.com/googleapis/release-please).
Maintainers do not run release commands locally — every release is a GitHub PR.

## The release flow

1. Contributors merge PRs to `main` using [Conventional Commits](https://www.conventionalcommits.org/)
   (`feat:`, `fix:`, `docs:`, `chore:`, etc.).
2. The `release-please.yml` workflow watches `main` and maintains an open
   **"Release PR"** that bumps `__version__`, updates `CHANGELOG.md`, and
   updates `.release-please-manifest.json` based on commits since the
   last release.
3. When you're ready to ship, merge the Release PR.
4. release-please tags the merge commit (e.g. `v0.2.0`) and creates a
   GitHub Release.
5. The tag push triggers `publish.yml`, which builds the wheel and
   publishes to PyPI via OIDC trusted publishing (no API tokens).

## Conventional Commits → version bump

| Commit type          | Bump  |
|----------------------|-------|
| `fix:`               | patch |
| `feat:`              | minor |
| `feat!:` / `BREAKING CHANGE:` in body | major |
| `chore:`, `docs:`, `test:`, `refactor:`, `style:`, `ci:` | none |

PR titles are validated by `pr-lint.yml` to match this scheme.

## First-time PyPI setup

These steps happen once, before the first publish:

1. **PyPI account**: create one at [pypi.org](https://pypi.org).
2. **Reserve the package name**: the first publish claims `bibliocommons-mcp`.
3. **OIDC trusted publishing**: on PyPI → Account settings → Publishing →
   Add a new pending publisher:
   - PyPI Project Name: `bibliocommons-mcp`
   - Owner: `pdugan20`
   - Repository: `bibliocommons-mcp`
   - Workflow: `publish.yml`
   - Environment: `pypi`
4. **GitHub environment**: in repo Settings → Environments, create
   `pypi`.
5. **RELEASE_PLEASE_TOKEN secret**: create a fine-scoped PAT (or use a
   GitHub App) with `contents: write` + `pull-requests: write` on this
   repo and add it as `RELEASE_PLEASE_TOKEN` in repo secrets. This is
   what lets the `release-please.yml` workflow's tag push cascade into
   `publish.yml` — the default `GITHUB_TOKEN` doesn't.
6. **Branch ruleset**: protect `main`, require status checks (CI must
   pass) so releases have a quality gate.

## Troubleshooting

### Publish workflow fails with 403

OIDC trust isn't set up. Verify the PyPI trusted publisher matches the
GitHub repo owner, repo name, workflow filename, and environment name
exactly.

### Release PR doesn't appear

`release-please.yml` only opens a PR when there are commits since the
last release that trigger a bump (i.e. `feat:` or `fix:` or breaking
changes). Pure `docs:`/`chore:`/`test:` commits don't trigger a
release.

### Wrong version after release

The single source of truth is `src/bibliocommons_mcp/__init__.py`.
`pyproject.toml` reads it via `[tool.hatch.version]`. If they drift,
update `__init__.py` (release-please does this automatically).

### CI rejects my version bump commit

`version-guard.yml` blocks any commit that touches `__version__` or
`.release-please-manifest.json` outside of release-please's own release
commit. If you really need to fix a stuck version, do it via a manual
release-please run or by editing the manifest in the release-please
PR itself.
