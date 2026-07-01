#!/usr/bin/env python3
"""初始化新项目 - 创建项目卡片并注册到项目看板，含角色分析.

Usage:
    ./init_project.py
    ./init_project.py --name "用户中心重构" --priority P1 --desc "重构用户注册/登录模块"
    ./init_project.py -n "..." -p P1 -d "..." --type fullstack --roles "前端开发,后端开发" --testers "集成测试" --mode parallel
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECTS_FILE = Path.home() / ".codex" / "projects" / "projects.json"

PROJECT_TYPES = {
    "single": {
        "label": "单应用",
        "desc": "单一后端/单一前端，一个开发即可覆盖",
        "suggested_roles": [("产需", "pm", ""), ("开发", "dev", ""), ("测试", "qa", "")],
    },
    "fullstack": {
        "label": "全栈",
        "desc": "前后端同项目，需要前端开发+后端开发分工",
        "suggested_roles": [
            ("产需", "pm", ""),
            ("前端开发", "dev", "前端"),
            ("后端开发", "dev", "后端"),
            ("集成测试", "qa", "集成"),
        ],
    },
    "multi-service": {
        "label": "多服务",
        "desc": "多个后端服务(微服务)在同一个项目中并行开发",
        "suggested_roles": [("产需", "pm", "")],
        "multi_dev": True,
    },
    "multi-platform": {
        "label": "多端",
        "desc": "Web + Mobile + Admin 等多端同时开发",
        "suggested_roles": [("产需", "pm", "")],
        "multi_dev": True,
    },
}

WORK_MODES = {
    "parallel": "所有角色同时启动，互不等待",
    "sequential": "角色之间有依赖关系，逐个启动",
    "mixed": "部分角色并行、部分串行",
}


def load_projects():
    if PROJECTS_FILE.exists():
        return json.loads(PROJECTS_FILE.read_text())
    return []


def save_projects(projects):
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(projects, ensure_ascii=False, indent=2))


def build_default_roles(project_type, dev_labels=None, qa_labels=None):
    """根据项目类型构建默认角色列表.
    
    如果显式传入了 dev_labels/qa_labels, 则完全替换 suggested_roles 中的对应角色；
    否则使用 suggested_roles 的默认配置。
    """
    type_info = PROJECT_TYPES.get(project_type, PROJECT_TYPES["single"])
    use_explicit_dev = dev_labels is not None
    use_explicit_qa = qa_labels is not None
    roles = []
    has_dev = False
    has_qa = False
    for label, rtype, specialty in type_info["suggested_roles"]:
        if rtype == "dev":
            has_dev = True
            if use_explicit_dev:
                continue  # 显式传入时跳过 suggested dev
            if type_info.get("multi_dev"):
                continue
        if rtype == "qa":
            has_qa = True
            if use_explicit_qa:
                continue  # 显式传入时跳过 suggested qa
            if type_info.get("multi_dev"):
                continue
        roles.append({"label": label, "type": rtype, "status": "pending", "note": specialty})
    if use_explicit_dev:
        for label in dev_labels:
            parts = label.split("/", 1)
            lbl = parts[0].strip()
            note = parts[1].strip() if len(parts) > 1 else ""
            roles.append({"label": lbl, "type": "dev", "status": "pending", "note": note})
    elif not has_dev:
        roles.append({"label": "开发", "type": "dev", "status": "pending", "note": ""})
    if use_explicit_qa:
        for label in qa_labels:
            parts = label.split("/", 1)
            lbl = parts[0].strip()
            note = parts[1].strip() if len(parts) > 1 else ""
            roles.append({"label": lbl, "type": "qa", "status": "pending", "note": note})
    elif not has_qa:
        roles.append({"label": "测试", "type": "qa", "status": "pending", "note": ""})
    if not any(r["type"] == "pm" for r in roles):
        roles.insert(0, {"label": "产需", "type": "pm", "status": "pending", "note": ""})
    return roles


def parse_role_args(role_strs):
    """解析 --roles '前端开发/React,后端开发/Go' 等."""
    result = []
    for s in role_strs:
        for item in s.split(","):
            item = item.strip()
            if item:
                result.append(item)
    return result


def init_project(name, priority, description, in_scope=None, out_scope=None, deadline="",
                 project_type="single", roles=None, work_mode="parallel"):
    projects = load_projects()
    project = {
        "id": f"PROJ-{len(projects) + 1:04d}",
        "name": name,
        "priority": priority.upper(),
        "status": "pending",
        "description": description,
        "in_scope": in_scope or [],
        "out_scope": out_scope or [],
        "deadline": deadline or "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "project_type": project_type,
        "work_mode": work_mode,
        "roles": roles,
        "dependencies": [],
        "logs": [],
    }
    projects.append(project)
    save_projects(projects)

    role_summary = ", ".join(f'{r["label"]}[{r["type"]}]' for r in project["roles"])
    print(f"[OK] 项目创建成功: {project['id']} - {project['name']}")
    print(f"     优先级: {project['priority']} | 类型: {project_type} | 模式: {work_mode}")
    print(f"     角色: {role_summary}")
    print(f"     创建时间: {project['created_at']}")
    return project


def _prompt_int(prompt, lo, hi):
    retries = 0
    while retries < 5:
        try:
            val = int(input(f"{prompt} ({lo}-{hi}): ").strip())
            if lo <= val <= hi:
                return val
            print(f"  请输入 {lo}-{hi} 之间的数字")
        except (ValueError, EOFError):
            retries += 1
            if retries >= 5:
                print(f"[ERROR] 无法获取输入，使用默认值 {lo}")
                return lo
            print(f"  请输入 {lo}-{hi} 之间的数字")
    return lo


def _prompt_choice(prompt, lo, hi):
    retries = 0
    while retries < 5:
        try:
            val = int(input(f"{prompt}: ").strip())
            if lo <= val <= hi:
                return val
        except (ValueError, EOFError):
            retries += 1
            if retries >= 5:
                print(f"[ERROR] 无法获取输入，使用默认值 {lo}")
                return lo
        print(f"  请输入 {lo}-{hi} 之间的数字")
    return lo


def interactive_role_analysis():
    """交互式角色分析."""
    print()
    print("=" * 50)
    print("  [角色分析] 请分析项目结构，确定需要的角色")
    print("=" * 50)

    type_keys = list(PROJECT_TYPES.keys())
    labels_map = {v["label"]: k for k, v in PROJECT_TYPES.items()}
    print("\n项目类型:")
    for i, k in enumerate(type_keys, 1):
        info = PROJECT_TYPES[k]
        print(f"  {i}. {info['label']} — {info['desc']}")
    type_choice = _prompt_choice(f"请选择 (1-{len(type_keys)})", 1, len(type_keys))
    project_type = type_keys[type_choice - 1]
    type_info = PROJECT_TYPES[project_type]

    if type_info.get("multi_dev"):
        print("\n项目涉及多个开发角色，请配置:")

    dev_count = _prompt_int("\n开发角色数量", 1, 5)
    defaults_map = {
        "fullstack": ["前端开发", "后端开发", "API开发", "中间件开发", "DevOps"],
        "multi-service": [
            "服务A开发",
            "服务B开发",
            "服务C开发",
            "服务D开发",
            "服务E开发",
        ],
        "multi-platform": [
            "Web开发",
            "Mobile开发",
            "API开发",
            "Admin开发",
            "桌面端开发",
        ],
    }
    defaults = defaults_map.get(project_type, [f"开发{i+1}" for i in range(5)])
    dev_labels = []
    for i in range(dev_count):
        dflt = defaults[i] if i < len(defaults) else f"开发{i+1}"
        label = input(f"  角色{i+1} 标签 (如: {dflt}, 留空='{dflt}'): ").strip()
        if not label:
            label = dflt
        note = input(f"  角色{i+1} 专注领域 (可选, 如: React/Go): ").strip()
        dev_labels.append(f"{label}/{note}" if note else label)

    qa_count = _prompt_int("\n测试角色数量", 0, 3)
    qa_labels = []
    for i in range(qa_count):
        dflt = "功能测试" if i == 0 else f"测试{i+1}"
        label = input(f"  角色{i+1} 标签 (如: {dflt}, 留空='{dflt}'): ").strip()
        if not label:
            label = dflt
        note = input(f"  角色{i+1} 专注领域 (可选, 如: E2E/性能): ").strip()
        qa_labels.append(f"{label}/{note}" if note else label)

    print("\n工作模式:")
    mode_keys = list(WORK_MODES.keys())
    for i, k in enumerate(mode_keys, 1):
        print(f"  {i}. {k} — {WORK_MODES[k]}")
    mode_choice = _prompt_choice(f"请选择 (1-{len(mode_keys)})", 1, len(mode_keys))
    work_mode = mode_keys[mode_choice - 1]

    roles = build_default_roles(project_type, dev_labels=dev_labels, qa_labels=qa_labels)

    print("\n" + "=" * 50)
    print("  角色清单确认:")
    for i, r in enumerate(roles, 1):
        note_str = f" ({r['note']})" if r.get("note") else ""
        print(f"    {i}. {r['label']} [{r['type']}]{note_str}")
    confirm = input("\n确认以上角色配置？(Y/n): ").strip().lower()
    if confirm == "n":
        print("[ABORTED] 角色分析已取消，可重新运行")
        sys.exit(0)

    return project_type, roles, work_mode


def main():
    parser = argparse.ArgumentParser(description="初始化新项目")
    parser.add_argument("--name", "-n", help="项目名称")
    parser.add_argument("--priority", "-p", choices=["P0", "P1", "P2", "P3"], help="优先级")
    parser.add_argument("--desc", "-d", help="项目描述")
    parser.add_argument("--deadline", help="期望交付日期")
    parser.add_argument("--type", "-t", choices=list(PROJECT_TYPES.keys()), help="项目类型")
    parser.add_argument("--roles", action="append", help="开发角色列表 (如: '前端开发/React,后端开发/Go')")
    parser.add_argument("--testers", action="append", help="测试角色列表 (如: '功能测试/E2E,性能测试')")
    parser.add_argument("--mode", choices=list(WORK_MODES.keys()), help="工作模式")
    args = parser.parse_args()

    has_role_flags = args.type or args.roles or args.testers or args.mode
    has_basic_info = args.name or args.priority or args.desc

    # 有 CLI 标志时走非交互模式，缺失用默认值
    if has_role_flags or has_basic_info:
        name = args.name or ""
        priority = args.priority or "P3"
        description = args.desc or ""
        deadline = args.deadline or ""
        project_type = args.type or "single"
        dev_labels = parse_role_args(args.roles) if args.roles else None
        qa_labels = parse_role_args(args.testers) if args.testers else None
        work_mode = args.mode or "parallel"
        roles = build_default_roles(project_type, dev_labels=dev_labels, qa_labels=qa_labels)
    else:
        # 无参数时全交互
        name = input("项目名称: ").strip()
        priority = input("优先级 (P0/P1/P2/P3): ").strip().upper()
        description = input("项目描述: ").strip()
        deadline = input("期望交付日期 (留空跳过): ").strip()
        project_type, roles, work_mode = interactive_role_analysis()

    init_project(name, priority, description, deadline=deadline,
                 project_type=project_type, roles=roles, work_mode=work_mode)


if __name__ == "__main__":
    main()
