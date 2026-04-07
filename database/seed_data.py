#!/usr/bin/env python3
"""插入初始数据"""

import pymysql
import sys

DB_CONFIG = {
    'host': '47.109.97.153',
    'port': 3306,
    'user': 'root',
    'password': 'Root@2025!',
    'database': 'baking_recipe_system',
    'charset': 'utf8mb4'
}

def seed_data():
    """插入初始数据"""
    try:
        print("正在连接到数据库...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 插入品类数据
        print("\n正在插入品类数据...")
        categories = [
            ('cat-001', '贝果', '贝果类面包'),
            ('cat-002', '碱水包', '碱水类面包'),
            ('cat-003', '欧包', '欧式面包'),
            ('cat-004', '恰巴塔', '意式恰巴塔'),
            ('cat-005', '曲奇', '美式曲奇'),
            ('cat-006', '燕麦片', '烤燕麦片'),
            ('cat-007', '布朗尼', '布朗尼类'),
            ('cat-008', '其他', '其他类别')
        ]
        
        for cat in categories:
            cursor.execute(
                "INSERT IGNORE INTO recipe_categories (id, name, description) VALUES (%s, %s, %s)",
                cat
            )
        print(f"✓ 插入 {len(categories)} 个品类")
        
        # 插入原料数据
        print("\n正在插入原料数据...")
        ingredients = [
            ('ing-001', '高筋面粉', 'g', 350, 11.5, 1.5, 74.0),
            ('ing-002', '全麦面粉', 'g', 340, 13.2, 2.5, 71.0),
            ('ing-003', '水', 'g', 0, 0, 0, 0),
            ('ing-004', '酵母粉', 'g', 325, 40.0, 7.0, 41.0),
            ('ing-005', '盐', 'g', 0, 0, 0, 0),
            ('ing-006', '糖', 'g', 400, 0, 0, 100.0),
            ('ing-007', '黄油', 'g', 717, 0.9, 81.0, 0.1),
            ('ing-008', '鸡蛋', 'g', 147, 13.3, 8.8, 2.8),
            ('ing-009', '肉松', 'g', 396, 41.8, 10.2, 30.3),
            ('ing-010', '芝士', 'g', 328, 25.0, 23.5, 3.5),
            ('ing-011', '番茄', 'g', 15, 0.9, 0.2, 3.3),
            ('ing-012', '咸蛋黄', 'g', 190, 13.9, 14.2, 1.4),
            ('ing-013', '黑芝麻粉', 'g', 531, 19.1, 46.1, 24.0),
            ('ing-014', '花生', 'g', 567, 24.8, 44.3, 21.7),
            ('ing-015', '腰果', 'g', 552, 17.3, 36.7, 41.0),
            ('ing-016', '红豆', 'g', 324, 20.2, 0.6, 63.4),
            ('ing-017', '可可粉', 'g', 229, 19.6, 13.7, 57.9),
            ('ing-018', '抹茶粉', 'g', 324, 29.6, 5.3, 39.0),
            ('ing-019', '斑斓粉', 'g', 350, 8.0, 2.0, 75.0),
            ('ing-020', '椰奶粉', 'g', 669, 6.6, 68.8, 14.1),
            ('ing-021', '奶粉', 'g', 491, 25.5, 26.5, 38.4),
            ('ing-022', '泡打粉', 'g', 53, 0, 0, 27.7),
            ('ing-023', '植物油', 'g', 899, 0, 99.9, 0),
            ('ing-024', '洋葱', 'g', 39, 1.1, 0.1, 9.0),
            ('ing-025', '香菜', 'g', 23, 2.1, 0.5, 3.3),
            ('ing-026', '鸡枞菌', 'g', 20, 2.5, 0.3, 3.0),
            ('ing-027', '鸡肉', 'g', 167, 19.3, 9.4, 0),
            ('ing-028', '乳酪丁', 'g', 350, 22.0, 28.0, 2.0),
            ('ing-029', '葡萄干', 'g', 299, 2.5, 0.4, 77.4),
            ('ing-030', '茉莉花', 'g', 0, 0, 0, 0),
            ('ing-031', '巧克力', 'g', 546, 4.9, 31.3, 61.2),
            ('ing-032', '核桃', 'g', 654, 14.9, 65.2, 13.7),
            ('ing-033', '燕麦片', 'g', 367, 15.0, 6.7, 61.6),
            ('ing-034', '海苔', 'g', 177, 29.4, 1.7, 44.3),
            ('ing-035', '香肠', 'g', 508, 13.0, 45.0, 11.0),
            ('ing-036', '辣椒', 'g', 32, 2.0, 0.2, 7.0),
            ('ing-037', '肉桂粉', 'g', 247, 3.9, 1.2, 80.6),
            ('ing-038', '奇亚籽', 'g', 486, 16.5, 30.7, 42.1),
            ('ing-039', '艾草粉', 'g', 321, 10.0, 2.5, 65.0),
            ('ing-040', '香蕉', 'g', 89, 1.1, 0.2, 22.8)
        ]
        
        for ing in ingredients:
            cursor.execute(
                """INSERT IGNORE INTO ingredients 
                (id, name, unit, calories_per_100g, protein_per_100g, fat_per_100g, carbs_per_100g) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                ing
            )
        print(f"✓ 插入 {len(ingredients)} 个原料")
        
        # 插入示例店铺
        print("\n正在插入示例店铺...")
        cursor.execute(
            "INSERT IGNORE INTO shops (id, name, owner_name, contact_phone) VALUES (%s, %s, %s, %s)",
            ('shop-001', '示例烘焙店', '张师傅', '13800138000')
        )
        print("✓ 插入示例店铺")
        
        connection.commit()
        
        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM recipe_categories")
        cat_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        ing_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM shops")
        shop_count = cursor.fetchone()[0]
        
        print(f"\n✓ 数据插入完成:")
        print(f"  - 品类: {cat_count} 条")
        print(f"  - 原料: {ing_count} 条")
        print(f"  - 店铺: {shop_count} 条")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 初始数据插入成功！")
        return True
        
    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("烘焙配方管理系统 - 插入初始数据")
    print("=" * 60)
    
    success = seed_data()
    sys.exit(0 if success else 1)
