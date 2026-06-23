# Google Planner

Combined Google Calendar and Google Tasks management using direct REST API calls with HTTP proxy support.

## Setup

Uses the same OAuth2 credentials for both Calendar and Tasks (already configured in the script).

## Commands

```bash
# Authenticate (calendar + tasks)
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py auth

# ====== Calendar ======
# List events (next 7 days)
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py list

# List events in a date range
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py list <start_iso> <end_iso>

# Add event
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py add "<title>" "<start_date>" "<end_date>" [description] [location] [--color <1-11>]
# Date format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS

# Delete event
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py delete <event_id>

# Update event
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py update <event_id> [options]
# Options: --summary <title> --desc <description> --loc <location>
#          --start <date> --end <date> --done --color <1-11>

# Search events
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py search <keyword>

# List calendars
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py calendars

# ====== Tasks ======
# List all tasks
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py tasks

# Add task
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py task-add "<title>" [notes] [due]
# Due format: YYYY-MM-DD

# Mark task done
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py task-done <task_id>

# Delete task
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py task-delete <task_id>

# Update task
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py task-update <task_id> [options]
# Options: --title <title> --notes <notes> --due <date>
```

## Color Scheme

Google Calendar colors (1-11). **不指定时自动根据关键词分配：**

| 颜色ID | 颜色 | 关键词 | 场景 |
|--------|------|--------|------|
| 11 | 番茄红 | 截止、deadline、ddl、提交、重要、紧急、必须 | 高优先级/截止事项 |
| 6 | 橘色 | 比赛、黑客松、hackathon、大赛、竞赛、路演 | 竞赛活动 |
| 9 | 蓝莓蓝 | 会议、meeting、论坛、分享、活动、培训 | 会议/论坛 |
| 7 | 孔雀青 | 学习、课程、上课、讲座、读书 | 学习培训 |
| 10 | 罗勒绿 | 其他 | 日常/默认 |

**自定义颜色**：使用 `--color <1-11>` 选项覆盖自动分配。

## Features

- HTTP proxy support (uses HTTPS_PROXY / HTTP_PROXY env vars)
- Auto token refresh for both Calendar and Tasks
- Calendar events with auto color assignment
- Full CRUD operations for both Calendar and Tasks

## Token

OAuth tokens are saved to:
- Calendar: `~/.config/gcalcli/token.pkl`
- Tasks: `~/.config/gtasks/token.pkl`

If you need to re-authenticate, delete the respective token file and run:
```bash
PYTHONIOENCODING=utf-8 uv run --with requests python $SKILL_DIR/scripts/google-planner.py auth
```
