-- 添加预约和寄养的支付相关字段
-- 执行前请先确认数据库名称（可能是 pet_shop_db 或其他名称）
-- 执行命令示例: 
--   mysql -h 127.0.0.1 -P 3306 -u root -p < migrations/add_payment_fields.sql
--   然后在MySQL提示符下输入: USE 你的数据库名;

-- 或者直接指定数据库:
--   mysql -h 127.0.0.1 -P 3306 -u root -p 数据库名 < migrations/add_payment_fields.sql

-- 修改 appointments 表
ALTER TABLE appointments 
ADD COLUMN payment_id BIGINT NULL COMMENT '支付记录ID' AFTER service_id,
ADD COLUMN price DECIMAL(10, 2) NULL COMMENT '服务价格快照' AFTER staff_id,
ADD COLUMN cancel_reason VARCHAR(200) NULL COMMENT '取消原因' AFTER status,
ADD INDEX idx_appointment_payment_id (payment_id),
ADD CONSTRAINT fk_appointments_payment FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL;

-- 修改 appointments 表的 status 枚举值
ALTER TABLE appointments 
MODIFY COLUMN status ENUM('pending', 'confirmed', 'completed', 'cancelled', 'refunded') NOT NULL DEFAULT 'pending' COMMENT '预约状态';

-- 修改 boarding 表
ALTER TABLE boarding 
ADD COLUMN payment_id BIGINT NULL COMMENT '支付记录ID' AFTER pet_id,
ADD COLUMN cancel_reason VARCHAR(200) NULL COMMENT '取消原因' AFTER notes,
ADD INDEX idx_boarding_payment_id (payment_id),
ADD CONSTRAINT fk_boarding_payment FOREIGN KEY (payment_id) REFERENCES payments(id) ON DELETE SET NULL;

-- 修改 boarding 表的 status 枚举值  
ALTER TABLE boarding
MODIFY COLUMN status ENUM('pending', 'active', 'completed', 'cancelled', 'refunded') NOT NULL DEFAULT 'pending' COMMENT '寄养状态';

-- 验证修改
DESCRIBE appointments;
DESCRIBE boarding;

