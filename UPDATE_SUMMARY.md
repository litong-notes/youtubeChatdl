# 更新总结 - SQLite 数据库存储

## 概述

本次更新将 YouTube 聊天下载器从 CSV 文件存储升级为 SQLite 数据库存储，并添加了用户频道 ID 字段，同时移除了负时间戳过滤。

## 主要变更

### 1. 存储方式升级

**之前 (CSV)**:
```csv
time,user,comment
0:15,用户名,消息内容
```

**现在 (SQLite)**:
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time_text TEXT,
    author TEXT,
    author_id TEXT,           -- 新增字段
    message TEXT,
    offset_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. 新增字段：author_id

- **字段名**: `author_id`
- **数据来源**: `authorExternalChannelId`
- **数据类型**: TEXT
- **说明**: YouTube 频道的唯一标识符
- **格式**: 通常以 "UC" 开头的字符串
- **示例**: `"UCxxxxxxxxxxxxxxxxxxxxx"`
- **用途**: 
  - 唯一标识用户
  - 跨视频追踪同一用户
  - 统计用户活跃度

### 3. 过滤逻辑调整

**之前**: 
- ❌ 跳过 `offset_ms < 0` 的消息
- ❌ 跳过 `time_text` 以 "-" 开头的消息

**现在**: 
- ✅ 保留所有消息，包括负时间戳消息
- ✅ 可以记录直播开始前的等待聊天

### 4. 数据库优化

**索引**:
- `idx_offset`: 在 `offset_ms` 字段上，优化时间排序查询
- `idx_author_id`: 在 `author_id` 字段上，优化用户查询

**统计功能**:
- 自动统计总消息数
- 自动统计独特用户数
- 自动显示时间范围

## 保留的字段对照表

| 字段名 | 类型 | 来源 | 说明 | 变更 |
|--------|------|------|------|------|
| id | INTEGER | 自增 | 主键 | 新增 |
| time_text | TEXT | videoOffsetTimeMsec / timestampText | 时间戳文本 | 无 |
| author | TEXT | authorName.simpleText | 用户名 | 无 |
| author_id | TEXT | authorExternalChannelId | 频道ID | **新增** |
| message | TEXT | message.runs[].text | 消息内容 | 重命名 (原msg) |
| offset_ms | INTEGER | videoOffsetTimeMsec | 偏移时间 | 重命名 (原offset) |
| created_at | TIMESTAMP | CURRENT_TIMESTAMP | 记录创建时间 | 新增 |

## 文件变更

### 修改的文件

1. **youtubeChatdl.py**
   - 导入 `sqlite3` 模块
   - 添加 `init_database()` 函数
   - 修改 `parse_messages()` 函数，添加 `author_id` 提取
   - 移除负时间戳过滤逻辑
   - 修改 `main()` 函数，使用 SQLite 存储
   - 添加统计信息显示

2. **.gitignore**
   - 添加 `*.db`, `*.sqlite`, `*.sqlite3` 忽略规则

3. **README.md**
   - 更新输出格式说明
   - 添加 SQL 查询示例
   - 更新工作流程说明
   - 更新保留字段说明
   - 更新注意事项
   - 添加查询工具说明

4. **CHANGES_SUMMARY.md**
   - 添加最新更改章节
   - 记录数据库架构

5. **回放消息字段说明.md**
   - 更新字段列表（添加 author_id）
   - 更新过滤规则说明
   - 添加数据库查询示例
   - 添加数据库索引说明

### 新增的文件

1. **query_example.py**
   - 数据库查询工具脚本
   - 功能：统计、TOP用户、搜索、导出等

## 代码示例

### 提取 author_id

```python
# 在 parse_messages() 函数中
author_id = r.get("authorExternalChannelId", "")
messages.append((time_text, author, author_id, msg, offset))
```

### 数据库插入

```python
cursor.execute('''
    INSERT INTO chat_messages (time_text, author, author_id, message, offset_ms)
    VALUES (?, ?, ?, ?, ?)
''', (time_text, author, author_id, msg, offset))
```

### 查询示例

```sql
-- 查看特定用户的所有消息
SELECT time_text, message FROM chat_messages 
WHERE author_id = 'UCxxxxxxxxxxxxxxxxxxxxx' 
ORDER BY offset_ms;

-- 统计用户活跃度
SELECT author, author_id, COUNT(*) as count 
FROM chat_messages 
GROUP BY author_id 
ORDER BY count DESC;
```

## 使用方法

### 下载聊天记录

```bash
python youtubeChatdl.py https://www.youtube.com/watch?v=VIDEO_ID
```

输出文件：`chatlog_VIDEO_ID.db`

### 查询数据库

```bash
python query_example.py chatlog_VIDEO_ID.db
```

### 手动查询

```bash
sqlite3 chatlog_VIDEO_ID.db

# 在 SQLite 命令行中
SELECT * FROM chat_messages LIMIT 10;
SELECT COUNT(*) FROM chat_messages;
SELECT DISTINCT author_id FROM chat_messages;
```

## 兼容性说明

- ✅ 保留了所有原有功能
- ✅ 数据结构更加规范和可查询
- ✅ 向后兼容：可使用 query_example.py 导出为 CSV
- ⚠️ 输出格式从 CSV 改为 SQLite（不向后兼容）

## 性能改进

1. **索引优化**: 通过索引加速查询
2. **批量提交**: 使用事务批量插入数据
3. **结构化存储**: 支持复杂查询和统计

## 测试建议

1. 测试正常时间戳消息的存储
2. 测试负时间戳消息的存储
3. 验证 author_id 正确提取
4. 测试数据库查询工具
5. 测试统计功能

## 已知限制

1. author_id 可能为空（某些消息类型）
2. 数据库文件需要足够的磁盘空间
3. 长时间直播可能产生大型数据库文件

## 未来改进建议

1. 添加消息类型字段（text/superchat）
2. 添加消息金额字段（Super Chat）
3. 支持断点续传
4. 添加数据去重逻辑
5. 支持多线程下载

---

**更新日期**: 2024-11-08  
**版本**: 2.0  
**主要改进**: SQLite 存储 + author_id 字段
