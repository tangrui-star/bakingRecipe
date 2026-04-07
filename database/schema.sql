-- 烘焙配方管理系统数据库结构
-- MySQL 8.0+

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='店铺表';

-- 配方品类表
DROP TABLE IF EXISTS `recipe_categories`;
CREATE TABLE `recipe_categories` (
  `id` VARCHAR(36) PRIMARY KEY COMMENT '品类ID',
  `name` VARCHAR(50) NOT NULL UNIQUE COMMENT '品类名称',
  `description` TEXT COMMENT '品类描述',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配方品类表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配方主表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配方版本表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='原料表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='配方版本-原料关联表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='制作步骤表';

SET FOREIGN_KEY_CHECKS = 1;
