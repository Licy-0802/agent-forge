#!/usr/bin/env python3
"""查看项目看板 - 展示所有项目及其角色级详情.

Usage:
    ./view_dashboard.py               # 查看所有项目
    ./view_dashboard.py --status dev  # 按阶段筛选
    ./view_dashboard.py --priority P1 # 按优先级筛选
    ./view_dashboard.py --detail      # 查看角色详情
"""

import argparse
import json
from pathlib import Path

PROJECTS_FILE = Path.home() / ".codex" / "projects" / "projects.json"

STATUS_LABELS = {
    "pending": "待启动",
    "requirements": "需求中",
    "development": "开发中",
    "testing": "测试中",
    "completed": "已完成",
    "blocked": "阻塞中",
}

STATUS_ORDER = ["pending", "requirements", "development", "testing", "completed", "blocked"]

STATUS_ICONS = {
    "pending": "⏳",
    "requirements": "📝",
    "development": "💻",
    "testing": "🧪",
    "completed": "✅",
    "blocked": "🚫",
}

ROLE_TYPE_LABELS = {"pm": "产需", "dev": "开发", "qa": "测试"}
ROLE_STATUS_ICONS = {"pending": "⏳", "active": "▶️", "done": "✅", "blocked": "🚫"}

TYPE_LABELS = {
    "single": "单应用",
    "fullstack": "全栈",
    "multi-service": "多服务",
    "multi-platform": "多端",
}

MODE_LABELS = {"parallel": "并行", "sequential": "串行", "mixed": "混合"}


def load_projects():
    if PROJECTS_FILE.exists():
        return json.loads(PROJECTS_FILE.read_text())
    return []


def get_status_label(status):
    return STATUS_LABELS.get(status, status)


def get_roles_summary(project):
    """返回角色状态摘要字符串."""
    roles = project.get("roles", [])
    if not roles:
        return "未配置角色"
    parts = []
    for r in roles:
        icon = ROLE_STATUS_ICONS.get(r.get("status", "pending"), "⏳")
        note_str = f"({r['note']})" if r.get("note") else ""
        parts.append(f"{icon}{r['label']}{note_str}")
    return " | ".join(parts)


def get_role_counts(project):
    """返回各类型角色的完成计数."""
    roles = project.get("roles", [])
    pm_roles = [r for r in roles if r.get("type") == "pm"]
    dev_roles = [r for r in roles if r.get("type") == "dev"]
    qa_roles = [r for r in roles if r.get("type") == "qa"]

    def fmt(roles):
        if not roles:
            return "-"
        done = sum(1 for r in roles if r.get("status") == "done")
        return f"{done}/{len(roles)}"

    return fmt(pm_roles), fmt(dev_roles), fmt(qa_roles)


def print_dashboard(projects, show_detail=False):
    if not projects:
        print("当前没有项目。使用 init_project.py 创建第一个项目。")
        return

    total = len(projects)
    by_status = {}
    by_priority = {}
    for s in STATUS_ORDER:
        by_status[s] = 0
    for p in projects:
        status = p.get("status", "pending")
        pri = p.get("priority", "P3")
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[pri] = by_priority.get(pri, 0) + 1

    active = [p for p in projects if p.get("status") not in ("completed",)]
    completed = [p for p in projects if p.get("status") == "completed"]

    print("=" * 80)
    print(f"  📋 项目看板 | 共 {total} 个项目")
    print(f"  进行中: {len(active)} | 已完成: {len(completed)} | 阻塞: {by_status.get('blocked', 0)}")
    pri_counts = " | ".join(
        f"{pri}: {by_priority.get(pri, 0)}"
        for pri in ["P0", "P1", "P2", "P3"]
        if by_priority.get(pri, 0) > 0
    )
    if pri_counts:
        print(f"  {pri_counts}")
    print("=" * 80)
    print()

    for status_key in STATUS_ORDER:
        group = [p for p in projects if p.get("status") == status_key]
        if not group:
            continue
        icon = STATUS_ICONS.get(status_key, "•")
        label = STATUS_LABELS.get(status_key, status_key)
        print(f"  [{icon} {label}]")
        for p in sorted(group, key=lambda x: x.get("priority", "P3")):
            pri = p.get("priority", "P3")
            name = p.get("name", "未命名")
            pid = p.get("id", "???")
            desc = p.get("description", "")
            short_desc = (desc[:50] + "..") if len(desc) > 50 else desc

            # 完整信息行
            ptype = TYPE_LABELS.get(p.get("project_type", "single"), p.get("project_type", "single"))
            mode = MODE_LABELS.get(p.get("work_mode", "parallel"), p.get("work_mode", "parallel"))

            if show_detail:
                print(f"    {pid} [{pri}] {name}")
                if short_desc:
                    print(f"      {short_desc}")
                print(f"      类型: {ptype} | 模式: {mode}")
                print(f"      角色: {get_roles_summary(p)}")
                # 显示角色完成计数
                pm_c, dev_c, qa_c = get_role_counts(p)
                print(f"      产需 {pm_c} | 开发 {dev_c} | 测试 {qa_c}")
            else:
                role_info = get_roles_summary(p)
                print(f"    {pid} [{pri}] {name}")
                if short_desc:
                    print(f"      {short_desc}")
                print(f"      {role_info}")
            print()
    print()


