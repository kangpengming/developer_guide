# 交付计划格式

计划只写已由 Pipeline 确定且授权的命令；`command` 是 argv 数组，不经 shell 解析。禁止写入凭据，敏感环境变量由运行环境提供。

```json
{
  "steps": [
    {
      "name": "backend-test",
      "command": ["./mvnw", "test"],
      "cwd": ".",
      "timeout_seconds": 1800,
      "env": {"MAVEN_OPTS": "-Xmx2g"},
      "allow_failure": false
    },
    {
      "name": "frontend-check",
      "command": ["npm", "run", "check"],
      "cwd": "web"
    }
  ]
}
```

运行：

```bash
python3 <skill-root>/scripts/run_delivery_plan.py \
  --plan /tmp/delivery-plan.json \
  --repo <repo> \
  --log-dir /tmp/delivery-logs-<unique> \
  --evidence-out /tmp/delivery-evidence-<unique>.json
```

`--log-dir` 和 `--evidence-out` 必须在仓库外且事先不存在。步骤默认超时 1800 秒；首个非允许失败的步骤失败后立即停止。
