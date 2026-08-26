# Antigravity CLI 调用与交接模板

## 调用约束

- 固定使用 `/home/rsp/.local/bin/antigravity`；调用前先检查版本和认证状态，不猜测远程主机、凭据或替代安装位置。
- 方案审核使用 `--mode plan --output-format json`。
- 飞书技术方案归档、生产模块补充、测试和已授权交付使用 `--mode accept-edits --output-format json`。
- 所有 Antigravity 调用都允许加入 `--dangerously-skip-permissions`，包括 Plan 审核、飞书归档、生产模块补充、CR 修改、测试和交付命令。该参数只跳过 Antigravity 自身的权限确认，不改变 `$delivery-pipeline` 的阶段授权、允许文件、外部操作范围和停止条件，也不自动授权额外 Git、飞书、文件、部署或环境操作。共享工作区内所有调用必须串行；上一次调用的状态与 diff 未核对完，不得开始下一次。
- 每次调用前记录当前分支、HEAD、`git status`、允许修改文件和预期命令；调用后记录实际模型、conversation ID、退出状态、结构化结果、`git status` 和限定范围 diff。
- 修改意见通过 `--conversation <conversation_id>` 继续原 conversation。方案审核复用方案 conversation；每个生产模块创建一个独立 conversation，其实现、CR 修改和测试修改均在该 conversation 内连续进行。

## 模型选择与回退

方案审核和生产模块补充依次使用：

1. `gemini-3.7-flash-high`
2. `gemini-3.6-flash-high`
3. `claude-opus-4-6-thinking`

飞书技术方案归档、测试和已授权交付执行依次使用：

1. `gemini-3.7-flash-medium`
2. `gemini-3.6-flash-medium`
3. `claude-opus-4-6-thinking`

只在模型不可用、调用超时或 CLI 调用失败时切换到下一模型。审核不通过、CR 不通过、测试失败或命令执行返回业务失败时，不得通过切换模型绕过问题；应在同一 conversation 中反馈并按对应阶段处理。所有候选模型均不可用时停止并报告调用证据。

## 基础命令形态

方案审核：

```text
/home/rsp/.local/bin/antigravity --model <review-model> --mode plan --output-format json [--dangerously-skip-permissions] --print='<方案审核交接>'
```

方案复审：

```text
/home/rsp/.local/bin/antigravity --conversation <conversation-id> --model <same-model> --mode plan --output-format json [--dangerously-skip-permissions] --print='<裁决与修订交接>'
```

飞书归档、模块补充、测试或已授权交付：

```text
/home/rsp/.local/bin/antigravity --model <execution-model> --mode accept-edits --output-format json [--dangerously-skip-permissions] --print='<限定范围交接>'
```

具体调用可以按任务设置受控超时，但不得用未验证参数改变权限边界。命令中的交接正文应通过安全参数传递，避免 shell 展开用户内容。

## 飞书技术方案归档交接

使用独立 conversation，并完整提供最终方案原文，不得只提供本地路径、摘要或变更说明。交接必须包含：

- 明确要求 Antigravity 实际执行归档，而非只给出操作建议。
- 精确文档标题、用户身份、目标文件夹 URL/token，以及原流水线规定的创建、移动和回查方式。
- 最终方案完整原文及“不删减、不润色、不改写、不重排”的约束。
- 新增网页或链接时，提供登记文档、五列字段及未知字段填写“待确认”的要求。
- 允许执行的飞书命令范围；禁止访问无关文档、改变权限、删除或覆盖其他云端内容。
- 返回文档 URL、标题、所有者/身份、所在目录、完整回读正文、链接新增行和每个命令退出结果。

Codex 必须把回读正文与交付原文逐项核对。缺失、顺序变化、格式转换改变内容、目录或身份错误、应登记链接缺失时，在同一 conversation 中给出差异并要求修正；一致前不得接受归档成功。

## 方案审核交接

交接必须包含：

- 角色：仅审核，不修改工作区。
- 完整技术方案及其版本标识。
- 仓库技术栈、已有架构与适用规范。
- 要求逐项检查架构、模块边界、数据流、接口和类设计、UML、错误路径、安全、可测试性、部署与回滚。
- 输出要求：意见编号、严重级别、依据、具体建议、是否阻塞；不得直接执行代码、Git 或部署操作。

Codex 回传复审时，对每条意见附裁决、理由、方案修改位置及修订后的完整相关内容。

## 单模块实现与 CR 交接

首次交接必须包含：

- 模块名称、职责、输入输出、稳定契约和依赖方向。
- 已由 Codex 完成的接口、核心类型、装配和不可改变的架构决策。
- 唯一允许修改的文件清单，以及明确禁止触碰的文件和操作。
- 验收标准、编码规范、异常与安全要求。
- 要求只补充本模块，不创建 commit、不 push、不部署、不处理下一模块。

CR 修改交接包含缺陷编号、文件与位置、预期行为和允许范围，明确要求保留已通过部分。三轮计数以 Antigravity 返回一次修改结果为一轮。

## 测试交接

说明对应生产模块、必须覆盖的正常/边界/异常场景、可替换的外部依赖和允许的测试文件。要求直接调用生产流程模块，不复制生产算法或编排。测试失败时附上执行命令、退出码和关键错误；若建议修改生产文件，Antigravity 必须先停止并报告，由 Codex 将模块退回生产 CR。

## 已授权交付交接

只传递代码查看阶段已展示并获得用户确认的后续计划和精确命令，同时包含分支、HEAD、upstream、远端状态、允许变更、验证结果及停止条件。确认后各阶段自动执行，不再请求 Commit、Push、部署、生产部署或合并 `main` 确认。调用可以直接加入 `--dangerously-skip-permissions`，但加入前后允许命令和操作范围必须完全相同。Antigravity 不得自行选择未列明的 merge/rebase、扩大暂存范围、改变提交信息、force push、猜测部署环境或绕过停止条件。执行后返回命令、退出码、关键输出和状态；任一前置状态变化立即停止，生产代码变化时返回代码查看门禁。
