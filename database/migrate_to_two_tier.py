#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
两级黑名单体系 DDL 迁移脚本

执行步骤：
1. ALTER TABLE users ADD COLUMN is_admin
2. ALTER TABLE blacklist ADD COLUMN blacklist_type, owner_id, source_push_request_id（含索引）
3. UPDATE blacklist SET blacklist_type='USER', owner_id=created_by WHERE created_by IS NOT NULL
4. UPDATE blacklist SET blacklist_type='SYSTEM' WHERE created_by IS NULL
5. CREATE TABLE push_requests
6. CREATE TABLE notifications
7. 输出统计报告

用法：
  python migrate_to_two_tier.py            # 执行实际迁移
  python migrate_to_two_tier.py --dry-run  # 仅打印 SQL，不修改数据库

需求：1.1、2.1、3.1、5.2、9.3、8.1
"""

import sys
import logging
import pymysql
from datetime import datetime

# ─── 日志配置 ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── 数据库连接配置 ───────────────────────────────────────────────────────────
DB_CONFIG = {
    "host": "47.109.97.153",
    "port": 3306,
    "user": "root",
    "password": "Root@2025!",
    "database": "baking_recipe_system",
    "charset": "utf8mb4",
}

# ─── DDL / DML 语句定义 ───────────────────────────────────────────────────────

# 步骤 1：users 表新增 is_admin 字段（需求 1.1）
DDL_USERS_ADD_IS_ADMIN = """\
ALTER TABLE users
  ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否管理员';\
"""

# 步骤 2：blacklist 表新增字段及索引（需求 2.1、3.1）
DDL_BLACKLIST_ADD_COLUMNS = """\
ALTER TABLE blacklist
  ADD COLUMN blacklist_type ENUM('USER','SYSTEM') NOT NULL DEFAULT 'USER'
    COMMENT '黑名单类型',
  ADD COLUMN owner_id VARCHAR(36) NULL
    COMMENT '用户黑名单归属用户ID（SYSTEM类型为NULL）',
  ADD COLUMN source_push_request_id INT NULL
    COMMENT '来源推送申请ID（仅SYSTEM类型）',
  ADD INDEX idx_blacklist_type (blacklist_type),
  ADD INDEX idx_owner_id (owner_id);\
"""

# 步骤 3：将 created_by 不为空的条目迁移为用户黑名单（需求 8.1）
DML_MIGRATE_USER_BLACKLIST = """\
UPDATE blacklist
  SET blacklist_type = 'USER',
      owner_id       = created_by
  WHERE created_by IS NOT NULL;\
"""

# 步骤 4：将 created_by 为空的条目设置为系统黑名单（需求 8.1）
DML_MIGRATE_SYSTEM_BLACKLIST = """\
UPDATE blacklist
  SET blacklist_type = 'SYSTEM'
  WHERE created_by IS NULL;\
"""

# 步骤 5：创建 push_requests 表（需求 5.2）
DDL_CREATE_PUSH_REQUESTS = """\
CREATE TABLE IF NOT EXISTS push_requests (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  blacklist_id        INT NOT NULL
    COMMENT '申请推送的用户黑名单条目ID',
  applicant_id        VARCHAR(36) NOT NULL
    COMMENT '申请人用户ID',
  evidence            TEXT NOT NULL
    COMMENT '证据描述（≥10字符）',
  status              ENUM('PENDING','APPROVED','REJECTED') NOT NULL DEFAULT 'PENDING',
  reject_reason       TEXT NULL
    COMMENT '拒绝原因（REJECTED时必填）',
  reviewed_by         VARCHAR(36) NULL
    COMMENT '审核管理员ID',
  reviewed_at         DATETIME NULL
    COMMENT '审核时间',
  created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_blacklist_id  (blacklist_id),
  INDEX idx_applicant_id  (applicant_id),
  INDEX idx_status        (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推送申请表';\
"""

# 步骤 6：创建 notifications 表（需求 9.3）
DDL_CREATE_NOTIFICATIONS = """\
CREATE TABLE IF NOT EXISTS notifications (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  user_id             VARCHAR(36) NOT NULL
    COMMENT '接收用户ID',
  type                ENUM('PUSH_APPROVED','PUSH_REJECTED') NOT NULL
    COMMENT '通知类型',
  push_request_id     INT NOT NULL
    COMMENT '关联推送申请ID',
  title               VARCHAR(200) NOT NULL
    COMMENT '消息标题',
  content             TEXT NOT NULL
    COMMENT '消息内容',
  is_read             BOOLEAN NOT NULL DEFAULT FALSE
    COMMENT '是否已读',
  created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id   (user_id),
  INDEX idx_is_read   (user_id, is_read),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站内通知表';\
"""

