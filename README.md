# YouTube 聊天回放下载器

一个用于批量下载 YouTube 直播聊天回放记录的 Python CLI 工具。

## 功能特点

- ✨ 全新 CLI 工具，支持批量下载频道所有直播回放
- 📺 自动获取频道的所有直播视频链接
- 💾 保存为 JSON 格式，包含完整的视频信息和聊天消息
- 🔄 增量模式：跳过已下载的视频
- ⏱️ 可配置的休眠间隔，避免请求过快
- 🍪 支持使用 Cookie 文件进行身份验证访问
- 📏 自动获取视频时长并智能停止
- 🔁 重试机制保证稳定性
- 📊 详细的统计信息

## 技术架构

- **依赖管理**: uv
- **依赖库**: requests, yt-dlp
- **架构**: 模块化 Python 包
- **核心功能**:
  - 使用 yt-dlp 获取频道直播列表
  - 循环下载每个直播的聊天回放
  - 提取 API 参数和 continuation tokens
  - 解析聊天消息并保存为 JSON

## 安装

### 使用 uv（推荐）

```bash
# 安装 uv（如果还没有安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆仓库
git clone <repository_url>
cd youtube-chat-downloader

# 使用 uv 安装依赖
uv pip install -e .
```

### 传统方式

```bash
pip install -e .
```

## 使用方法

### 批量下载频道所有直播回放

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt \
  --output-dir chat_replays \
  --incremental \
  --sleep-interval 10
```

### 下载单个视频

```bash
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --cookies www.youtube.com_cookies.txt
```

### CLI 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--cookies` | Cookies 文件路径 | `www.youtube.com_cookies.txt` |
| `--output-dir` | 输出目录 | `chat_replays` |
| `--save-type` | 保存类型（目前仅支持 json） | `json` |
| `--incremental` | 增量模式：跳过已存在的文件 | 关闭 |
| `--sleep-interval` | 视频之间的休眠间隔（秒） | `5` |
| `--channel` | YouTube 频道直播页面链接 | `https://www.youtube.com/@chenyifaer/streams` |
| `--url` | 单个视频URL（如指定则只下载该视频） | - |
| `--auto-import-db` | 自动将下载的JSON导入到SQLite数据库 | 关闭 |
| `--db-path` | SQLite数据库路径（配合--auto-import-db使用） | `chat_database.db` |

## Cookie 文件（可选）

如果需要访问受限制的视频聊天记录，可以使用浏览器扩展导出 Cookie：

1. 安装浏览器扩展（如 "Get cookies.txt LOCALLY"）
2. 访问 YouTube 并登录
3. 导出 cookies.txt 文件
4. 将文件重命名为 `www.youtube.com_cookies.txt` 并放在项目目录

## 输出格式

聊天记录保存为 JSON 文件，文件名格式：`{直播日期}_{视频ID}.json`

例如：`20240115_abcdefghijk.json`

### JSON 文件结构

```json
{
  "video_info": {
    "id": "视频ID",
    "title": "视频标题",
    "duration": 3600,
    "upload_date": "20240115",
    "url": "https://www.youtube.com/watch?v=..."
  },
  "messages": [
    {
      "time_text": "0:05",
      "author": "用户名",
      "author_id": "UCxxxxxxxxxx",
      "message": "消息内容",
      "offset_ms": 5000
    }
  ],
  "statistics": {
    "total_messages": 1234,
    "unique_authors": 567,
    "time_range": {
      "min": "0:00",
      "max": "1:23:45"
    }
  }
}
```

## 工作流程

1. 使用 yt-dlp 获取频道所有直播视频链接（模拟 `--flat-playlist --match-filter "is_live"` 参数）
2. 遍历每个视频链接：
   - 获取视频信息（时长、ID、标题等）
   - 检查增量模式（如启用且文件已存在则跳过）
   - 获取页面 HTML 并提取 API 密钥和 ytInitialData
   - 查找初始 continuation token
   - 循环获取聊天消息直到结束
   - 保存为 JSON 文件
   - 休眠指定时间后处理下一个视频
3. 显示最终统计信息

## 示例：批量下载特定频道

```bash
# 下载 chenyifaer 频道的所有直播回放
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt \
  --incremental \
  --sleep-interval 10
```

