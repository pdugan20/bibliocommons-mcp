from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import yaml

from scripts.classify_docker_impact import requires_docker_build

ROOT = Path(__file__).parents[1]
PINNED_ACTION = re.compile(r"uses:\s+[^\s@]+@[0-9a-f]{40}(?:\s+#.*)?$")
APPROVAL_GATED_UPDATE_TYPES = {
    "digest",
    "pin",
    "pinDigest",
    "lockFileMaintenance",
}
AUTOMERGE_UPDATE_TYPES = {"patch", "minor"}
UNCONSTRAINED_GATE_KEYS = {
    "description",
    "matchUpdateTypes",
    "dependencyDashboardApproval",
    "automerge",
}


def _workflow(name: str) -> tuple[str, dict]:
    text = (ROOT / ".github" / "workflows" / name).read_text()
    return text, yaml.safe_load(text)


def _assert_unsafe_updates_are_approval_gated(renovate: dict) -> None:
    package_rules = renovate["packageRules"]

    for rule in package_rules:
        if rule.get("automerge") is not True:
            continue
        update_types = set(rule.get("matchUpdateTypes", []))
        assert update_types
        assert update_types <= AUTOMERGE_UPDATE_TYPES

    for update_type in APPROVAL_GATED_UPDATE_TYPES:
        matching = [
            rule
            for rule in package_rules
            if update_type in rule.get("matchUpdateTypes", [])
        ]
        assert matching
        assert not any(rule.get("automerge") is True for rule in matching)
        terminal = matching[-1]
        assert terminal is package_rules[-1]
        assert set(terminal) == UNCONSTRAINED_GATE_KEYS
        assert set(terminal["matchUpdateTypes"]) == APPROVAL_GATED_UPDATE_TYPES
        assert terminal["dependencyDashboardApproval"] is True
        assert terminal["automerge"] is False


def _assert_automerge_release_ages(renovate: dict) -> None:
    expected_ages = {"pep621": "7 days", "github-actions": "14 days"}

    package_rules = renovate["packageRules"]
    for index, rule in enumerate(package_rules):
        if rule.get("automerge") is not True:
            continue
        managers = rule.get("matchManagers")
        assert isinstance(managers, list)
        assert len(managers) == 1
        manager = managers[0]
        update_types = set(rule["matchUpdateTypes"])
        assert rule.get("minimumReleaseAge") == expected_ages[manager]

        for later in package_rules[index + 1 :]:
            if "minimumReleaseAge" not in later:
                continue
            later_managers = set(later.get("matchManagers", []))
            later_update_types = set(later.get("matchUpdateTypes", []))
            can_match_manager = not later_managers or manager in later_managers
            can_match_update = not later_update_types or bool(
                update_types & later_update_types
            )
            if can_match_manager and can_match_update:
                assert later["minimumReleaseAge"] == expected_ages[manager]


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


def test_every_external_action_is_commit_pinned() -> None:
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            if "uses:" not in line:
                continue
            assert PINNED_ACTION.search(line), f"{path}:{line_number}: {line}"


def test_ci_tools_do_not_float() -> None:
    workflows = "\n".join(
        path.read_text()
        for path in sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    )

    assert "@latest" not in workflows
    assert "pip install ruff==0.16.3" in workflows
    assert workflows.count("pip install build==1.5.0") == 2
    assert workflows.count("version: 0.4.83") == 2


