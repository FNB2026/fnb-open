# FNB Open

<p align="center">
  <b>English</b> | <a href="#中文">中文</a>
</p>

---

FNB is a **local-first personal memory operating system and AI social paradigm platform**.

It turns flows of life, digital assets, conversations, events, and relationships into user-owned, auditable, explainable, permissioned domain objects.

This repository contains the public manifesto, domain model, protocol drafts, synthetic examples, and community governance documents.

**The official product implementation remains private** until the security, privacy, and beta readiness gates are complete.

---

## What is FNB?

FNB is built on the belief that:

- **Users own their data** — not platforms, not AI models
- **Every AI inference should have evidence** — no black-box relationship decisions
- **Every relationship should be user-governed** — not algorithm-defined
- **Every memory should have a source** — traceable, verifiable, auditable
- **Every correction should be preserved** — users can confirm, reject, or rewrite
- **Local-first first, cloud optional** — your data lives on your device

## What FNB is Not

- Not a traditional social feed or content platform
- Not a generic notes or journaling app
- Not a CRM
- Not a blockchain speculation project
- Not a data-harvesting AI assistant
- Not the "next WeChat" or "next Notion"

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Flow** | Event stream / runtime — the continuous flow of life |
| **Node** | Actor, entity, message, or compute unit — stable objects in the flow |
| **Block** | Aggregated state, knowledge block, or asset block — structured from flow |
| **Memory** | First-class domain object with source, score, lifecycle, and visibility |
| **Asset** | File, image, audio, or variant — unified media infrastructure |
| **Event** | Append-only operation log — the source of audit truth |
| **Relationship** | Evidence-backed, user-governed connections between actors |
| **Permission** | Granular access control matrix with ownership and policy |
| **Audit** | Immutable trail of data access and mutation |
| **Correction** | User-controlled PATCH with full undo/redact support |
| **AIInference** | Structured record of every model judgment |
| **Explanation** | Human-readable rationale for every AI decision |

## Current Public Boundary

### Public Now
- Manifesto
- Domain model documentation
- Protocol drafts
- JSON Schema v0.1 drafts
- End-to-end synthetic protocol examples
- Executable v0.1 conformance fixtures and CI validation
- Synthetic examples
- Community governance

### Planned Public Later (Phase 2+)
- Additional JSON Schema definitions and conformance rules
- OpenAPI preview
- TypeScript SDK
- Go SDK
- Mock server
- Plugin starter

### Not Public Before Beta Readiness
- Official backend implementation
- Official mobile app implementation
- Official web console implementation
- Authentication internals
- Worker credential internals
- Production storage and ledger logic
- Real user data pipelines
- Real deployment scripts

### Never Public
- Real user data
- Real chat logs, photos, audio recordings
- Real relationship graphs
- Private keys or production secrets
- Private infrastructure topology

## Roadmap

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Public manifesto and domain model | 🟢 Now |
| Phase 2 | Protocol schemas and SDK preview | 🟡 In progress |
| Phase 3 | Selective engineering modules | 📋 Future |
| Phase 4 | Full source-code release evaluation after beta | 📋 Future |

## Contact / 联系我们

