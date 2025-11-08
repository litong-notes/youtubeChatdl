"""JSON 文件导入到 SQLite 数据库模块"""

import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime


def init_database(db_path):
    """初始化SQLite数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建视频信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            duration INTEGER,
            upload_date TEXT,
            url TEXT,
            total_messages INTEGER,
            unique_authors INTEGER,
            time_range_min TEXT,
            time_range_max TEXT,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建聊天消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            time_text TEXT,
            author TEXT,
            author_id TEXT,
            message TEXT,
            offset_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(video_id)
        )
    ''')
    
    # 创建索引
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_video_id ON chat_messages(video_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_offset ON chat_messages(offset_ms)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_author_id ON chat_messages(author_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_video_upload_date ON videos(upload_date)
    ''')
    
    conn.commit()
    return conn


def video_exists(cursor, video_id):
    """检查视频是否已存在于数据库中"""
    cursor.execute('SELECT video_id FROM videos WHERE video_id = ?', (video_id,))
    return cursor.fetchone() is not None


def get_video_message_count(cursor, video_id):
    """获取视频的消息数量"""
    cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE video_id = ?', (video_id,))
    return cursor.fetchone()[0]


def import_json_to_db(json_path, conn, incremental=True, verbose=True):
    """导入单个JSON文件到数据库
    
    Args:
        json_path: JSON文件路径
        conn: 数据库连接
        incremental: 是否增量导入（跳过已存在的视频）
        verbose: 是否显示详细信息
    
    Returns:
        导入的消息数量，如果跳过则返回0
    """
    cursor = conn.cursor()
    
    # 读取JSON文件
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    video_info = data.get('video_info', {})
    messages = data.get('messages', [])
    statistics = data.get('statistics', {})
    
    video_id = video_info.get('id', 'unknown')
    
    # 检查增量模式
    if incremental and video_exists(cursor, video_id):
        existing_count = get_video_message_count(cursor, video_id)
        if verbose:
            print(f"⏭️ 跳过已存在的视频: {video_id} (已有 {existing_count} 条消息)")
        return 0
    
    # 插入或更新视频信息
    time_range = statistics.get('time_range', {})
    cursor.execute('''
        INSERT OR REPLACE INTO videos 
        (video_id, title, duration, upload_date, url, 
         total_messages, unique_authors, time_range_min, time_range_max, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        video_id,
        video_info.get('title', ''),
        video_info.get('duration', 0),
        video_info.get('upload_date', ''),
        video_info.get('url', ''),
        statistics.get('total_messages', 0),
        statistics.get('unique_authors', 0),
        time_range.get('min', '0:00'),
        time_range.get('max', '0:00'),
        datetime.now().isoformat()
    ))
    
    # 如果不是增量模式且视频已存在，先删除旧消息
    if not incremental and video_exists(cursor, video_id):
        cursor.execute('DELETE FROM chat_messages WHERE video_id = ?', (video_id,))
    
    # 批量插入消息
    message_count = 0
    for msg in messages:
        cursor.execute('''
            INSERT INTO chat_messages 
            (video_id, time_text, author, author_id, message, offset_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            video_id,
            msg.get('time_text', '0:00'),
            msg.get('author', ''),
            msg.get('author_id', ''),
            msg.get('message', ''),
            msg.get('offset_ms', 0)
        ))
        message_count += 1
    
    conn.commit()
    
    if verbose:
        print(f"✅ 导入视频: {video_id} - {video_info.get('title', 'Unknown')} ({message_count} 条消息)")
    
    return message_count


def import_directory_to_db(json_dir, db_path, incremental=True, verbose=True):
    """导入整个目录的JSON文件到数据库
    
    Args:
        json_dir: JSON文件目录
        db_path: 数据库文件路径
        incremental: 是否增量导入
        verbose: 是否显示详细信息
    
    Returns:
        (成功数, 跳过数, 失败数, 总消息数)
    """
    json_dir = Path(json_dir)
    if not json_dir.exists():
        print(f"❌ 目录不存在: {json_dir}")
        return (0, 0, 0, 0)
    
    # 获取所有JSON文件
    json_files = list(json_dir.glob('*.json'))
    if not json_files:
        print(f"⚠️ 目录中没有找到JSON文件: {json_dir}")
        return (0, 0, 0, 0)
    
    if verbose:
        print(f"📂 找到 {len(json_files)} 个JSON文件")
        print(f"💾 数据库: {db_path}")
        print(f"🔄 增量模式: {'开启' if incremental else '关闭'}")
        print()
    
    # 初始化数据库
    conn = init_database(db_path)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    total_messages = 0
    
    for idx, json_file in enumerate(json_files, 1):
        if verbose:
            print(f"[{idx}/{len(json_files)}] 处理: {json_file.name}")
        
        try:
            message_count = import_json_to_db(json_file, conn, incremental, verbose)
            if message_count > 0:
                success_count += 1
                total_messages += message_count
            else:
                skip_count += 1
        except Exception as e:
            fail_count += 1
            if verbose:
                print(f"❌ 导入失败: {e}")
                import traceback
                traceback.print_exc()
    
    conn.close()
    
    if verbose:
        print()
        print("=" * 60)
        print("📊 导入统计")
        print("=" * 60)
        print(f"✅ 成功: {success_count} 个视频")
        print(f"⏭️ 跳过: {skip_count} 个视频")
        print(f"❌ 失败: {fail_count} 个视频")
        print(f"💬 总消息数: {total_messages} 条")
        print(f"💾 数据库: {db_path}")
    
    return (success_count, skip_count, fail_count, total_messages)


def get_database_stats(db_path):
    """获取数据库统计信息"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库不存在: {db_path}")
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 视频总数
    cursor.execute('SELECT COUNT(*) FROM videos')
    video_count = cursor.fetchone()[0]
    
    # 消息总数
    cursor.execute('SELECT COUNT(*) FROM chat_messages')
    message_count = cursor.fetchone()[0]
    
    # 独特作者数
    cursor.execute('SELECT COUNT(DISTINCT author_id) FROM chat_messages WHERE author_id != ""')
    author_count = cursor.fetchone()[0]
    
    # 数据库大小
    db_size = os.path.getsize(db_path)
    db_size_mb = db_size / (1024 * 1024)
    
    # 最早和最晚的视频
    cursor.execute('SELECT MIN(upload_date), MAX(upload_date) FROM videos WHERE upload_date != ""')
    date_range = cursor.fetchone()
    
    conn.close()
    
    stats = {
        'video_count': video_count,
        'message_count': message_count,
        'author_count': author_count,
        'db_size_mb': db_size_mb,
        'date_range': date_range
    }
    
    return stats


def print_database_stats(db_path):
    """打印数据库统计信息"""
    stats = get_database_stats(db_path)
    if not stats:
        return
    
    print("=" * 60)
    print("📊 数据库统计信息")
    print("=" * 60)
    print(f"📺 视频总数: {stats['video_count']}")
    print(f"💬 消息总数: {stats['message_count']:,}")
    print(f"👤 独特作者: {stats['author_count']:,}")
    print(f"💾 数据库大小: {stats['db_size_mb']:.2f} MB")
    if stats['date_range'][0] and stats['date_range'][1]:
        print(f"📅 视频日期范围: {stats['date_range'][0]} ~ {stats['date_range'][1]}")
    print("=" * 60)
