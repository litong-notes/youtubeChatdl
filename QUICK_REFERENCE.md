# 快速参考卡片

## 安装

```bash
# 使用 uv
uv pip install -e .

# 使用 pip
pip install -r requirements.txt
```

## 基本用法

### 下载单个视频

```bash
python -m youtube_chat_downloader.cli --url "VIDEO_URL"
```

### 批量下载频道

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams"
```

## 常用命令组合

### 增量下载（可中断恢复）

```bash
python -m youtube_chat_downloader.cli \
  --channel "CHANNEL_URL" \
  --incremental \
  --sleep-interval 10
```

### 指定输出目录

```bash
python -m youtube_chat_downloader.cli \
  --channel "CHANNEL_URL" \
  --output-dir my_chats
```

### 使用 cookies

```bash
python -m youtube_chat_downloader.cli \
  --url "VIDEO_URL" \
  --cookies www.youtube.com_cookies.txt
```

## CLI 参数速查

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--url` | - | 单个视频 URL | - |
| `--channel` | - | 频道直播页面 | @chenyifaer |
| `--cookies` | - | Cookies 文件 | www.youtube.com_cookies.txt |
| `--output-dir` | - | 输出目录 | chat_replays |
| `--save-type` | - | 保存类型 | json |
| `--incremental` | - | 增量模式 | False |
| `--sleep-interval` | - | 休眠间隔（秒） | 5 |

## 输出格式

### 文件命名

```
{上传日期}_{视频ID}.json
```

例如：`20240115_abcD1234efg.json`

### JSON 结构

```json
{
  "video_info": { "id", "title", "duration", "upload_date", "url" },
  "messages": [ { "time_text", "author", "author_id", "message", "offset_ms" } ],
  "statistics": { "total_messages", "unique_authors", "time_range" }
}
```

## 辅助工具

### 测试工具

```bash
python test_cli.py
```

### 格式转换（SQLite → JSON）

```bash
python convert_db_to_json.py chatlog_VIDEO_ID.db
```

### 旧版脚本（SQLite）

```bash
python youtubeChatdl.py VIDEO_URL
```

## 常见错误处理

### ModuleNotFoundError

```bash
source .venv/bin/activate
uv pip install -e .
```

### 未找到 ytInitialData

- 检查 cookies 文件是否存在
- 更新 cookies（重新导出）

### 请求失败

- 检查网络连接
- 增加休眠间隔
- 使用有效的 cookies

## 数据分析

### Python

```python
import json
with open('FILE.json') as f:
    data = json.load(f)
print(data['statistics'])
```

### jq

```bash
# 视频标题
jq '.video_info.title' FILE.json

# 消息总数
jq '.statistics.total_messages' FILE.json

# 搜索关键词
jq '.messages[] | select(.message | contains("关键词"))' FILE.json
```

## 文档链接

- 📖 [README.md](README.md) - 项目概述
- 📚 [USAGE_GUIDE.md](USAGE_GUIDE.md) - 详细指南
- 📝 [CHANGELOG.md](CHANGELOG.md) - 更新日志
- 🔧 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - 实施总结

## 技术支持

提问时请提供：
1. 完整错误信息
2. 使用的命令
3. Python 版本
4. 依赖版本

---

更多详情请查看 [完整文档](README.md)
