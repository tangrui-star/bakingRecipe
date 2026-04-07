-- 用户认证相关表结构
USE `baking_recipe_system`;

SET FOREIGN_KEY_CHECKS = 0;

-- 用户表
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 刷新令牌表
DROP TABLE IF EXISTS `refresh_tokens`;
CREATE TABLE `refresh_tokens` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '令牌ID',
  `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
  `token` VARCHAR(500) NOT NULL UNIQUE COMMENT '刷新令牌',
  `expires_at` TIMESTAMP NOT NULL COMMENT '过期时间',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_token` (`token`),
  INDEX `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='刷新令牌表';

-- 登录日志表
DROP TABLE IF EXISTS `login_logs`;
CREATE TABLE `login_logs` (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';

-- 修改shops表，添加与用户的关联
ALTER TABLE `shops` ADD COLUMN `owner_user_id` VARCHAR(36) COMMENT '店主用户ID' AFTER `id`;
ALTER TABLE `shops` ADD INDEX `idx_owner_user_id` (`owner_user_id`);

SET FOREIGN_KEY_CHECKS = 1;

SELECT '用户认证表创建成功！' AS message;