- **Discussions / 社区讨论**: [GitHub Discussions](https://github.com/FNB2026/fnb-open/discussions) — philosophical discussions, protocol proposals, Q&A
- **Issues / 问题反馈**: [GitHub Issues](https://github.com/FNB2026/fnb-open/issues) — bug reports, documentation issues
- **Security / 安全报告**: See [SECURITY.md](./SECURITY.md) — report vulnerabilities privately
- **Maintainer / 维护者**: [FNB2026 on GitHub](https://github.com/FNB2026)

## License / 许可证

- **Documents**: CC BY-NC-SA 4.0
- **Protocol and SDK repositories**: Apache 2.0

This repository is a public documentation and protocol-draft repository. Its
documents use a non-commercial Creative Commons license; future code repositories
or modules will carry their own OSI-compatible or copyleft license as stated.

---

**FNB is not finished. It is being built in the open, one principled decision at a time.**

---

<h2 id="中文">中文</h2>

<p align="center">
  <a href="#fnb-open">English</a> | <b>中文</b>
</p>

# FNB Open

FNB 是一个**本地优先的个人记忆操作系统与 AI 社交新范式平台**。

它将人生流、数字资产、对话、事件和关系，转化为用户拥有的、可审计、可解释、有权限控制的领域对象。

本仓库包含公开发布的宣言、领域模型、协议草案、合成样本和社区治理文档。

**官方产品实现保持私有**，直到安全、隐私和 Beta 就绪门禁全部通过。

---

## FNB 是什么

FNB 相信：

- **用户拥有自己的数据** — 而非平台或 AI 模型
- **每一次 AI 推断都应有证据** — 不做黑箱式的关系决策
- **每一段关系都应由用户治理** — 而非由算法定义
- **每一份记忆都应可追溯来源** — 可追踪、可验证、可审计
- **每一次纠正都应被保留** — 用户可以确认、拒绝或重写
- **本地优先，云端可选** — 你的数据存在于你的设备上

## FNB 不是

- 不是传统信息流或内容平台
- 不是通用笔记或日记应用
- 不是 CRM
- 不是区块链投机项目
- 不是数据收割型 AI 助手
- 不是"下一个微信"或"下一个 Notion"

## 核心概念

| 概念 | 说明 |
|------|------|
| **Flow（流）** | 事件流 / 运行时 — 持续流动的人生 |
| **Node（节点）** | 角色、实体、消息或计算单元 — 流中的稳定对象 |
| **Block（块）** | 聚合状态、知识块或资产块 — 从流中结构化产出 |
| **Memory（记忆）** | 具有来源、评分、生命周期和可见性的一等对象 |
| **Asset（资产）** | 文件、图片、音频或变体 — 统一媒体基础设施 |
| **Event（事件）** | 仅追加的操作日志 — 审计真相的来源 |
| **Relationship（关系）** | 有证据支撑、用户治理的角色间连接 |
| **Permission（权限）** | 具有所有权和策略的细粒度访问控制矩阵 |
| **Audit（审计）** | 不可篡改的数据访问和变更记录 |
| **Correction（纠正）** | 用户控制的 PATCH 操作，支持完全撤销/编辑 |
| **AIInference（AI 推断）** | 每一次模型判断的结构化记录 |
| **Explanation（解释）** | 每一次 AI 决策的人类可读理据 |

## 当前公开边界

### 现已公开
- 宣言
- 领域模型文档
- 协议草案
- JSON Schema v0.1 草案
- 端到端合成协议示例
- 合成样本
- 社区治理

### 计划后续公开（Phase 2+）
- 更多 JSON Schema 定义与一致性规则
- OpenAPI 预览
- TypeScript SDK
- Go SDK
- Mock 服务器
- 插件启动模板

### Beta 就绪前不公开
- 官方后端实现
- 官方移动端应用
- 官方 Web 控制台
- 认证内部实现
- Worker 凭据内部实现
- 生产存储和账本逻辑
- 真实用户数据流水线
- 真实部署脚本

### 永不公开
- 真实用户数据
- 真实聊天记录、照片、录音
- 真实关系图谱
- 私钥或生产密钥
- 私有基础设施拓扑

## 路线图

| 阶段 | 目标 | 状态 |
|------|------|------|
| Phase 1 | 公开发布宣言和领域模型 | 🟢 当前 |
| Phase 2 | 协议规范和 SDK 预览 | 🟡 进行中 |
| Phase 3 | 选择性开放工程模块 | 📋 未来 |
| Phase 4 | Beta 后评估完整源码开放 | 📋 未来 |

## 联系我们

- **社区讨论**: [GitHub Discussions](https://github.com/FNB2026/fnb-open/discussions) — 哲学讨论、协议提案、问答
- **问题反馈**: [GitHub Issues](https://github.com/FNB2026/fnb-open/issues) — Bug 报告、文档问题
- **安全报告**: 参见 [SECURITY.md](./SECURITY.md) — 私密提交漏洞
- **维护者**: [FNB2026 on GitHub](https://github.com/FNB2026)

## 许可证

- **文档**: CC BY-NC-SA 4.0
- **协议和 SDK 仓库**: Apache 2.0

本仓库是公开文档与协议草案仓库。文档使用带非商业限制的 Creative Commons
许可证；未来代码仓库或工程模块会在各自仓库/目录中声明 OSI 兼容或 copyleft
许可证。

---

**FNB 尚未完成。它正在开放构建，一个有原则的决策接一个决策。**
