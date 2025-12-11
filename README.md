# PetMaster 宠物店管理系统

一个基于 FastAPI + MySQL + uni-app 的完整宠物店管理系统。支持宠物档案管理、服务预约、商品销售、寄养管理、支付交易等全面的业务功能。

## 技术栈

- **后端框架**: FastAPI 0.104.1
- **Web 服务器**: Uvicorn 0.24.0
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0.23
- **认证**: JWT (python-jose 3.3.0)
- **密码加密**: bcrypt 4.0.1
- **配置管理**: Pydantic 2.5.0, python-dotenv 1.0.0
- **日志**: loguru 0.7.2
- **支付集成**: python-alipay-sdk 3.0.4
- **前端**: uni-app (管理后台 + 用户小程序)
- **容器化**: Docker & Docker Compose
- **运维工具**: 1Panel (可选)

## 项目结构

```
PetMaster-fastapi/
├── app/                        # 应用核心代码
│   ├── __init__.py
│   ├── config.py               # 应用配置管理
│   ├── database.py             # 数据库连接和初始化
│   │
│   ├── models/                 # SQLAlchemy ORM 数据模型 (10个)
│   │   ├── __init__.py         # 模型导出
│   │   ├── user.py             # 用户模型
│   │   ├── pet.py              # 宠物模型
│   │   ├── service.py          # 服务项目模型
│   │   ├── product.py          # 商品模型
│   │   ├── appointment.py      # 预约模型
│   │   ├── boarding.py         # 寄养模型
│   │   ├── transaction.py      # 交易模型
│   │   ├── payment.py          # 支付模型
│   │   └── member.py           # 会员卡/等级/积分模型
│   │
│   ├── schemas/                # Pydantic 请求/响应数据模型 (10个)
│   │   ├── __init__.py         # Schema导出
│   │   ├── user.py             # 用户Schema
│   │   ├── pet.py              # 宠物Schema（含健康记录）
│   │   ├── service.py          # 服务项目Schema
│   │   ├── product.py          # 商品Schema
│   │   ├── appointment.py      # 预约Schema
│   │   ├── boarding.py         # 寄养Schema
│   │   ├── transaction.py      # 交易Schema
│   │   ├── payment.py          # 支付Schema
│   │   └── member.py           # 会员卡/等级Schema
│   │
│   ├── crud/                   # CRUD 数据操作层 (10个)
│   │   ├── __init__.py         # CRUD导出
│   │   ├── base.py             # CRUD基类（泛型实现）
│   │   ├── crud_user.py        # 用户CRUD
│   │   ├── crud_pet.py         # 宠物CRUD
│   │   ├── crud_service.py     # 服务CRUD
│   │   ├── crud_product.py     # 商品CRUD
│   │   ├── crud_appointment.py # 预约CRUD
│   │   ├── crud_boarding.py    # 寄养CRUD
│   │   ├── crud_transaction.py # 交易CRUD
│   │   └── crud_payment.py     # 支付CRUD
│   │
│   ├── routers/                # API 路由处理器 (14个)
│   │   ├── __init__.py
│   │   ├── auth.py             # 认证路由（登录/注册）
│   │   ├── users.py            # 用户管理路由
│   │   ├── pets.py             # 宠物档案路由
│   │   ├── pet_health_records.py # 宠物健康记录路由
│   │   ├── services.py         # 服务项目路由
│   │   ├── products.py         # 商品管理路由
│   │   ├── appointments.py     # 预约管理路由
│   │   ├── boarding.py         # 寄养管理路由
│   │   ├── transactions.py     # 交易记录路由
│   │   ├── payments.py         # 支付管理路由
│   │   ├── member_cards.py     # 会员卡管理路由
│   │   ├── member_levels.py    # 会员等级管理路由
│   │   └── points.py           # 积分管理路由
│   │
│   ├── services/               # 业务服务层 (2个)
│   │   ├── __init__.py
│   │   └── payment_service.py  # 统一支付服务
│   │
│   └── utils/                  # 工具函数和中间件 (8个)
│       ├── __init__.py
│       ├── security.py         # JWT认证和密码加密
│       ├── alipay.py           # 支付宝SDK集成
│       ├── dependencies.py     # 依赖注入（权限控制）
│       ├── exceptions.py       # 自定义异常处理
│       ├── logger.py           # 日志配置（loguru）
│       ├── file_utils.py       # 文件上传工具
│       └── recaptcha.py        # Google reCAPTCHA验证
│
├── scripts/                    # 脚本工具
│   └── test_alipay_sign.py     # 支付宝签名测试脚本
├── logs/                       # 日志输出目录
├── uploads/                    # 文件上传目录
├── Dockerfile                  # Docker 容器构建文件
├── docker-compose.yml          # Docker Compose 编排文件
├── alembic.ini                 # 数据库迁移配置
├── main.py                     # 应用启动入口
├── init_data.py                # 数据库初始化脚本
├── petmaster.sql               # 数据库 SQL 初始化脚本
├── requirements.txt            # Python 依赖包
├── 部署文档.md                  # 详细部署指南
└── README.md                   # 项目说明
```

