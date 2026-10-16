#!/usr/bin/env python3
"""Run Antigravity with compact JSON handoffs and deterministic evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ANTIGRAVITY = "/home/rsp/.local/bin/antigravity"
DEFAULT_MODELS = {
    "review": ["gemini-3.8-flash-high", "claude-opus-4-6-thinking"],
    "module": ["gemini-3.8-flash-high", "claude-opus-4-6-thinking"],
    "execute": ["gemini-3.8-flash-medium", "claude-opus-4-6-thinking"],
}
DEFAULT_TIMEOUTS = {"review": "5m", "module": "10m", "execute": "10m"}
CONVERSATION_KEYS = {"conversation_id", "conversationId", "conversationID"}


def model_version(model: str) -> tuple[int, ...]:
    """提取 Gemini 模型版本，供可用模型按新到旧排序。"""
    match = re.match(r"^gemini-(\d+(?:\.\d+)*)-flash-", model)
    return tuple(int(part) for part in match.group(1).split(".")) if match else ()


def resolve_models(stage: str) -> tuple[list[str], dict[str, object]]:
    """查询当前可用模型，并为指定阶段生成实际回退顺序。"""
    try:
        result = subprocess.run(
            [ANTIGRAVITY, "models"], text=True, capture_output=True, check=False, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return DEFAULT_MODELS[stage], {
            "error": type(error).__name__,
            "fallback_to_defaults": True,
        }
    discovery: dict[str, object] = {
        "exit_code": result.returncode,
        "stderr": result.stderr.strip()[-2000:],
    }
    if result.returncode != 0:
        discovery["fallback_to_defaults"] = True
        return DEFAULT_MODELS[stage], discovery

    available = {
        model
        for line in result.stdout.splitlines()
        if line.strip()
        for model in [line.split()[0]]
        if re.match(r"^(?:gemini|claude|gpt)-", model)
    }
    effort = "high" if stage in {"review", "module"} else "medium"
    gemini_models = sorted(
        (
            model
            for model in available
            if re.match(rf"^gemini-\d+(?:\.\d+)*-flash-{effort}$", model)
        ),
        key=model_version,
        reverse=True,
    )
    models = gemini_models + [
        model for model in DEFAULT_MODELS[stage] if model.startswith("claude-") and model in available
    ]
    discovery["available_models"] = sorted(available)
    discovery["selected_models"] = models
    if not models:
        discovery["no_supported_models"] = True
    return models, discovery


def parse_cli_json(output: str) -> object | None:
    """Parse a JSON response without making JSON output mandatory for diagnostics."""
    try:
        return json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return None


def find_conversation_id(value: object) -> str | None:
    """Find a conversation identifier in nested CLI JSON."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in CONVERSATION_KEYS and item:
                return str(item)
        for item in value.values():
            found = find_conversation_id(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_conversation_id(item)
            if found:
                return found
    return None


def conversation_id_from(stdout: str, stderr: str) -> str | None:
    """Extract the ID from structured output, with CLI logs as a fallback."""
    found = find_conversation_id(parse_cli_json(stdout))
    if found:
        return found
    match = re.search(r"conversation(?:ID| ID|_id)[=\"': ]+([0-9a-f-]{16,})", stderr, re.IGNORECASE)
    return match.group(1) if match else None


def emit(evidence: dict[str, object], output_path: Path | None) -> None:
    """Print evidence and optionally persist the exact same JSON."""
    content = json.dumps(evidence, ensure_ascii=False, indent=2)
    if output_path:
        output_path.write_text(content + "\n", encoding="utf-8")
    print(content)


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
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repo,
        capture_output=True,
        check=False,
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


def prompt_for(stage: str, handoff: dict[str, object], repo: Path) -> str:
    prefix = {
        "review": "只审核，不修改工作区。",
        "module": (
            "必须直接使用文件编辑工具完成指定单模块，不要只返回代码或说明。"
            "只修改允许文件，完成前核对工作区已产生预期 diff，不执行交付。"
        ),
        "execute": "只执行已授权范围；状态变化或失败立即停止。",
    }[stage]
    workspace = (
        f"\n目标仓库是 {repo}。所有相对路径均相对于该目录；"
        "禁止读写 Antigravity scratch 目录。"
    )
    return prefix + workspace + "\n交接 JSON：\n" + json.dumps(handoff, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=DEFAULT_MODELS, required=True)
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--timeout")
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.evidence_out and args.evidence_out.resolve().is_relative_to(repo):
        parser.error("--evidence-out must be outside --repo")
    handoff = json.loads(args.handoff.read_text(encoding="utf-8"))
    timeout = args.timeout or str(handoff.get("timeout") or DEFAULT_TIMEOUTS[args.stage])
    require_changes = bool(handoff.get("require_changes", args.stage == "module"))
    before = git_state(repo)
    before_files = working_fingerprints(repo)
    allowed_files = {str(path) for path in handoff.get("allowed_files", [])}
    attempts: list[dict[str, object]] = []
    models, model_discovery = resolve_models(args.stage)
    for model in models:
        command = [
            ANTIGRAVITY,
            "--model", model,
            "--mode", "plan" if args.stage == "review" else "accept-edits",
            "--output-format", "json",
            "--dangerously-skip-permissions",
            "--print-timeout", timeout,
            "--add-dir", str(repo),
        ]
        conversation_id = handoff.get("conversation_id")
        if conversation_id:
            command.extend(["--conversation", str(conversation_id)])
        else:
            command.append("--new-project")
        command.append("--print=" + prompt_for(args.stage, handoff, repo))
        result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
        parsed_stdout = parse_cli_json(result.stdout)
        conversation_id = conversation_id_from(result.stdout, result.stderr)
        attempt = {
            "model": model,
            "exit_code": result.returncode,
            "conversation_id": conversation_id,
            "stdout_chars": len(result.stdout),
            "stderr": result.stderr.strip()[-4000:],
        }
        if args.stage == "review":
            attempt["response"] = parsed_stdout if parsed_stdout is not None else result.stdout.strip()
        elif result.stdout:
            attempt["response_preview"] = result.stdout.strip()[-2000:]
        attempts.append(attempt)
        current_files = working_fingerprints(repo)
        changed_during_attempt = {
            path for path in set(before_files) | set(current_files)
            if before_files.get(path) != current_files.get(path)
        }
        if result.returncode != 0 and (args.stage == "execute" or changed_during_attempt):
            evidence = {
                "before": before,
                "after": git_state(repo),
                "attempts": attempts,
                "model_discovery": model_discovery,
                "touched_files": sorted(changed_during_attempt),
                "stopped_without_fallback": True,
                "timeout": timeout,
            }
            emit(evidence, args.evidence_out)
            return 1
        if result.returncode == 0 and (args.stage != "review" or result.stdout.strip()):
            after = git_state(repo)
            after_files = working_fingerprints(repo)
            touched = {
                path for path in set(before_files) | set(after_files)
                if before_files.get(path) != after_files.get(path)
            }
            unexpected = sorted(touched - allowed_files)
            evidence = {
                "before": before,
                "after": after,
                "attempts": attempts,
                "model_discovery": model_discovery,
                "conversation_id": conversation_id,
                "touched_files": sorted(touched),
                "unexpected_files": unexpected,
                "timeout": timeout,
            }
            if unexpected:
                emit(evidence, args.evidence_out)
                return 2
            if require_changes and not touched:
                evidence["no_expected_changes"] = True
                emit(evidence, args.evidence_out)
                return 3
            emit(evidence, args.evidence_out)
            return 0
    emit({
        "before": before,
        "after": git_state(repo),
        "attempts": attempts,
        "model_discovery": model_discovery,
        "timeout": timeout,
    }, args.evidence_out)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