# 所有步骤按顺序排列，每项为 (描述, SQL)
MIGRATION_STEPS = [
    ("步骤 1：users 表新增 is_admin 字段", DDL_USERS_ADD_IS_ADMIN),
    ("步骤 2：blacklist 表新增 blacklist_type / owner_id / source_push_request_id 字段及索引",
     DDL_BLACKLIST_ADD_COLUMNS),
    ("步骤 3：将 created_by 不为空的条目迁移为用户黑名单", DML_MIGRATE_USER_BLACKLIST),
    ("步骤 4：将 created_by 为空的条目设置为系统黑名单", DML_MIGRATE_SYSTEM_BLACKLIST),
    ("步骤 5：创建 push_requests 表", DDL_CREATE_PUSH_REQUESTS),
    ("步骤 6：创建 notifications 表", DDL_CREATE_NOTIFICATIONS),
]


# ─── 辅助函数 ─────────────────────────────────────────────────────────────────

def column_exists(cursor, table: str, column: str) -> bool:
    """检查列是否已存在，避免重复 ALTER。"""
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = %s
          AND COLUMN_NAME  = %s
        """,
        (table, column),
    )
    return cursor.fetchone()[0] > 0


def table_exists(cursor, table: str) -> bool:
    """检查表是否已存在。"""
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = %s
        """,
        (table,),
    )
    return cursor.fetchone()[0] > 0


def get_row_count(cursor, table: str, condition: str = "") -> int:
    """获取满足条件的行数，用于统计报告。"""
    sql = f"SELECT COUNT(*) FROM `{table}`"
    if condition:
        sql += f" WHERE {condition}"
    cursor.execute(sql)
    return cursor.fetchone()[0]


# ─── 核心迁移逻辑 ─────────────────────────────────────────────────────────────