### 模块说明

#### 数据模型层 (Models)

| 文件 | 说明 |
|------|------|
| `user.py` | 用户表，包含角色（admin/staff/member）、认证信息 |
| `pet.py` | 宠物档案，支持健康记录关联 |
| `service.py` | 服务项目定义（洗澡、美容、寄养等） |
| `product.py` | 商品信息和库存管理 |
| `appointment.py` | 服务预约记录 |
| `boarding.py` | 宠物寄养记录 |
| `transaction.py` | 消费交易记录 |
| `payment.py` | 支付订单和状态 |
| `member.py` | 会员卡、会员等级、积分规则、充值记录 |

#### API路由层 (Routers)

| 路由 | 路径前缀 | 功能 |
|------|---------|------|
| `auth.py` | `/auth` | 用户注册、登录认证 |
| `users.py` | `/users` | 用户信息管理 |
| `pets.py` | `/pets` | 宠物档案CRUD |
| `pet_health_records.py` | `/pets/{id}/health-records` | 宠物健康记录 |
| `services.py` | `/services` | 服务项目管理 |
| `products.py` | `/products` | 商品管理 |
| `appointments.py` | `/appointments` | 预约管理 |
| `boarding.py` | `/boarding` | 寄养管理 |
| `transactions.py` | `/transactions` | 交易记录 |
| `payments.py` | `/payments` | 支付管理 |
| `member_cards.py` | `/member-cards` | 会员卡管理 |
| `member_levels.py` | `/member-levels` | 会员等级管理 |
| `points.py` | `/points` | 积分管理 |

#### 工具层 (Utils)

| 文件 | 功能 |
|------|------|
| `security.py` | JWT Token生成/验证、密码哈希 |
| `alipay.py` | 支付宝沙箱/生产环境集成 |
| `dependencies.py` | FastAPI依赖注入、权限验证 |
| `exceptions.py` | 自定义HTTP异常类 |
| `logger.py` | 日志配置和格式化 |
| `file_utils.py` | 文件上传、存储、验证 |
| `recaptcha.py` | Google reCAPTCHA v2/v3验证 |


## 配置说明

### 环境变量配置

创建 `.env` 文件，配置以下环境变量：

```env
# 应用配置
APP_NAME=PetMaster
APP_VERSION=1.0.0
DEBUG=true
API_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8001

# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=petmaster
DATABASE_PASSWORD=your_password
DATABASE_NAME=pet_shop_db

# JWT 认证配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760

# 支付宝配置
ALIPAY_APP_ID=your_app_id
ALIPAY_APP_PRIVATE_KEY=your_private_key
ALIPAY_ALI_PUBLIC_KEY=your_public_key
ALIPAY_USE_SANDBOX=true
```

### 配置优先级（从高到低）：
1. 环境变量（系统环境变量）
2. `.env` 文件（项目根目录）
3. 代码中的默认值

> **安全提示**: 不要将 `.env` 文件提交到 Git 仓库，建议使用 `.env.example` 作为配置模板。

## 快速开始

### 前置要求

- Python 3.10+
- MySQL 8.0+
- Docker & Docker Compose (可选)

### 方式一：本地开发

#### 1. 克隆项目

```bash
git clone <repository-url>
cd PetMaster
```

#### 2. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量

在项目根目录创建 `.env` 文件（参考上面的配置说明）

#### 5. 初始化数据库

```bash
# 方法一：使用 SQL 文件（需要已创建数据库）
mysql -u petmaster -p pet_shop_db < petmaster.sql

# 方法二：运行初始化脚本（自动创建表）
python init_data.py

# 方法三：使用 Alembic 迁移
alembic upgrade head
```

#### 6. 启动应用

