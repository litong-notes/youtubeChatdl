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

聊天记录将保存为 `chatlog.csv` 文件，格式如下：

```csv
time,user,comment
0:15,用户名1,消息内容1
0:30,用户名2,消息内容2
```

## 工作流程

1. 使用 yt-dlp 获取视频时长
2. 获取页面 HTML 并提取 API 密钥和 ytInitialData
3. 查找初始 continuation token
4. 循环获取聊天消息：
   - 调用 YouTube API 获取聊天数据
   - 解析消息（过滤负时间戳）
   - 增量写入 CSV 文件
   - 提取下一个 continuation token
5. 最后进行去重处理

## 保留的消息字段

在聊天回放消息解析逻辑中，保留的字段包括：

- **time_text**: 时间戳（格式：M:SS 或 H:MM:SS）
- **author**: 用户名（来自 authorName.simpleText）
- **msg**: 消息内容（来自 message.runs[].text）
- **offset**: 视频偏移时间（毫秒，来自 videoOffsetTimeMsec）

支持的消息类型：
- `liveChatTextMessageRenderer` - 普通文本消息
- `liveChatPaidMessageRenderer` - 付费消息（Super Chat）

## 注意事项

- 脚本会自动跳过负时间戳的消息
- 最多迭代 3000 次防止无限循环
- 当达到视频时长时自动停止
- 包含重试机制处理网络错误
- 最后会自动删除重复的聊天记录

## 许可证

本项目为开源工具，请遵守 YouTube 使用条款。
