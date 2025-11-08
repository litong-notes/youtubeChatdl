# YouTube 聊天回放下载器

一个用于下载 YouTube 直播聊天回放记录的 Python 工具脚本。

## 功能特点

- 下载 YouTube 视频的聊天回放记录
- 自动获取视频时长并智能停止
- 支持使用 Cookie 文件进行身份验证访问
- 时间戳标准化（过滤负偏移时间）
- 增量式 CSV 导出
- 自动去重处理
- 重试机制保证稳定性

## 技术架构

- **依赖库**: requests, yt-dlp, 正则表达式解析, 标准库辅助工具
- **架构**: 单文件过程式架构
- **核心功能**:
  - 获取页面 HTML
  - 提取 API 参数
  - 迭代 continuation tokens
  - 解析聊天消息
  - 处理重试逻辑

## 安装依赖

```bash
pip install requests yt-dlp
```

## 使用方法

```bash
python youtubeChatdl.py <youtube_url>
```

### 示例

```bash
python youtubeChatdl.py https://www.youtube.com/watch?v=VIDEO_ID
```

## Cookie 文件（可选）

如果需要访问受限制的视频聊天记录，可以在项目目录下放置 `www.youtube.com_cookies.txt` 文件。

该工具会自动使用 Cookie 文件进行身份验证。

## 输出格式

聊天记录将保存为 SQLite 数据库文件 `chatlog_<video_id>.db`，包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 自增主键 |
| time_text | TEXT | 时间戳文本（格式：M:SS 或 H:MM:SS） |
| author | TEXT | 用户名 |
| author_id | TEXT | YouTube 频道 ID（通常以 UC 开头） |
| message | TEXT | 消息内容 |
| offset_ms | INTEGER | 视频偏移时间（毫秒） |
| created_at | TIMESTAMP | 记录创建时间 |

### 查询示例

```sql
-- 查看所有消息
SELECT time_text, author, message FROM chat_messages ORDER BY offset_ms;

-- 查看特定用户的所有消息
SELECT time_text, message FROM chat_messages WHERE author_id = 'UC...' ORDER BY offset_ms;

-- 统计每个用户的消息数
SELECT author, COUNT(*) as msg_count FROM chat_messages GROUP BY author_id ORDER BY msg_count DESC;
```

## 工作流程

1. 使用 yt-dlp 获取视频时长和视频 ID
2. 获取页面 HTML 并提取 API 密钥和 ytInitialData
3. 查找初始 continuation token
4. 初始化 SQLite 数据库
5. 循环获取聊天消息：
   - 调用 YouTube API 获取聊天数据
   - 解析消息（包括负时间戳消息）
   - 批量插入 SQLite 数据库
   - 提取下一个 continuation token
6. 显示统计信息

## 保留的消息字段

在聊天回放消息解析逻辑中，保留并存储到数据库的字段包括：

- **time_text**: 时间戳文本（格式：M:SS 或 H:MM:SS）
- **author**: 用户名（来自 authorName.simpleText）
- **author_id**: YouTube 频道 ID（来自 authorExternalChannelId，通常以 UC 开头）
- **message**: 消息内容（来自 message.runs[].text）
- **offset_ms**: 视频偏移时间（毫秒，来自 videoOffsetTimeMsec）

支持的消息类型：
- `liveChatTextMessageRenderer` - 普通文本消息
- `liveChatPaidMessageRenderer` - 付费消息（Super Chat）

## 注意事项

- 脚本会保留所有消息，包括负时间戳的消息（直播开始前的等待消息）
- 最多迭代 3000 次防止无限循环
- 当达到视频时长时自动停止
- 包含重试机制处理网络错误
- 数据库文件按视频 ID 命名，格式为 `chatlog_<video_id>.db`
- 使用索引优化查询性能（offset_ms 和 author_id）

## 数据库查询工具

项目包含一个数据库查询示例脚本 `query_example.py`，提供以下功能：

```bash
python query_example.py chatlog_<video_id>.db
```

### 功能特性

- 📊 显示数据库统计信息（总消息数、用户数、时间范围）
- 🏆 TOP 用户排行榜
- 💬 显示最近消息
- 🔍 关键词搜索
- 👤 查看指定用户的所有消息
- ⏰ 按时间范围查询消息
- 📤 导出为 CSV 格式

## 许可证

本项目为开源工具，请遵守 YouTube 使用条款。
