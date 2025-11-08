#!/usr/bin/env python3
"""将旧版 SQLite 数据库转换为新的 JSON 格式"""

import sys
import json
import sqlite3
import re
from pathlib import Path


def ms_to_timestamp(ms):
    """将毫秒转换为 0:00 格式"""
    try:
        s = int(ms) // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
    except:
        return "0:00"


def convert_db_to_json(db_path, output_path=None):
    """转换 SQLite 数据库到 JSON 格式"""
    
    # 从文件名提取 video_id
    match = re.search(r'chatlog_(.+)\.db', str(db_path))
    video_id = match.group(1) if match else "unknown"
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有消息
    cursor.execute('''
        SELECT time_text, author, author_id, message, offset_ms
        FROM chat_messages
        ORDER BY offset_ms
    ''')
    rows = cursor.fetchall()
    
    messages = []
    for time_text, author, author_id, message, offset_ms in rows:
        messages.append({
            "time_text": time_text,
            "author": author,
            "author_id": author_id,
            "message": message,
            "offset_ms": offset_ms
        })
    
    # 获取统计信息
    cursor.execute('SELECT COUNT(*) FROM chat_messages')
    total_messages = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT author_id) FROM chat_messages WHERE author_id != ""')
    unique_authors = cursor.fetchone()[0]
    
    cursor.execute('SELECT MIN(offset_ms), MAX(offset_ms) FROM chat_messages')
    min_offset, max_offset = cursor.fetchone()
    
    conn.close()
    
    # 构建 JSON 数据
    data = {
        "video_info": {
            "id": video_id,
            "title": "",
            "duration": 0,
            "upload_date": "",
            "url": f"https://www.youtube.com/watch?v={video_id}"
        },
        "messages": messages,
        "statistics": {
            "total_messages": total_messages,
            "unique_authors": unique_authors,
            "time_range": {
                "min": ms_to_timestamp(min_offset if min_offset else 0),
                "max": ms_to_timestamp(max_offset if max_offset else 0)
            }
        }
    }
    
    # 确定输出文件路径
    if output_path is None:
        output_path = Path(db_path).stem + ".json"
    
    # 保存 JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 转换完成:")
    print(f"   输入: {db_path}")
    print(f"   输出: {output_path}")
    print(f"   消息数: {total_messages}")
    print(f"   用户数: {unique_authors}")
    
    return output_path


def main():
    if len(sys.argv) < 2:
        print("使用方法: python convert_db_to_json.py <database.db> [output.json]")
        print("\n示例:")
        print("  python convert_db_to_json.py chatlog_abc123.db")
        print("  python convert_db_to_json.py chatlog_abc123.db output.json")
        sys.exit(1)
    
    db_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(db_path).exists():
        print(f"❌ 错误: 文件不存在: {db_path}")
        sys.exit(1)
    
    try:
        convert_db_to_json(db_path, output_path)
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
