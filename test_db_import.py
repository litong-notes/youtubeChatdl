#!/usr/bin/env python3
"""测试数据库导入功能"""

import os
import json
import tempfile
from pathlib import Path
from youtube_chat_downloader.db_importer import (
    import_json_to_db,
    import_directory_to_db,
    init_database,
    get_database_stats,
    print_database_stats
)


def create_test_json(output_dir, video_id="test123", message_count=10):
    """创建测试JSON文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    test_data = {
        "video_info": {
            "id": video_id,
            "title": f"测试视频 {video_id}",
            "duration": 3600,
            "upload_date": "20240115",
            "url": f"https://www.youtube.com/watch?v={video_id}"
        },
        "messages": [
            {
                "time_text": f"{i}:00",
                "author": f"用户{i % 5}",
                "author_id": f"UC{i % 5}",
                "message": f"测试消息 {i}",
                "offset_ms": i * 60000
            }
            for i in range(message_count)
        ],
        "statistics": {
            "total_messages": message_count,
            "unique_authors": 5,
            "time_range": {
                "min": "0:00",
                "max": f"{message_count}:00"
            }
        }
    }
    
    filename = f"20240115_{video_id}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    return filepath


def test_single_import():
    """测试单个文件导入"""
    print("=" * 60)
    print("测试 1: 单个JSON文件导入")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试JSON
        json_file = create_test_json(tmpdir, "test001", 20)
        print(f"✅ 创建测试文件: {json_file}")
        
        # 创建数据库
        db_path = os.path.join(tmpdir, "test.db")
        conn = init_database(db_path)
        
        # 导入
        message_count = import_json_to_db(json_file, conn, incremental=True, verbose=True)
        conn.close()
        
        print(f"✅ 导入了 {message_count} 条消息")
        
        # 显示统计
        print_database_stats(db_path)
    
    print("✅ 测试 1 通过\n")


def test_directory_import():
    """测试目录批量导入"""
    print("=" * 60)
    print("测试 2: 目录批量导入")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        json_dir = os.path.join(tmpdir, "jsons")
        db_path = os.path.join(tmpdir, "test.db")
        
        # 创建多个测试JSON文件
        for i in range(5):
            create_test_json(json_dir, f"test{i:03d}", 10 + i * 5)
        
        print(f"✅ 创建了 5 个测试JSON文件")
        
        # 批量导入
        success, skipped, failed, total = import_directory_to_db(
            json_dir,
            db_path,
            incremental=True,
            verbose=True
        )
        
        assert success == 5, f"应该成功导入5个文件，实际: {success}"
        assert skipped == 0, f"应该跳过0个文件，实际: {skipped}"
        assert failed == 0, f"应该失败0个文件，实际: {failed}"
        
        print(f"✅ 批量导入成功: {success} 个视频, {total} 条消息")
    
    print("✅ 测试 2 通过\n")


def test_incremental_import():
    """测试增量导入"""
    print("=" * 60)
    print("测试 3: 增量导入（跳过已存在）")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        json_dir = os.path.join(tmpdir, "jsons")
        db_path = os.path.join(tmpdir, "test.db")
        
        # 创建测试文件
        create_test_json(json_dir, "test001", 10)
        create_test_json(json_dir, "test002", 15)
        
        # 第一次导入
        print("第一次导入:")
        success1, _, _, total1 = import_directory_to_db(
            json_dir,
            db_path,
            incremental=True,
            verbose=True
        )
        
        # 第二次导入（应该跳过）
        print("\n第二次导入（增量模式）:")
        success2, skipped2, _, total2 = import_directory_to_db(
            json_dir,
            db_path,
            incremental=True,
            verbose=True
        )
        
        assert success1 == 2, f"第一次应该成功2个，实际: {success1}"
        assert success2 == 0, f"第二次应该成功0个（全部跳过），实际: {success2}"
        assert skipped2 == 2, f"第二次应该跳过2个，实际: {skipped2}"
        
        print("✅ 增量模式工作正常")
    
    print("✅ 测试 3 通过\n")


def main():
    """运行所有测试"""
    print("\n🧪 数据库导入功能测试\n")
    
    try:
        test_single_import()
        test_directory_import()
        test_incremental_import()
        
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
