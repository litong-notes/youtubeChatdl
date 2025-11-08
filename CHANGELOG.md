# 更新日志

## [2.1.0] - 2024

### 新增功能 - 数据库导入

- 🗄️ JSON 文件导入到 SQLite 数据库
- 📥 独立的导入命令 `ytchat-import`
- 🔄 支持增量导入（跳过已存在的视频）
- 📊 数据库统计信息查看
- 🤖 下载时自动导入数据库 (`--auto-import-db`)
- 🔍 优化的数据库索引提升查询性能
- 📈 完整的视频和消息表结构

### 新增文件

- `youtube_chat_downloader/db_importer.py`: 数据库导入模块
- `youtube_chat_downloader/import_to_db.py`: 导入CLI工具
- `test_db_import.py`: 数据库导入测试
- `DB_IMPORT_GUIDE.md`: 数据库导入详细指南

### 新增 CLI 参数

- `--auto-import-db`: 自动将下载的JSON导入到数据库
- `--db-path`: SQLite数据库路径

### 数据库结构

- `videos` 表：存储视频元数据
- `chat_messages` 表：存储聊天消息
- 4个索引：video_id, offset_ms, author_id, upload_date

## [2.0.0] - 2024

### 新增功能

- ✨ 全新的 CLI 工具架构
- 📦 使用 uv 进行依赖管理
- 📺 支持批量下载频道所有直播视频的聊天回放
- 💾 JSON 格式输出（替代 SQLite）
- 🔄 增量下载模式：自动跳过已下载的视频
- ⏱️ 可配置的休眠间隔
- 🎯 支持单个视频下载和批量频道下载两种模式

### 技术改进

- 📁 模块化架构：将代码分为 `cli.py` 和 `fetcher.py`
- 🔧 使用 `pyproject.toml` 管理项目配置和依赖
- 📊 增强的统计信息显示
- 🌐 改进的视频信息获取逻辑
- 📝 完整的视频元数据保存（标题、时长、上传日期、URL）

### CLI 参数

- `--cookies`: Cookies 文件路径
- `--output-dir`: 输出目录
- `--save-type`: 保存类型（json）
- `--incremental`: 增量模式
- `--sleep-interval`: 休眠间隔（秒）
- `--channel`: YouTube 频道直播页面链接
- `--url`: 单个视频 URL

### 输出格式变化

从 SQLite 数据库改为 JSON 文件：
- 文件名格式：`{上传日期}_{视频ID}.json`
- 包含完整的视频信息、聊天消息和统计数据
- 更易于查询和处理

### 工作流程优化

1. 自动获取频道所有直播视频链接（模拟 yt-dlp 的 `--flat-playlist` 参数）
2. 循环处理每个视频：
   - 获取视频元数据
   - 检查增量模式（跳过已存在的文件）
   - 下载聊天回放
   - 保存为 JSON
   - 休眠指定时间

### 向后兼容

- 保留旧版 `youtubeChatdl.py` 脚本（SQLite 版本）
- 保留 `query_example.py` 数据库查询工具

### 使用示例

```bash
# 批量下载频道直播
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt \
  --incremental \
  --sleep-interval 10

# 下载单个视频
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --cookies www.youtube.com_cookies.txt
```

## [1.0.0] - 之前版本

- 基础的单视频聊天回放下载功能
- SQLite 数据库存储
- Cookie 支持
- 重试机制