这会：
- 自动获取该频道的所有直播视频
- 逐个下载每个视频的聊天回放
- 跳过已存在的文件（增量模式）
- 每个视频之间休眠 10 秒

## 数据库导入（新功能）

### 将 JSON 导入到 SQLite 数据库

除了 JSON 格式，现在还支持将数据导入到 SQLite 数据库，便于查询和分析。

#### 方法 1: 下载时自动导入

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --auto-import-db \
  --db-path chat_database.db
```

#### 方法 2: 独立导入命令

```bash
# 导入已下载的 JSON 文件
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path chat_database.db \
  --incremental
```

#### 查看数据库统计

```bash
python -m youtube_chat_downloader.import_to_db \
  --db-path chat_database.db \
  --stats
```

### 数据库查询示例

```python
import sqlite3

conn = sqlite3.connect('chat_database.db')
cursor = conn.cursor()

# 查询所有视频
cursor.execute('SELECT video_id, title, total_messages FROM videos')
for video_id, title, count in cursor.fetchall():
    print(f"{title}: {count} 条消息")

# 查询特定视频的消息
cursor.execute('''
    SELECT time_text, author, message 
    FROM chat_messages 
    WHERE video_id = ? 
    ORDER BY offset_ms
''', ('VIDEO_ID',))

# 搜索包含关键词的消息
cursor.execute('''
    SELECT v.title, cm.author, cm.message
    FROM chat_messages cm
    JOIN videos v ON cm.video_id = v.video_id
    WHERE cm.message LIKE ?
''', ('%关键词%',))

conn.close()
```

**详细说明请查看**: [数据库导入指南](DB_IMPORT_GUIDE.md)

## 查询 JSON 数据

可以使用 Python 或 jq 工具来查询 JSON 数据：

### 使用 Python

```python
import json

with open('chat_replays/20240115_abcdefghijk.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 查看视频信息
print(f"视频标题: {data['video_info']['title']}")
print(f"总消息数: {data['statistics']['total_messages']}")

# 遍历消息
for msg in data['messages']:
    print(f"{msg['time_text']} | {msg['author']}: {msg['message']}")
```

### 使用 jq

```bash
# 查看视频标题
jq '.video_info.title' chat_replays/20240115_abcdefghijk.json

# 统计消息数
jq '.messages | length' chat_replays/20240115_abcdefghijk.json

# 查看前10条消息
jq '.messages[:10]' chat_replays/20240115_abcdefghijk.json

# 查找特定用户的消息
jq '.messages[] | select(.author == "用户名")' chat_replays/20240115_abcdefghijk.json
```

## 注意事项

- 脚本会保留所有消息，包括负时间戳的消息（直播开始前的等待消息）
- 最多迭代 3000 次防止无限循环
- 当达到视频时长时自动停止
- 包含重试机制处理网络错误
- 使用增量模式可以安全地中断和恢复下载
- 建议设置合理的休眠间隔避免请求过快

## 旧版本（SQLite）

旧版本的单文件脚本 `youtubeChatdl.py` 仍然保留在项目中，使用 SQLite 数据库保存数据：

```bash
python youtubeChatdl.py <youtube_url>
```

### 从 SQLite 迁移到 JSON

如果你有旧版本生成的 SQLite 数据库文件，可以使用转换工具：

```bash
python convert_db_to_json.py chatlog_VIDEO_ID.db [output.json]
```

这将把 SQLite 数据库转换为新的 JSON 格式。

## 项目结构

```
youtube-chat-downloader/
├── youtube_chat_downloader/
│   ├── __init__.py
│   ├── cli.py               # CLI 入口
│   └── fetcher.py           # 核心获取逻辑
├── youtubeChatdl.py         # 旧版脚本（SQLite）
├── query_example.py         # 数据库查询示例
├── convert_db_to_json.py    # SQLite 转 JSON 工具
├── test_cli.py              # 测试脚本
├── example_usage.sh         # 使用示例
├── pyproject.toml           # uv 项目配置
├── requirements.txt         # pip 依赖
└── README.md
```

## 许可证

本项目为开源工具，请遵守 YouTube 使用条款。
