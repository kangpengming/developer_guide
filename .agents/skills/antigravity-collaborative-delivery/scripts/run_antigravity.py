#!/usr/bin/env python3
"""Run Antigravity with compact JSON handoffs and deterministic evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ANTIGRAVITY = "/home/rsp/.local/bin/antigravity"
MODELS = {
    "review": ["gemini-3.7-flash-high", "gemini-3.6-flash-high", "claude-opus-4-6-thinking"],
    "module": ["gemini-3.7-flash-high", "gemini-3.6-flash-high", "claude-opus-4-6-thinking"],
    "execute": ["gemini-3.7-flash-medium", "gemini-3.6-flash-medium", "claude-opus-4-6-thinking"],
}


def git_state(repo: Path) -> dict[str, object]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--branch"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True, check=False
    )
    return {"status": result.stdout.strip(), "head": head.stdout.strip(), "exit_code": result.returncode}


def working_fingerprints(repo: Path) -> dict[str, str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"], cwd=repo, capture_output=True, check=False
    )
    fingerprints: dict[str, str] = {}
    entries = [entry for entry in result.stdout.split(b"\0") if entry]
    index = 0
    while index < len(entries):
        entry = entries[index]
        status = entry[:2].decode("ascii", errors="replace")
        path = entry[3:].decode("utf-8", errors="surrogateescape")
        if status[0] in {"R", "C"} and index + 1 < len(entries):
            index += 1
            path = entries[index].decode("utf-8", errors="surrogateescape")
        file_path = repo / path
        fingerprint = "<deleted>"
        if file_path.is_file():
            fingerprint = hashlib.sha256(file_path.read_bytes()).hexdigest()
        elif file_path.is_dir():
            fingerprint = "<directory>"
        fingerprints[path] = fingerprint
        index += 1
    return fingerprints


def prompt_for(stage: str, handoff: dict[str, object]) -> str:
    prefix = {
        "review": "只审核，不修改工作区。",
        "module": "只处理指定单模块和允许文件，不执行交付。",
        "execute": "只执行已授权范围；状态变化或失败立即停止。",
    }[stage]
    return prefix + "\n交接 JSON：\n" + json.dumps(handoff, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=MODELS, required=True)
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--timeout", default="2m")
    args = parser.parse_args()
    handoff = json.loads(args.handoff.read_text(encoding="utf-8"))
    before = git_state(args.repo)
    before_files = working_fingerprints(args.repo)
    allowed_files = {str(path) for path in handoff.get("allowed_files", [])}
    attempts: list[dict[str, object]] = []
    for model in MODELS[args.stage]:
        command = [
            ANTIGRAVITY,
            "--model", model,
            "--mode", "plan" if args.stage == "review" else "accept-edits",
            "--output-format", "json",
            "--dangerously-skip-permissions",
            "--print-timeout", args.timeout,
        ]
        conversation_id = handoff.get("conversation_id")
        if conversation_id:
            command.extend(["--conversation", str(conversation_id)])
        command.append("--print=" + prompt_for(args.stage, handoff))
        result = subprocess.run(command, cwd=args.repo, text=True, capture_output=True, check=False)
        attempt = {
            "model": model,
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
        attempts.append(attempt)
        current_files = working_fingerprints(args.repo)
        changed_during_attempt = {
            path for path in set(before_files) | set(current_files)
            if before_files.get(path) != current_files.get(path)
        }
        if result.returncode != 0 and (args.stage == "execute" or changed_during_attempt):
            print(json.dumps({
                "before": before,
                "after": git_state(args.repo),
                "attempts": attempts,
                "touched_files": sorted(changed_during_attempt),
                "stopped_without_fallback": True,
            }, ensure_ascii=False, indent=2))
            return 1
        if result.returncode == 0 and (args.stage != "review" or result.stdout.strip()):
            after = git_state(args.repo)
            after_files = working_fingerprints(args.repo)
            touched = {
                path for path in set(before_files) | set(after_files)
                if before_files.get(path) != after_files.get(path)
            }
            unexpected = sorted(touched - allowed_files)
            evidence = {
                "before": before,
                "after": after,
                "attempts": attempts,
                "touched_files": sorted(touched),
                "unexpected_files": unexpected,
            }
            print(json.dumps(evidence, ensure_ascii=False, indent=2))
            return 2 if unexpected else 0
    print(json.dumps({"before": before, "after": git_state(args.repo), "attempts": attempts}, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
