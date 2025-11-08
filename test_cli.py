#!/usr/bin/env python3
"""测试 CLI 工具的简单脚本"""

import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from youtube_chat_downloader.fetcher import (
    get_livestream_urls,
    get_video_info,
    fetch_video_chat
)


def test_get_livestream_urls():
    """测试获取频道直播列表"""
    print("=" * 60)
    print("测试: 获取频道直播视频列表")
    print("=" * 60)
    
    channel_url = "https://www.youtube.com/@chenyifaer/streams"
    cookies_file = "www.youtube.com_cookies.txt"
    
    if not os.path.exists(cookies_file):
        print(f"⚠️ Cookie 文件不存在: {cookies_file}")
        cookies_file = None
    
    try:
        urls = get_livestream_urls(channel_url, cookies_file)
        print(f"✅ 找到 {len(urls)} 个直播视频")
        
        if urls:
            print("\n前 5 个视频链接:")
            for i, url in enumerate(urls[:5], 1):
                print(f"  {i}. {url}")
        else:
            print("⚠️ 没有找到任何直播视频")
        
        return urls
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def test_get_video_info(url):
    """测试获取单个视频信息"""
    print("\n" + "=" * 60)
    print("测试: 获取视频信息")
    print("=" * 60)
    
    cookies_file = "www.youtube.com_cookies.txt"
    if not os.path.exists(cookies_file):
        cookies_file = None
    
    try:
        info = get_video_info(url, cookies_file)
        print(f"✅ 视频信息:")
        print(f"  ID: {info['id']}")
        print(f"  标题: {info['title']}")
        print(f"  时长: {info['duration']} 秒")
        print(f"  上传日期: {info['upload_date']}")
        print(f"  URL: {info['url']}")
        return info
    except Exception as e:
        print(f"❌ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主测试函数"""
    print("YouTube 聊天回放下载器 - 测试脚本\n")
    
    # 测试 1: 获取频道直播列表
    urls = test_get_livestream_urls()
    
    # 测试 2: 如果找到视频，获取第一个视频的信息
    if urls:
        print(f"\n使用第一个视频进行测试: {urls[0]}")
        info = test_get_video_info(urls[0])
        
        if info:
            print("\n" + "=" * 60)
            print("💡 提示：如需下载聊天回放，请运行:")
            print("=" * 60)
            print(f"python -m youtube_chat_downloader.cli --url \"{urls[0]}\"")
    else:
        print("\n⚠️ 没有找到视频，无法进行进一步测试")
        print("请检查频道 URL 或尝试其他频道")


if __name__ == "__main__":
    main()
