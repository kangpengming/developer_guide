# Antigravity CLI 约定

先根据已加载 `SKILL.md` 的真实路径得到 `<skill-root>`，再运行：

```bash
python3 <skill-root>/scripts/run_antigravity.py --stage review|module|execute --handoff handoff.json --repo <repo> --evidence-out /tmp/antigravity-evidence.json
```

仓库内 Skill 的常见路径是 `.agents/skills/antigravity-collaborative-delivery`，但以当前实际加载路径为准；禁止从项目根目录直接调用不存在的 `scripts/run_antigravity.py`。
证据文件必须位于目标仓库外，避免污染工作区或绕过越界检查。

脚本固定使用 `/home/rsp/.local/bin/antigravity`、JSON 输出和 `--dangerously-skip-permissions`，串行调用并输出统一证据。使用 `--add-dir <repo>` 绑定目标仓库；新 conversation 加 `--new-project`，复审沿用原 conversation 项目；禁止写入默认 scratch 目录。模型顺序：

- review/module：`gemini-3.7-flash-high`、`gemini-3.6-flash-high`、`claude-opus-4-6-thinking`
- archive/test/delivery：`gemini-3.7-flash-medium`、`gemini-3.6-flash-medium`、`claude-opus-4-6-thinking`

仅模型不可用、超时或进程失败时回退；审核/CR 不通过、测试或业务命令失败不得换模型绕过。
默认超时：审核 `5m`，单模块开发和交付 `10m`；可用 handoff 顶层 `timeout` 或命令行 `--timeout` 覆盖，命令行优先。
脚本从 CLI JSON 返回中提取 `conversation_id`，并写入统一证据；后续 CR 修改必须把该 ID 回填到下一份 handoff。
`module` 默认必须产生允许范围内的文件变更；CLI 返回 0 但无变更仍视为失败，不切换模型绕过。仅当模块已满足交接契约时，才在 handoff 显式设置 `"require_changes": false`。

## handoff.json

```json
{
  "task": "具体任务与验收",
  "conversation_id": null,
  "allowed_files": ["精确相对路径"],
  "scope": "允许的外部操作或命令",
  "stop_conditions": ["范围变化即停止"],
  "timeout": "10m",
  "require_changes": true
}
```

- review：包含完整方案，要求只审核并输出编号、级别、依据、建议、是否阻塞；复审传原 conversation ID 和 Codex 裁决。
- archive：包含最终方案全文、精确标题、用户身份、folder token、链接五列；返回 URL、身份、目录、完整回读和命令结果。
- module：包含单模块职责/契约、骨架、允许文件、验收；禁止处理下一模块或交付。
- test：包含对应模块与正常/边界/异常场景；复用生产流程。需改生产代码时停止并报告。
- delivery：包含代码查看阶段确认的精确命令、分支/HEAD/远端、验证和停止条件；禁止扩大暂存、改变提交信息、rebase、force push 或猜部署。

脚本比较调用前后文件指纹；改动 `allowed_files` 外路径时返回失败但不擅自回滚。它不替代 Pipeline 授权或停止条件，外部写入后仍由 Codex 核对实际状态。
