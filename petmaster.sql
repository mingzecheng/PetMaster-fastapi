-- =========================================
-- 宠物店管理系统数据库设计（核心业务版）
-- 技术栈：FastAPI + MySQL + uni-app + 1Panel
-- 核心业务：宠物档案、商品库存、会员管理、预约与寄养
-- =========================================
-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS pet_shop_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE pet_shop_db;

-- =========================================
-- 1. 用户与会员表
-- =========================================
CREATE TABLE IF NOT EXISTS users
(
    id            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    username      VARCHAR(50)  NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    mobile        VARCHAR(20) UNIQUE COMMENT '手机号',
    email         VARCHAR(100) UNIQUE COMMENT '邮箱',
    role          ENUM ('admin','staff','member') DEFAULT 'member' COMMENT '角色：管理员/员工/会员',
    created_at    TIMESTAMP                       DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at    TIMESTAMP                       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='用户与会员表';

-- =========================================
-- 2. 宠物档案表
-- =========================================
CREATE TABLE IF NOT EXISTS pets
(
    id            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '宠物ID',
    owner_id      BIGINT      NOT NULL COMMENT '宠物主人ID，关联 users.id',
    name          VARCHAR(50) NOT NULL COMMENT '宠物名称',
    species       VARCHAR(50) COMMENT '宠物种类（狗、猫等）',
    breed         VARCHAR(50) COMMENT '品种',
    gender        ENUM ('male','female') COMMENT '性别',
    birthday      DATE COMMENT '生日',
    weight        DECIMAL(5, 2) COMMENT '体重(kg)',
    health_status VARCHAR(255) COMMENT '健康状况描述',
    image_url     VARCHAR(500) DEFAULT NULL COMMENT '宠物图片URL',
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_pet_owner FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='宠物档案表';

-- =========================================
-- 3. 健康记录表
-- =========================================
CREATE TABLE IF NOT EXISTS pet_health_records
(
    id           BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '健康记录ID',
    pet_id       BIGINT NOT NULL COMMENT '宠物ID，关联 pets.id',
    record_date  DATE   NOT NULL COMMENT '记录日期',
    description  TEXT COMMENT '健康检查或治疗描述',
    veterinarian VARCHAR(50) COMMENT '兽医姓名',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    CONSTRAINT fk_health_pet FOREIGN KEY (pet_id) REFERENCES pets (id) ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='宠物健康记录表';

-- =========================================
-- 4. 商品表
-- =========================================
CREATE TABLE IF NOT EXISTS products
(
    id         BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '商品ID',
    name       VARCHAR(100)   NOT NULL COMMENT '商品名称',
    category   VARCHAR(50) COMMENT '商品分类',
    price      DECIMAL(10, 2) NOT NULL COMMENT '商品价格',
    stock      INT       DEFAULT 0 COMMENT '库存数量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='商品库存表';

-- =========================================
-- 5. 服务项目表
-- =========================================
CREATE TABLE IF NOT EXISTS services
(
    id               BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '服务ID',
    name             VARCHAR(100)   NOT NULL COMMENT '服务名称',
    description      TEXT COMMENT '服务描述',
    price            DECIMAL(10, 2) NOT NULL COMMENT '服务价格',
    duration_minutes INT COMMENT '服务时长（分钟）',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='服务项目表';

-- =========================================
-- 6. 预约表
-- =========================================
CREATE TABLE IF NOT EXISTS appointments
(
    id               BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '预约ID',
    pet_id           BIGINT   NOT NULL COMMENT '宠物ID',
    service_id       BIGINT   NOT NULL COMMENT '服务ID',
    appointment_time DATETIME NOT NULL COMMENT '预约时间',
    staff_id         BIGINT COMMENT '员工ID，关联 users.id',
    status           ENUM ('pending','confirmed','completed','cancelled') DEFAULT 'pending' COMMENT '预约状态',
    created_at       TIMESTAMP                                            DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at       TIMESTAMP                                            DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_appointment_pet FOREIGN KEY (pet_id) REFERENCES pets (id) ON DELETE CASCADE,
    CONSTRAINT fk_appointment_service FOREIGN KEY (service_id) REFERENCES services (id) ON DELETE CASCADE,
    CONSTRAINT fk_appointment_staff FOREIGN KEY (staff_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='预约服务表';

-- =========================================
-- 7. 寄养表
-- =========================================
CREATE TABLE IF NOT EXISTS boarding
(
    id         BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '寄养ID',
    pet_id     BIGINT NOT NULL COMMENT '宠物ID',
    start_date DATE   NOT NULL COMMENT '寄养开始日期',
    end_date   DATE   NOT NULL COMMENT '寄养结束日期',
    daily_rate DECIMAL(10, 2) COMMENT '每日费用',
    staff_id   BIGINT COMMENT '负责员工ID',
    status     ENUM ('ongoing','completed','cancelled') DEFAULT 'ongoing' COMMENT '寄养状态',
    created_at TIMESTAMP                                DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP                                DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT fk_boarding_pet FOREIGN KEY (pet_id) REFERENCES pets (id) ON DELETE CASCADE,
    CONSTRAINT fk_boarding_staff FOREIGN KEY (staff_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='寄养管理表';

-- =========================================
-- 8. 积分与消费记录表
-- =========================================
CREATE TABLE IF NOT EXISTS transactions
(
    id            BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '交易ID',
    user_id       BIGINT                                                   NOT NULL COMMENT '会员ID',
    type          ENUM ('purchase','service','points_add','points_deduct') NOT NULL COMMENT '交易类型',
    related_id    BIGINT COMMENT '关联ID：商品ID或服务ID',
    amount        DECIMAL(10, 2) COMMENT '交易金额',
    points_change INT       DEFAULT 0 COMMENT '积分变化',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '交易时间',
    CONSTRAINT fk_transaction_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='会员积分及消费记录表';