```bash
# 方法一：直接运行 main.py（IDE 右键运行）
python main.py

# 方法二：使用 Uvicorn 开发服务器
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

#### 7. 访问应用

- **API 文档**: http://localhost:8001/api/v1/docs
- **ReDoc 文档**: http://localhost:8001/api/v1/redoc
- **OpenAPI Schema**: http://localhost:8001/api/v1/openapi.json

### 方式二：Docker Compose（推荐生产使用）

#### 1. 配置环境变量

创建 `.env` 文件：

```bash
DATABASE_USER=petmaster
DATABASE_PASSWORD=your_secure_password
DATABASE_NAME=pet_shop_db
SECRET_KEY=your-very-secret-key-change-this-in-production
```

#### 2. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

#### 3. 初始化数据

```bash
# 数据库会自动初始化，或手动执行
docker-compose exec app python init_data.py
```

访问：http://localhost:8000/api/v1/docs

## API 文档

系统已集成 Swagger UI 和 ReDoc，启动后可直接访问 API 文档。

### 认证模块 (`/api/v1/auth`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/register` | 用户注册 | 公开 |
| POST | `/login` | 用户登录获取 Token | 公开 |

**注册请求参数**:
- `username` (string, 必需): 用户名，3-50字符，唯一
- `password` (string, 必需): 密码，最少6字符
- `mobile` (string, 可选): 手机号
- `email` (string, 可选): 邮箱

**登录请求参数**:
- `username` (string, 必需): 用户名或手机号
- `password` (string, 必需): 密码
- `recaptcha_token` (string, 可选): reCAPTCHA token

---

### 用户管理 (`/api/v1/users`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/me` | 获取当前用户信息 | 已登录 |
| PUT | `/me` | 更新当前用户信息 | 已登录 |
| POST | `/me/change-password` | 修改密码 | 已登录 |
| GET | `/` | 获取用户列表 | 员工+ |
| POST | `/` | 创建新用户 | 管理员 |
| GET | `/{user_id}` | 获取指定用户信息 | 管理员 |
| PUT | `/{user_id}` | 更新指定用户信息 | 管理员 |
| DELETE | `/{user_id}` | 删除用户 | 管理员 |

**查询参数** (GET /):
- `skip` (int): 分页偏移量，默认0
- `limit` (int): 每页数量，默认100
- `role` (string): 按角色筛选 (admin/staff/member)
- `username` (string): 按用户名模糊搜索

---

### 宠物档案 (`/api/v1/pets`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/` | 创建宠物档案 | 已登录 |
| GET | `/` | 获取宠物列表 | 已登录 |
| GET | `/{pet_id}` | 获取宠物详情 | 已登录 |
| PUT | `/{pet_id}` | 更新宠物信息 | 已登录 |
| DELETE | `/{pet_id}` | 删除宠物 | 已登录 |
| POST | `/{pet_id}/upload-image` | 上传宠物图片 | 已登录 |
| DELETE | `/{pet_id}/image` | 删除宠物图片 | 已登录 |
| POST | `/{pet_id}/health-records` | 添加健康记录 | 已登录 |
| GET | `/{pet_id}/health-records` | 获取健康记录列表 | 已登录 |

**创建/更新参数**:
- `name` (string): 宠物名称
- `species` (string): 物种（狗/猫/其他）
- `breed` (string): 品种
- `age` (int): 年龄
- `gender` (string): 性别
- `weight` (decimal): 体重(kg)
- `owner_id` (int): 主人用户ID

> **权限说明**: 普通会员只能操作自己的宠物，员工和管理员可以操作所有宠物

---

### 宠物健康记录 (`/api/v1/pet_health_records`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/` | 创建健康记录 | 已登录 |
| GET | `/pet/{pet_id}` | 获取宠物的所有健康记录 | 已登录 |
| GET | `/{record_id}` | 获取健康记录详情 | 已登录 |
| PUT | `/{record_id}` | 更新健康记录 | 已登录 |
| DELETE | `/{record_id}` | 删除健康记录 | 已登录 |

**健康记录字段**:
- `pet_id` (int): 宠物ID
- `record_date` (date): 记录日期
- `record_type` (string): 记录类型（体检/疫苗/驱虫/手术等）
- `description` (string): 描述
- `hospital` (string): 医院名称
- `doctor` (string): 医生姓名
- `cost` (decimal): 费用

---

