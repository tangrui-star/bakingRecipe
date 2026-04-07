-- 订单黑名单检查系统数据表

-- 订单检查记录表
CREATE TABLE IF NOT EXISTS order_screening_records (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    shop_id VARCHAR(36) NOT NULL COMMENT '店铺ID',
    file_name VARCHAR(255) NOT NULL COMMENT '上传的文件名',
    total_orders INT NOT NULL DEFAULT 0 COMMENT '总订单数',
    matched_count INT NOT NULL DEFAULT 0 COMMENT '命中黑名单数量',
    screening_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '检查时间',
    created_by VARCHAR(36) COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_shop_id (shop_id),
    INDEX idx_screening_time (screening_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单检查记录表';

-- 订单检查详情表
CREATE TABLE IF NOT EXISTS order_screening_details (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    screening_id INT NOT NULL COMMENT '检查记录ID',
    order_name VARCHAR(100) COMMENT '订单姓名',
    order_phone VARCHAR(20) COMMENT '订单电话',
    order_address TEXT COMMENT '订单地址',
    order_data JSON COMMENT '完整订单数据',
    blacklist_id INT NOT NULL COMMENT '命中的黑名单ID',
    match_type VARCHAR(20) NOT NULL COMMENT '匹配类型: phone/name/address/wechat',
    match_value VARCHAR(255) COMMENT '匹配的值',
    risk_level VARCHAR(20) COMMENT '风险等级',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_screening_id (screening_id),
    INDEX idx_blacklist_id (blacklist_id),
    FOREIGN KEY (screening_id) REFERENCES order_screening_records(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单检查详情表';
