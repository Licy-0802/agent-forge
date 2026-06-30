# agent-forge 🛠️

**A multi-agent workflow for Codex** — a Principal orchestrates Product, Developer and Tester agents through parallel project pipelines.

Stop switching context between projects. Let your agents form a crew.

---

## What it does

agent-forge turns your Codex workspace into a **four-agent workshop**:

| Role | What they do |
|------|-------------|
| **Principal** | Schedules, delegates, reviews. Does not write code or chase status. |
| **Product-to-Requirements** | Turns PRDs into technical specs (tables + JSON examples + SQL DDL). |
| **Developer** | Implements code and unit tests from the technical spec. |
| **Tester** | Runs test cases, reports bugs (read-only mode). |

Every handoff goes through the Principal. The three workers never talk to each other directly — keeping the bottleneck in the right place.

---

## How it works

```
User → Principal appointed
  → Principal creates threads for Product / Developer / Tester
  → Each role activates and waits for tasks
  → Principal dispatches PRD → Product writes technical spec → review
  → Principal dispatches spec → Developer writes code → review
  → Principal dispatches code → Tester tests → bug report
  → All clear → project marked done
```

Multiple projects run in parallel at different stages. One project can be in testing while another is in development and a third is being spec'd out.

### Three absolute rules (for the Principal)

1. **No polling** — dispatch and move on. The agent reports back when done.
2. **No coding** — never write code, specs, or tests yourself. Return work that doesn't pass.
3. **No babysitting** — trust the agents. If they're stuck, they'll come to you.

---

## Quick start

### In Codex (desktop app)

```bash
# Step 1: Install the skill
#   Add agent-forge/SKILL.md as a personal skill in Codex settings.

# Step 2: In a new Codex thread, say:
开启多 agent 模式，你的角色是主理人

# Step 3: The Principal creates threads for the other 3 roles.
#         Click each new thread in the sidebar to activate them.
```

### What happens next

The Principal (your current thread) creates three new threads and sends activation commands. You just click each thread to confirm. From there, the Principal handles dispatching, reviewing, and closing out projects.

```
Principal thread:  "开启多 agent 模式，你的角色是主理人"
  → create_thread → "产需对话"    → sends "开启多 agent 模式，你的角色是产需"
  → create_thread → "开发对话"    → sends "开启多 agent 模式，你的角色是开发"
  → create_thread → "测试对话"    → sends "开启多 agent 模式，你的角色是测试"
  → User clicks each → Roles go online
  → Let's go
```

### Managing projects

```bash
python3 scripts/init_project.py "User Auth System"          # Create a project
python3 scripts/view_dashboard.py                           # See all projects
python3 scripts/transition_project.py PROJ-001 "开发中"     # Move to next stage
```

---

## Repository structure

```
agent-forge/
├── README.md                         # This file
├── LICENSE                           # MIT
├── SKILL.md                          # Codex skill entry point
├── references/
│   ├── principal-prompt.md           # Principal system prompt
│   ├── product-to-requirements-prompt.md  # Product-to-Reqs system prompt
│   ├── developer-prompt.md           # Developer system prompt
│   ├── tester-prompt.md              # Tester system prompt
│   ├── roles.md                      # Detailed role descriptions
│   └── workflow.md                   # Workflow and handoff specs
└── scripts/
    ├── init_project.py               # Create a new project
    ├── transition_project.py         # Move project to next stage
    └── view_dashboard.py             # View all project statuses
```

---

## Requirements

- [Codex](https://codex.openai.com/) desktop app (macOS)
- Python 3.10+ (for the helper scripts)

---

## License

MIT

---

## Note on language

The system prompt files in `references/` are written in **Chinese** by design — this project targets Chinese-speaking development teams who write PRDs and technical specs in Chinese. The README, SKILL.md description, and code comments are in English for discoverability.
