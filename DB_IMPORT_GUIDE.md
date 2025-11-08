# JSON 导入到 SQLite 数据库使用指南

## 概述

新增功能允许将下载的 JSON 聊天回放文件导入到 SQLite 数据库，便于查询和分析。

## 功能特点

- ✅ 批量导入 JSON 文件到 SQLite 数据库
- ✅ 增量导入：自动跳过已存在的视频
- ✅ 完整的视频信息和消息存储
- ✅ 优化的索引提升查询性能
- ✅ 数据库统计信息查看

## 数据库结构

### 表结构

#### videos 表
存储视频元数据

| 字段 | 类型 | 说明 |
|------|------|------|
| video_id | TEXT | 视频ID（主键）|
| title | TEXT | 视频标题 |
| duration | INTEGER | 视频时长（秒）|
| upload_date | TEXT | 上传日期 |
| url | TEXT | 视频URL |
| total_messages | INTEGER | 消息总数 |
| unique_authors | INTEGER | 独特作者数 |
| time_range_min | TEXT | 时间范围最小值 |
| time_range_max | TEXT | 时间范围最大值 |
| imported_at | TIMESTAMP | 首次导入时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### chat_messages 表
存储聊天消息

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增主键 |
| video_id | TEXT | 视频ID（外键）|
| time_text | TEXT | 时间文本（如 "1:23"）|
| author | TEXT | 作者名称 |
| author_id | TEXT | 作者频道ID |
| message | TEXT | 消息内容 |
| offset_ms | INTEGER | 视频偏移时间（毫秒）|
| created_at | TIMESTAMP | 创建时间 |

### 索引

- `idx_video_id`: 视频ID索引
- `idx_offset`: 消息时间偏移索引
- `idx_author_id`: 作者ID索引
- `idx_video_upload_date`: 视频上传日期索引

## 使用方法

### 方法 1: 独立导入命令

使用专门的导入命令：

```bash
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path chat_database.db \
  --incremental
```

#### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--json-dir` | JSON文件目录 | chat_replays |
| `--db-path` | 数据库路径 | chat_database.db |
| `--incremental` | 增量模式（跳过已存在）| 关闭 |
| `--stats` | 仅显示统计信息 | 关闭 |
| `--quiet` | 安静模式 | 关闭 |

### 方法 2: 下载时自动导入

在下载时添加 `--auto-import-db` 参数：

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --auto-import-db \
  --db-path chat_database.db
```

这会在下载完成后自动将 JSON 文件导入到数据库。

## 使用示例

### 示例 1: 首次导入所有 JSON 文件

```bash
# 导入 chat_replays 目录下的所有 JSON
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path my_chat.db
```

### 示例 2: 增量导入（推荐）

```bash
# 只导入新的文件，跳过已存在的视频
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path my_chat.db \
  --incremental
```

### 示例 3: 查看数据库统计

```bash
# 不导入，仅查看数据库信息
python -m youtube_chat_downloader.import_to_db \
  --db-path my_chat.db \
  --stats
```

输出示例：
```
============================================================
📊 数据库统计信息
============================================================
📺 视频总数: 15
💬 消息总数: 45,678
👤 独特作者: 1,234
💾 数据库大小: 12.45 MB
📅 视频日期范围: 20240101 ~ 20240115
============================================================
```

### 示例 4: 下载并自动导入

```bash
# 下载新视频并自动导入数据库
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --auto-import-db
```

### 示例 5: 安静模式批量导入

```bash
# 减少输出信息
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --incremental \
  --quiet
```

## 数据库查询

### 使用 Python 查询

```python
import sqlite3

conn = sqlite3.connect('chat_database.db')
cursor = conn.cursor()

# 查询所有视频
cursor.execute('SELECT video_id, title, total_messages FROM videos')
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} ({row[2]} 条消息)")

# 查询特定视频的消息
cursor.execute('''
    SELECT time_text, author, message 
    FROM chat_messages 
    WHERE video_id = ? 
    ORDER BY offset_ms
''', ('VIDEO_ID',))

for time_text, author, message in cursor.fetchall():
    print(f"[{time_text}] {author}: {message}")

# 统计最活跃的用户
cursor.execute('''
    SELECT author, COUNT(*) as count 
    FROM chat_messages 
    GROUP BY author_id 
    ORDER BY count DESC 
    LIMIT 10
''')

print("最活跃用户:")
for author, count in cursor.fetchall():
    print(f"  {author}: {count} 条消息")

conn.close()
```

### 使用 SQL 查询

```sql
-- 查看所有视频
SELECT video_id, title, total_messages, upload_date 
FROM videos 
ORDER BY upload_date DESC;

-- 查看特定视频的消息
SELECT time_text, author, message 
FROM chat_messages 
WHERE video_id = 'VIDEO_ID' 
ORDER BY offset_ms;