def run_migration(dry_run: bool = False) -> bool:
    """
    执行迁移。

    Args:
        dry_run: True 时仅打印 SQL，不连接数据库。

    Returns:
        True 表示成功，False 表示失败。
    """
    separator = "=" * 70
    print(separator)
    print("两级黑名单体系 DDL 迁移脚本")
    print(f"执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if dry_run:
        print("【DRY-RUN 模式】仅打印 SQL，不修改数据库")
    print(separator)

    # ── Dry-run：直接打印所有 SQL 后退出 ──────────────────────────────────────
    if dry_run:
        print("\n以下是将要执行的 SQL 语句：\n")
        for desc, sql in MIGRATION_STEPS:
            print(f"-- {desc}")
            print(sql)
            print()
        print(separator)
        print("Dry-run 完成，未对数据库做任何修改。")
        return True

    # ── 实际执行 ──────────────────────────────────────────────────────────────
    conn = None
    success_steps = 0
    failed_steps = 0
    errors = []

    try:
        logger.info("正在连接数据库 %s:%s/%s …",
                    DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["database"])
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        logger.info("数据库连接成功。")

        # ── 步骤 1：users.is_admin ─────────────────────────────────────────
        desc, sql = MIGRATION_STEPS[0]
        logger.info(desc)
        if column_exists(cursor, "users", "is_admin"):
            logger.info("  ↳ 列 users.is_admin 已存在，跳过。")
            success_steps += 1
        else:
            try:
                cursor.execute(sql)
                conn.commit()
                logger.info("  ↳ 完成。")
                success_steps += 1
            except Exception as e:
                failed_steps += 1
                msg = f"{desc} 失败：{e}"
                errors.append(msg)
                logger.error("  ↳ %s", msg)

        # ── 步骤 2：blacklist 新增字段 ────────────────────────────────────
        desc, sql = MIGRATION_STEPS[1]
        logger.info(desc)
        already_has_type = column_exists(cursor, "blacklist", "blacklist_type")
        already_has_owner = column_exists(cursor, "blacklist", "owner_id")
        already_has_src = column_exists(cursor, "blacklist", "source_push_request_id")

        if already_has_type and already_has_owner and already_has_src:
            logger.info("  ↳ 所有列已存在，跳过。")
            success_steps += 1
        else:
            # 动态构建 ALTER 语句，只添加缺失的列
            clauses = []
            if not already_has_type:
                clauses.append(
                    "ADD COLUMN blacklist_type ENUM('USER','SYSTEM') NOT NULL DEFAULT 'USER' "
                    "COMMENT '黑名单类型'"
                )
            if not already_has_owner:
                clauses.append(
                    "ADD COLUMN owner_id VARCHAR(36) NULL "
                    "COMMENT '用户黑名单归属用户ID（SYSTEM类型为NULL）'"
                )
            if not already_has_src:
                clauses.append(
                    "ADD COLUMN source_push_request_id INT NULL "
                    "COMMENT '来源推送申请ID（仅SYSTEM类型）'"
                )

            # 索引：只在列刚创建时添加（若列已存在则索引也应已存在）
            if not already_has_type:
                clauses.append("ADD INDEX idx_blacklist_type (blacklist_type)")
            if not already_has_owner:
                clauses.append("ADD INDEX idx_owner_id (owner_id)")

            alter_sql = "ALTER TABLE blacklist\n  " + ",\n  ".join(clauses) + ";"
            try:
                cursor.execute(alter_sql)
                conn.commit()
                logger.info("  ↳ 完成。")
                success_steps += 1
            except Exception as e:
                failed_steps += 1
                msg = f"{desc} 失败：{e}"
                errors.append(msg)
                logger.error("  ↳ %s", msg)

        # ── 步骤 3 & 4：数据迁移（逐条处理，单条失败不中断整体）────────────
        for step_idx in (2, 3):
            desc, sql = MIGRATION_STEPS[step_idx]
            logger.info(desc)
            try:
                cursor.execute(sql)
                affected = cursor.rowcount
                conn.commit()
                logger.info("  ↳ 完成，影响 %d 行。", affected)
                success_steps += 1
            except Exception as e:
                failed_steps += 1
                msg = f"{desc} 失败：{e}"
                errors.append(msg)
                logger.error("  ↳ %s", msg)

        # ── 步骤 5：push_requests 表 ──────────────────────────────────────
        desc, sql = MIGRATION_STEPS[4]
        logger.info(desc)
        if table_exists(cursor, "push_requests"):
            logger.info("  ↳ 表 push_requests 已存在，跳过。")
            success_steps += 1
        else:
            try:
                cursor.execute(sql)
                conn.commit()
                logger.info("  ↳ 完成。")
                success_steps += 1
            except Exception as e:
                failed_steps += 1
                msg = f"{desc} 失败：{e}"
                errors.append(msg)
                logger.error("  ↳ %s", msg)

        # ── 步骤 6：notifications 表 ──────────────────────────────────────
        desc, sql = MIGRATION_STEPS[5]
        logger.info(desc)
        if table_exists(cursor, "notifications"):
            logger.info("  ↳ 表 notifications 已存在，跳过。")
            success_steps += 1
        else:
            try:
                cursor.execute(sql)
                conn.commit()
                logger.info("  ↳ 完成。")
                success_steps += 1
            except Exception as e:
                failed_steps += 1
                msg = f"{desc} 失败：{e}"
                errors.append(msg)
                logger.error("  ↳ %s", msg)

        # ── 统计报告（需求 8.2）──────────────────────────────────────────
        print()
        print(separator)
        print("迁移统计报告")
        print(separator)
        print(f"执行步骤总数：{len(MIGRATION_STEPS)}")
        print(f"成功步骤数  ：{success_steps}")
        print(f"失败步骤数  ：{failed_steps}")

        try:
            user_bl_count = get_row_count(cursor, "blacklist", "blacklist_type = 'USER'")
            sys_bl_count = get_row_count(cursor, "blacklist", "blacklist_type = 'SYSTEM'")
            print(f"\n黑名单条目统计：")
            print(f"  用户黑名单（USER）  ：{user_bl_count} 条")
            print(f"  系统黑名单（SYSTEM）：{sys_bl_count} 条")
        except Exception as e:
            logger.warning("统计黑名单条目时出错：%s", e)

        if errors:
            print(f"\n错误详情（共 {len(errors)} 条）：")
            for err in errors:
                print(f"  ✗ {err}")

        print(separator)

        return failed_steps == 0

    except pymysql.Error as e:
        logger.error("数据库连接失败：%s", e)
        return False
    except Exception as e:
        logger.error("迁移过程中发生未预期错误：%s", e)
        return False
    finally:
        if conn:
            conn.close()
            logger.info("数据库连接已关闭。")


# ─── 入口 ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    if not dry_run:
        print("⚠️  即将对数据库执行不可逆的 DDL/DML 变更！")
        print("   建议先使用 --dry-run 参数预览 SQL。")
        confirm = input("确认继续？(yes/no): ").strip().lower()
        if confirm != "yes":
            print("已取消。")
            sys.exit(0)

    success = run_migration(dry_run=dry_run)
    sys.exit(0 if success else 1)
