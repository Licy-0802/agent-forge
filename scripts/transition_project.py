#!/usr/bin/env python3
"""项目阶段流转 - 支持角色级和项目级操作.

Usage:
    ./transition_project.py PROJ-0001 --to requirements      # 项目进入需求阶段
    ./transition_project.py PROJ-0001 --role 前端开发 --start  # 启动指定角色
    ./transition_project.py PROJ-0001 --role 前端开发 --done   # 标记角色完成
    ./transition_project.py PROJ-0001 --advance                # 推进到下一阶段(所有角色完成后)
    ./transition_project.py PROJ-0001 --status blocked --note "等待依赖"  # 阻塞
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

PROJECTS_FILE = Path.home() / ".codex" / "projects" / "projects.json"

# 阶段定义: 阶段名 -> 所需角色类型
PHASE_ROLE_TYPES = {
    "pending": "pm",
    "requirements": "pm",
    "development": "dev",
    "testing": "qa",
    "completed": None,
    "blocked": None,
}

PHASE_LABELS = {
    "pending": "待启动",
    "requirements": "需求中",
    "development": "开发中",
    "testing": "测试中",
    "completed": "已完成",
    "blocked": "阻塞中",
}

PHASE_LABEL_TO_KEY = {v: k for k, v in PHASE_LABELS.items()}

ROLE_TYPE_LABELS = {"pm": "产需", "dev": "开发", "qa": "测试"}

# 标准流转路径
PHASE_FLOW = ["pending", "requirements", "development", "testing", "completed"]


def load_projects():
    if PROJECTS_FILE.exists():
        return json.loads(PROJECTS_FILE.read_text())
    return []


def save_projects(projects):
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(projects, ensure_ascii=False, indent=2))


def find_project(project_id):
    projects = load_projects()
    for p in projects:
        if p.get("id") == project_id:
            return p, projects
    return None, projects


def get_phase_key(status_str):
    """支持中文/英文阶段名."""
    if status_str in PHASE_LABELS:
        return status_str
    if status_str in PHASE_LABEL_TO_KEY:
        return PHASE_LABEL_TO_KEY[status_str]
    return None


def get_phase_label(phase_key):
    return PHASE_LABELS.get(phase_key, phase_key)


def find_role(project, role_label):
    """按标签查找角色."""
    roles = project.get("roles", [])
    for r in roles:
        if r.get("label") == role_label:
            return r
    # 模糊匹配
    for r in roles:
        if role_label in r.get("label", ""):
            return r
    return None


def roles_of_type(project, rtype):
    return [r for r in project.get("roles", []) if r.get("type") == rtype]


def all_roles_complete(project, rtype):
    """某类型的所有角色是否都已完成."""
    roles = roles_of_type(project, rtype)
    return len(roles) > 0 and all(r.get("status") == "done" for r in roles)


def save_and_report(project, projects, msg):
    save_projects(projects)
    print(f"[OK] {project['id']} {project['name']}: {msg}")
    # 显示当前角色状态摘要
    if project.get("roles"):
        print("     角色状态:")
        for r in project["roles"]:
            status_icons = {"pending": "⏳", "active": "▶️", "done": "✅", "blocked": "🚫"}
            icon = status_icons.get(r.get("status", "pending"), "⏳")
            note_str = f" ({r['note']})" if r.get("note") else ""
            print(f"       {icon} {r['label']} [{ROLE_TYPE_LABELS.get(r['type'], r['type'])}] - {r.get('status', 'pending')}{note_str}")
    return True


def cmd_advance(project, projects, force=False):
    """将项目推进到下一阶段. 检查当前阶段的所有角色是否已完成."""
    current = get_phase_key(project.get("status", "pending"))
    if current == "completed":
        print(f"[SKIP] {project['id']} 已经完成")
        return True
    if current == "blocked":
        print(f"[ERROR] {project['id']} 当前阻塞中，请先解除阻塞再推进")
        return False

    # 找到当前阶段类型对应的角色
    current_rtype = PHASE_ROLE_TYPES.get(current)
    if current_rtype and not all_roles_complete(project, current_rtype):
        incomplete = [r for r in roles_of_type(project, current_rtype) if r.get("status") != "done"]
        labels = ", ".join(r["label"] for r in incomplete)
        print(f"[ERROR] 当前阶段 {get_phase_label(current)} 还有角色未完成: {labels}")
        if not force:
            print("       使用 --force 强制推进")
            return False

    # 找下一阶段
    try:
        idx = PHASE_FLOW.index(current)
        next_phase = PHASE_FLOW[idx + 1]
    except (ValueError, IndexError):
        print(f"[ERROR] 无法从 {get_phase_label(current)} 推进")
        return False

    # 更新项目状态
    old_label = get_phase_label(current)
    new_label = get_phase_label(next_phase)
    project["status"] = next_phase

    # 自动激活下一阶段的角色
    next_rtype = PHASE_ROLE_TYPES.get(next_phase)
    if next_rtype:
        for r in roles_of_type(project, next_rtype):
            if r.get("status") == "pending":
                r["status"] = "active"

    log_entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "from": old_label,
        "to": new_label,
        "note": f"阶段推进: {old_label} → {new_label}",
    }
    project.setdefault("logs", []).append(log_entry)
    return save_and_report(project, projects, f"{old_label} → {new_label}")


def cmd_role_start(project, projects, role_label):
    """启动指定角色."""
    role = find_role(project, role_label)
    if not role:
        print(f"[ERROR] 未找到角色 '{role_label}'，可用角色:")
        for r in project.get("roles", []):
            print(f"  - {r['label']} ({r.get('status', 'pending')})")
        return False
    if role.get("status") not in ("pending", "blocked"):
        print(f"[SKIP] 角色 '{role_label}' 当前状态: {role.get('status')}，无需启动")
        return False
    role["status"] = "active"
    return save_and_report(project, projects, f"角色 '{role_label}' 开始工作")


def cmd_role_done(project, projects, role_label):
    """标记指定角色完成."""
    role = find_role(project, role_label)
    if not role:
        print(f"[ERROR] 未找到角色 '{role_label}'")
        return False
    if role.get("status") == "done":
        print(f"[SKIP] 角色 '{role_label}' 已完成")
        return False
    old_status = role.get("status", "pending")
    role["status"] = "done"

    # 检查同类型角色是否全部完成 -> 自动建议推进
    rtype = role.get("type")
    if rtype and all_roles_complete(project, rtype):
        type_label = ROLE_TYPE_LABELS.get(rtype, rtype)
        current_phase = get_phase_label(project.get("status", "pending"))
        print(f"[INFO] 所有 '{type_label}' 角色已完成，项目可以推进至下一阶段")
        print(f"       使用: transition_project.py {project['id']} --advance")

    return save_and_report(project, projects, f"角色 '{role_label}' 完成 ({old_status} → done)")


def cmd_role_block(project, projects, role_label, note=""):
    """阻塞指定角色."""
    role = find_role(project, role_label)
    if not role:
        print(f"[ERROR] 未找到角色 '{role_label}'")
        return False
    old_status = role.get("status", "pending")
    role["status"] = "blocked"
    return save_and_report(project, projects, f"角色 '{role_label}' 阻塞{f' ({note})' if note else ''}")


def cmd_role_resume(project, projects, role_label):
    """恢复指定角色."""
    role = find_role(project, role_label)
    if not role:
        print(f"[ERROR] 未找到角色 '{role_label}'")
        return False
    if role.get("status") != "blocked":
        print(f"[SKIP] 角色 '{role_label}' 未阻塞，无需恢复")
        return False
    role["status"] = "active"
    return save_and_report(project, projects, f"角色 '{role_label}' 恢复工作")


def cmd_set_status(project, projects, new_status, note=""):
    """直接设置项目状态."""
    old_label = get_phase_label(project.get("status", "pending"))
    new_label = get_phase_label(new_status)
    project["status"] = new_status

    # 如果解除阻塞，自动激活当前阶段的角色
    if new_status == "development" or new_status not in ("blocked", "completed"):
        rtype = PHASE_ROLE_TYPES.get(new_status)
        if rtype:
            for r in roles_of_type(project, rtype):
                if r.get("status") == "pending":
                    r["status"] = "active"

    log_entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "from": old_label,
        "to": new_label,
        "note": note or f"状态设置: {old_label} → {new_label}",
    }
    project.setdefault("logs", []).append(log_entry)
    return save_and_report(project, projects, f"{old_label} → {new_label}")


def main():
    parser = argparse.ArgumentParser(description="项目阶段流转 - 角色级和项目级操作")
    parser.add_argument("project_id", help="项目 ID (如 PROJ-0001)")
    parser.add_argument("--to", help="设置项目阶段 (pending/requirements/development/testing/completed/blocked)")
    parser.add_argument("--role", help="目标角色标签 (如 前端开发)")
    parser.add_argument("--start", action="store_true", help="启动指定角色")
    parser.add_argument("--done", action="store_true", help="标记角色完成")
    parser.add_argument("--block", action="store_true", help="阻塞角色/项目")
    parser.add_argument("--resume", action="store_true", help="恢复角色/项目")
    parser.add_argument("--advance", action="store_true", help="推进到下一阶段")
    parser.add_argument("--force", action="store_true", help="强制推进(忽略未完成角色)")
    parser.add_argument("--note", "-n", help="备注")
    args = parser.parse_args()

    project, projects = find_project(args.project_id)
    if not project:
        print(f"[ERROR] 未找到项目: {args.project_id}")
        return

    # 项目级阻塞/恢复
    if args.block and not args.role:
        current = get_phase_key(project.get("status", "pending"))
        return cmd_set_status(project, projects, "blocked", note=args.note or "")
    if args.resume and not args.role:
        return cmd_set_status(project, projects, "development", note=args.note or "解除阻塞")

    # 角色级操作
    if args.role:
        if args.start:
            return cmd_role_start(project, projects, args.role)
        if args.done:
            return cmd_role_done(project, projects, args.role)
        if args.block:
            return cmd_role_block(project, projects, args.role, note=args.note or "")
        if args.resume:
            return cmd_role_resume(project, projects, args.role)
        print(f"[ERROR] 请指定角色操作: --start / --done / --block / --resume")
        return

    # 项目阶段设置
    if args.to:
        phase_key = get_phase_key(args.to)
        if not phase_key or phase_key not in PHASE_LABELS:
            valid = ", ".join(PHASE_LABELS.values())
            print(f"[ERROR] 无效阶段，有效值: {valid}")
            return
        return cmd_set_status(project, projects, phase_key, note=args.note or "")

    # 推进阶段
    if args.advance:
        return cmd_advance(project, projects, force=args.force)

    print("请指定操作: --to, --advance, --role <标签> --start/--done/--block/--resume")
    print(f"项目 '{project.get('name', '?')}' 当前状态: {get_phase_label(project.get('status', 'pending'))}")


if __name__ == "__main__":
    main()
