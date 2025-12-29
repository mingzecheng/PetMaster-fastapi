-- 创建会员卡消费记录表
-- 执行命令: mysql -h 127.0.0.1 -P 3306 -u root -p 数据库名 < migrations/create_card_consumption_records.sql

CREATE TABLE IF NOT EXISTS card_consumption_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '消费记录ID',
    member_card_id BIGINT NOT NULL COMMENT '会员卡ID',
    amount DECIMAL(10, 2) NOT NULL COMMENT '消费金额',
    balance_before DECIMAL(10, 2) COMMENT '消费前余额',
    balance_after DECIMAL(10, 2) COMMENT '消费后余额',
    related_type VARCHAR(50) COMMENT '关联类型：appointment/boarding/product',
    related_id BIGINT COMMENT '关联ID',
    payment_id BIGINT COMMENT '关联支付ID（组合支付时）',
    remark VARCHAR(255) COMMENT '备注',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_consumption_card FOREIGN KEY (member_card_id) REFERENCES member_cards(id) ON DELETE CASCADE,
    CONSTRAINT fk_consumption_payment FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL,
    INDEX idx_card (member_card_id),
    INDEX idx_related (related_type, related_id),
    INDEX idx_payment (payment_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会员卡消费记录表';

-- 验证表创建
DESCRIBE card_consumption_records;
