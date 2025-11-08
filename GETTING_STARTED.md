# 开始使用 YouTube 聊天回放下载器

## 5分钟快速上手

### 步骤 1: 安装依赖

```bash
# 进入项目目录
cd youtube-chat-downloader

# 激活虚拟环境（如果有）
source .venv/bin/activate

# 安装依赖
uv pip install -e .
```

### 步骤 2: 准备 Cookies（推荐）

1. 安装浏览器扩展 "Get cookies.txt LOCALLY"
2. 访问 YouTube 并登录
3. 导出 cookies.txt
4. 重命名为 `www.youtube.com_cookies.txt`
5. 放在项目根目录

> 💡 提示：公开视频可以不需要 cookies，但建议准备以访问更多内容

### 步骤 3: 运行你的第一个下载

**测试单个视频：**

```bash
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**下载 chenyifaer 频道的所有直播：**

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental
```

### 步骤 4: 查看结果

下载的文件保存在 `chat_replays/` 目录：

```bash
ls chat_replays/
# 输出: 20240115_abcD1234efg.json
```

查看 JSON 内容：

```bash
cat chat_replays/20240115_abcD1234efg.json | head -50
```

或使用 Python：

```python
import json

with open('chat_replays/20240115_abcD1234efg.json', 'r') as f:
    data = json.load(f)
    
print(f"视频: {data['video_info']['title']}")
print(f"消息数: {data['statistics']['total_messages']}")
```

## 常用场景

### 场景 1: 定期更新下载（增量模式）

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --incremental \
  --sleep-interval 10
```

- ✅ 自动跳过已下载的视频
- ✅ 可以随时中断（Ctrl+C）
- ✅ 下次运行会从中断处继续

### 场景 2: 下载其他频道

```bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@YOUR_CHANNEL/streams" \
  --output-dir your_channel_chats
```

### 场景 3: 批量处理多个频道

创建脚本 `download_all.sh`:

```bash
#!/bin/bash
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@channel1/streams" \
  --output-dir channel1 --incremental

python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@channel2/streams" \
  --output-dir channel2 --incremental
```

运行：
```bash
chmod +x download_all.sh
./download_all.sh
```

## 下一步

- 📖 阅读 [完整文档](README.md)
- 📚 查看 [使用指南](USAGE_GUIDE.md)
- 🔍 参考 [快速参考卡](QUICK_REFERENCE.md)
- 💡 查看 [使用示例](example_usage.sh)

## 需要帮助？

- 查看 [常见问题](USAGE_GUIDE.md#常见问题)
- 查看 [故障排除](USAGE_GUIDE.md#故障排除)
- 阅读 [实施总结](IMPLEMENTATION_SUMMARY.md)

## 完成！

现在你已经可以开始下载 YouTube 直播聊天回放了！🎉
