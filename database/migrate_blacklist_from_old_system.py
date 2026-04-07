#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从旧BlackNameList系统迁移黑名单数据到bakingRecipe系统
"""

import pymysql
import sys
import json
from datetime import datetime

# 旧系统数据库配置（BlackNameList）
OLD_DB_CONFIG = {
    'host': '47.109.97.153',
    'port': 3306,
    'user': 'root',
    'password': 'Root@2025!',
    'database': 'blacklist',
    'charset': 'utf8mb4'
}

# 新系统数据库配置（bakingRecipe）
NEW_DB_CONFIG = {
    'host': '47.109.97.153',
    'port': 3306,
    'user': 'root',
    'password': 'Root@2025!',
    'database': 'baking_recipe_system',
    'charset': 'utf8mb4'
}

# 默认店铺ID（需要先在bakingRecipe系统中创建店铺）
DEFAULT_SHOP_ID = '2c2f8124-150b-4351-956a-5d86d2f377aa'  # test的烘焙店


def migrate_blacklist_data(dry_run=True):
    """
    迁移黑名单数据
    
    Args:
        dry_run: 如果为True，只预览不执行实际迁移
    """
    old_conn = None
    new_conn = None
    
    try:
        # 连接到旧数据库
        print("正在连接到BlackNameList数据库...")
        old_conn = pymysql.connect(**OLD_DB_CONFIG)
        old_cursor = old_conn.cursor(pymysql.cursors.DictCursor)
        
        # 连接到新数据库
        print("正在连接到bakingRecipe数据库...")
        new_conn = pymysql.connect(**NEW_DB_CONFIG)
        new_cursor = new_conn.cursor()
        
        # 检查默认店铺ID
        if not DEFAULT_SHOP_ID:
            print("\n❌ 错误：请先设置DEFAULT_SHOP_ID")
            print("请在bakingRecipe系统中创建店铺，然后将店铺ID填入此脚本")
            return False
        
        # 验证店铺存在
        new_cursor.execute("SELECT id FROM shops WHERE id = %s", (DEFAULT_SHOP_ID,))
        if not new_cursor.fetchone():
            print(f"\n❌ 错误：店铺ID {DEFAULT_SHOP_ID} 不存在")
            return False
        
        # 查询旧系统的黑名单数据
        print("\n正在读取BlackNameList数据...")
        old_cursor.execute("""
            SELECT 
                id,
                sequence_number,
                new_id,
                ktt_name,
                wechat_name,
                wechat_id,
                order_name_phone,
                phone_numbers,
                order_address1,
                order_address2,
                blacklist_reason,
                risk_level,
                created_by,
                created_at,
                updated_at
            FROM blacklist
            ORDER BY id
        """)
        
        old_records = old_cursor.fetchall()
        total_count = len(old_records)
        
        print(f"✓ 找到 {total_count} 条黑名单记录")
        
        if dry_run:
            print("\n【预览模式】以下是前5条记录：")
            for i, record in enumerate(old_records[:5]):
                print(f"\n记录 {i+1}:")
                print(f"  ID: {record['id']}")
                print(f"  唯一标识: {record['new_id']}")
                print(f"  KTT名字: {record['ktt_name']}")
                print(f"  电话: {record['phone_numbers']}")
                print(f"  风险等级: {record['risk_level']}")
                print(f"  原因: {record['blacklist_reason'][:50] if record['blacklist_reason'] else 'N/A'}...")
            
            print(f"\n共 {total_count} 条记录待迁移")
            print("\n要执行实际迁移，请运行: python migrate_blacklist_from_old_system.py --execute")
            return True
        
        # 执行迁移
        print("\n开始迁移数据...")
        success_count = 0
        error_count = 0
        errors = []
        
        for record in old_records:
            try:
                # 处理phone_numbers字段（可能是JSON字符串或列表）
                phone_numbers = record['phone_numbers']
                if isinstance(phone_numbers, str):
                    try:
                        phone_numbers = json.loads(phone_numbers)
                    except:
                        phone_numbers = []
                elif phone_numbers is None:
                    phone_numbers = []
                
                # 转换phone_numbers为JSON字符串
                phone_numbers_json = json.dumps(phone_numbers, ensure_ascii=False)
                
                # 映射风险等级
                risk_level_map = {
                    'HIGH': 'HIGH',
                    'MEDIUM': 'MEDIUM',
                    'LOW': 'LOW',
                    'high': 'HIGH',
                    'medium': 'MEDIUM',
                    'low': 'LOW'
                }
                risk_level = risk_level_map.get(record['risk_level'], 'MEDIUM')
                
                # 插入到新数据库
                insert_sql = """
                    INSERT INTO blacklist (
                        shop_id,
                        new_id,
                        ktt_name,
                        wechat_name,
                        wechat_id,
                        order_name_phone,
                        phone_numbers,
                        order_address1,
                        order_address2,
                        blacklist_reason,
                        risk_level,
                        created_by,
                        created_at,
                        updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """
                
                new_cursor.execute(insert_sql, (
                    DEFAULT_SHOP_ID,
                    record['new_id'],
                    record['ktt_name'],
                    record['wechat_name'],
                    record['wechat_id'],
                    record['order_name_phone'],
                    phone_numbers_json,
                    record['order_address1'],
                    record['order_address2'],
                    record['blacklist_reason'],
                    risk_level,
                    record['created_by'],
                    record['created_at'],
                    record['updated_at']
                ))
                
                success_count += 1
                
                if success_count % 10 == 0:
                    print(f"  已迁移 {success_count}/{total_count} 条记录...")
                
            except Exception as e:
                error_count += 1
                error_msg = f"记录ID {record['id']} 迁移失败: {str(e)}"
                errors.append(error_msg)
                print(f"  ⚠️  {error_msg}")
        
        # 提交事务
        new_conn.commit()
        
        # 输出结果
        print(f"\n{'='*60}")
        print("迁移完成！")
        print(f"{'='*60}")
        print(f"总记录数: {total_count}")
        print(f"成功迁移: {success_count}")
        print(f"失败记录: {error_count}")
        
        if errors:
            print(f"\n错误详情:")
            for error in errors[:10]:  # 只显示前10个错误
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... 还有 {len(errors) - 10} 个错误")
        
        # 验证迁移结果
        new_cursor.execute("SELECT COUNT(*) FROM blacklist WHERE shop_id = %s", (DEFAULT_SHOP_ID,))
        migrated_count = new_cursor.fetchone()[0]
        print(f"\n验证: bakingRecipe系统中现有 {migrated_count} 条黑名单记录")
        
        return True
        
    except pymysql.Error as e:
        print(f"\n❌ 数据库错误: {e}")
        if new_conn:
            new_conn.rollback()
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        if new_conn:
            new_conn.rollback()
        return False
    finally:
        if old_conn:
            old_conn.close()
        if new_conn:
            new_conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("BlackNameList → bakingRecipe 黑名单数据迁移工具")
    print("=" * 60)
    print()
    
    # 检查命令行参数
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        dry_run = False
        print("⚠️  警告：即将执行实际迁移！")
        confirm = input("确认继续？(yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            sys.exit(0)
    
    success = migrate_blacklist_data(dry_run=dry_run)
    sys.exit(0 if success else 1)
