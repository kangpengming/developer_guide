#!/usr/bin/env python3
"""Run an approved delivery plan while keeping model-visible output compact."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import time
from collections import deque
from pathlib import Path

SUMMARY_PATTERN = re.compile(
    r"(tests? run|tests? passed|tests? failed|build (success|failure)|\bpassed\b|\bfailed\b|"
    r"\berror\b|coverage|deployed|active \(running\)|status[:=])",
    re.IGNORECASE,
)
SECRET_PATTERN = re.compile(
    r"(?i)(authorization|password|passwd|secret|token|api[-_]?key)(\s*[:=]\s*)(\S+)"
)
SECRET_FLAGS = {"authorization", "password", "passwd", "secret", "token", "api-key", "api_key"}


def redact(line: str) -> str:
    """Hide common credential assignments from model-visible evidence."""
    return SECRET_PATTERN.sub(r"\1\2<redacted>", line.rstrip())[:500]


def redact_command(command: list[str]) -> list[str]:
    """Hide common secret values while preserving the executed argv shape."""
    visible: list[str] = []
    hide_next = False
    for argument in command:
        if hide_next:
            visible.append("<redacted>")
            hide_next = False
            continue
        visible.append(redact(argument))
        flag = argument.lstrip("-").lower()
        hide_next = flag in SECRET_FLAGS and "=" not in argument
    return visible


def resolve_outside(repo: Path, path: Path, label: str) -> Path:
    """Require logs and evidence outside the target repository."""
    resolved = path.resolve()
    if resolved.is_relative_to(repo):
        raise ValueError(f"{label} must be outside repo")
    return resolved


def resolve_cwd(repo: Path, value: str) -> Path:
    """Resolve a step directory without allowing repository escape."""
    resolved = (repo / value).resolve()
    if not resolved.is_relative_to(repo) or not resolved.is_dir():
        raise ValueError(f"invalid step cwd: {value}")
    return resolved


def log_summary(path: Path, failed: bool) -> list[str]:
    """Return matched success lines or a short failure tail."""
    tail: deque[str] = deque(maxlen=20)
    matched: deque[str] = deque(maxlen=12)
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            cleaned = redact(line)
            tail.append(cleaned)
            if SUMMARY_PATTERN.search(cleaned):
                matched.append(cleaned)
    selected = tail if failed else matched
    return [line for line in selected if line]


def run_step(repo: Path, log_dir: Path, index: int, step: dict[str, object]) -> dict[str, object]:
    """Run one argv-only step and persist its complete combined log."""
    name = str(step.get("name") or f"step-{index}")
    command = step.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        raise ValueError(f"{name}: command must be a non-empty string array")
    cwd = resolve_cwd(repo, str(step.get("cwd") or "."))
    timeout = int(step.get("timeout_seconds") or 1800)
    if timeout < 1 or timeout > 86400:
        raise ValueError(f"{name}: timeout_seconds must be 1..86400")
    extra_env = step.get("env") or {}
    if not isinstance(extra_env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in extra_env.items()):
        raise ValueError(f"{name}: env must contain string keys and values")
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "-", name).strip("-") or f"step-{index}"
    log_path = log_dir / f"{index:02d}-{safe_name}.log"
    started = time.monotonic()
    timed_out = False
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env={**os.environ, **extra_env},
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            exit_code = 124
    failed = exit_code != 0
    return {
        "name": name,
        "command": redact_command(command),
        "cwd": str(cwd.relative_to(repo)) or ".",
        "exit_code": exit_code,
        "duration_seconds": round(time.monotonic() - started, 3),
        "timed_out": timed_out,
        "log": str(log_path),
        "summary": log_summary(log_path, failed),
        "allow_failure": bool(step.get("allow_failure", False)),
    }


def emit(payload: dict[str, object], evidence: Path | None) -> None:
    """Print evidence and optionally persist the same JSON outside the repo."""
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    if evidence:
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(content + "\n", encoding="utf-8")
    print(content)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    try:
        log_dir = resolve_outside(repo, args.log_dir, "--log-dir")
        evidence = resolve_outside(repo, args.evidence_out, "--evidence-out") if args.evidence_out else None
        if log_dir.exists():
            raise ValueError("--log-dir must be a new path")
        if evidence and evidence.exists():
            raise ValueError("--evidence-out must not already exist")
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        log_dir.mkdir(parents=True)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    steps = plan.get("steps") if isinstance(plan, dict) else None
    if not isinstance(steps, list) or not steps:
        parser.error("plan.steps must be a non-empty array")
    results: list[dict[str, object]] = []
    status = "passed"
    try:
        for index, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                raise ValueError(f"step {index} must be an object")
            result = run_step(repo, log_dir, index, step)
            results.append(result)
            if result["exit_code"] != 0 and not result["allow_failure"]:
                status = "failed"
                break
    except (OSError, ValueError) as error:
        status = "invalid"
        results.append({"error": str(error)})
    payload = {"status": status, "repo": str(repo), "steps": results}
    emit(payload, evidence)
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
