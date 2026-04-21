"""
将所有用户黑名单数据迁移至系统黑名单，合并相同电话号码的重复条目。

合并规则：
- 相同电话号码的条目合并为一条
- 风险等级取最高（HIGH > MEDIUM > LOW）
- blacklist_reason 合并（去重拼接）
- ktt_name / wechat_name / order_address 取第一条非空值
- 合并后的条目 blacklist_type 设为 SYSTEM，owner_id 设为 NULL
- 被合并的重复条目删除

用法：
  python merge_to_system.py            # 执行实际迁移
  python merge_to_system.py --dry-run  # 仅预览，不修改数据库
"""

import sys
import json
import pymysql
from datetime import datetime

DB_CONFIG = dict(host='47.109.97.153', port=3306, user='root',
                 password='Root@2025!', database='baking_recipe_system', charset='utf8mb4')

RISK_ORDER = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
DRY_RUN = '--dry-run' in sys.argv

def higher_risk(a, b):
    return a if RISK_ORDER.get(a, 2) <= RISK_ORDER.get(b, 2) else b

def merge_reasons(reasons):
    parts = []
    for r in reasons:
        if r and r.strip() and r.strip() not in parts:
            parts.append(r.strip())
    return '；'.join(parts) if parts else None

def run():
    sep = '=' * 60
    print(sep)
    print('用户黑名单 → 系统黑名单迁移脚本')
    print(f'执行时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    if DRY_RUN:
        print('【DRY-RUN 模式】仅预览，不修改数据库')
    print(sep)

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # 取所有用户黑名单
    cursor.execute("SELECT * FROM blacklist WHERE blacklist_type = 'USER' ORDER BY id")
    user_items = cursor.fetchall()
    print(f'\n用户黑名单总数: {len(user_items)}')

    # 按电话号码分组
    phone_groups = {}   # phone_key -> [items]
    no_phone = []       # 没有电话的条目

    for item in user_items:
        phones = item['phone_numbers']
        if phones:
            try:
                phone_list = json.loads(phones) if isinstance(phones, str) else phones
                phone_list = sorted([p for p in phone_list if p])
            except Exception:
                phone_list = []
        else:
            phone_list = []

        if phone_list:
            key = json.dumps(phone_list, ensure_ascii=False)
            phone_groups.setdefault(key, []).append(item)
        else:
            no_phone.append(item)

    # 统计
    dup_groups = {k: v for k, v in phone_groups.items() if len(v) > 1}
    unique_groups = {k: v for k, v in phone_groups.items() if len(v) == 1}
    print(f'有电话唯一条目: {len(unique_groups)} 组')
    print(f'有电话重复条目: {len(dup_groups)} 组（共 {sum(len(v) for v in dup_groups.values())} 条）')
    print(f'无电话条目: {len(no_phone)} 条')

    if DRY_RUN:
        print('\n--- 重复条目预览 ---')
        for key, items in dup_groups.items():
            print(f'\n电话: {key}，共 {len(items)} 条')
            for it in items:
                print(f'  id={it["id"]} ktt={it["ktt_name"]} risk={it["risk_level"]} reason={str(it["blacklist_reason"])[:40]}')
        print('\n--- 操作预览 ---')
        total_keep = len(unique_groups) + len(dup_groups) + len(no_phone)
        total_delete = sum(len(v) - 1 for v in dup_groups.values())
        print(f'将保留 {total_keep} 条（合并后），删除 {total_delete} 条重复')
        print(f'全部转为 SYSTEM 类型，owner_id 设为 NULL')
        print(f'\nDry-run 完成，未修改数据库。')
        conn.close()
        return

    # 确认
    print('\n即将执行以下操作：')
    total_keep = len(unique_groups) + len(dup_groups) + len(no_phone)
    total_delete = sum(len(v) - 1 for v in dup_groups.values())
    print(f'  保留 {total_keep} 条（合并后）')
    print(f'  删除 {total_delete} 条重复')
    print(f'  全部转为 SYSTEM 类型')
    confirm = input('\n确认继续？(yes/no): ').strip().lower()
    if confirm != 'yes':
        print('已取消。')
        conn.close()
        return

    merged = 0
    deleted = 0
    converted = 0

    try:
        # 1. 处理重复组：合并后保留一条
        for key, items in dup_groups.items():
            # 合并
            best_risk = items[0]['risk_level']
            for it in items[1:]:
                best_risk = higher_risk(best_risk, it['risk_level'])

            reasons = [it['blacklist_reason'] for it in items]
            merged_reason = merge_reasons(reasons)

            # 取第一条非空值
            def first_non_empty(field):
                for it in items:
                    v = it.get(field)
                    if v and str(v).strip():
                        return v
                return None

            keep = items[0]
            delete_ids = [it['id'] for it in items[1:]]

            # 更新保留条目
            cursor.execute("""
                UPDATE blacklist SET
                    blacklist_type = 'SYSTEM',
                    owner_id = NULL,
                    risk_level = %s,
                    blacklist_reason = %s,
                    ktt_name = %s,
                    wechat_name = %s,
                    order_address1 = %s,
                    order_address2 = %s
                WHERE id = %s
            """, (
                best_risk,
                merged_reason,
                first_non_empty('ktt_name'),
                first_non_empty('wechat_name'),
                first_non_empty('order_address1'),
                first_non_empty('order_address2'),
                keep['id']
            ))
            merged += 1

            # 删除重复条目
            if delete_ids:
                fmt = ','.join(['%s'] * len(delete_ids))
                cursor.execute(f"DELETE FROM blacklist WHERE id IN ({fmt})", delete_ids)
                deleted += len(delete_ids)

        # 2. 处理唯一有电话条目：直接转 SYSTEM
        for key, items in unique_groups.items():
            cursor.execute(
                "UPDATE blacklist SET blacklist_type = 'SYSTEM', owner_id = NULL WHERE id = %s",
                (items[0]['id'],)
            )
            converted += 1

        # 3. 处理无电话条目：直接转 SYSTEM
        for item in no_phone:
            cursor.execute(
                "UPDATE blacklist SET blacklist_type = 'SYSTEM', owner_id = NULL WHERE id = %s",
                (item['id'],)
            )
            converted += 1

        conn.commit()

        print(f'\n{sep}')
        print('迁移完成')
        print(f'  合并重复组: {merged} 组')
        print(f'  删除重复条目: {deleted} 条')
        print(f'  直接转换条目: {converted} 条')

        # 验证
        cursor.execute("SELECT blacklist_type, COUNT(*) FROM blacklist GROUP BY blacklist_type")
        print('\n迁移后黑名单分布：')
        for row in cursor.fetchall():
            print(f'  {row["blacklist_type"]}: {row["COUNT(*)"]} 条')
        print(sep)

    except Exception as e:
        conn.rollback()
        print(f'迁移失败，已回滚: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    run()
