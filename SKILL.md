---
name: project-orchestrator
description: 定义主理人(Principal)、产品转需求(Product-to-Requirements)、开发(Developer)、测试(Tester)四个角色及其协同工作流，解决多项目并行开发中的资源分配、优先级管理和进度追踪问题。当需要管理多个并行项目、建立标准化开发流程、或多角色协作时使用此 skill。
---

# 多项目管理 - 动态角色协同工作流

## 概述

本 skill 提供一套**可伸缩的多角色协同框架**。核心思路：不再是固定的"一个产需 + 一个开发 + 一个测试"，而是由**主理人在立项时做角色分析**，根据项目结构动态决定需要哪些角色实例。

适用场景：

- 同时有 2+ 个项目在并行开发
- 同一个项目需要前后端分工 / 多服务协作 / 多端并行
- 需要清晰的标准化流转规范
- 希望避免资源争抢和上下文切换导致的效率损失

## 核心概念：角色类型 vs 角色实例

本框架定义了四种**角色类型**，但每种类型可以有多个**角色实例**（实例化）：

| 角色类型 | 类型标识 | 说明 | 典型实例 |
|---------|---------|------|---------|
| 主理人 (Principal) | `principal` | 唯一，不实例化 | 主理人本人 |
| 产需 (PM) | `pm` | 每个项目一个，处理需求 | 产需 |
| 开发 (Developer) | `dev` | 可多个**实例** | 前端开发、后端开发、服务A开发 |
| 测试 (QA) | `qa` | 可多个**实例** | 集成测试、功能测试、性能测试 |

### 关键变化

**之前**: 一个项目 = 1 产需 + 1 开发 + 1 测试，线性流水线
**现在**: 一个项目 = 1 产需 + N 个开发实例 + M 个测试实例，由主理人分析决定

### 主理人角色分析（立项时的关键步骤）

立项时，主理人判断：

1. **项目类型** — 单应用 / 全栈 / 多服务 / 多端
2. **需要几个开发？** 各自负责什么？(如: 前端开发/React, 后端开发/Go)
3. **需要几个测试？** 各自负责什么？(如: 集成测试/E2E, 性能测试)
4. **工作模式** — 并行 / 串行 / 混合（角色间依赖关系）

```
      立项
       │
       ▼
   角色分析 ← 主理人根据项目结构判断
       │
       ▼
   需求阶段 (1个产需)
       │
       ▼
   开发阶段 (N个开发实例，并行/串行)
       │
       ▼
   测试阶段 (M个测试实例)
       │
       ▼
   项目闭环 (主理人确认)
```

## 四个角色类型

### 主理人 (Principal)
项目经理 / 决策者。**唯一不实例化的角色**，由用户（或 Codex 扮演）担任。

- 立项目 + 做角色分析
- 定优先级、排冲突
- 各阶段流转的唯一决策者
- 发现角色不足时，可动态追加角色实例

### 产需 (PM)
每个项目固定一个。将产品构想落地为可执行的需求文档。

### 开发 (Developer)
**可多个实例**。每个实例按需求文档实现功能。实例之间根据工作模式决定并行或串行关系。

### 测试 (QA)
**可多个实例**。每个实例根据需求文档验证质量。

## 工作流

```
主理人 → [立项+角色分析]
       → [指派产需] → 产需 → [需求文档]
       → 主理人 → [审核] → 开发N个 → [代码+自测]
       → 主理人 → [确认所有开发完成]
       → [指派测试] → 测试M个 → [测试报告]
       → 主理人 → [确认闭环]
```

**关键规则**:
- 所有角色间交接必须经过主理人
- 只有全部开发实例完成，项目才能进入测试阶段
- 只有全部测试实例完成，项目才能闭环
- 产需、开发、测试之间不直接交互

## 多项目管理

### 优先级体系
- **P0 - 紧急**: 阻塞其他项目或核心业务
- **P1 - 高**: 当前迭代必须交付
- **P2 - 中**: 下一迭代规划
- **P3 - 低**: 待定

### 项目状态
```
待启动 → 需求中 → 开发中 → 测试中 → 已完成
                             ↘ 阻塞中
```

### 每个角色的状态
```
⏳ pending (待启动) → ▶️ active (进行中) → ✅ done (已完成)
                                               ↘ 🚫 blocked (阻塞中)
```

## 脚本使用

### 创建项目（含角色分析）

```bash
# 交互式（推荐），包含角色分析步骤
scripts/init_project.py

# 命令行快速创建（单应用默认角色）
scripts/init_project.py -n "用户中心" -p P1 -d "重构"

# 命令行指定角色
scripts/init_project.py -n "商城" -p P1 -d "..." --type fullstack \
  --roles "前端开发/React,后端开发/Go" --testers "集成测试/E2E" --mode parallel
```

### 角色级操作

```bash
# 启动角色（标记为进行中）
scripts/transition_project.py PROJ-0001 --role 前端开发 --start

# 标记角色完成
scripts/transition_project.py PROJ-0001 --role 前端开发 --done

# 角色阻塞/恢复
scripts/transition_project.py PROJ-0001 --role 前端开发 --block --note "等待API"
scripts/transition_project.py PROJ-0001 --role 前端开发 --resume
```

### 项目级操作

```bash
# 推进到下一阶段（自动检查角色是否全部完成）
scripts/transition_project.py PROJ-0001 --advance

# 强制推进（忽略未完成角色）
scripts/transition_project.py PROJ-0001 --advance --force

# 直接设置阶段
scripts/transition_project.py PROJ-0001 --to requirements

# 阻塞/恢复项目
scripts/transition_project.py PROJ-0001 --block --note "等待第三方依赖"
scripts/transition_project.py PROJ-0001 --resume
```

### 查看看板

```bash
# 总览
scripts/view_dashboard.py

# 指定项目详情
scripts/view_dashboard.py --project PROJ-0001

# 完整角色详情
scripts/view_dashboard.py --detail
```

## 参考资料

- `references/roles.md`: 各角色类型详解 + 角色分析指南
- `references/workflow.md`: 完整工作流、角色实例化流程、项目卡片模板
