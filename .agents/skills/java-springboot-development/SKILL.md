---
name: java-springboot-development
description: 指导 Java、Spring Boot 及 MySQL 关联开发的新增、修改、评审、重构和测试，按《阿里巴巴 Java 开发手册》归纳编程、Lombok、异常日志、安全、数据库、模块化、工程与设计规则，并要求测试复用生产流程模块，覆盖现代分层、DTO/Entity 边界、事务和 Maven/Gradle 验证。用户要求开发或评审 Java/Spring Boot 功能、业务流程模块、Lombok 注解、接口、SQL、表结构、Schema 迁移、持久化代码或 JUnit/Mockito 测试时使用。
---

# Java Spring Boot 开发规范

先读取适用范围内的 `AGENTS.md`、构建文件和邻近实现。以仓库现有架构与风格为优先，只做当前任务的最小改动；既有风格不得覆盖 `AGENTS.md` 的硬性安全和交付门禁。

## 执行流程

1. 确认仓库、分支、工作区状态、Java 版本、Spring Boot 版本、构建系统、MySQL 等关联中间件及已有实现。
2. 根据改动内容读取对应参考：
   - Java 命名、包、可见性、Lombok、异常、日志或依赖：读取 [Java 规范](references/java-guidelines.md)。
   - Spring Boot API、分层、模型、校验、事务或配置：读取 [Spring Boot 规范](references/spring-boot-guidelines.md)。
   - 测试设计、JUnit 5、Mockito 或构建验证：读取 [测试与构建规范](references/testing-and-build.md)。
   - MySQL 表结构、索引、SQL、ORM、事务或 Schema 迁移：读取 [MySQL 规范](references/mysql-guidelines.md)。
   - 鉴权、输入输出、敏感数据、上传、重放或其他安全问题：读取 [安全规范](references/security-guidelines.md)。
   - 错误码、依赖治理、远程调用、架构或设计评审：读取 [工程与设计规范](references/engineering-and-design.md)。
3. 沿用项目结构实现最小必要改动，按业务流程的大步骤建立职责明确的生产模块并组合流程，避免无关重构和格式化。
4. 为行为变更补充正常、边界和异常路径测试；测试直接调用生产流程模块，通过替换外部依赖保持隔离，不在测试目录重写业务流程。
5. 自动选择构建命令并先运行相关测试，再运行完整检查。记录命令、退出状态和关键结果。
6. 汇总修改文件、设计取舍、测试证据和剩余风险。任何测试失败时停止后续提交、推送或部署。

## 构建命令选择

按以下优先级选择，不猜测仓库自定义参数：

1. 存在可执行 `mvnw`：使用 `./mvnw`。
2. 存在可执行 `gradlew`：使用 `./gradlew`。
3. 存在 `pom.xml`：使用 `mvn`。
4. 存在 `build.gradle` 或 `build.gradle.kts`：使用 `gradle`。
5. 无法识别时停止并询问。

Maven 通常运行相关测试、`test`、`verify`；Gradle 通常运行相关测试、`test`、`check`。若仓库文档或现有 CI 定义了更严格命令，采用更严格要求。

## 规则来源与适用顺序

这些参考文件依据阿里巴巴官方 p3c 仓库《Java 开发手册（黄山版）》分类归纳，并结合当前 Java、Spring Boot、JUnit 5 和迁移工具实践改写，不是原文副本。依次遵守适用的 `AGENTS.md` 硬性门禁、仓库明确约定、当前框架的安全实践和本 Skill；手册中的组织专属规则或旧框架规则仅在仓库采用对应机制时应用。
