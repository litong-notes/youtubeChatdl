#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 数据库查询示例脚本
用于查询 youtubeChatdl.py 生成的聊天记录数据库
"""

import sqlite3
import sys


def connect_db(db_path):
    """连接到数据库"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"❌ 数据库连接错误: {e}")
        sys.exit(1)


def show_statistics(conn):
    """显示数据库统计信息"""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("📊 数据库统计信息")
    print("="*60)
    
    # 总消息数
    cursor.execute('SELECT COUNT(*) FROM chat_messages')
    total_count = cursor.fetchone()[0]
    print(f"总消息数: {total_count:,}")
    
    # 独特用户数
    cursor.execute('SELECT COUNT(DISTINCT author_id) FROM chat_messages WHERE author_id != ""')
    unique_authors = cursor.fetchone()[0]
    print(f"独特用户数: {unique_authors:,}")
    
    # 时间范围
    cursor.execute('SELECT MIN(offset_ms), MAX(offset_ms) FROM chat_messages')
    min_offset, max_offset = cursor.fetchone()
    print(f"时间范围: {min_offset} ms 到 {max_offset} ms")
    
    # 负时间戳消息数
    cursor.execute('SELECT COUNT(*) FROM chat_messages WHERE offset_ms < 0')
    negative_count = cursor.fetchone()[0]
    print(f"直播前消息数: {negative_count:,}")
    
    print("="*60 + "\n")


def show_top_users(conn, limit=10):
    """显示消息最多的用户"""
    cursor = conn.cursor()
    
    print(f"\n🏆 消息数量 TOP {limit} 用户")
    print("-"*60)
    
    cursor.execute('''
        SELECT author, author_id, COUNT(*) as msg_count
        FROM chat_messages
        GROUP BY author_id
        ORDER BY msg_count DESC
        LIMIT ?
    ''', (limit,))
    
    for i, row in enumerate(cursor.fetchall(), 1):
        author_id_display = row['author_id'][:20] + "..." if len(row['author_id']) > 20 else row['author_id']
        print(f"{i:2}. {row['author']:20} ({author_id_display:23}) - {row['msg_count']:,} 条")
    
    print()


def show_recent_messages(conn, limit=20):
    """显示最近的消息"""
    cursor = conn.cursor()
    
    print(f"\n💬 最近 {limit} 条消息")
    print("-"*60)
    
    cursor.execute('''
        SELECT time_text, author, message
        FROM chat_messages
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    
    for row in cursor.fetchall():
        print(f"[{row['time_text']:>8}] {row['author']:15} : {row['message']}")
    
    print()


def show_messages_by_time(conn, start_time=None, end_time=None):
    """显示指定时间范围的消息"""
    cursor = conn.cursor()
    
    if start_time is None and end_time is None:
        return
    
    print(f"\n⏰ 时间范围消息")
    print("-"*60)
    
    query = 'SELECT time_text, author, message, offset_ms FROM chat_messages WHERE '
    params = []
    
    if start_time is not None:
        query += 'offset_ms >= ? '
        params.append(start_time)
    
    if end_time is not None:
        if start_time is not None:
            query += 'AND '
        query += 'offset_ms <= ? '
        params.append(end_time)
    
    query += 'ORDER BY offset_ms'
    
    cursor.execute(query, params)
    
    count = 0
    for row in cursor.fetchall():
        print(f"[{row['time_text']:>8}] {row['author']:15} : {row['message']}")
        count += 1
    
    print(f"\n共 {count} 条消息")
    print()


def search_messages(conn, keyword):
    """搜索包含关键词的消息"""
    cursor = conn.cursor()
    
    print(f"\n🔍 搜索关键词: '{keyword}'")
    print("-"*60)
    
    cursor.execute('''
        SELECT time_text, author, message
        FROM chat_messages
        WHERE message LIKE ?
        ORDER BY offset_ms
    ''', (f'%{keyword}%',))
    
    results = cursor.fetchall()
    
    for row in results:
        print(f"[{row['time_text']:>8}] {row['author']:15} : {row['message']}")
    
    print(f"\n共找到 {len(results)} 条消息")
    print()


def show_user_messages(conn, author_id):
    """显示指定用户的所有消息"""
    cursor = conn.cursor()
    
    print(f"\n👤 用户消息 (ID: {author_id})")
    print("-"*60)
    
    cursor.execute('''
        SELECT time_text, author, message
        FROM chat_messages
        WHERE author_id = ?
        ORDER BY offset_ms
    ''', (author_id,))
    
    results = cursor.fetchall()
    
    if results:
        author_name = results[0]['author']
        print(f"用户名: {author_name}")
        print()
        
        for row in results:
            print(f"[{row['time_text']:>8}] {row['message']}")
        
        print(f"\n共 {len(results)} 条消息")
    else:
        print("未找到该用户的消息")
    
    print()


def export_to_csv(conn, output_file):
    """导出到 CSV 文件"""
    import csv
    
    cursor = conn.cursor()
    cursor.execute('''
        SELECT time_text, author, author_id, message, offset_ms
        FROM chat_messages
        ORDER BY offset_ms
    ''')
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_text', 'author', 'author_id', 'message', 'offset_ms'])
        writer.writerows(cursor.fetchall())
    
    print(f"✅ 已导出到 {output_file}")


def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python query_example.py <database_file>")
        print("\n示例:")
        print("  python query_example.py chatlog_VIDEO_ID.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    conn = connect_db(db_path)
    
    print(f"\n📂 数据库文件: {db_path}")
    
    # 显示统计信息
    show_statistics(conn)
    
    # 显示 TOP 用户
    show_top_users(conn, 10)
    
    # 显示最近消息
    show_recent_messages(conn, 20)
    
    # 交互式查询
    print("\n" + "="*60)
    print("🔧 交互式查询")
    print("="*60)
    print("1. 搜索关键词")
    print("2. 查看指定用户消息")
    print("3. 查看时间范围消息")
    print("4. 导出为 CSV")
    print("5. 退出")
    
    while True:
        try:
            choice = input("\n请选择操作 (1-5): ").strip()
            
            if choice == '1':
                keyword = input("输入搜索关键词: ").strip()
                if keyword:
                    search_messages(conn, keyword)
            
            elif choice == '2':
                author_id = input("输入用户频道 ID: ").strip()
                if author_id:
                    show_user_messages(conn, author_id)
            
            elif choice == '3':
                print("输入时间范围（毫秒），留空表示不限制")
                start = input("起始时间 (ms): ").strip()
                end = input("结束时间 (ms): ").strip()
                start_ms = int(start) if start else None
                end_ms = int(end) if end else None
                show_messages_by_time(conn, start_ms, end_ms)
            
            elif choice == '4':
                output = input("输入输出文件名 (默认: export.csv): ").strip()
                output = output if output else "export.csv"
                export_to_csv(conn, output)
            
            elif choice == '5':
                break
            
            else:
                print("无效的选择，请输入 1-5")
        
        except KeyboardInterrupt:
            print("\n\n退出")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    conn.close()
    print("\n再见！👋\n")


if __name__ == "__main__":
    main()
