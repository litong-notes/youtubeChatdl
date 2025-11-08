#!/bin/bash
# YouTube 聊天回放下载器使用示例

# 1. 下载单个视频（测试）
echo "示例 1: 下载单个视频"
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --cookies www.youtube.com_cookies.txt \
  --output-dir chat_replays

# 2. 批量下载频道所有直播（基础）
echo "示例 2: 批量下载 chenyifaer 频道"
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt

# 3. 批量下载 + 增量模式 + 休眠间隔
echo "示例 3: 批量下载（增量模式 + 10秒休眠）"
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt \
  --incremental \
  --sleep-interval 10 \
  --output-dir chat_replays

# 4. 自定义输出目录
echo "示例 4: 自定义输出目录"
python -m youtube_chat_downloader.cli \
  --channel "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt \
  --output-dir /path/to/output

# 5. 不使用 cookies（公开视频）
echo "示例 5: 不使用 cookies"
python -m youtube_chat_downloader.cli \
  --url "https://www.youtube.com/watch?v=PUBLIC_VIDEO_ID" \
  --cookies non_existent_file.txt
