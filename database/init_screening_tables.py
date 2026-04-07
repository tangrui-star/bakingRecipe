#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单检查系统 - 数据库表初始化脚本
"""

import pymysql
import os
from pathlib import Path

# 数据库配置
DB_CONFIG = {
    'host': '47.109.97.153',
    'port': 3306,
    'user': 'tangRui',
    'password': 'tangRui@2024',
    'database': 'baking_recipe_system',
    'charset': 'utf8mb4'
}

def init_screening_tables():
    """初始化订单检查表"""
    print("=" * 60)
    print("订单检查系统 - 数据库表初始化")
    print("=" * 60)
    
    try:
        # 连接数据库
        print("\n正在连接到MySQL数据库...")
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✓ 数据库连接成功")
        
        # 读取SQL脚本
        sql_file = Path(__file__).parent / 'screening_schema.sql'
        print(f"\n正在读取SQL脚本: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        print(f"✓ 找到 {len(sql_statements)} 条SQL语句")
        
        # 执行SQL语句
        print("\n正在执行SQL脚本...")
        for i, statement in enumerate(sql_statements, 1):
            try:
                cursor.execute(statement)
                print(f"✓ 执行语句 {i}/{len(sql_statements)}")
            except Exception as e:
                print(f"警告: 执行语句 {i} 时出错: {e}")
        
        conn.commit()
        print("\n✓ 订单检查表创建成功")
        
        # 验证表是否创建成功
        cursor.execute("SHOW TABLES LIKE 'order_screening%'")
        tables = cursor.fetchall()
        print(f"\n已创建的表: {[table[0] for table in tables]}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("初始化完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        raise

if __name__ == '__main__':
    init_screening_tables()
