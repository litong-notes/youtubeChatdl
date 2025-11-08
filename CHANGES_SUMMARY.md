# 更改总结 / Changes Summary

## 完成的任务 / Completed Tasks

### 1. 添加中文 README.md
- ✅ 创建了完整的中文 README.md 文档
- 包含功能特点、技术架构、安装说明、使用方法等
- 详细说明了工作流程和注意事项

### 2. 翻译日语为中文
- ✅ 将代码中所有日语注释和字符串翻译为中文
- 翻译内容包括：
  - 函数文档字符串
  - 代码注释
  - 打印输出的消息文本
  - 错误提示信息

### 3. 保留的回放消息字段
代码实现逻辑（parse_messages函数）中保留的4个核心字段：

#### time_text (时间戳文本)
- **类型**: `str`
- **格式**: `"M:SS"` 或 `"H:MM:SS"`
- **来源**: `videoOffsetTimeMsec` 或 `timestampText.simpleText`
- **示例**: `"0:15"`, `"1:30:45"`
- **说明**: 消息在视频中的时间位置

#### author (用户名)
- **类型**: `str`
- **来源**: `authorName.simpleText`
- **处理**: 自动去除首尾空格
- **说明**: 发送聊天消息的用户名称

#### msg (消息内容)
- **类型**: `str`
- **来源**: `message.runs[]` 数组中所有 `text` 字段的拼接
- **处理**: 拼接、去空格、删除非法字符
- **说明**: 聊天消息的实际文本内容

#### offset (偏移时间)
- **类型**: `int`
- **单位**: 毫秒 (milliseconds)
- **来源**: `videoOffsetTimeMsec`
- **用途**: 用于排序和时长计算

### 4. 支持的消息类型
- `liveChatTextMessageRenderer` - 普通文本消息
- `liveChatPaidMessageRenderer` - 付费消息（Super Chat）

### 5. CSV 输出格式
```csv
time,user,comment
0:15,用户名,消息内容
0:30,另一个用户,另一条消息
```

### 6. 过滤规则
代码会跳过以下消息：
- 空用户名的消息
- 空消息内容
- 负时间戳的消息

## 文件变更清单 / File Changes

### 新增文件 / New Files
1. `README.md` - 中文项目说明文档
2. `回放消息字段说明.md` - 详细的字段说明文档
3. `.gitignore` - Git 忽略文件配置
4. `CHANGES_SUMMARY.md` - 本文件

### 修改文件 / Modified Files
1. `youtubeChatdl.py` - 将所有日语翻译为中文

## 韩语检查 / Korean Check
- ✅ 代码中未发现韩语内容

## 备注 / Notes
- 所有翻译保持了原意和代码功能不变
- 添加了合适的 .gitignore 文件
- 创建了详细的中文文档

---

## 最新更改 (2024) / Latest Changes

### 数据存储改进
- ✅ **使用 SQLite 数据库替代 CSV 文件**
  - 数据库文件命名格式：`chatlog_<video_id>.db`
  - 结构化存储，支持复杂查询
  - 添加索引优化查询性能

### 新增字段
- ✅ **添加 author_id 字段**
  - 来源：`authorExternalChannelId`
  - 存储用户的 YouTube 频道 ID（通常以 UC 开头）
  - 用于唯一标识用户

### 过滤逻辑调整
- ✅ **移除负时间戳过滤**
  - 现在保留所有消息，包括负时间戳消息
  - 可以记录直播开始前的等待聊天

### 数据库架构
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time_text TEXT,
    author TEXT,
    author_id TEXT,
    message TEXT,
    offset_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_offset ON chat_messages(offset_ms);
CREATE INDEX idx_author_id ON chat_messages(author_id);
```

### 统计功能
- 自动显示总消息数
- 自动显示独特用户数
- 自动显示时间范围
