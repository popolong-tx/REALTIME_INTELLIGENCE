#!/bin/bash

# Backend Deployment Script
# 量化交易建议系统 - 后端部署

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}后端服务部署${NC}"
echo -e "${GREEN}========================================${NC}"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
APP_NAME=${APP_NAME:-quant-trading-advisor}
APP_PORT=${APP_PORT:-8000}
APP_WORKERS=${APP_WORKERS:-4}
APP_ENV=${APP_ENV:-production}

echo -e "\n${YELLOW}1. 检查 Python 环境...${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "Python 版本: ${PYTHON_VERSION}"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo -e "创建虚拟环境..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo -e "\n${YELLOW}2. 安装依赖...${NC}"

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ 依赖安装完成${NC}"

echo -e "\n${YELLOW}3. 运行数据库迁移...${NC}"

# Run Alembic migrations
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    echo -e "${GREEN}✓ 数据库迁移完成${NC}"
else
    echo -e "${YELLOW}跳过数据库迁移${NC}"
fi

echo -e "\n${YELLOW}4. 收集静态文件...${NC}"

# Collect static files (if applicable)
if [ -f "manage.py" ]; then
    python manage.py collectstatic --noinput
fi

echo -e "\n${YELLOW}5. 创建日志目录...${NC}"

# Create log directory
mkdir -p logs
chmod 755 logs

echo -e "\n${YELLOW}6. 配置 systemd 服务...${NC}"

# Create systemd service file
sudo tee /etc/systemd/system/${APP_NAME}.service > /dev/null <<EOF
[Unit]
Description=Quant Trading Advisor Backend
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app \\
    --host ${HOST:-0.0.0.0} \\
    --port ${APP_PORT} \\
    --workers ${APP_WORKERS} \\
    --log-level ${LOG_LEVEL:-info} \\
    --access-log \\
    --log-config logging.ini
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ systemd 服务配置完成${NC}"

echo -e "\n${YELLOW}7. 启动服务...${NC}"

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable ${APP_NAME}
sudo systemctl restart ${APP_NAME}

# Wait for service to start
sleep 5

# Check service status
if sudo systemctl is-active --quiet ${APP_NAME}; then
    echo -e "${GREEN}✓ 服务启动成功${NC}"
else
    echo -e "${RED}✗ 服务启动失败${NC}"
    sudo systemctl status ${APP_NAME}
    exit 1
fi

echo -e "\n${YELLOW}8. 配置 Nginx 反向代理...${NC}"

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/${APP_NAME} > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Frontend
    location / {
        root /var/www/${APP_NAME}/frontend/build;
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /var/www/${APP_NAME}/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:${APP_PORT}/health;
        access_log off;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx 配置完成${NC}"

echo -e "\n${YELLOW}9. 配置防火墙...${NC}"

# Configure firewall
if command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow ${APP_PORT}/tcp
    echo -e "${GREEN}✓ 防火墙配置完成${NC}"
fi

echo -e "\n${YELLOW}10. 验证部署...${NC}"

# Health check
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${APP_PORT}/health 2>/dev/null || echo "000")

if [ "$HEALTH_CHECK" == "200" ]; then
    echo -e "${GREEN}✓ 健康检查通过${NC}"
else
    echo -e "${YELLOW}⚠ 健康检查返回: ${HEALTH_CHECK}${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}后端服务部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n服务信息:"
echo -e "  应用名称: ${APP_NAME}"
echo -e "  端口: ${APP_PORT}"
echo -e "  工作进程: ${APP_WORKERS}"
echo -e "  环境: ${APP_ENV}"
echo -e "\n常用命令:"
echo -e "  查看状态: sudo systemctl status ${APP_NAME}"
echo -e "  查看日志: sudo journalctl -u ${APP_NAME} -f"
echo -e "  重启服务: sudo systemctl restart ${APP_NAME}"
echo -e "  停止服务: sudo systemctl stop ${APP_NAME}"
