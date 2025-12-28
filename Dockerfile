# =====================================================
# PetMaster FastAPI 后端 Dockerfile
# 用于云端部署 (Render, Zeabur, Railway, Fly.io 等)
# =====================================================

# 使用官方 Python 3.11 精简镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖 (用于 MySQL 客户端和加密库)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建上传目录
RUN mkdir -p /app/uploads/pets /app/logs

# 暴露端口 (云平台会自动映射)
EXPOSE 8001

# 启动命令 (使用 uvicorn 生产模式)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
