"""JSON 导入到 SQLite 数据库的 CLI 工具"""

import argparse
from .db_importer import import_directory_to_db, print_database_stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将 JSON 聊天回放文件导入到 SQLite 数据库"
    )
    parser.add_argument(
        "--json-dir",
        type=str,
        default="chat_replays",
        help="JSON 文件目录 (默认: chat_replays)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="chat_database.db",
        help="SQLite 数据库路径 (默认: chat_database.db)"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="增量模式：跳过已存在的视频"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="仅显示数据库统计信息（不导入）"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="安静模式：减少输出信息"
    )
    
    args = parser.parse_args()
    
    # 如果只是查看统计信息
    if args.stats:
        print_database_stats(args.db_path)
        return
    
    # 执行导入
    verbose = not args.quiet
    
    if verbose:
        print("=" * 60)
        print("📥 JSON 文件导入到 SQLite 数据库")
        print("=" * 60)
        print()
    
    success, skipped, failed, total_messages = import_directory_to_db(
        args.json_dir,
        args.db_path,
        args.incremental,
        verbose
    )
    
    # 显示最终数据库统计
    if verbose and success > 0:
        print()
        print_database_stats(args.db_path)


if __name__ == "__main__":
    main()
