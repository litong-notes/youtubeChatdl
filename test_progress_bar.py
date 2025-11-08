#!/usr/bin/env python3
"""测试进度条功能的简单脚本"""

import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from youtube_chat_downloader.fetcher import (
    parse_messages,
    ms_to_timestamp
)
from tqdm import tqdm
import time


def test_progress_bar():
    """测试进度条显示"""
    print("=" * 60)
    print("测试: 进度条显示")
    print("=" * 60)
    
    # 模拟视频长度（秒）
    duration = 100
    
    # 创建进度条
    pbar = tqdm(
        total=duration, 
        unit='s', 
        desc='下载进度', 
        bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:.0f}/{total:.0f}s [{elapsed}<{remaining}]'
    )
    
    # 模拟下载过程
    for i in range(0, duration + 1, 10):
        pbar.n = i
        pbar.refresh()
        time.sleep(0.1)
    
    pbar.close()
    print("✅ 进度条测试完成")


def test_message_parsing():
    """测试消息解析（不输出消息）"""
    print("\n" + "=" * 60)
    print("测试: 消息解析（静默模式）")
    print("=" * 60)
    
    # 模拟一些假的消息数据
    fake_actions = [
        {
            "replayChatItemAction": {
                "actions": [{
                    "addChatItemAction": {
                        "item": {
                            "liveChatTextMessageRenderer": {
                                "authorName": {"simpleText": "测试用户"},
                                "authorExternalChannelId": "test123",
                                "message": {"runs": [{"text": "测试消息"}]},
                                "videoOffsetTimeMsec": "60000"
                            }
                        }
                    }
                }]
            }
        }
    ]
    
    messages, latest_offset = parse_messages(fake_actions)
    
    print(f"✅ 成功解析 {len(messages)} 条消息")
    print(f"   最新偏移量: {ms_to_timestamp(latest_offset)}")
    print("   （消息内容未输出到终端，符合预期）")


def main():
    """主测试函数"""
    print("YouTube 聊天回放下载器 - 进度条功能测试\n")
    
    # 测试 1: 进度条显示
    test_progress_bar()
    
    # 测试 2: 消息解析（不输出）
    test_message_parsing()
    
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
