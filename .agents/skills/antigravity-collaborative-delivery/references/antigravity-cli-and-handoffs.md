# Antigravity CLI 约定

优先运行：

```bash
python3 scripts/run_antigravity.py --stage review|module|execute --handoff handoff.json --repo <repo>
```

脚本固定使用 `/home/rsp/.local/bin/antigravity`、JSON 输出、`--dangerously-skip-permissions`，串行调用并输出统一证据。模型顺序内置：

- review/module：`gemini-3.7-flash-high`、`gemini-3.6-flash-high`、`claude-opus-4-6-thinking`
- archive/test/delivery：`gemini-3.7-flash-medium`、`gemini-3.6-flash-medium`、`claude-opus-4-6-thinking`

仅模型不可用、超时或进程失败时回退；审核/CR 不通过、测试或业务命令失败不得换模型绕过。

## handoff.json

```json
{
  "task": "具体任务与验收",
  "conversation_id": null,
  "allowed_files": ["精确相对路径"],
  "scope": "允许的外部操作或命令",
  "stop_conditions": ["范围变化即停止"]
}
```

- review：包含完整方案，要求只审核并输出编号、级别、依据、建议、是否阻塞；复审传原 conversation ID 和 Codex 裁决。
- archive：包含最终方案全文、精确标题、用户身份、folder token、链接五列；返回 URL、身份、目录、完整回读和命令结果。
- module：包含单模块职责/契约、骨架、允许文件、验收；禁止处理下一模块或交付。
- test：包含对应模块与正常/边界/异常场景；复用生产流程。需改生产代码时停止并报告。
- delivery：包含代码查看阶段确认的精确命令、分支/HEAD/远端、验证和停止条件；禁止扩大暂存、改变提交信息、rebase、force push 或猜部署。

脚本比较调用前后文件指纹；改动 `allowed_files` 外路径时返回失败但不擅自回滚。它不替代 Pipeline 授权或停止条件，外部写入后仍由 Codex 核对实际状态。
