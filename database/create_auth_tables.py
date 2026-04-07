#!/usr/bin/env python3
"""创建用户认证表"""

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

def create_auth_tables():
    """创建用户认证相关表"""
    try:
        print("正在连接到数据库...")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 用户表
        print("\n创建用户表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `users` (
              `id` VARCHAR(36) PRIMARY KEY COMMENT '用户ID',
              `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
              `email` VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
              `phone` VARCHAR(20) COMMENT '手机号',
              `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
              `avatar` VARCHAR(255) COMMENT '头像URL',
              `gender` ENUM('male', 'female', 'other') COMMENT '性别',
              `shop_id` VARCHAR(36) COMMENT '关联店铺ID',
              `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否激活',
              `is_verified` BOOLEAN DEFAULT FALSE COMMENT '是否验证邮箱',
              `last_login` TIMESTAMP NULL COMMENT '最后登录时间',
              `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              FOREIGN KEY (`shop_id`) REFERENCES `shops`(`id`) ON DELETE SET NULL,
              INDEX `idx_email` (`email`),
              INDEX `idx_username` (`username`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表'
        """)
        print("✓ 用户表创建成功")
        
        # 刷新令牌表
        print("\n创建刷新令牌表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `refresh_tokens` (
              `id` VARCHAR(36) PRIMARY KEY COMMENT '令牌ID',
              `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
              `token` VARCHAR(500) NOT NULL UNIQUE COMMENT '刷新令牌',
              `expires_at` TIMESTAMP NOT NULL COMMENT '过期时间',
              `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
              INDEX `idx_user_id` (`user_id`),
              INDEX `idx_token` (`token`),
              INDEX `idx_expires_at` (`expires_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='刷新令牌表'
        """)
        print("✓ 刷新令牌表创建成功")
        
        # 登录日志表
        print("\n创建登录日志表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `login_logs` (
              `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
              `user_id` VARCHAR(36) COMMENT '用户ID',
              `ip_address` VARCHAR(45) COMMENT 'IP地址',
              `user_agent` VARCHAR(255) COMMENT '用户代理',
              `login_status` ENUM('success', 'failed') NOT NULL COMMENT '登录状态',
              `fail_reason` VARCHAR(100) COMMENT '失败原因',
              `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
              INDEX `idx_user_id` (`user_id`),
              INDEX `idx_created_at` (`created_at`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表'
        """)
        print("✓ 登录日志表创建成功")
        
        connection.commit()
        
        # 验证表创建
        cursor.execute("SHOW TABLES LIKE 'users'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"\n✓ 用户表验证成功，当前用户数: {user_count}")
        
        cursor.close()
        connection.close()
        
        print("\n🎉 用户认证表创建完成！")
        return True
        
    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("创建用户认证表")
    print("=" * 60)
    
    success = create_auth_tables()
    sys.exit(0 if success else 1)
