#!/usr/bin/env python3
"""
重新启用所有账号的脚本
将所有账号的 enabled 设置为 1，保留错误和成功次数
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env file from parent directory
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import init_db, close_db


async def reset_all_accounts():
    """重新启用所有账号（不重置错误和成功次数）"""
    db = await init_db()

    try:
        # 获取当前禁用的账号数量
        disabled_row = await db.fetchone("SELECT COUNT(*) as cnt FROM accounts WHERE enabled=0")
        disabled_count = disabled_row['cnt'] if disabled_row else 0

        # 获取总账号数量
        total_row = await db.fetchone("SELECT COUNT(*) as cnt FROM accounts")
        total_count = total_row['cnt'] if total_row else 0

        print(f"数据库中共有 {total_count} 个账号")
        print(f"其中 {disabled_count} 个账号已被禁用")

        if disabled_count == 0:
            print("所有账号都已启用，无需操作")
            await close_db()
            return

        # 只重新启用账号，不重置错误和成功次数
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        await db.execute("""
            UPDATE accounts
            SET enabled=1, updated_at=?
            WHERE enabled=0
        """, (now,))

        print(f"✓ 已重新启用 {disabled_count} 个账号")
        print("✓ 保留了所有账号的错误和成功次数")

        # 显示更新后的状态
        rows = await db.fetchall("""
            SELECT id, label, enabled, error_count, success_count
            FROM accounts
            ORDER BY created_at DESC
        """)

        print("\n当前账号状态:")
        print("-" * 80)
        print(f"{'ID':<38} {'标签':<20} {'启用':<6} {'错误':<6} {'成功':<6}")
        print("-" * 80)
        for row in rows:
            acc_id = row['id']
            label = row['label'] or "(无标签)"
            enabled = row['enabled']
            error_count = row['error_count'] or 0
            success_count = row['success_count'] or 0
            enabled_str = "是" if enabled else "否"
            print(f"{acc_id:<38} {label:<20} {enabled_str:<6} {error_count:<6} {success_count:<6}")

    finally:
        await close_db()


async def main_async():
    print("=" * 80)
    print("重新启用所有账号")
    print("=" * 80)
    print()

    try:
        await reset_all_accounts()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("=" * 80)
    print("操作完成")
    print("=" * 80)
    return 0


def main():
    return asyncio.run(main_async())


if __name__ == "__main__":
    exit(main())
