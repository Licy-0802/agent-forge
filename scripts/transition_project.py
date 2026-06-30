#!/usr/bin/env python3
"""Transition a project to a new phase and log the change."""

import json
import sys
from datetime import datetime
from pathlib import Path

VALID_TRANSITIONS = [
    ("待启动", "需求中"),
    ("需求中", "开发中"),
    ("开发中", "测试中"),
    ("测试中", "已完成"),
    # Any status can go to 阻塞中 and back
]

def get_project(board, project_id):
    for p in board["projects"]:
        if p["id"] == project_id:
            return p
    return None

def is_valid_transition(from_status, to_status):
    if to_status == "阻塞中":
        return from_status in ("需求中", "开发中", "测试中")
    if from_status == "阻塞中":
        return True
    return (from_status, to_status) in VALID_TRANSITIONS

def main():
    if len(sys.argv) < 3:
        print("用法: transition_project.py <项目ID> <目标状态>")
        print("状态列表: 待启动 | 需求中 | 开发中 | 测试中 | 已完成 | 阻塞中")
        print("示例: transition_project.py PROJ-001 开发中")
        sys.exit(1)

    project_id = sys.argv[1]
    to_status = sys.argv[2]

    board_path = Path.cwd() / "work_queue" / "status_board.json"
    if not board_path.exists():
        print("错误: 看板文件不存在。请先运行 init_project.py 创建项目。")
        sys.exit(1)

    board = json.loads(board_path.read_text(encoding="utf-8"))
    project = get_project(board, project_id)

    if not project:
        print(f"错误: 未找到项目 {project_id}")
        print(f"当前项目: {', '.join(p['id'] for p in board['projects'])}")
        sys.exit(1)

    from_status = project["status"]
    if from_status == to_status:
        print(f"项目 {project_id} 已经在 [{from_status}] 状态")
        return

    if not is_valid_transition(from_status, to_status):
        print(f"错误: 不允许从 [{from_status}] 转换到 [{to_status}]")
        print(f"允许的下一状态: ", end="")
        for f, t in VALID_TRANSITIONS:
            if f == from_status:
                print(t, end=" ")
        if from_status not in ("已完成", "阻塞中"):
            print("阻塞中", end=" ")
        print()
        sys.exit(1)

    project["status"] = to_status
    project["updated_at"] = datetime.now().isoformat()

    board_path.write_text(json.dumps(board, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"项目 {project_id} ({project['name']})")
    print(f"  状态: [{from_status}] → [{to_status}]")
    print(f"  时间: {project['updated_at'][:19]}")

    if to_status == "需求中":
        print(f"\n下一步: 向产需角色派发任务，提供 PRD 文档路径")
    elif to_status == "开发中":
        print(f"\n下一步: 向开发角色派发任务，提供技术文档路径")
    elif to_status == "测试中":
        print(f"\n下一步: 向测试角色派发任务，提供技术文档和代码路径")
    elif to_status == "已完成":
        print(f"\n项目完成! 可以归档项目文档。")
    elif to_status == "阻塞中":
        print(f"\n请在看板中记录阻塞原因。")

if __name__ == "__main__":
    main()
