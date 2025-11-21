#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from parent directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import init_db, close_db, row_to_dict


async def gather_stats():
    """连接数据库，查询并打印全面的账户统计信息。"""
    db = await init_db()

    try:
        accounts = await db.fetchall("SELECT * FROM accounts ORDER BY created_at DESC")
    except Exception as e:
        print(f"查询账户时出错: {e}", file=sys.stderr)
        await close_db()
        sys.exit(1)

    accounts = [row_to_dict(acc) for acc in accounts]
    total_accounts = len(accounts)

    if total_accounts == 0:
        print("数据库中没有找到任何账户。")
        await close_db()
        return

    # --- 汇总统计 ---
    enabled_accounts = [acc for acc in accounts if acc.get('enabled')]
    disabled_accounts = [acc for acc in accounts if not acc.get('enabled')]
    refresh_failed_accounts = [acc for acc in accounts if acc.get('last_refresh_status') == 'failed']
    never_used_accounts = [acc for acc in accounts if acc.get('success_count', 0) == 0]
    error_accounts = [acc for acc in accounts if acc.get('error_count', 0) > 0]
    total_success_count = sum(acc.get('success_count', 0) for acc in accounts)

    print("--- 账户统计摘要 ---")
    print(f"总账户数: {total_accounts}")
    print(f"  - 启用中: {len(enabled_accounts)}")
    print(f"  - 已禁用: {len(disabled_accounts)}")
    print("-" * 20)
    print(f"Token刷新失败数: {len(refresh_failed_accounts)}")
    print(f"从未使用过的账户数: {len(never_used_accounts)}")
    print(f"有错误记录的账户数: {len(error_accounts)}")
    print(f"所有账户总成功调用次数: {total_success_count}")
    print("-" * 20)

    # --- 详细列表 ---
    print("\n--- 账户详细列表 ---")
    header = "| {:<8s} | {:<6s} | {:<15s} | {:<5s} | {:<5s} | {:<12s} | {:<20s} |".format(
        "状态", "启用", "标签 (Label)", "成功", "错误", "刷新状态", "最后刷新时间"
    )
    print(header)
    print("-" * len(header))

    for acc in accounts:
        # 状态 emoji
        status_icon = "✅" if acc.get('enabled') else "❌"
        if acc.get('last_refresh_status') == 'failed':
            status_icon = "⚠️"

        # 格式化输出
        enabled_str = "是" if acc.get('enabled') else "否"
        label = acc.get('label') or "(无)"

        # 截断过长的标签
        if len(label) > 15:
            label = label[:12] + "..."

        last_refresh_time = acc.get('last_refresh_time') or "从未"
        last_refresh_status = acc.get('last_refresh_status') or "never"

        print("| {:<10s} | {:<8s} | {:<15s} | {:<5d} | {:<5d} | {:<12s} | {:<20s} |".format(
            status_icon,
            enabled_str,
            label,
            acc.get('success_count', 0),
            acc.get('error_count', 0),
            last_refresh_status,
            last_refresh_time
        ))

    print("-" * len(header))
    await close_db()


def main():
    """脚本主入口"""
    asyncio.run(gather_stats())
    sys.exit(0)


if __name__ == "__main__":
    main()
