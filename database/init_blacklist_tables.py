#!/usr/bin/env python3
"""黑名单表初始化脚本"""

import pymysql
import sys
import os

# 数据库连接配置
DB_CONFIG = {
    'host': '47.109.97.153',
    'port': 3306,
    'user': 'root',
    'password': 'Root@2025!',
    'charset': 'utf8mb4'
}

DB_NAME = 'baking_recipe_system'

def init_blacklist_tables():
    """初始化黑名单表"""
    try:
        # 连接到数据库
        print("正在连接到MySQL数据库...")
        connection = pymysql.connect(**DB_CONFIG, database=DB_NAME)
        cursor = connection.cursor()
        
        # 读取并执行SQL文件
        print("正在读取黑名单表SQL脚本...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(script_dir, 'blacklist_schema.sql')
        
        with open(sql_file, 'r', encoding='utf-8') as f:
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
                    print(f"警告: 执行语句 {i+1} 时出错: {e}")
        
        connection.commit()
        
        # 验证表创建
        cursor.execute("SHOW TABLES LIKE 'blacklist'")
        result = cursor.fetchone()
        
        if result:
            print(f"\n✓ 黑名单表创建成功")
            
            # 显示表结构
            cursor.execute("DESCRIBE blacklist")
            columns = cursor.fetchall()
            print(f"\n表结构:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        else:
            print("\n❌ 黑名单表创建失败")
            return False
        
        print(f"\n🎉 黑名单表初始化完成！")
        
        cursor.close()
        connection.close()
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ 找不到 blacklist_schema.sql 文件")
        print(f"请确保文件在: {sql_file}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("黑名单系统 - 数据库表初始化")
    print("=" * 60)
    print()
    
    success = init_blacklist_tables()
    sys.exit(0 if success else 1)
