#!/usr/bin/env python3
"""Return whether a changed-path set can affect the shipped Docker image."""

from __future__ import annotations

import sys
from collections.abc import Iterable

IMAGE_FILES = {
    ".dockerignore",
    ".github/workflows/docker-build.yml",
    "Dockerfile",
    "README.md",
    "pyproject.toml",
    "scripts/classify_docker_impact.py",
}
IMAGE_PREFIXES = ("src/",)


def requires_docker_build(paths: Iterable[str]) -> bool:
    """Return True when any normalized repository path affects the image."""

    return any(
        path in IMAGE_FILES or path.startswith(IMAGE_PREFIXES)
        for raw_path in paths
        if (path := raw_path.strip().removeprefix("./"))
    )


def main() -> None:
    print("true" if requires_docker_build(sys.stdin) else "false")


if __name__ == "__main__":
    main()
