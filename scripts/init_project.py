#!/usr/bin/env python3
"""Create a new project with standard directory structure."""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

def get_next_id(board):
    existing = [p["id"] for p in board["projects"]]
    if not existing:
        return "PROJ-001"
    nums = [int(e.split("-")[1]) for e in existing if e.startswith("PROJ-")]
    return f"PROJ-{max(nums) + 1:03d}"

def main():
    if len(sys.argv) > 1:
        project_name = " ".join(sys.argv[1:])
    else:
        project_name = input("项目名称: ").strip()

    if not project_name:
        print("错误: 项目名称不能为空")
        sys.exit(1)

    workdir = Path.cwd()
    board_path = workdir / "work_queue" / "status_board.json"
    projects_dir = workdir / "projects"

    # Load or create board
    if board_path.exists():
        board = json.loads(board_path.read_text(encoding="utf-8"))
    else:
        board = {"projects": []}
        board_path.parent.mkdir(parents=True, exist_ok=True)

    project_id = get_next_id(board)

    # Create project directories
    proj_dir = projects_dir / project_id
    (proj_dir / "docs").mkdir(parents=True, exist_ok=True)
    (proj_dir / "src").mkdir(parents=True, exist_ok=True)
    (proj_dir / "tests").mkdir(parents=True, exist_ok=True)

    # Add to board
    entry = {
        "id": project_id,
        "name": project_name,
        "status": "待启动",
        "priority": "P2",
        "phase": "pending",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    board["projects"].append(entry)
    board_path.write_text(json.dumps(board, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n项目创建成功!")
    print(f"  ID:       {project_id}")
    print(f"  名称:     {project_name}")
    print(f"  状态:     待启动")
    print(f"  目录:     {proj_dir}")
    print(f"  看板:     {board_path}")

if __name__ == "__main__":
    main()
