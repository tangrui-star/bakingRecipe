-- 创建数据库
CREATE DATABASE IF NOT EXISTS `baking_recipe_system` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `baking_recipe_system`;

-- 烘焙配方管理系统数据库结构
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 店铺表
DROP TABLE IF EXISTS `shops`;
CREATE TABLE `shops` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '店铺ID',
  `name` VARCHAR(100) NOT NULL COMMENT '店铺名称',
  `owner_name` VARCHAR(50) COMMENT '店主姓名',
  `contact_phone` VARCHAR(20) COMMENT '联系电话',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='店铺表';

-- 配方品类表
DROP TABLE IF EXISTS `recipe_categories`;
CREATE TABLE `recipe_categories` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '品类ID',
  `name` VARCHAR(50) NOT NULL UNIQUE COMMENT '品类名称',
  `description` TEXT COMMENT '品类描述',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配方品类表';

-- 配方主表
DROP TABLE IF EXISTS `recipes`;
CREATE TABLE `recipes` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '配方唯一ID',
  `shop_id` VARCHAR(36) NOT NULL COMMENT '店铺ID',
  `category_id` VARCHAR(36) NOT NULL COMMENT '品类ID',
  `current_name` VARCHAR(100) NOT NULL COMMENT '当前配方名称',
  `current_version` INT DEFAULT 1 COMMENT '当前版本号',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`shop_id`) REFERENCES `shops`(`id`),
  FOREIGN KEY (`category_id`) REFERENCES `recipe_categories`(`id`),
  INDEX `idx_shop_category` (`shop_id`, `category_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配方主表';

-- 配方版本表
DROP TABLE IF EXISTS `recipe_versions`;
CREATE TABLE `recipe_versions` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '版本ID',
  `recipe_id` VARCHAR(36) NOT NULL COMMENT '配方ID',
  `version` INT NOT NULL COMMENT '版本号',
  `name` VARCHAR(100) NOT NULL COMMENT '配方名称',
  `base_quantity` DECIMAL(10,2) COMMENT '基础数量（个）',
  `base_weight` DECIMAL(10,2) COMMENT '单个重量（克）',
  `total_calories` DECIMAL(10,2) COMMENT '总热量（千卡）',
  `notes` TEXT COMMENT '备注说明',
  `calculation_rule` TEXT COMMENT '计算规则',
  `created_by` VARCHAR(50) COMMENT '创建人',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`recipe_id`) REFERENCES `recipes`(`id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_recipe_version` (`recipe_id`, `version`),
  INDEX `idx_recipe_id` (`recipe_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配方版本表';

-- 原料表
DROP TABLE IF EXISTS `ingredients`;
CREATE TABLE `ingredients` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '原料ID',
  `name` VARCHAR(100) NOT NULL UNIQUE COMMENT '原料名称',
  `unit` VARCHAR(10) DEFAULT 'g' COMMENT '计量单位',
  `calories_per_100g` DECIMAL(10,2) COMMENT '每100克热量（千卡）',
  `protein_per_100g` DECIMAL(10,2) COMMENT '每100克蛋白质（克）',
  `fat_per_100g` DECIMAL(10,2) COMMENT '每100克脂肪（克）',
  `carbs_per_100g` DECIMAL(10,2) COMMENT '每100克碳水化合物（克）',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='原料表';

-- 配方版本-原料关联表
DROP TABLE IF EXISTS `recipe_version_ingredients`;
CREATE TABLE `recipe_version_ingredients` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '关联ID',
  `recipe_version_id` VARCHAR(36) NOT NULL COMMENT '配方版本ID',
  `ingredient_id` VARCHAR(36) NOT NULL COMMENT '原料ID',
  `weight` DECIMAL(10,2) NOT NULL COMMENT '重量（克）',
  `sort_order` INT DEFAULT 0 COMMENT '排序',
  FOREIGN KEY (`recipe_version_id`) REFERENCES `recipe_versions`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`ingredient_id`) REFERENCES `ingredients`(`id`),
  INDEX `idx_recipe_version` (`recipe_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='配方版本-原料关联表';

-- 制作步骤表
DROP TABLE IF EXISTS `recipe_steps`;
CREATE TABLE `recipe_steps` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '步骤ID',
  `recipe_version_id` VARCHAR(36) NOT NULL COMMENT '配方版本ID',
  `step_number` INT NOT NULL COMMENT '步骤序号',
  `description` TEXT NOT NULL COMMENT '步骤描述',
  `duration_minutes` INT COMMENT '耗时（分钟）',
  `temperature` INT COMMENT '温度（℃）',
  FOREIGN KEY (`recipe_version_id`) REFERENCES `recipe_versions`(`id`) ON DELETE CASCADE,
  INDEX `idx_recipe_version` (`recipe_version_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='制作步骤表';

-- 插入默认品类
INSERT INTO `recipe_categories` (`id`, `name`, `description`) VALUES
('cat-001', '贝果', '贝果类面包'),
('cat-002', '碱水包', '碱水类面包'),
('cat-003', '欧包', '欧式面包'),
('cat-004', '恰巴塔', '意式恰巴塔'),
('cat-005', '曲奇', '美式曲奇'),
('cat-006', '燕麦片', '烤燕麦片'),
('cat-007', '布朗尼', '布朗尼类'),
('cat-008', '其他', '其他类别');

-- 插入常用原料及营养数据
INSERT INTO `ingredients` (`id`, `name`, `unit`, `calories_per_100g`, `protein_per_100g`, `fat_per_100g`, `carbs_per_100g`) VALUES
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
('ing-040', '香蕉', 'g', 89, 1.1, 0.2, 22.8);

-- 插入示例店铺
INSERT INTO `shops` (`id`, `name`, `owner_name`, `contact_phone`) VALUES
('shop-001', '示例烘焙店', '张师傅', '13800138000');

SET FOREIGN_KEY_CHECKS = 1;

-- 显示创建结果
SELECT '数据库创建成功！' AS message;
SELECT COUNT(*) AS category_count FROM recipe_categories;
SELECT COUNT(*) AS ingredient_count FROM ingredients;
