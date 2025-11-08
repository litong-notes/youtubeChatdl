# 修复 get_livestream_urls 函数获取不到直播视频列表的问题

## 问题描述

`get_livestream_urls` 函数无法获取到任何直播回放视频，返回空列表。

## 根本原因

在 `extract_flat=True` 模式下，yt-dlp 返回的视频条目中：
- **`was_live`** 字段的值是 `None`（不存在）
- **`live_status`** 字段的值是 `'was_live'`（字符串）

原代码检查 `entry.get('was_live')` 始终返回 `None`，条件判断失败，导致所有视频被跳过。

## 修复方案

将条件判断从：
```python
if entry and entry.get('was_live'):
```

改为：
```python
if entry and entry.get('live_status') == 'was_live':
```

## 验证结果

### 修复前
```
找到 0 个视频
```

### 修复后
```
找到 369 个直播视频
```

### 与 yt-dlp 命令行对比

命令：
```bash
yt-dlp --flat-playlist --match-filter "is_live" --print "%(webpage_url)s" \
  "https://www.youtube.com/@chenyifaer/streams" --cookies www.youtube.com_cookies.txt
```

结果：
- Python API: 369 个视频 ✓
- 命令行: 369 个视频 ✓
- 前10个视频顺序完全一致 ✓

## 技术细节

在 yt-dlp 的 flat extraction 模式下，`live_status` 字段可能的值包括：
- `'was_live'` - 过去的直播（直播回放）
- `'is_live'` - 正在直播
- `'is_upcoming'` - 即将直播
- `None` - 普通视频（非直播）

本项目的目标是下载直播回放的聊天记录，因此应该过滤 `live_status == 'was_live'` 的视频。

## 相关文件

- `youtube_chat_downloader/fetcher.py` - 修改了 `get_livestream_urls` 函数（第187行）

## 测试

运行测试脚本验证修复：
```bash
python test_cli.py
```

预期输出：
```
✅ 找到 369 个直播视频
前 5 个视频链接:
  1. https://www.youtube.com/watch?v=...
  2. https://www.youtube.com/watch?v=...
  ...
```
