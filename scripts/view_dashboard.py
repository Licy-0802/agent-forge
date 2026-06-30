#!/usr/bin/env python3
"""View formatted project status board."""

import json
import sys
from pathlib import Path

STATUS_ORDER = {"待启动": 0, "需求中": 1, "开发中": 2, "测试中": 3, "已完成": 4, "阻塞中": 5}
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

def show(board, filter_status=None):
    projects = board["projects"]
    if filter_status:
        projects = [p for p in projects if p["status"] == filter_status]

    if not projects:
        print("暂无项目记录。")
        return

    # Sort by priority then creation date
    projects.sort(key=lambda p: (PRIORITY_ORDER.get(p.get("priority", "P2"), 99), p.get("created_at", "")))

    print(f"{'ID':<12} {'项目名称':<20} {'状态':<10} {'优先级':<8} {'创建时间':<20}")
    print("-" * 70)
    for p in projects:
        print(f"{p['id']:<12} {p['name']:<20} {p['status']:<10} {p.get('priority', 'P2'):<8} {p.get('created_at', '')[:19]:<20}")

    # Summary
    print()
    total = len(board["projects"])
    completed = sum(1 for p in board["projects"] if p["status"] == "已完成")
    blocked = sum(1 for p in board["projects"] if p["status"] == "阻塞中")
    print(f"总计: {total} 个项目 | 已完成: {completed} | 阻塞中: {blocked}")

def main():
    board_path = Path.cwd() / "work_queue" / "status_board.json"

    if not board_path.exists():
        print("尚未创建任何项目。")
        print(f"请先运行: python3 {Path(__file__).resolve().parent}/init_project.py")
        sys.exit(1)

    board = json.loads(board_path.read_text(encoding="utf-8"))

    filter_status = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--status", "-s"):
            filter_status = sys.argv[2] if len(sys.argv) > 2 else None
        else:
            filter_status = sys.argv[1]

    show(board, filter_status)

if __name__ == "__main__":
    main()
