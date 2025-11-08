"""YouTube 聊天回放下载器 CLI"""

import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from .fetcher import get_livestream_urls, fetch_video_chat


def generate_filename(video_info):
    """根据视频信息生成文件名"""
    video_id = video_info["id"]
    upload_date = video_info.get("upload_date", "unknown")
    
    if upload_date and upload_date != "unknown":
        try:
            dt = datetime.strptime(upload_date, "%Y%m%d")
            date_str = dt.strftime("%Y%m%d")
        except:
            date_str = upload_date
    else:
        date_str = "unknown"
    
    filename = f"{date_str}_{video_id}.json"
    return filename


def save_to_json(data, output_dir):
    """保存数据为JSON文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    filename = generate_filename(data["video_info"])
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 直播聊天回放下载器 - 批量下载频道直播回放消息"
    )
    parser.add_argument(
        "--cookies",
        type=str,
        default="www.youtube.com_cookies.txt",
        help="Cookies 文件路径 (默认: www.youtube.com_cookies.txt)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="chat_replays",
        help="输出目录 (默认: chat_replays)"
    )
    parser.add_argument(
        "--save-type",
        type=str,
        default="json",
        choices=["json"],
        help="保存类型 (默认: json)"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="增量模式：跳过已存在的文件"
    )
    parser.add_argument(
        "--sleep-interval",
        type=int,
        default=5,
        help="视频之间的休眠间隔（秒）(默认: 5)"
    )
    parser.add_argument(
        "--channel",
        type=str,
        default="https://www.youtube.com/@chenyifaer/streams",
        help="YouTube 频道直播页面链接 (默认: @chenyifaer)"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="单个视频URL（如果指定，则只下载该视频）"
    )
    
    args = parser.parse_args()
    
    cookies_file = args.cookies if os.path.exists(args.cookies) else None
    if not cookies_file:
        print(f"⚠️ 警告：Cookies 文件 '{args.cookies}' 不存在，将在无认证模式下运行")
    
    if args.url:
        video_urls = [args.url]
        print(f"📺 处理单个视频: {args.url}")
    else:
        print(f"🔍 正在获取频道的直播视频列表: {args.channel}")
        video_urls = get_livestream_urls(args.channel, cookies_file)
        print(f"✅ 找到 {len(video_urls)} 个直播视频")
    
    if not video_urls:
        print("❌ 没有找到任何直播视频")
        return
    
    successful = 0
    skipped = 0
    failed = 0
    
    for idx, url in enumerate(video_urls, 1):
        print(f"\n{'='*60}")
        print(f"处理视频 {idx}/{len(video_urls)}: {url}")
        print(f"{'='*60}")
        
        try:
            from .fetcher import get_video_info
            video_info = get_video_info(url, cookies_file)
            filename = generate_filename(video_info)
            filepath = os.path.join(args.output_dir, filename)
            
            if args.incremental and os.path.exists(filepath):
                print(f"⏭️ 跳过已存在的文件: {filename}")
                skipped += 1
                continue
            
            data = fetch_video_chat(url, cookies_file, verbose=True)
            
            if data:
                saved_path = save_to_json(data, args.output_dir)
                print(f"💾 已保存到: {saved_path}")
                print(f"📊 统计: {data['statistics']['total_messages']} 条消息, "
                      f"{data['statistics']['unique_authors']} 个用户")
                successful += 1
            else:
                print(f"❌ 无法获取视频数据")
                failed += 1
            
            if idx < len(video_urls):
                print(f"😴 休眠 {args.sleep_interval} 秒...")
                time.sleep(args.sleep_interval)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断，退出程序...")
            break
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"📊 最终统计")
    print(f"{'='*60}")
    print(f"✅ 成功: {successful}")
    print(f"⏭️ 跳过: {skipped}")
    print(f"❌ 失败: {failed}")
    print(f"📁 输出目录: {args.output_dir}")


if __name__ == "__main__":
    main()
