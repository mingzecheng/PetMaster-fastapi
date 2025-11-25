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
PetMaster/
├── app/                    # 应用核心代码
│   ├── models/            # SQLAlchemy ORM数据模型
│   │   ├── user.py        # 用户模型
│   │   ├── pet.py         # 宠物模型
│   │   ├── service.py     # 服务模型
│   │   ├── product.py     # 商品模型
│   │   ├── appointment.py # 预约模型
│   │   ├── boarding.py    # 寄养模型
│   │   ├── transaction.py # 交易模型
│   │   └── payment.py     # 支付模型
│   ├── schemas/           # Pydantic 请求/响应数据模型
│   ├── crud/              # CRUD 数据操作层
│   ├── routers/           # API 路由处理器
│   ├── utils/             # 工具函数和中间件
│   │   ├── security.py    # JWT认证和密码加密
│   │   ├── alipay.py      # 支付宝SDK集成
│   │   ├── dependencies.py # 依赖注入
│   │   ├── exceptions.py  # 自定义异常
│   │   └── logger.py      # 日志配置
│   ├── config.py          # 应用配置管理
│   └── database.py        # 数据库连接和初始化
├── Dockerfile             # Docker 容器构建文件
├── docker-compose.yml     # Docker Compose 编排文件
├── alembic.ini           # 数据库迁移配置
├── main.py               # 应用启动入口
├── init_data.py          # 数据库初始化脚本
├── petmaster.sql         # 数据库 SQL 初始化脚本
├── requirements.txt      # Python 依赖包
├── 部署文档.md           # 详细部署指南
└── README.md            # 项目说明
```

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

### 核心功能模块

#### 认证与授权 (`/api/v1/auth`)
- `POST /register` - 用户注册
- `POST /login` - 用户登录获取 Token

#### 用户管理 (`/api/v1/users`)
- `GET /me` - 获取当前用户信息
- `PUT /me` - 更新当前用户信息
- `GET /` - 获取用户列表（管理员）
- `GET /{user_id}` - 获取指定用户信息（管理员）
- `PUT /{user_id}` - 更新用户信息（管理员）
- `DELETE /{user_id}` - 删除用户（管理员）

#### 宠物档案 (`/api/v1/pets`)
- `POST /` - 创建宠物档案
- `GET /` - 查看宠物列表
- `GET /{pet_id}` - 查看宠物详情
- `PUT /{pet_id}` - 更新宠物信息
- `DELETE /{pet_id}` - 删除宠物

#### 商品管理 (`/api/v1/products`)
- `POST /` - 创建商品（员工）
- `GET /` - 查看商品列表
- `GET /{product_id}` - 查看商品详情
- `PUT /{product_id}` - 更新商品（员工）
- `DELETE /{product_id}` - 下架商品（员工）
- `PATCH /{product_id}/stock` - 更新库存（员工）

#### 服务管理 (`/api/v1/services`)
- `POST /` - 创建服务（员工）
- `GET /` - 查看服务列表
- `GET /{service_id}` - 查看服务详情
- `PUT /{service_id}` - 更新服务（员工）
- `DELETE /{service_id}` - 删除服务（员工）

#### 预约管理 (`/api/v1/appointments`)
- `POST /` - 创建服务预约
- `GET /` - 查看预约列表
- `GET /{appointment_id}` - 查看预约详情
- `PUT /{appointment_id}` - 更新预约状态
- `DELETE /{appointment_id}` - 取消预约

#### 寄养管理 (`/api/v1/boarding`)
- `POST /` - 创建寄养记录
- `GET /` - 查看寄养列表
- `GET /ongoing` - 获取进行中的寄养（员工）
- `GET /{boarding_id}` - 查看寄养详情
- `PUT /{boarding_id}` - 更新寄养状态（员工）
- `DELETE /{boarding_id}` - 删除寄养（员工）

#### 交易管理 (`/api/v1/transactions`)
- `POST /` - 创建交易（员工）
- `GET /` - 查看交易列表
- `GET /me` - 查看个人交易记录
- `GET /me/points` - 查看积分余额
- `GET /me/spending` - 查看消费统计
- `GET /{transaction_id}` - 查看交易详情

#### 支付管理 (`/api/v1/payments`)
- `POST /alipay/create` - 创建支付宝支付订单
- `GET /{out_trade_no}/status` - 查询支付状态
- `GET /` - 查看支付列表
- `POST /alipay/notify` - 支付宝异步通知回调

## 权限与角色

系统采用基于角色的权限控制（RBAC）模型，分为三种用户角色：

| 角色 | admin（管理员）| staff（员工）| member（会员）|
|------|---------------|-------------|-------------|
| 用户管理 | ✓ | ✗ | ✗ |
| 商品管理 | ✓ | ✓ | ✗ |
| 服务管理 | ✓ | ✓ | ✗ |
| 预约管理 | ✓ | ✓ | ✓ |
| 寄养管理 | ✓ | ✓ | ✓ |
| 宠物档案 | ✓ | ✓ | 仅自己的 |
| 交易记录 | ✓ | ✓ | 仅自己的 |
| 支付管理 | ✓ | ✓ | ✓ |

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