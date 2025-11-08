# YouTube 聊天回放下载器 - 使用指南

## 快速开始

### 1. 安装依赖

**使用 uv（推荐）:**
```bash
uv pip install -e .
```

**使用 pip:**
```bash
pip install -r requirements.txt
```

### 2. 准备 Cookies 文件（可选但推荐）

为了访问会员专属或需要登录的直播回放，建议准备 cookies 文件：

1. 安装浏览器扩展：
   - Chrome: "Get cookies.txt LOCALLY"
   - Firefox: "cookies.txt"

2. 登录 YouTube

3. 使用扩展导出 cookies 为 Netscape 格式

4. 将文件重命名为 `www.youtube.com_cookies.txt` 并放在项目根目录

### 3. 运行命令

#### 下载单个视频的聊天回放

```bash
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### 批量下载频道所有直播回放

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams"
```

## 详细使用说明

### 命令行参数

```
python -m youtube_chat_downloader.cli [选项]
```

#### 必选参数（二选一）

- `--url <URL>` - 下载单个视频
- `--channel <URL>` - 批量下载频道（默认: @chenyifaer）

#### 可选参数

- `--cookies <文件路径>` - Cookies 文件位置（默认: www.youtube.com_cookies.txt）
- `--output-dir <目录>` - 输出目录（默认: chat_replays）
- `--save-type {json}` - 保存格式（当前仅支持 json）
- `--incremental` - 增量模式：跳过已存在的文件
- `--sleep-interval <秒>` - 视频之间的休眠时间（默认: 5 秒）

### 使用场景

#### 场景 1：测试单个视频

第一次使用时，建议先测试单个视频：

```bash
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 场景 2：批量下载特定频道

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt \
  --output-dir chenyifaer_chats
```

#### 场景 3：增量下载（可中断和恢复）

使用 `--incremental` 参数可以安全地中断下载并稍后继续：

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --sleep-interval 10
```

如果下载过程被中断（Ctrl+C），再次运行相同命令时会自动跳过已下载的文件。

#### 场景 4：自定义休眠时间

为了避免请求过于频繁，可以增加视频之间的休眠时间：

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --sleep-interval 30
```

#### 场景 5：无 Cookies 模式（仅公开视频）

如果只下载公开视频，可以不使用 cookies：

```bash
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --cookies non_existent.txt
```

## 输出文件格式

### 文件命名

文件按以下格式命名：`{上传日期}_{视频ID}.json`

示例：
- `20240115_abcD1234efg.json`
- `20231225_xyzABC98765.json`

### JSON 结构

```json
{
  "video_info": {
    "id": "abcD1234efg",
    "title": "【直播回放】聊天记录",
    "duration": 7265,
    "upload_date": "20240115",
    "url": "https://www.youtube.com/watch?v=abcD1234efg"
  },
  "messages": [
    {
      "time_text": "1:23",
      "author": "观众名字",
      "author_id": "UCxxxxxxxxxxxxxxxxxxxx",
      "message": "消息内容",
      "offset_ms": 83000
    }
  ],
  "statistics": {
    "total_messages": 5432,
    "unique_authors": 876,
    "time_range": {
      "min": "0:00",
      "max": "2:01:05"
    }
  }
}
```

## 数据分析示例

### Python 分析

```python
import json
from collections import Counter

# 读取 JSON 文件
with open('chat_replays/20240115_abcD1234efg.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 基本信息
print(f"视频: {data['video_info']['title']}")
print(f"时长: {data['video_info']['duration']} 秒")
print(f"消息总数: {data['statistics']['total_messages']}")

# 最活跃的用户
authors = [msg['author'] for msg in data['messages']]
top_authors = Counter(authors).most_common(10)
print("\n最活跃用户:")
for author, count in top_authors:
    print(f"  {author}: {count} 条消息")

# 搜索关键词
keyword = "谢谢"
matches = [msg for msg in data['messages'] if keyword in msg['message']]
print(f"\n包含 '{keyword}' 的消息: {len(matches)} 条")
```

