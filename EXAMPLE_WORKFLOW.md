# 完整工作流程示例

本文档展示如何使用 YouTube 聊天回放下载器的完整工作流程。

## 场景 1: 首次使用 - 下载并导入数据库

### 步骤 1: 准备环境

```bash
# 激活虚拟环境
source .venv/bin/activate

# 确认安装正确
python -m youtube_chat_downloader.cli --help
```

### 步骤 2: 下载聊天回放并自动导入数据库

```bash
# 一次完成下载和导入
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt \
  --incremental \
  --auto-import-db \
  --db-path chenyifaer_chat.db \
  --sleep-interval 10
```

这个命令会：
1. 获取频道的所有直播视频
2. 逐个下载聊天回放到 `chat_replays/` 目录
3. 自动将JSON导入到 `chenyifaer_chat.db` 数据库
4. 跳过已存在的视频（增量模式）
5. 每个视频间休眠10秒

### 步骤 3: 查看数据库统计

```bash
python -m youtube_chat_downloader.import_to_db \
  --db-path chenyifaer_chat.db \
  --stats
```

输出示例：
```
============================================================
📊 数据库统计信息
============================================================
📺 视频总数: 25
💬 消息总数: 123,456
👤 独特作者: 5,678
💾 数据库大小: 45.67 MB
📅 视频日期范围: 20231201 ~ 20240115
============================================================
```

## 场景 2: 定期更新 - 增量下载新视频

### 每天/每周运行

```bash
#!/bin/bash
# update_chats.sh - 定期更新脚本

cd /path/to/youtube-chat-downloader
source .venv/bin/activate

# 下载新视频并自动导入数据库
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --auto-import-db \
  --db-path chenyifaer_chat.db \
  --sleep-interval 10

# 显示更新后的统计
python -m youtube_chat_downloader.import_to_db \
  --db-path chenyifaer_chat.db \
  --stats

echo "更新完成: $(date)"
```

设置 cron 任务（每天凌晨2点运行）：
```bash
0 2 * * * /path/to/update_chats.sh >> /path/to/update.log 2>&1
```

## 场景 3: 多频道管理

### 下载多个频道

```bash
#!/bin/bash
# download_multiple_channels.sh

CHANNELS=(
  "https://www.youtube.com/@chenyifaer/streams"
  "https://www.youtube.com/@channel2/streams"
  "https://www.youtube.com/@channel3/streams"
)

for channel in "${CHANNELS[@]}"; do
  # 提取频道名
  channel_name=$(echo $channel | cut -d'@' -f2 | cut -d'/' -f1)
  
  echo "=========================================="
  echo "处理频道: $channel_name"
  echo "=========================================="
  
  python -m youtube_chat_downloader.cli \
    --channel "$channel" \
    --output-dir "chat_replays_${channel_name}" \
    --incremental \
    --auto-import-db \
    --db-path "${channel_name}_chat.db" \
    --sleep-interval 15
  
  echo ""
done

echo "所有频道处理完成！"
```

## 场景 4: 仅下载JSON，稍后导入

有时你可能想先下载所有JSON，稍后再导入数据库。

### 步骤 1: 仅下载

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --sleep-interval 10
```

### 步骤 2: 稍后批量导入

```bash
# 导入所有JSON到数据库
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path chenyifaer_chat.db \
  --incremental
```

## 场景 5: 数据分析工作流

### 完整的分析流程

```bash
# 1. 更新数据
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --auto-import-db

# 2. 导出统计报告
python << 'EOF'
import sqlite3
import csv
from datetime import datetime

conn = sqlite3.connect('chat_database.db')
cursor = conn.cursor()

# 生成报告
report_date = datetime.now().strftime('%Y%m%d')
report_file = f'chat_report_{report_date}.csv'

with open(report_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['视频ID', '标题', '日期', '消息数', '用户数'])
    
    cursor.execute('''
        SELECT video_id, title, upload_date, total_messages, unique_authors
        FROM videos
        ORDER BY upload_date DESC
    ''')
    
    writer.writerows(cursor.fetchall())

print(f"报告已生成: {report_file}")
conn.close()
EOF

# 3. 查看报告
cat chat_report_*.csv | head -20
```

## 场景 6: 单个视频快速下载

```bash
# 快速下载单个视频
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --auto-import-db

# 查询该视频的消息
python << 'EOF'
import sqlite3

conn = sqlite3.connect('chat_database.db')
cursor = conn.cursor()

video_id = 'VIDEO_ID'

cursor.execute('''
    SELECT time_text, author, message
    FROM chat_messages
    WHERE video_id = ?
    ORDER BY offset_ms
    LIMIT 100
''', (video_id,))

print(f"视频 {video_id} 的前100条消息:\n")
for time_text, author, message in cursor.fetchall():
    print(f"[{time_text}] {author}: {message}")

