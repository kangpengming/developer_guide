---
name: antigravity-collaborative-delivery
description: 以 delivery-pipeline 为唯一主状态机，编排 Codex 与 Antigravity CLI 完成架构设计、方案审核、逐模块生产代码补充与 CR、模块测试及已授权交付。完整功能开发默认使用；用户明确要求 Antigravity 协作、架构设计、UML、分块开发或让 Antigravity 执行测试、Git、部署和验收时使用。简单问答、只读查询、纯说明或无需开发交付的局部任务不触发。
---

# Antigravity 协作交付

本 Skill 是 `$delivery-pipeline` 的扩展编排层，不替代、不复制其状态机与门禁。Codex 负责最终架构决策、生产代码骨架和 CR；Antigravity 负责方案建议、单模块补充、测试以及获得授权后的交付命令。

## 启动与优先级

1. 完整读取并执行 `$delivery-pipeline`，以其当前阶段作为唯一主状态；不得跳过、重排或弱化任何进入条件、成功证据、停止条件和确认门禁。
2. Java 或 Spring Boot 项目同时完整读取 `$java-springboot-development`。其他语言读取仓库适用规范，并使用该语言的 protocol、trait、抽象类型、接口或稳定函数契约表达边界。
3. 冲突时依次遵守：适用范围内的 `AGENTS.md` 安全门禁、`delivery-pipeline`、语言开发 Skill、本 Skill。
4. 原流水线可以独立使用。完整功能开发默认加载本 Skill；简单问答、只读分析和不涉及完整开发交付的局部操作继续使用原有适用规则。
5. 调用 Antigravity 前完整读取 [CLI 调用与交接模板](references/antigravity-cli-and-handoffs.md)。

## 阶段扩展

以下内容只扩展原阶段；未写出的规则全部继承 `$delivery-pipeline`。

### 技术方案

- Codex 以架构师身份给出目标、范围、非目标、总体架构、模块边界、依赖方向、数据流、接口清单、类与接口设计、验收标准、风险、回滚和替代方案。
- 方案必须包含 Mermaid `classDiagram`，展示关键接口、实现类、依赖、继承与组合关系。Java 在稳定边界和可替换依赖处优先定义 `interface`，但不得为没有替换、隔离或契约价值的实现制造空接口；其他语言采用原生稳定契约。
- Codex 完成初稿后，让 Antigravity 以 Plan 模式审核。Codex 对每条意见记录“采纳”“部分采纳”或“拒绝”、理由和对应修改；修改后沿用同一审核 conversation 复审。
- 审核最多三轮。三轮后仍存在会阻断正确性、安全性、可维护性或可交付性的意见时，按原技术方案阶段停止并报告用户；非阻塞分歧由 Codex 作最终架构决定并留痕。

### 技术方案归档

- 归档对象是 Antigravity 审核结束且由 Codex 最终确认的完整方案。
- Codex 向 Antigravity 提供最终方案原文、精确文档标题、目标文件夹、链接登记要求和允许执行的飞书操作；Antigravity 使用独立 conversation 实际完成飞书文档创建、原文写入、必要的链接表格登记和写后回查。
- Antigravity 必须严格执行原流水线及 `AGENTS.md` 的飞书原文写入、链接登记和回查要求；审核意见记录不得替代或删减最终方案正文。不得摘要、改写、重排、猜测未知字段或把文档留在错误身份或目录下。
- Codex 核对 Antigravity 返回的文档 URL、标题、所在目录、完整回读正文和链接登记行，并与最终方案逐项比对。证据不完整或内容不一致时，交回同一归档 conversation 修正；完全一致前不得进入代码开发。

### 代码开发

- Codex 先实现与已确认方案一致的目录结构、模块边界、接口、核心类型、类关系和必要装配，形成可供逐块实现的架构骨架。
- 按方案中的模块顺序，每次只把一个模块及其允许文件交给 Antigravity；每个模块新建独立 conversation，针对该模块的 CR 意见继续使用同一 conversation。
- Antigravity 补充一块生产代码后，Codex 检查职责边界、契约、依赖方向、异常与安全、代码规范、越界改动和与方案的一致性。未通过时给出具体意见并要求在同一 conversation 修改，最多三轮。
- 当前模块 CR 通过前不得交付下一模块。三轮仍未通过时停止并报告差异与恢复条件；Antigravity 修改允许范围外文件时立即停止，保留 diff 作为证据，不继续调用。

### 单元测试

- 每个生产模块通过 CR 后，立即让 Antigravity 为该模块编写测试；测试必须复用生产模块，不得重写业务流程。
- Codex 不做测试代码逐行 CR，但必须核验正常、边界、异常场景是否覆盖，并实际运行相关测试；完成全部模块后仍执行语言 Skill 和原流水线要求的完整检查。
- 仅测试代码有问题时，在该模块 conversation 中交回 Antigravity 修改。若修复触及生产代码，该模块必须重新进入生产代码 CR，CR 通过后重新运行测试。

### Commit 至合并 main

- 阶段定义、顺序、证据、停止条件和确认门禁完全继承 `$delivery-pipeline`，本 Skill 不提供替代规则。
- Codex 收集证据、展示计划并取得原流水线要求的确认；Antigravity 只执行已经取得授权且范围未变化的 Git、部署、功能验证和合并命令。
- Antigravity 可以按参考中的受控规则使用 `--dangerously-skip-permissions` 执行已授权命令；该参数只解决 headless 权限交互，不构成新增授权，也不得扩大已确认范围。
- Commit 后紧接 Push 时沿用原流水线的一次确认规则；部署、生产部署和合并 `main` 仍分别取得原规则要求的独立确认。
- 远端变化、冲突、允许范围变化、验证失败或授权失效时立即停止，不得让 Antigravity自行扩大操作。

## 完成证据

除原流水线证据外，持续记录每次 Antigravity 调用的阶段、模块或外部操作范围、允许文件、模型、conversation ID、退出状态、前后工作区状态和 diff；飞书归档还要记录身份、目标目录、文档 URL、回读与逐项比对结果。记录方案意见裁决、每模块 CR 轮次、测试场景与结果。最终交接中说明哪些内容由 Codex 决策或编写、哪些由 Antigravity 补充或执行，以及是否存在未采纳意见。