def test_routine_updater_ownership_is_disjoint_and_fail_closed() -> None:
    renovate = json.loads((ROOT / "renovate.json").read_text())
    dependabot = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text())

    assert renovate["enabled"] is True
    assert set(renovate["enabledManagers"]) == {
        "npm",
        "pep621",
        "dockerfile",
        "github-actions",
    }
    assert renovate["platformAutomerge"] is True
    assert renovate["automergeType"] == "pr"
    assert renovate["automergeStrategy"] == "squash"
    assert renovate["internalChecksFilter"] == "strict"
    assert renovate["vulnerabilityAlerts"] == {"enabled": False}
    assert renovate["lockFileMaintenance"] == {
        "enabled": True,
        "schedule": ["before 6am on monday"],
        "dependencyDashboardApproval": True,
        "automerge": False,
    }

    assert {
        (entry["package-ecosystem"], entry["directory"])
        for entry in dependabot["updates"]
    } == {
        ("npm", "/web"),
        ("pip", "/"),
        ("docker", "/"),
        ("github-actions", "/"),
    }
    assert all(
        entry["open-pull-requests-limit"] == 0 for entry in dependabot["updates"]
    )

    package_rules = renovate["packageRules"]
    assert any(
        rule.get("matchUpdateTypes") == ["major"]
        and rule.get("dependencyDashboardApproval") is True
        and rule.get("automerge") is False
        for rule in package_rules
    )
    assert any(
        rule.get("matchCurrentVersion") == "/^0\\./"
        and set(rule.get("matchUpdateTypes", [])) == {"minor", "major"}
        and rule.get("dependencyDashboardApproval") is True
        and rule.get("automerge") is False
        for rule in package_rules
    )
    assert any(
        rule.get("matchManagers") == ["dockerfile"]
        and rule.get("matchPackageNames") == ["python"]
        and set(rule.get("matchUpdateTypes", [])) == {"minor", "major"}
        and rule.get("dependencyDashboardApproval") is True
        and rule.get("automerge") is False
        for rule in package_rules
    )
    assert any(
        rule.get("matchManagers") == ["github-actions"]
        and rule.get("matchPackageNames") == ["actions/python-versions"]
        and set(rule.get("matchUpdateTypes", [])) == {"minor", "major"}
        and rule.get("groupName") == "CI Python interpreter line"
        and rule.get("dependencyDashboardApproval") is True
        and rule.get("automerge") is False
        for rule in package_rules
    )
    assert any(
        rule.get("description") == "All web updates require generated-bundle approval"
        and rule.get("matchManagers") == ["npm"]
        and rule.get("matchFileNames") == ["web/package.json"]
        and rule.get("dependencyDashboardApproval") is True
        and rule.get("automerge") is False
        and "matchDepTypes" not in rule
        and "matchCurrentVersion" not in rule
        and "matchUpdateTypes" not in rule
        for rule in package_rules
    )
    assert all(
        rule.get("dependencyDashboardApproval", True) is True
        and rule.get("automerge") is False
        for rule in package_rules
        if rule.get("matchManagers") == ["npm"]
    )
    assert any(
        rule.get("matchManagers") == ["dockerfile"]
        and set(rule.get("matchUpdateTypes", []))
        == {"patch", "minor", "digest", "pin", "pinDigest"}
        and "minimumReleaseAge" not in rule
        and rule.get("automerge") is False
        for rule in package_rules
    )

    _assert_unsafe_updates_are_approval_gated(renovate)
    _assert_automerge_release_ages(renovate)


def test_unsafe_update_gate_rejects_narrowing_and_late_overrides() -> None:
    renovate = json.loads((ROOT / "renovate.json").read_text())

    for selector, value in (
        ("matchManagers", ["pep621"]),
        ("matchFileNames", ["pyproject.toml"]),
    ):
        narrowed = copy.deepcopy(renovate)
        narrowed["packageRules"][-1][selector] = value
        try:
            _assert_unsafe_updates_are_approval_gated(narrowed)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"unsafe gate accepted {selector} narrowing")

    late_unsafe_automerge = copy.deepcopy(renovate)
    late_unsafe_automerge["packageRules"].append(
        {"matchUpdateTypes": ["digest"], "automerge": True}
    )
    try:
        _assert_unsafe_updates_are_approval_gated(late_unsafe_automerge)
    except AssertionError:
        pass
    else:
        raise AssertionError("late digest automerge override was accepted")

    selector_only_override = copy.deepcopy(renovate)
    selector_only_override["packageRules"].append(
        {
            "matchManagers": ["github-actions"],
            "dependencyDashboardApproval": False,
        }
    )
    try:
        _assert_unsafe_updates_are_approval_gated(selector_only_override)
    except AssertionError:
        pass
    else:
        raise AssertionError("selector-only approval override was accepted")


def test_automerge_release_age_rejects_shortened_actions_quarantine() -> None:
    renovate = json.loads((ROOT / "renovate.json").read_text())
    shortened = copy.deepcopy(renovate)
    actions = next(
        rule
        for rule in shortened["packageRules"]
        if rule.get("matchManagers") == ["github-actions"]
        and rule.get("automerge") is True
    )
    actions["minimumReleaseAge"] = "1 day"

    try:
        _assert_automerge_release_ages(shortened)
    except AssertionError:
        pass
    else:
        raise AssertionError("one-day Actions quarantine was accepted")

    later_override = copy.deepcopy(renovate)
    later_override["packageRules"].append(
        {
            "matchManagers": ["github-actions"],
            "matchUpdateTypes": ["minor"],
            "minimumReleaseAge": "1 day",
        }
    )
    try:
        _assert_automerge_release_ages(later_override)
    except AssertionError:
        pass
    else:
        raise AssertionError("later one-day Actions override was accepted")
