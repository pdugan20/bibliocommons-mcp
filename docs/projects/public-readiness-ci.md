# Project: Public-readiness CI / tooling

## Goal

Lock in the CI/tooling additions that matter for an open-source project external contributors trust and can build against. Drop the ones that look impressive but add maintenance without commensurate value.

## Why

Right now the project's CI is solid for a personal repo: ruff, prettier, markdownlint, six-cell test matrix, release-please. To make this a project _other_ people contribute to with confidence, three classes of guarantee matter:

1. **No silent breaking changes** — schema, behavior, or packaging.
2. **A contributor can land a PR with confidence the project will build, install, and not embarrass them.**
3. **Security and conventions are surfaced where contributors will see them.**

## Triage

Items considered in the roadmap, re-evaluated through that lens:

### Worth doing (in priority order)

| Item                                    | Why it matters publicly                                                                                                                                                                                                                                                                             | Effort |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| **TestPyPI staging publish**            | Catches `pyproject.toml` errors, missing wheels, classifier typos before they hit prod PyPI (where you can't re-publish the same version). Clickwheel has `test-publish.yml`. Wires into release-please via a pre-release tag flow.                                                                 | ~1h    |
| **`mcpdiff` schema snapshots**          | Snapshots every tool's `inputSchema` + `outputSchema` and fails CI on accidental changes. External consumers depend on tool schemas; silent edits to descriptions are a tool-poisoning vector. Worth it as soon as we're a public OSS project.                                                      | ~1h    |
| **Raise coverage floor from 60% → 80%** | We're at 86%. Locking in 80% prevents accidental regression. Cheap win, no new infrastructure.                                                                                                                                                                                                      | ~5m    |
| **Pre-commit hook self-test**           | The credential-leak grep in `.pre-commit-config.yaml` is meant to block PRs that leak a card number or PIN. Add a `tests/test_precommit_guards.py` that deliberately tries to commit known-bad strings and asserts the hook rejects them. Demonstrates the guard works — a real reassurance signal. | ~30m   |
| **`claude-code-lint` in CI**            | Modest signal that the project follows Claude Code conventions. Low cost (one `npx` line). Clickwheel runs it.                                                                                                                                                                                      | ~10m   |
| **`CODE_OF_CONDUCT.md`**                | GitHub's community-profile widget calls this out as missing. Use the Contributor Covenant template.                                                                                                                                                                                                 | ~5m    |
| **Issue / PR templates**                | Already shipped — but worth surfacing in CONTRIBUTING.                                                                                                                                                                                                                                              | done   |
| **Branch protection ruleset**           | Already set up — `Ruff` + `Tests (ubuntu-latest, 3.12)` are required for merge.                                                                                                                                                                                                                     | done   |

### Skip

| Item                                                         | Why skipped                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MCP Inspector CLI in CI**                                  | `tests/test_mcp_smoke.py` covers the same handshake validation in-process, pinned to our SDK version. Inspector is the right manual debugging tool (documented in CONTRIBUTING). Adding to CI adds Node-side churn for no new signal.                                                                                                         |
| **Sentry MCP integration**                                   | Useful only when there's a deployed instance to monitor. Most users `pipx install` and run locally — there's no central instance to instrument. Revisit if a hosted offering ever exists.                                                                                                                                                     |
| **Live state-changing CI test** (place + cancel a real hold) | Can't run safely without a dedicated test account and a target library that won't reject the rapid create/delete pattern as bot behavior. Replay cassettes cover read paths; body-shape unit tests cover writes. The remaining risk (gateway breaks production state-change endpoint silently) is low and would surface fast in user reports. |
| **Repo-level `claudelint`**                                  | Your personal `claudelint` skill exists locally. It's the right tool, but tying CI to a personal-config validator hurts non-pdugan20 contributors. Skip unless `claudelint` becomes a public package.                                                                                                                                         |
| **Standalone `fastmcp` 3.x migration**                       | The official `mcp` SDK v2 server covers the current OAuth, Streamable HTTP, and MCP Apps requirements. Adding another server framework is unnecessary.                                                                                                                                                                                        |

## Order to execute

If we do nothing else, these three together convert "polished personal project" into "ready for external contributors":

1. **TestPyPI staging publish** — single biggest reassurance signal that the next release won't break installs.
2. **`mcpdiff` schema snapshots** — protects external API consumers.
3. **Pre-commit self-test** — proves the credential guard works.

The other items (raise coverage floor, `claude-code-lint`, `CODE_OF_CONDUCT.md`) are 5–10 minutes each — bundle them all into one "public-readiness pass" PR.

## Effort

**~3h** for the recommended set bundled together. The skipped items would be another 4–6h with marginal ROI.

## Open questions

- **TestPyPI publishing on every release, or only manual?** Lean **every** — release-please can emit a pre-release tag pattern (e.g. `v0.3.0-rc1`) and publish.yml routes based on tag shape. More to wire but more reassuring.
- **`mcpdiff` snapshot location.** `tests/__snapshots__/tools.json` or `tests/snapshots/`? Whatever's idiomatic for the tool.
- **Should `CODE_OF_CONDUCT.md` be the Contributor Covenant v2.1 verbatim or trimmed?** Verbatim is the safer choice — readers know what they're getting.

## Dependencies / blockers

- TestPyPI publish requires a TestPyPI trusted-publisher setup (separate from prod PyPI). Same pattern, different account.
- `mcpdiff` is an external Node tool — confirm it's actively maintained before committing to it as a CI dep.
