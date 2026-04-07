#!/usr/bin/env python3
"""数据库初始化脚本"""

import pymysql
import sys

# 数据库连接配置
DB_CONFIG = {
    'host': '47.109.97.153',
    'port': 3306,
    'user': 'root',
    'password': 'Root@2025!',
    'charset': 'utf8mb4'
}

DB_NAME = 'baking_recipe_system'

def init_database():
    """初始化数据库"""
    try:
        # 连接到MySQL服务器（不指定数据库）
        print("正在连接到MySQL服务器...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 创建数据库
        print(f"正在创建数据库 {DB_NAME}...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✓ 数据库 {DB_NAME} 创建成功")
        
        # 切换到新数据库
        cursor.execute(f"USE `{DB_NAME}`")
        
        # 读取并执行SQL文件
        print("正在读取SQL脚本...")
        with open('init_database.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句并执行
        print("正在执行SQL脚本...")
        sql_statements = sql_content.split(';')
        
        for i, statement in enumerate(sql_statements):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except Exception as e:
                    # 忽略某些错误（如CREATE DATABASE已存在）
                    if 'already exists' not in str(e).lower():
                        print(f"警告: 执行语句 {i+1} 时出错: {e}")
        
        connection.commit()
        
        # 验证表创建
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n✓ 成功创建 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 检查数据
        cursor.execute("SELECT COUNT(*) FROM recipe_categories")
        cat_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        ing_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM shops")
        shop_count = cursor.fetchone()[0]
        
        print(f"\n✓ 初始数据插入成功:")
        print(f"  - 品类: {cat_count} 条")
        print(f"  - 原料: {ing_count} 条")
        print(f"  - 店铺: {shop_count} 条")
        
        print(f"\n🎉 数据库初始化完成！")
        print(f"数据库名称: {DB_NAME}")
        print(f"数据库地址: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except FileNotFoundError:
        print("❌ 找不到 init_database.sql 文件")
        print("请确保在 database 目录下运行此脚本")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("烘焙配方管理系统 - 数据库初始化")
    print("=" * 60)
    print()
    
    success = init_database()
    sys.exit(0 if success else 1)
