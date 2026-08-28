#!/usr/bin/env python3
"""Emit deterministic delivery preflight, build plan, or Skill validation evidence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> dict[str, object]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def git_value(repo: Path, *args: str) -> str | None:
    result = run(["git", *args], repo)
    return str(result["stdout"]) if result["exit_code"] == 0 else None


def preflight(repo: Path) -> int:
    status = run(["git", "status", "--porcelain=v1", "--branch"], repo)
    head = git_value(repo, "rev-parse", "HEAD")
    origin_main = git_value(repo, "rev-parse", "origin/main")
    merge_base = git_value(repo, "merge-base", "HEAD", "origin/main") if origin_main else None
    diff_check = run(["git", "diff", "--check"], repo)
    payload = {
        "repo": str(repo.resolve()),
        "branch": git_value(repo, "branch", "--show-current"),
        "head": head,
        "origin_main": origin_main,
        "merge_base": merge_base,
        "status": status,
        "diff_check": diff_check,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status["exit_code"] == 0 and diff_check["exit_code"] == 0 else 1


def build_plan(repo: Path) -> int:
    candidates = [
        ("mvnw", [["./mvnw", "test"], ["./mvnw", "verify"]]),
        ("gradlew", [["./gradlew", "test"], ["./gradlew", "check"]]),
        ("pom.xml", [["mvn", "test"], ["mvn", "verify"]]),
        ("build.gradle", [["gradle", "test"], ["gradle", "check"]]),
        ("build.gradle.kts", [["gradle", "test"], ["gradle", "check"]]),
    ]
    for marker, commands in candidates:
        path = repo / marker
        if path.exists() and (marker not in {"mvnw", "gradlew"} or os.access(path, os.X_OK)):
            print(json.dumps({"marker": marker, "commands": commands}, ensure_ascii=False, indent=2))
            return 0
    print(json.dumps({"error": "build system not detected"}, ensure_ascii=False))
    return 1


def validate_skills(repo: Path, python: Path, validator: Path, skills: list[str]) -> int:
    results = [run([str(python), str(validator), skill], repo) for skill in skills]
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    return 0 if all(item["exit_code"] == 0 for item in results) else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--repo", type=Path, default=Path.cwd())
    build_parser = subparsers.add_parser("build-plan")
    build_parser.add_argument("--repo", type=Path, default=Path.cwd())
    validate_parser = subparsers.add_parser("validate-skills")
    validate_parser.add_argument("--repo", type=Path, default=Path.cwd())
    validate_parser.add_argument("--python", type=Path, default=Path(sys.executable))
    validate_parser.add_argument("--validator", type=Path, required=True)
    validate_parser.add_argument("skills", nargs="+")
    args = parser.parse_args()
    if args.command == "preflight":
        return preflight(args.repo)
    if args.command == "build-plan":
        return build_plan(args.repo)
    return validate_skills(args.repo, args.python, args.validator, args.skills)


if __name__ == "__main__":
    raise SystemExit(main())
