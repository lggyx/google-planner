# Google Planner

一个简洁的 Google 日历和任务管理 CLI 工具，支持日历颜色自动分配。

## 功能特性

- 📅 **日历管理** - 添加、查看、搜索、删除日历事件
- ✅ **任务管理** - 添加、查看、完成、删除任务
- 🎨 **智能配色** - 根据事件关键词自动分配颜色
- 🔐 **安全凭证** - OAuth 密钥通过 `.env` 文件管理，不暴露在代码中
- 🌐 **代理支持** - 支持 HTTP/HTTPS 代理

## 快速开始

### 1. 安装依赖

```bash
uv pip install requests
# 或
pip install requests
```

### 2. 配置凭证

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的 Google OAuth 凭证
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

#### 获取 Google OAuth 凭证

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建项目（或选择现有项目）
3. 启用 **Google Calendar API** 和 **Google Tasks API**
4. 进入「凭据」→ 创建 **OAuth 客户端 ID**
5. 应用类型选择「桌面应用」
6. 复制客户端 ID 和密钥到 `.env` 文件

### 3. 首次授权

```bash
python scripts/google-planner.py auth
```

按照提示打开浏览器授权，将授权码粘贴回终端。

### 4. 使用

```bash
# 查看日历事件
python scripts/google-planner.py list

# 添加日历事件
python scripts/google-planner.py add "会议" "2026-07-01" "2026-07-01"

# 查看任务
python scripts/google-planner.py tasks

# 添加任务
python scripts/google-planner.py task-add "完成报告" "这是任务备注" "2026-07-05"
```

## 命令参考

### 日历命令

| 命令 | 说明 |
|------|------|
| `list [start] [end]` | 列出事件（默认未来7天） |
| `add <标题> <开始> <结束> [描述] [地点]` | 添加事件 |
| `delete <event_id>` | 删除事件 |
| `update <event_id> [options]` | 更新事件 |
| `search <关键词>` | 搜索事件 |
| `calendars` | 列出所有日历 |

#### update 选项
- `--summary <标题>` - 修改标题
- `--desc <描述>` - 修改描述
- `--loc <地点>` - 修改地点
- `--start <日期>` - 修改开始时间
- `--end <日期>` - 修改结束时间
- `--done` - 标记完成
- `--color <1-11>` - 设置颜色

### 任务命令

| 命令 | 说明 |
|------|------|
| `tasks` | 列出所有任务 |
| `task-add <标题> [备注] [截止日期]` | 添加任务 |
| `task-done <task_id>` | 标记任务完成 |
| `task-delete <task_id>` | 删除任务 |
| `task-update <task_id> [options]` | 更新任务 |

#### task-update 选项
- `--title <标题>` - 修改标题
- `--notes <备注>` - 修改备注
- `--due <日期>` - 修改截止日期

## 颜色方案

Google Calendar 支持 11 种颜色。不指定时自动根据关键词分配：

| 颜色ID | 颜色 | 关键词 | 适用场景 |
|--------|------|--------|----------|
| 11 | 🔴 番茄红 | 截止、deadline、ddl、提交、重要、紧急 | 高优先级/截止事项 |
| 6 | 🟠 橘色 | 比赛、黑客松、hackathon、大赛、竞赛、路演 | 竞赛活动 |
| 9 | 🔵 蓝莓蓝 | 会议、meeting、论坛、分享、活动、培训 | 会议/论坛 |
| 7 | 🟢 孔雀青 | 学习、课程、上课、讲座、读书 | 学习培训 |
| 10 | 🟢 罗勒绿 | 其他 | 日常/默认 |

### 自定义颜色

使用 `--color <1-11>` 选项覆盖自动分配：

```bash
python scripts/google-planner.py add "重要会议" "2026-07-01" "2026-07-01" --color 11
```

## 与 Claude Code 配合使用

在 Claude Code 中使用时，skill 会自动加载，无需额外配置。

## 文件结构

```
google-planner/
├── .env               # 你的凭证（不提交）
├── .env.example       # 凭证模板
├── .gitignore         # 忽略 .env
├── SKILL.md           # Claude Code skill 文档
├── README.md          # 本文档
└── scripts/
    └── google-planner.py  # 主程序
```

## License

MIT
