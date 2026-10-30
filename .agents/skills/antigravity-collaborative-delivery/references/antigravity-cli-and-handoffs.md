# Antigravity CLI 约定

向 Antigravity 发送当前任务的完整技术方案、相关目录结构、架构设计和必要源码属于 `AGENTS.md` 已常驻授权的协作范围，无须逐次确认。调用前排除凭据、密钥、Token、个人数据和无关文件；无法安全排除时停止。

先根据已加载 `SKILL.md` 的真实路径得到 `<skill-root>`，再通过执行器的宿主机权限或等效非沙箱方式运行以下命令；这是启动命令的执行环境要求，不是额外 CLI 参数：

```bash
python3 <skill-root>/scripts/run_antigravity.py --stage review|module|execute --handoff handoff.json --repo <repo> --evidence-out /tmp/antigravity-evidence.json
```

仓库内 Skill 的常见路径是 `.agents/skills/antigravity-collaborative-delivery`，但以当前实际加载路径为准；禁止从项目根目录直接调用不存在的 `scripts/run_antigravity.py`。
证据文件必须位于目标仓库外，避免污染工作区或绕过越界检查。

脚本固定使用 `/home/rsp/.local/bin/antigravity`、JSON 输出和 `--dangerously-skip-permissions`，禁止传入 `--sandbox`，串行调用并输出统一证据。宿主机权限只解除执行环境限制，不改变 `allowed_files`、`scope` 或停止条件。使用 `--add-dir <repo>` 绑定目标仓库；新 conversation 加 `--new-project`，复审沿用原 conversation 项目；禁止写入默认 scratch 目录。每次调用前通过 `antigravity models` 检测当前可用模型，同等级 Gemini Flash 按版本从新到旧选择，再使用 Claude 回退；检测失败才使用已验证的默认顺序：

- review/module：`gemini-3.8-flash-high`、`claude-opus-4-6-thinking`
- archive/test/delivery：`gemini-3.8-flash-medium`、`claude-opus-4-6-thinking`

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
