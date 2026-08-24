#!/bin/bash

# Frontend Deployment Script
# 量化交易建议系统 - 前端部署

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}前端应用部署${NC}"
echo -e "${GREEN}========================================${NC}"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
APP_NAME=${APP_NAME:-quant-trading-advisor}
DEPLOY_DIR=${DEPLOY_DIR:-/var/www/${APP_NAME}}
BACKEND_URL=${BACKEND_URL:-http://localhost:8000}

echo -e "\n${YELLOW}1. 检查 Node.js 环境...${NC}"

# Check Node.js version
NODE_VERSION=$(node --version 2>&1)
echo -e "Node.js 版本: ${NODE_VERSION}"

if [ -z "$NODE_VERSION" ]; then
    echo -e "${RED}Node.js 未安装，请先安装 Node.js 18+${NC}"
    exit 1
fi

echo -e "\n${YELLOW}2. 安装依赖...${NC}"

# Navigate to frontend directory
cd frontend

# Install dependencies
npm ci --production=false

echo -e "${GREEN}✓ 依赖安装完成${NC}"

echo -e "\n${YELLOW}3. 配置环境变量...${NC}"

# Create production environment file
cat > .env.production <<EOF
REACT_APP_API_URL=${BACKEND_URL}
REACT_APP_ENV=production
GENERATE_SOURCEMAP=false
EOF

echo -e "${GREEN}✓ 环境变量配置完成${NC}"

echo -e "\n${YELLOW}4. 构建生产版本...${NC}"

# Build production version
npm run build

echo -e "${GREEN}✓ 构建完成${NC}"

echo -e "\n${YELLOW}5. 部署到服务器...${NC}"

# Create deploy directory
sudo mkdir -p ${DEPLOY_DIR}

# Copy build files
sudo cp -r build/* ${DEPLOY_DIR}/

# Set permissions
sudo chown -R www-data:www-data ${DEPLOY_DIR}
sudo chmod -R 755 ${DEPLOY_DIR}

echo -e "${GREEN}✓ 部署完成${NC}"

echo -e "\n${YELLOW}6. 配置 Nginx...${NC}"

# Create Nginx configuration for frontend
sudo tee /etc/nginx/sites-available/${APP_NAME}-frontend > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    root ${DEPLOY_DIR};
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml+rss;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # SPA fallback
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/${APP_NAME}-frontend /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx 配置完成${NC}"

echo -e "\n${YELLOW}7. 配置 SSL (Let's Encrypt)...${NC}"

# Check if certbot is installed
if command -v certbot &> /dev/null; then
    echo -e "安装 SSL 证书..."
    sudo certbot --nginx -d your-domain.com --non-interactive --agree-tos --email your-email@example.com
    echo -e "${GREEN}✓ SSL 证书安装完成${NC}"
else
    echo -e "${YELLOW}certbot 未安装，请手动配置 SSL${NC}"
fi

echo -e "\n${YELLOW}8. 验证部署...${NC}"

# Test frontend
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null || echo "000")

if [ "$FRONTEND_STATUS" == "200" ]; then
    echo -e "${GREEN}✓ 前端访问正常${NC}"
else
    echo -e "${YELLOW}⚠ 前端访问返回: ${FRONTEND_STATUS}${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}前端应用部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\n部署信息:"
echo -e "  部署目录: ${DEPLOY_DIR}"
echo -e "  后端地址: ${BACKEND_URL}"
echo -e "\n访问地址:"
echo -e "  HTTP: http://your-domain.com"
echo -e "  HTTPS: https://your-domain.com"
echo -e "\n常用命令:"
echo -e "  查看日志: sudo tail -f /var/log/nginx/access.log"
echo -e "  重启 Nginx: sudo systemctl restart nginx"
echo -e "  更新部署: npm run build && sudo cp -r build/* ${DEPLOY_DIR}/"
