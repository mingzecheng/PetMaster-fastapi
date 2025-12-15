-- =========================================
-- 订单管理系统 - 数据库迁移脚本
-- 添加订单表和订单明细表
-- 执行时间：2025-12-14
-- =========================================

USE pet_shop_db;

-- =========================================
-- 1. 订单主表
-- =========================================
CREATE TABLE IF NOT EXISTS orders
(
    id            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '订单ID',
    order_no      VARCHAR(50) NOT NULL UNIQUE COMMENT '订单编号',
    user_id       BIGINT      NOT NULL COMMENT '用户ID',
    payment_id    BIGINT COMMENT '支付记录ID',
    total_amount  DECIMAL(10, 2) NOT NULL COMMENT '订单总金额',
    status        VARCHAR(20) DEFAULT 'pending' COMMENT '订单状态: pending/paid/cancelled/completed/refunded',
    remark        TEXT COMMENT '订单备注',
    created_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at    TIMESTAMP   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    paid_at       TIMESTAMP COMMENT '支付时间',
    completed_at  TIMESTAMP COMMENT '完成时间',
    
    INDEX idx_order_no (order_no),
    INDEX idx_user_id (user_id),
    INDEX idx_payment_id (payment_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    
    CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_order_payment FOREIGN KEY (payment_id) REFERENCES payments (id) ON DELETE SET NULL
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='订单主表';

-- =========================================
-- 2. 订单明细表
-- =========================================
CREATE TABLE IF NOT EXISTS order_items
(
    id            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '明细ID',
    order_id      BIGINT         NOT NULL COMMENT '订单ID',
    product_id    BIGINT COMMENT '商品ID（可能已删除）',
    product_name  VARCHAR(100)   NOT NULL COMMENT '商品名称（快照）',
    product_price DECIMAL(10, 2) NOT NULL COMMENT '商品价格（快照）',
    quantity      INT            NOT NULL COMMENT '购买数量',
    subtotal      DECIMAL(10, 2) NOT NULL COMMENT '小计金额',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_order_id (order_id),
    INDEX idx_product_id (product_id),
    
    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='订单明细表';

-- =========================================
-- 说明
-- =========================================
-- 1. orders 表存储订单主信息
-- 2. order_items 表存储订单商品明细，使用商品快照避免商品删除/改价影响历史订单
-- 3. 外键约束：
--    - user_id → users.id (CASCADE删除)
--    - payment_id → payments.id (SET NULL，保留订单即使支付被删除)
--    - order_id → orders.id (CASCADE删除明细)
--    - product_id → products.id (SET NULL，保留历史记录)
