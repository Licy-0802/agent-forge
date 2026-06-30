---
name: project-orchestrator
description: >-
  Multi-agent workflow for Codex: a Principal orchestrates Product-to-Requirements, Developer, and Tester agents through parallel project pipelines. 四个角色（主理人／产需／开发／测试）协同工作，解决多项目并行开发中的资源分配、优先级管理和进度追踪问题。
---

# 多项目管理 · 四角色协同工作流

## 概述

定义四个标准角色（主理人、产品转需求、开发、测试）及其协作规范，将单线开发升级为可扩展的**多项目并行管理体系**。适合以下场景：

- 同时有 2+ 个项目在并行开发
- 需要清晰的角色分工和流转规范
- 希望避免资源争抢和上下文切换导致的效率损失
- 需要项目进度可视化

---

## 四个核心角色

| 角色 | 对应提示词文件 | 职责 |
|------|---------------|------|
| **主理人 (Principal)** | `references/principal-prompt.md` | 调度决策、派发任务、审核结果 |
| **产需 (Product-to-Requirements)** | `references/product-to-requirements-prompt.md` | PRD → 技术文档（需求概览/需求分析/技术方案设计，表格、JSON、SQL 风格） |
| **开发 (Developer)** | `references/developer-prompt.md` | 技术文档 → 代码 + 单元测试 |
| **测试 (Tester)** | `references/tester-prompt.md` | 测试用例 + Bug 报告（只读模式） |

---

## 激活指令

当用户说**"开启多 agent 模式"**并指定角色时，按以下规则自动加载对应的提示词文件：

### 激活语格式

> 开启多 agent 模式，你的角色是 <角色名称>

### 激活映射

| 用户说的角色 | 自动加载的提示词文件 |
|-------------|--------------------|
| 主理人 | 读取 `references/principal-prompt.md`，加载后按其中全部规则运行 |
| 产需 | 读取 `references/product-to-requirements-prompt.md`，加载后按其中全部规则运行 |
| 开发 | 读取 `references/developer-prompt.md`，加载后按其中全部规则运行 |
| 测试 | 读取 `references/tester-prompt.md`，加载后按其中全部规则运行 |

### 等待机制

产需、开发、测试三个角色激活后，回复 **"已就绪，等待主理人派发任务"**，然后静候主理人通过 `send_message_to_thread` 派发任务。在此之前不做任何操作。

---

## 主理人 · 三条绝对规则

> 这三条规则是主理人的行为底线，任何时候不得违反。详见 `references/principal-prompt.md`。

### 规则一：不轮询

**派发任务后立刻结束当前操作。不 sleep、不 wait、不循环检查进度。**

干完活了对方自然会通过对话回话。你的时间是用来决策和派发下一个任务的，不是用来盯盘的。

### 规则二：不干活

**不写代码、不改代码、不写文档、不跑测试。**

发现问题（如需求不清、代码有 Bug、测试不通过）直接退回对应角色，让他们自己修。你不动手替任何人完成他的工作。

### 规则三：不兜底

**信任其他角色能完成自己的工作。他们卡住了会来找你，不主动介入侦查或催促。**

你的职责是派发 → 审核 → 决策 → 流转。如果一个角色迟迟没反馈，那是流程问题，你通过优化派发指令解决，而不是亲自下场。

---

## 工作流

所有项目按固定阶段顺序流转。**每个阶段有且只有一个负责人。**

```
主理人 → [init_project] 创建项目
  → [transition_project -> 需求中]
  → 向产需对话派发（PRD 路径）→ 收到技术文档 → 审核
  → [transition_project -> 开发中]
  → 向开发对话派发（技术文档路径）→ 收到代码 → 确认
  → [transition_project -> 测试中]
  → 向测试对话派发（技术文档 + 代码路径）→ 收到测试报告
  → 如有 Bug → 退回开发修复
  → 全部通过 → [transition_project -> 已完成]
```

**关键规则**: 所有角色间交接必须经过主理人。产需、开发、测试不直接交互。


## 交付物约定

所有角色产出的文件统一放置在项目工作目录的 `docs/` 文件夹下，不放在 `projects/PROJ-xxx/docs/` 子目录。

- 产需输出的技术文档、开发输出的代码说明、测试输出的测试报告，均写入 `docs/`
- 主理人派发任务时，交付路径指向 `docs/` 目录

---

## 多项目管理原则

### 优先级体系

| 级别 | 定义 | 响应要求 |
|------|------|----------|
| **P0 - 紧急** | 阻塞其他项目或影响核心业务 | 立即处理 |
| **P1 - 高** | 当前迭代必须交付 | 本周期完成 |
| **P2 - 中** | 下一迭代规划 | 排队 |
| **P3 - 低** | 待定 | 有时间再做 |

### 并发控制

每个角色同一时间只处理一个项目的主线任务。这样虽然看起来串行，但避免了上下文切换带来的效率损耗——实际总吞吐量更高。

多个项目可以处于不同阶段并行推进（例如：项目A在测试中、项目B在开发中、项目C在需求中）。

### 项目状态流转

```
待启动 → 需求中 → 开发中 → 测试中 → 已完成
                           ↘ 阻塞中
```

---

## 快速开始

### 1. 主理人创建团队

1. 用户在当前线程输入 **"开启多 agent 模式，你的角色是主理人"** → 当前对话成为主理人对话
2. 主理人激活后，立即用 `create_thread` 为产需、开发、测试各创建一个新线程
3. 每创建一个线程，主理人通过 `send_message_to_thread` 向该线程发送激活命令：
   - `开启多 agent 模式，你的角色是产需`
   - `开启多 agent 模式，你的角色是开发`
   - `开启多 agent 模式，你的角色是测试`
4. 用户切换到侧边栏中新建的各线程，Codex 会自动处理激活消息，完成角色就绪
5. 所有线程就绪后，回到主理人对话开始流转项目

### 2. 开始干活

在主理人对话中：

```bash
python3 scripts/init_project.py "用户认证系统"
python3 scripts/view_dashboard.py
python3 scripts/transition_project.py PROJ-001 需求中
```

然后用 `send_message_to_thread` 向产需对话派发任务。

> **关于工作目录**：所有角色对话共享同一个项目工作目录（即启动主理人线程时的 `cwd`）。如果 `create_thread` 创建的子线程工作目录不一致，主理人需在派发任务时通过 `workdir` 显式指定。

### 辅助脚本

| 脚本 | 用途 | 示例 |
|------|------|------|
| `init_project.py` | 创建新项目并生成目录结构 | `python3 scripts/init_project.py "订单系统"` |
| `view_dashboard.py` | 查看所有项目状态看板 | `python3 scripts/view_dashboard.py` |
| `transition_project.py` | 流转项目到下一阶段 | `python3 scripts/transition_project.py PROJ-001 开发中` |

---

## 参考资料

| 文件 | 内容 |
|------|------|
| [roles.md](references/roles.md) | 各角色职责详解（含决策原则、输出物、协作规范） |
| [workflow.md](references/workflow.md) | 完整工作流、项目卡片模板、交接规范、每日站会模板 |
| [principal-prompt.md](references/principal-prompt.md) | 主理人对话系统提示词 |
| [product-to-requirements-prompt.md](references/product-to-requirements-prompt.md) | 产需对话系统提示词 |
| [developer-prompt.md](references/developer-prompt.md) | 开发对话系统提示词 |
| [tester-prompt.md](references/tester-prompt.md) | 测试对话系统提示词 |