### 使用 jq 命令行工具

```bash
# 查看视频标题
jq '.video_info.title' chat_replays/20240115_*.json

# 统计总消息数
jq '.statistics.total_messages' chat_replays/20240115_*.json

# 提取所有用户名（去重）
jq -r '.messages[].author' chat_replays/20240115_*.json | sort -u

# 查找包含特定关键词的消息
jq '.messages[] | select(.message | contains("谢谢"))' chat_replays/20240115_*.json

# 统计每个时间段的消息数
jq '.messages | group_by(.time_text) | map({time: .[0].time_text, count: length})' \
  chat_replays/20240115_*.json
```

## 常见问题

### Q: 如何获取其他频道的直播？

A: 将频道的直播页面 URL 传递给 `--channel` 参数：

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@CHANNEL_NAME/streams"
```

### Q: 下载速度慢怎么办？

A: 这是正常的，因为：
1. 每个视频需要多次 API 请求获取完整聊天记录
2. 设置了休眠间隔避免请求过快
3. 包含了重试机制

可以通过减小 `--sleep-interval` 加快速度，但不建议设置过低。

### Q: 为什么有些视频下载不了？

A: 可能的原因：
1. 视频没有聊天功能（如上传的视频而非直播）
2. 聊天功能被禁用
3. 需要 cookies 才能访问（会员专属等）
4. 视频已被删除或设为私密

### Q: 如何中断并恢复下载？

A: 使用 `--incremental` 参数，然后：
1. 按 Ctrl+C 中断
2. 再次运行相同的命令
3. 程序会自动跳过已下载的文件

### Q: 输出文件太大怎么办？

A: JSON 文件可以：
1. 使用 gzip 压缩：`gzip chat_replays/*.json`
2. 提取需要的字段：使用 jq 过滤
3. 转换为数据库：导入到 SQLite/PostgreSQL 等

## 故障排除

### 错误：No module named 'requests'

**解决方案：**
```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
uv pip install -e .
```

### 错误：未找到 ytInitialData

**解决方案：**
1. 确保有有效的 cookies 文件
2. 检查视频是否可以正常访问
3. 尝试更新 cookies（重新导出）

### 错误：重试后仍无法获取

**解决方案：**
1. 检查网络连接
2. 增加重试间隔（代码中的 `time.sleep(3)`）
3. 检查 YouTube 是否限制了访问

## 高级技巧

### 1. 并行下载多个频道

创建一个脚本 `download_channels.sh`：

```bash
#!/bin/bash
channels=(
  "https://www.youtube.com/@channel1/streams"
  "https://www.youtube.com/@channel2/streams"
  "https://www.youtube.com/@channel3/streams"
)

for channel in "${channels[@]}"; do
  name=$(echo $channel | cut -d'@' -f2 | cut -d'/' -f1)
  python -m youtube_chat_downloader.cli \
    --channel "$channel" \
    --output-dir "chats_${name}" \
    --incremental \
    --sleep-interval 10
done
```

### 2. 定时自动下载

使用 cron 定时任务（Linux/Mac）：

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点运行
0 2 * * * cd /path/to/project && python -m youtube_chat_downloader.cli --incremental
```

### 3. 监控下载进度

使用 `tee` 保存日志：

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental 2>&1 | tee download.log
```

## 相关工具

- **旧版脚本**: `python youtubeChatdl.py <url>` - SQLite 输出
- **数据库查询**: `python query_example.py chatlog_xxx.db` - 查询 SQLite 数据
- **格式转换**: `python convert_db_to_json.py chatlog_xxx.db` - SQLite → JSON
- **测试工具**: `python test_cli.py` - 测试频道列表获取

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 技术支持

如遇到问题，请提供以下信息：
1. 错误信息的完整输出
2. 使用的命令
3. Python 版本（`python --version`）
4. 依赖版本（`uv pip list`）