conn.close()
EOF
```

## 场景 7: 数据迁移 - 从旧版SQLite到新数据库

如果你之前使用旧版脚本生成了SQLite数据库：

```bash
# 1. 转换旧数据库为JSON
python convert_db_to_json.py chatlog_video1.db output1.json
python convert_db_to_json.py chatlog_video2.db output2.json

# 2. 将JSON导入到新数据库
mkdir old_chats
mv output*.json old_chats/

python -m youtube_chat_downloader.import_to_db \
  --json-dir old_chats \
  --db-path new_unified_chat.db
```

## 场景 8: 备份和恢复

### 备份

```bash
# 备份JSON文件
tar -czf chat_replays_backup_$(date +%Y%m%d).tar.gz chat_replays/

# 备份数据库
cp chat_database.db chat_database_backup_$(date +%Y%m%d).db

# 或使用SQLite备份
sqlite3 chat_database.db ".backup chat_database_backup.db"
```

### 恢复

```bash
# 从JSON恢复到新数据库
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path recovered_chat.db

# 或直接恢复数据库文件
cp chat_database_backup_20240115.db chat_database.db
```

## 场景 9: 数据清理和维护

```bash
# 查看数据库大小
ls -lh chat_database.db

# 优化数据库（减少文件大小）
sqlite3 chat_database.db "VACUUM;"

# 删除特定日期之前的数据
python << 'EOF'
import sqlite3

conn = sqlite3.connect('chat_database.db')
cursor = conn.cursor()

# 删除2023年之前的数据
cursor.execute('DELETE FROM chat_messages WHERE video_id IN (SELECT video_id FROM videos WHERE upload_date < "20230101")')
cursor.execute('DELETE FROM videos WHERE upload_date < "20230101"')

conn.commit()
print(f"已删除 {cursor.rowcount} 条记录")
conn.close()
EOF

# 重新优化
sqlite3 chat_database.db "VACUUM;"
```

## 场景 10: 自动化监控脚本

```bash
#!/bin/bash
# monitor_and_update.sh - 监控并自动更新

LOG_FILE="monitor.log"
DB_PATH="chat_database.db"
ERROR_EMAIL="your@email.com"

echo "========================================" >> $LOG_FILE
echo "开始更新: $(date)" >> $LOG_FILE

# 更新数据
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --auto-import-db \
  --db-path $DB_PATH 2>&1 | tee -a $LOG_FILE

# 检查错误
if [ ${PIPESTATUS[0]} -ne 0 ]; then
  echo "错误：更新失败" >> $LOG_FILE
  echo "更新失败，请查看日志" | mail -s "聊天下载器错误" $ERROR_EMAIL
  exit 1
fi

# 获取统计信息
python -m youtube_chat_downloader.import_to_db \
  --db-path $DB_PATH \
  --stats >> $LOG_FILE

echo "完成更新: $(date)" >> $LOG_FILE
echo "========================================" >> $LOG_FILE
```

## 性能优化建议

### 对于大量视频

```bash
# 增加休眠间隔避免请求过快
python -m youtube_chat_downloader.cli \
  --channel "CHANNEL_URL" \
  --sleep-interval 30 \
  --incremental \
  --auto-import-db
```

### 对于大型数据库

```python
# 定期优化数据库
import sqlite3

conn = sqlite3.connect('chat_database.db')

# 分析表统计
conn.execute('ANALYZE')

# 清理碎片
conn.execute('VACUUM')

# 重建索引
conn.execute('REINDEX')

conn.close()
```

## 故障排查

### 下载中断

```bash
# 增量模式会自动跳过已下载的文件
python -m youtube_chat_downloader.cli \
  --channel "CHANNEL_URL" \
  --incremental \
  --auto-import-db
```

### 数据库损坏

```bash
# 检查数据库完整性
sqlite3 chat_database.db "PRAGMA integrity_check;"

# 如果损坏，从JSON重建
rm chat_database.db
python -m youtube_chat_downloader.import_to_db \
  --json-dir chat_replays \
  --db-path chat_database.db
```

### 磁盘空间不足

```bash
# 查看空间使用
du -sh chat_replays/
du -sh *.db

# 清理旧JSON（已导入数据库）
# 注意：确保已成功导入后再删除
rm chat_replays/*.json

# 或压缩JSON
tar -czf chat_replays_archive.tar.gz chat_replays/
rm -rf chat_replays/
```

## 总结

关键要点：
1. 使用 `--incremental` 避免重复下载
2. 使用 `--auto-import-db` 自动导入数据库
3. 定期备份 JSON 和数据库文件
4. 使用合理的 `--sleep-interval` 避免请求过快
5. 定期运行 `VACUUM` 优化数据库
6. 监控磁盘空间使用情况

根据你的需求选择合适的工作流程，享受数据分析的乐趣！