def show_project_detail(project_id):
    """展示单个项目的完整看板."""
    projects = load_projects()
    target = None
    for p in projects:
        if p.get("id") == project_id:
            target = p
            break
    if not target:
        print(f"[ERROR] 未找到项目: {project_id}")
        return

    name = target.get("name", "未命名")
    pid = target.get("id", "???")
    status = get_status_label(target.get("status", "pending"))
    priority = target.get("priority", "P3")
    ptype = TYPE_LABELS.get(target.get("project_type", "single"), target.get("project_type", "single"))
    mode = MODE_LABELS.get(target.get("work_mode", "parallel"), target.get("work_mode", "parallel"))
    desc = target.get("description", "")
    deadline = target.get("deadline", "")
    created = target.get("created_at", "")

    print("=" * 72)
    print(f"  {pid} {name}")
    print(f"  优先级: {priority} | 状态: {status}")
    print(f"  类型: {ptype} | 模式: {mode}")
    if desc:
        print(f"  描述: {desc}")
    if deadline:
        print(f"  截止: {deadline}")
    if created:
        print(f"  创建: {created}")
    print("=" * 72)
    print()

    # 角色详情
    roles = target.get("roles", [])
    if roles:
        print("  [角色状态]")
        for r in roles:
            icon = ROLE_STATUS_ICONS.get(r.get("status", "pending"), "⏳")
            rtype_label = ROLE_TYPE_LABELS.get(r.get("type", ""), r.get("type", ""))
            note_str = f" ({r['note']})" if r.get("note") else ""
            print(f"    {icon} {r['label']} [{rtype_label}]{note_str} → {r.get('status', 'pending')}")
        print()

    # 日志
    logs = target.get("logs", [])
    if logs:
        print("  [流转日志]")
        for log in logs[-5:]:
            t = log.get("time", "")
            note = log.get("note", "")
            print(f"    [{t}] {note}")
        print()


def main():
    parser = argparse.ArgumentParser(description="查看项目看板")
    parser.add_argument("--status", "-s", help="按阶段筛选 (pending/requirements/development/testing/completed/blocked)")
    parser.add_argument("--priority", "-p", choices=["P0", "P1", "P2", "P3"], help="按优先级筛选")
    parser.add_argument("--detail", "-d", action="store_true", help="显示角色级详情")
    parser.add_argument("--project", help="查看单个项目详情 (如 PROJ-0001)")
    args = parser.parse_args()

    if args.project:
        return show_project_detail(args.project)

    projects = load_projects()

    if args.status:
        valid_statuses = set(STATUS_LABELS.keys()) | set(STATUS_LABELS.values())
        if args.status in STATUS_LABELS:
            filter_key = args.status
        elif args.status in STATUS_LABELS.values():
            # 反向查找
            filter_key = next(k for k, v in STATUS_LABELS.items() if v == args.status)
        else:
            print(f"[ERROR] 无效状态: {args.status}，有效值: {', '.join(STATUS_LABELS.values())}")
            return
        projects = [p for p in projects if p.get("status") == filter_key]

    if args.priority:
        projects = [p for p in projects if p.get("priority") == args.priority]

    print_dashboard(projects, show_detail=args.detail)


if __name__ == "__main__":
    main()
