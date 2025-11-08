# Bug 修复总结 - get_livestream_urls 无法获取直播视频列表

## Issue

`get_livestream_urls()` 函数无法获取到任何直播回放视频，返回空列表（0个视频），而 yt-dlp 命令行工具能正常获取到369个视频。

## 根本原因

在使用 `extract_flat=True` 模式时，yt-dlp 返回的视频条目中的字段与非 flat 模式不同：

**问题代码（修复前）:**
```python
if entry and entry.get('was_live'):  # was_live 字段在 flat 模式下是 None
    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
    urls.append(video_url)
```

在 flat extraction 模式下：
- `was_live` 字段 = `None`（不存在）
- `is_live` 字段 = `None`（不存在）
- `live_status` 字段 = `'was_live'`（字符串，存在）

因此 `entry.get('was_live')` 始终返回 `None`，条件判断失败，所有视频被跳过。

## 解决方案

修改条件判断，检查 `live_status` 字段而不是 `was_live` 字段：

**修复代码（修复后）:**
```python
if entry and entry.get('live_status') == 'was_live':  # 正确检查 live_status 字段
    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
    urls.append(video_url)
```

## 技术细节

### yt-dlp flat extraction 模式下的 live_status 值

- `'was_live'` - 过去的直播（直播回放）✅ 我们需要的
- `'is_live'` - 正在直播
- `'is_upcoming'` - 即将直播
- `None` - 普通视频（非直播）

### 对照的 yt-dlp 命令

```bash
yt-dlp --flat-playlist --match-filter "is_live" \
  --print "%(webpage_url)s" \
  "https://www.youtube.com/@chenyifaer/streams" \
  --cookies www.youtube.com_cookies.txt
```

## 修改的文件

### youtube_chat_downloader/fetcher.py

**位置**: 第 187 行

**修改前**:
```python
if entry and entry.get('was_live'):
```

**修改后**:
```python
if entry and entry.get('live_status') == 'was_live':
```

## 验证结果

### 修复前
```
✅ 找到 0 个直播视频  ❌ 错误
```

### 修复后
```
✅ 找到 369 个直播视频  ✅ 正确
```

### 与命令行对比
| 项目 | Python API | yt-dlp 命令行 | 状态 |
|-----|-----------|--------------|-----|
| 视频数量 | 369 | 369 | ✅ 一致 |
| 前10个视频 | 匹配 | 匹配 | ✅ 一致 |
| 视频顺序 | 一致 | 一致 | ✅ 正确 |

## 测试

### 运行单元测试
```bash
python test_cli.py
```

预期输出：
```
✅ 找到 369 个直播视频
前 5 个视频链接:
  1. https://www.youtube.com/watch?v=c4xErt69Gkk
  2. https://www.youtube.com/watch?v=bLEThN1LSsM
  ...
```

### 验证脚本
创建并运行验证脚本 `/tmp/final_verification.py` 确认修复：
```
✅ 修复成功！get_livestream_urls 现在与 yt-dlp 命令行行为一致
```

## 影响范围

- ✅ 修复了批量下载功能（从频道获取所有直播）
- ✅ 不影响单个视频下载功能
- ✅ 不影响聊天消息解析功能
- ✅ 完全向后兼容

## 相关文档更新

以下文档已更新以反映正确的实现：
- `IMPLEMENTATION_SUMMARY.md` - 更新了 `get_livestream_urls()` 的实现说明
- `FIX_LIVESTREAM_URLS.md` - 新增详细的修复文档

## 总结

这是一个关键的 bug 修复，使得频道批量下载功能能够正常工作。问题的根本原因是对 yt-dlp flat extraction 模式下返回的数据结构理解不正确。修复后，Python API 的行为完全匹配 yt-dlp 命令行工具。

**修复日期**: 2025-01-XX  
**修复者**: AI Assistant  
**严重程度**: 高（核心功能完全不可用）  
**状态**: ✅ 已修复并验证