### 商品管理 (`/api/v1/products`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/` | 创建商品 | 员工+ |
| GET | `/` | 获取商品列表 | 公开 |
| GET | `/{product_id}` | 获取商品详情 | 公开 |
| PUT | `/{product_id}` | 更新商品信息 | 员工+ |
| DELETE | `/{product_id}` | 删除商品 | 员工+ |
| PATCH | `/{product_id}/stock` | 更新库存 | 员工+ |

**查询参数** (GET /):
- `category` (string): 按分类筛选
- `name` (string): 按名称搜索

**库存更新参数**:
- `quantity` (int): 库存变化量（正数增加，负数减少）

---

### 服务管理 (`/api/v1/services`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/` | 创建服务项目 | 员工+ |
| GET | `/` | 获取服务列表 | 公开 |
| GET | `/{service_id}` | 获取服务详情 | 公开 |
| PUT | `/{service_id}` | 更新服务信息 | 员工+ |
| DELETE | `/{service_id}` | 删除服务 | 员工+ |

**服务字段**:
- `name` (string): 服务名称
- `description` (string): 服务描述
- `price` (decimal): 价格
- `duration` (int): 服务时长(分钟)
- `is_active` (bool): 是否启用

---

### 预约管理 (`/api/v1/appointments`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/` | 创建预约 | 已登录 |
| GET | `/` | 获取预约列表 | 已登录 |
| GET | `/{appointment_id}` | 获取预约详情 | 已登录 |
| PUT | `/{appointment_id}` | 更新预约 | 已登录 |
| DELETE | `/{appointment_id}` | 取消预约 | 已登录 |

**查询参数** (GET /):
- `pet_id` (int): 按宠物筛选
- `status_filter` (string): 按状态筛选 (pending/confirmed/completed/cancelled)
- `start_date` (datetime): 开始日期
- `end_date` (datetime): 结束日期

**预约状态**:
- `pending`: 待确认
- `confirmed`: 已确认
- `completed`: 已完成
- `cancelled`: 已取消

---

### 寄养管理 (`/api/v1/boarding`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/` | 创建寄养记录 | 已登录 |
| GET | `/` | 获取寄养列表 | 已登录 |
| GET | `/ongoing` | 获取进行中的寄养 | 员工+ |
| GET | `/{boarding_id}` | 获取寄养详情 | 已登录 |
| PUT | `/{boarding_id}` | 更新寄养信息 | 员工+ |
| DELETE | `/{boarding_id}` | 删除寄养记录 | 员工+ |

**寄养字段**:
- `pet_id` (int): 宠物ID
- `start_date` (date): 开始日期
- `end_date` (date): 结束日期
- `daily_rate` (decimal): 日费用
- `special_care` (string): 特殊护理需求
- `status` (string): 状态 (reserved/checked_in/checked_out/cancelled)

---

### 交易管理 (`/api/v1/transactions`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/` | 创建交易记录 | 员工+ |
| GET | `/` | 获取交易列表 | 已登录 |
| GET | `/me` | 获取我的交易记录 | 已登录 |
| GET | `/me/points` | 获取我的总积分 | 已登录 |
| GET | `/me/spending` | 获取我的总消费 | 已登录 |
| GET | `/{transaction_id}` | 获取交易详情 | 已登录 |

**查询参数** (GET /):
- `user_id` (int): 按用户筛选（员工+）
- `transaction_type` (string): 按类型筛选

---

### 支付管理 (`/api/v1/payments`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/alipay/create` | 创建支付宝支付 | 已登录 |
| GET | `/{out_trade_no}/status` | 查询支付状态 | 已登录 |
| GET | `/{out_trade_no}/poll` | 轮询支付状态 | 已登录 |
| GET | `/` | 获取支付列表 | 已登录 |
| POST | `/alipay/notify` | 支付宝异步通知 | 公开 |

**创建支付参数**:
- `amount` (decimal): 支付金额（元）
- `subject` (string): 商品标题
- `description` (string): 商品描述
- `related_id` (int): 关联ID
- `related_type` (string): 关联类型 (product/appointment/member_card_recharge)

---

