#!/bin/bash

# Database and Cache Deployment Script
# 量化交易建议系统 - 数据库部署

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}数据库和缓存服务部署${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}请不要使用 root 用户运行此脚本${NC}"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
DB_NAME=${DB_NAME:-quant_advisor}
DB_USER=${DB_USER:-postgres}
DB_PASSWORD=${DB_PASSWORD:-postgres}
REDIS_PASSWORD=${REDIS_PASSWORD:-redis}

echo -e "\n${YELLOW}1. 检查 PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL 已安装${NC}"
else
    echo -e "${YELLOW}安装 PostgreSQL...${NC}"
    if [ "$(uname)" == "Darwin" ]; then
        brew install postgresql@15
    elif [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y postgresql-15
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y postgresql15-server
    fi
fi

echo -e "\n${YELLOW}2. 检查 Redis...${NC}"
if command -v redis-cli &> /dev/null; then
    echo -e "${GREEN}✓ Redis 已安装${NC}"
else
    echo -e "${YELLOW}安装 Redis...${NC}"
    if [ "$(uname)" == "Darwin" ]; then
        brew install redis
    elif [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y redis-server
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y redis
    fi
fi

echo -e "\n${YELLOW}3. 配置 PostgreSQL...${NC}"

# Start PostgreSQL
if [ "$(uname)" == "Darwin" ]; then
    brew services start postgresql@15
else
    sudo systemctl start postgresql
fi

# Create database and user
echo -e "创建数据库用户和数据库..."
sudo -u postgres psql <<EOF
-- Create user
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';

-- Create database
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};

-- Connect to database
\c ${DB_NAME}

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO ${DB_USER};
EOF

echo -e "${GREEN}✓ PostgreSQL 配置完成${NC}"

echo -e "\n${YELLOW}4. 配置 Redis...${NC}"

# Configure Redis
if [ "$(uname)" == "Darwin" ]; then
    brew services start redis
else
    sudo systemctl start redis
fi

# Set Redis password
redis-cli CONFIG SET requirepass "${REDIS_PASSWORD}" 2>/dev/null || true

echo -e "${GREEN}✓ Redis 配置完成${NC}"

echo -e "\n${YELLOW}5. 运行数据库迁移...${NC}"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Alembic migrations
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    echo -e "${GREEN}✓ 数据库迁移完成${NC}"
else
    echo -e "${YELLOW}跳过数据库迁移（未找到 alembic.ini）${NC}"
fi

echo -e "\n${YELLOW}6. 初始化数据...${NC}"

# Run initialization script
if [ -f "scripts/init-data.py" ]; then
    python scripts/init-data.py
    echo -e "${GREEN}✓ 数据初始化完成${NC}"
else
    echo -e "${YELLOW}跳过数据初始化（未找到初始化脚本）${NC}"
fi

echo -e "\n${YELLOW}7. 验证部署...${NC}"

# Test PostgreSQL connection
if PGPASSWORD="${DB_PASSWORD}" psql -h localhost -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL 连接成功${NC}"
else
    echo -e "${RED}✗ PostgreSQL 连接失败${NC}"
    exit 1
fi

# Test Redis connection
if redis-cli -a "${REDIS_PASSWORD}" ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis 连接成功${NC}"
else
    echo -e "${RED}✗ Redis 连接失败${NC}"
    exit 1
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}数据库和缓存服务部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n数据库信息:"
echo -e "  数据库: ${DB_NAME}"
echo -e "  用户: ${DB_USER}"
echo -e "  端口: 5432"
echo -e "\nRedis 信息:"
echo -e "  端口: 6379"
echo -e "  密码: ${REDIS_PASSWORD}"
echo -e "\n${YELLOW}请确保更新 .env 文件中的数据库连接信息${NC}"
