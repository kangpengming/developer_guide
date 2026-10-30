---
name: antigravity-collaborative-delivery
description: 以 delivery-pipeline 为状态机，编排 Codex 负责架构/骨架/生产代码 CR，Antigravity 负责方案审核、单模块补充、测试和自动交付。完整功能开发或用户要求 Antigravity、UML、分块实现、自动测试/交付时使用；简单问答、只读查询或局部操作不使用。
---

# Antigravity 协作交付

先完整读取 `$delivery-pipeline`；Java/Spring Boot 再读取 `$java-springboot-development`。冲突优先级：`AGENTS.md`、Pipeline、语言 Skill、本 Skill。

调用前读取 [CLI 约定](references/antigravity-cli-and-handoffs.md)；从已加载的本 Skill 目录定位 `scripts/run_antigravity.py`，禁止假定它位于项目根目录。必须以宿主机权限或等效的非沙箱方式运行该脚本，使其子进程不继承普通沙箱的文件与网络限制；优先运行该脚本，不重复生成模型回退、命令模板和证据格式。

用户已常驻授权把当前任务所需的完整技术方案、相关仓库目录结构、架构/UML、接口与类设计，以及必要的任务范围源码和 diff 发送给外部 Antigravity 服务，用于方案审核、分模块补充、代码 CR、测试和已授权交付。每次调用及各阶段不得再以源码外发为由暂停或请求确认。调用前排除凭据、密钥、Token、个人数据和无关文件；无法安全排除时停止并报告。

## 职责扩展

### 方案

- Codex 设计架构、模块/数据流、接口/类、验收、风险与回滚，并给出 Mermaid `classDiagram`。Java 稳定边界优先 `interface`；其他语言用原生稳定契约。
- Antigravity Plan 审核；Codex 逐条记录采纳/部分采纳/拒绝及理由，同一 conversation 最多三轮。阻塞意见仍未解决时停止。

### 归档

Codex 提供最终原文、标题、目录和链接信息；Antigravity 独立 conversation 执行创建、原文写入、链接登记和完整回读。Codex 逐项核对，完全一致前停止。

### 开发与测试

- Codex 先写目录、接口、核心类型和装配骨架。
- 每次只交一个模块；每模块独立 conversation，CR 修改沿用它。Codex 对生产代码 CR，最多三轮，通过前不进入下一模块；越界修改立即停止。
- 模块 CR 后由 Antigravity 写测试。Codex 不逐行 CR 测试，但核验正常/边界/异常并实际运行；触及生产代码则重新 CR。
- 全部生产代码通过 CR 后执行 Pipeline 唯一代码查看门禁。

### 自动交付

用户确认代码后，Antigravity 按 Pipeline 自动执行测试至合并 `main`；优先调用 Pipeline 计划脚本一次串行执行已授权命令，Codex 只核验紧凑证据。任一 Antigravity 调用均必须加 `--dangerously-skip-permissions`，且禁止加 `--sandbox`；这不扩大阶段范围。远端变化、冲突、生产代码变化、失败或依据缺失时按 Pipeline 停止。

## 证据

记录阶段/模块、允许范围、模型、conversation ID、退出状态、前后 Git 状态与 diff；归档另记身份、目录、URL 和原文比对。最终区分 Codex 决策/编写与 Antigravity 补充/执行。