### 会员卡管理 (`/api/v1/member_cards`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| POST | `/` | 创建会员卡 | 管理员 |
| GET | `/{card_id}` | 获取会员卡详情 | 已登录 |
| GET | `/user/{user_id}` | 获取用户的会员卡 | 已登录 |
| POST | `/{card_id}/recharge` | 会员卡充值（后台） | 管理员 |
| GET | `/{card_id}/recharge-records` | 获取充值记录 | 已登录 |
| POST | `/{card_id}/freeze` | 冻结会员卡 | 管理员 |
| POST | `/{card_id}/unfreeze` | 解冻会员卡 | 管理员 |
| DELETE | `/{card_id}` | 注销会员卡 | 管理员 |
| POST | `/{card_id}/recharge-payment` | 创建充值支付（自助） | 已登录 |
| GET | `/{card_id}/recharge-payment/{out_trade_no}` | 查询充值支付状态 | 已登录 |

**会员卡状态**:
- `active`: 正常使用
- `frozen`: 已冻结

---

### 会员等级管理 (`/api/v1/member_levels`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/` | 获取所有会员等级 | 公开 |
| GET | `/{level_id}` | 获取等级详情 | 公开 |
| POST | `/` | 创建会员等级 | 管理员 |
| PUT | `/{level_id}` | 更新会员等级 | 管理员 |
| DELETE | `/{level_id}` | 删除会员等级 | 管理员 |

**等级字段**:
- `name` (string): 等级名称
- `level` (int): 等级序号
- `min_points` (int): 最低积分要求
- `discount` (decimal): 折扣率
- `description` (string): 描述
- `is_active` (bool): 是否启用

---

### 积分管理 (`/api/v1/points`)

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/users/{user_id}/records` | 获取用户积分明细 | 已登录 |
| POST | `/users/{user_id}/adjust` | 手动调整积分 | 管理员 |
| POST | `/transactions/{transaction_id}/earn` | 消费获得积分 | 已登录 |

**积分规则**:
- 消费1元 = 1积分
- 积分可用于会员等级升级
- 管理员可手动调整用户积分

## 权限与角色

系统采用基于角色的权限控制（RBAC）模型，分为三种用户角色：

| 功能模块 | admin（管理员）| staff（员工）| member（会员）|
|----------|---------------|-------------|---------------|
| 用户管理 | ✓ | ✗ | ✗ |
| 商品管理 | ✓ | ✓ | ✗ |
| 服务管理 | ✓ | ✓ | ✗ |
| 预约管理 | ✓ | ✓ | ✓ |
| 寄养管理 | ✓ | ✓ | ✓ |
| 宠物档案 | ✓ | ✓ | 仅自己的 |
| 健康记录 | ✓ | ✓ | 仅自己宠物的 |
| 交易记录 | ✓ | ✓ | 仅自己的 |
| 支付管理 | ✓ | ✓ | ✓ |
| 会员卡管理 | ✓ | ✓ | 仅自己的 |
| 会员等级管理 | ✓ | ✗ | ✗ |
| 积分规则管理 | ✓ | ✗ | ✗ |
| 积分查询 | ✓ | ✓ | 仅自己的 |

**认证方式**: JWT Token（Bearer Token）
- 获取 Token：调用 `/api/v1/auth/login`
- 使用 Token：在请求 Header 中添加 `Authorization: Bearer <token>`
- Token 过期时间：30 分钟（可在 `.env` 中配置）

## 开发指南

### 项目代码规范

- **代码风格**: 遵循 PEP 8 规范
- **类型提示**: 所有函数都应包含类型提示
- **文档字符串**: 使用 docstring 记录类和函数
- **异常处理**: 使用 `app/utils/exceptions.py` 中的自定义异常

### 添加新功能的步骤

1. **定义数据模型** (`app/models/`)
   ```python
   from sqlalchemy import Column, String, Integer
   from app.database import Base
   
   class MyModel(Base):
       __tablename__ = "my_table"
       id = Column(Integer, primary_key=True)
       name = Column(String(100))
   ```

2. **定义 Pydantic Schema** (`app/schemas/`)
   ```python
   from pydantic import BaseModel
   
   class MySchema(BaseModel):
       name: str
       
       class Config:
           from_attributes = True
   ```

3. **实现 CRUD 操作** (`app/crud/`)
   ```python
   from app.crud.base import CRUDBase
   from app.models.my_model import MyModel
   from app.schemas.my_schema import MySchema
   
   crud_my_model = CRUDBase[MyModel, MySchema, MySchema](MyModel)
   ```

4. **创建 API 路由** (`app/routers/`)
   ```python
   from fastapi import APIRouter
   from app.crud.my_crud import crud_my_model
   
   router = APIRouter(prefix="/my-resource", tags=["My Resource"])
   
   @router.post("/")
   def create_item(item: MySchema):
       return crud_my_model.create(item)
   ```

5. **在 main.py 中注册路由**
   ```python
   from app.routers import my_router
   app.include_router(my_router.router, prefix=settings.API_PREFIX)
   ```

### 数据库迁移

使用 Alembic 进行数据库版本控制：

```bash
# 创建新的迁移文件（自动检测 ORM 变更）
alembic revision --autogenerate -m "add new table"

