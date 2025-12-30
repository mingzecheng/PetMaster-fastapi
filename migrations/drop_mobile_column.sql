-- 删除 users 表的 mobile 字段
-- 执行前请确保已有数据已经迁移或不再需要手机号字段

ALTER TABLE users DROP COLUMN IF EXISTS mobile;
