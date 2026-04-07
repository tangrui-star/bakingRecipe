-- 黑名单系统数据库结构
-- MySQL 8.0+

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 黑名单表
DROP TABLE IF EXISTS `blacklist`;
CREATE TABLE `blacklist` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '黑名单ID',
  `shop_id` VARCHAR(36) COMMENT '店铺ID',
  `new_id` VARCHAR(10) UNIQUE COMMENT '10位唯一标识',
  `ktt_name` VARCHAR(100) COMMENT 'KTT名字',
  `wechat_name` VARCHAR(100) COMMENT '微信名字',
  `wechat_id` VARCHAR(100) COMMENT '微信号',
  `order_name_phone` TEXT COMMENT '下单名字和电话（原始）',
  `phone_numbers` JSON COMMENT '提取的电话号码列表',
  `order_address1` TEXT COMMENT '下单地址1',
  `order_address2` TEXT COMMENT '下单地址2',
  `blacklist_reason` TEXT COMMENT '入黑名单原因',
  `risk_level` ENUM('HIGH','MEDIUM','LOW') DEFAULT 'MEDIUM' COMMENT '风险等级',
  `created_by` VARCHAR(36) COMMENT '创建用户ID',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  INDEX `idx_shop_id` (`shop_id`),
  INDEX `idx_ktt_name` (`ktt_name`),
  INDEX `idx_risk_level` (`risk_level`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='黑名单表';

SET FOREIGN_KEY_CHECKS = 1;