-- 搜索包含关键词的消息
SELECT v.title, cm.time_text, cm.author, cm.message
FROM chat_messages cm
JOIN videos v ON cm.video_id = v.video_id
WHERE cm.message LIKE '%关键词%';

-- 统计每个视频的消息数
SELECT v.video_id, v.title, COUNT(cm.id) as msg_count
FROM videos v
LEFT JOIN chat_messages cm ON v.video_id = cm.video_id
GROUP BY v.video_id
ORDER BY msg_count DESC;

-- 查找特定用户的所有消息
SELECT v.title, cm.time_text, cm.message
FROM chat_messages cm
JOIN videos v ON cm.video_id = v.video_id
WHERE cm.author_id = 'UC...'
ORDER BY v.upload_date, cm.offset_ms;

-- 统计每天的消息数
SELECT v.upload_date, SUM(v.total_messages) as daily_total
FROM videos v
GROUP BY v.upload_date
ORDER BY v.upload_date;

-- 查找最活跃的用户
SELECT author, author_id, COUNT(*) as msg_count
FROM chat_messages
WHERE author_id != ''
GROUP BY author_id
ORDER BY msg_count DESC
LIMIT 20;
```

## 工作流程

### 推荐工作流程

```bash
# 1. 下载新的直播回放（增量模式）
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --output-dir chat_replays

# 2. 导入新的 JSON 到数据库（增量模式）
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path chat_database.db \
  --incremental

# 3. 查看数据库统计
python -m youtube_chat_downloader.import_to_db \
  --db-path chat_database.db \
  --stats
```

### 一步完成（推荐）

```bash
# 下载并自动导入
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --auto-import-db \
  --db-path chat_database.db
```

## 数据分析示例

### Python 数据分析

```python
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 连接数据库
conn = sqlite3.connect('chat_database.db')

# 读取数据到 DataFrame
df_videos = pd.read_sql_query('SELECT * FROM videos', conn)
df_messages = pd.read_sql_query('SELECT * FROM chat_messages', conn)

# 视频消息数分布
print(df_videos[['title', 'total_messages']].sort_values('total_messages', ascending=False))

# 最活跃用户
top_users = df_messages['author'].value_counts().head(10)
print("最活跃用户:")
print(top_users)

# 绘图
top_users.plot(kind='bar', title='最活跃用户 Top 10')
plt.tight_layout()
plt.savefig('top_users.png')

conn.close()
```

## 常见问题

### Q: 增量导入和非增量导入有什么区别？

A: 
- **增量模式** (`--incremental`): 跳过数据库中已存在的视频，只导入新视频
- **非增量模式**: 如果视频已存在，会删除旧数据并重新导入

推荐使用增量模式以提高效率。

### Q: 如何重新导入某个视频？

A: 有两种方法：
1. 从数据库中删除该视频：
   ```sql
   DELETE FROM chat_messages WHERE video_id = 'VIDEO_ID';
   DELETE FROM videos WHERE video_id = 'VIDEO_ID';
   ```
2. 使用非增量模式重新导入整个目录

### Q: 数据库文件会很大吗？

A: 取决于视频数量和消息数。一般来说：
- 每个视频约 0.5-2 MB（取决于消息数）
- 100 个视频约 50-200 MB
- 建议定期备份数据库文件

### Q: 可以导入多个目录吗？

A: 可以多次运行导入命令，指定不同的 `--json-dir`，所有数据会合并到同一个数据库。

### Q: 如何迁移到新数据库？

A: 
```bash
# 导出所有 JSON 到新数据库
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path new_database.db
```

## 性能优化

### 大量数据导入

对于大量 JSON 文件的导入，建议：

1. 使用增量模式减少重复导入
2. 批量处理而不是单个文件导入
3. 定期运行 VACUUM 优化数据库：
   ```python
   import sqlite3
   conn = sqlite3.connect('chat_database.db')
   conn.execute('VACUUM')
   conn.close()
   ```

### 查询优化

数据库已创建了必要的索引，但对于复杂查询，可以：

1. 使用 `EXPLAIN QUERY PLAN` 分析查询
2. 考虑创建额外的复合索引
3. 使用视图简化常用查询

## 备份建议

```bash
# 备份数据库
cp chat_database.db chat_database_backup_$(date +%Y%m%d).db

# 或使用 SQLite 备份命令
sqlite3 chat_database.db ".backup chat_database_backup.db"
```

## 相关工具

- `query_example.py`: 旧版 SQLite 数据库查询示例（单视频）
- `convert_db_to_json.py`: SQLite → JSON 转换工具

## 总结

通过将 JSON 文件导入到 SQLite 数据库：
- ✅ 统一管理所有聊天数据
- ✅ 快速查询和分析
- ✅ 支持复杂的 SQL 查询
- ✅ 便于数据备份和迁移
- ✅ 可以与各种数据分析工具集成

建议工作流程：下载时使用 `--auto-import-db` 自动导入，或定期运行导入命令更新数据库。