# 查看迁移历史
alembic history

# 执行迁移（升级）
alembic upgrade head

# 回滚到上一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision>
```

### 日志输出

使用 `loguru` 库进行日志记录：

```python
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
```

### 异常处理

```python
from app.utils.exceptions import ValidationError, NotFoundError, ForbiddenError

# 验证错误
raise ValidationError("Invalid input")

# 资源不存在
raise NotFoundError("Resource not found")

# 权限不足
raise ForbiddenError("Access denied")
```

## 部署指南

详细的部署说明请参考项目根目录中的 `部署文档.md`，包含以下部署方式：

- **Docker Compose 部署**（推荐）- 一键启动完整环境
- **1Panel 平台部署** - 可视化运维管理
- **服务器直接部署** - 传统虚拟主机部署

### 快速部署（Docker Compose）

```bash
# 1. 配置环境变量
echo "DATABASE_PASSWORD=your_password" > .env
echo "SECRET_KEY=your_secret_key" >> .env

# 2. 启动服务
docker-compose up -d

# 3. 访问应用
# http://localhost:8000/api/v1/docs
```

### 生产环境建议

- 使用 Nginx 反向代理和负载均衡
- 启用 HTTPS 和 SSL 证书
- 配置防火墙和安全组规则
- 定期备份数据库和上传文件
- 监控应用性能和日志
- 使用强密码和定期更新依赖

## 前端对接

### uni-app 前端配置

#### 1. API 基础地址配置

```javascript
// utils/request.js
const BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8001/api/v1'
  : 'https://api.your-domain.com/api/v1';

export const request = (options) => {
  return uni.request({
    url: BASE_URL + options.url,
    method: options.method || 'GET',
    data: options.data || {},
    header: {
      'Authorization': 'Bearer ' + uni.getStorageSync('token'),
      'Content-Type': 'application/json',
      ...options.header
    }
  });
};
```

#### 2. 登录认证流程

```javascript
// 登录
const login = async (username, password) => {
  const res = await request({
    url: '/auth/login',
    method: 'POST',
    data: { username, password }
  });
  
  if (res.data.access_token) {
    uni.setStorageSync('token', res.data.access_token);
    uni.setStorageSync('user', res.data.user);
  }
  return res;
};

// 获取当前用户
const getCurrentUser = async () => {
  const res = await request({
    url: '/users/me',
    method: 'GET'
  });
  return res.data;
};
```

#### 3. 跨域配置

Backend 已在 `config.py` 中配置 CORS，确保 `CORS_ORIGINS` 包含前端地址：

```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080","https://your-domain.com"]
```

### 常见对接问题

**Q: 跨域请求失败？**
A: 检查 `.env` 中的 `CORS_ORIGINS` 配置是否包含前端地址。

**Q: Token 认证失败？**
A: 确保：
1. Token 在请求 Header 中格式正确：`Authorization: Bearer <token>`
2. Token 未过期
3. `SECRET_KEY` 配置正确

**Q: 上传文件失败？**
A: 检查 `UPLOAD_DIR` 目录权限和 `MAX_UPLOAD_SIZE` 配置。

## 常见问题 (FAQ)

### 数据库连接失败

**原因**：数据库未启动或连接信息错误

**解决**：
```bash
# 检查 MySQL 状态
service mysql status

# 验证连接信息
mysql -h <DATABASE_HOST> -u <DATABASE_USER> -p<DATABASE_PASSWORD>
```

### JWT 认证错误

**原因**：Token 过期或 `SECRET_KEY` 配置错误

**解决**：
1. 重新登录获取新 Token
2. 确保 `.env` 中的 `SECRET_KEY` 没有改变

### CORS 错误

**原因**：前端域名未在允许列表中

**解决**：更新 `.env` 中的 `CORS_ORIGINS`

## 技术支持

- **文档**: 查看 `部署文档.md` 获取详细的部署和运维指南
- **API 文档**: 启动应用后访问 `/api/v1/docs`
- **日志**: 查看 `logs/` 目录中的应用日志

## 许可证

MIT