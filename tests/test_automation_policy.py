from __future__ import annotations

from pathlib import Path

import yaml

from scripts.classify_docker_impact import requires_docker_build

ROOT = Path(__file__).parents[1]


def _workflow(name: str) -> tuple[str, dict]:
    text = (ROOT / ".github" / "workflows" / name).read_text()
    return text, yaml.safe_load(text)


def test_docker_impact_classification_is_exact() -> None:
    for path in (
        "Dockerfile",
        ".dockerignore",
        "README.md",
        "pyproject.toml",
        "src/bibliocommons_mcp/server.py",
        ".github/workflows/docker-build.yml",
        "scripts/classify_docker_impact.py",
    ):
        assert requires_docker_build([path]), path

    for path in (
        "web/package-lock.json",
        "docs-mintlify/index.mdx",
        ".github/workflows/ci.yml",
        "tests/test_auth.py",
    ):
        assert not requires_docker_build([path]), path


def test_ci_gate_aggregates_every_ci_job() -> None:
    _, workflow = _workflow("ci.yml")
    jobs = workflow["jobs"]
    gate = jobs["ci-gate"]

    assert workflow["permissions"] == {"contents": "read"}
    assert gate["name"] == "CI Gate"
    assert "always()" in gate["if"]
    assert set(gate["needs"]) == set(jobs) - {"ci-gate"}


def test_docker_workflow_always_emits_a_stable_gate() -> None:
    text, workflow = _workflow("docker-build.yml")
    gate = workflow["jobs"]["gate"]

    assert workflow["permissions"] == {"contents": "read"}
    assert gate["name"] == "Docker Gate"
    assert set(gate["needs"]) == {"impact", "build"}
    assert "always()" in gate["if"]
    assert "branches: [main]\n    paths:" not in text


def test_docker_build_is_admitted_only_by_the_classifier() -> None:
    _, workflow = _workflow("docker-build.yml")
    build = workflow["jobs"]["build"]

    assert build["needs"] == "impact"
    assert build["if"] == "needs.impact.outputs.build == 'true'"
