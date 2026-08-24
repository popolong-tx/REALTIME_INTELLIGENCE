# 量化交易建议系统

基于人工智能的股票分析和交易建议平台。

## 快速开始

### 推荐方式：统一启动 UI 与 API

```bash
./start-ui.sh
```

`start.sh`、`start-dev.sh` 和前端目录内的 `npm start` 都会转到同一个入口，
不会再启动过时的 3000 端口 React 服务。

### 兼容旧命令

```bash
./start-dev.sh
```

### 手动启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements-ui.txt

# 启动统一服务
python -m uvicorn app.main_ui:app --host 0.0.0.0 --port 8000 --reload
```

### 访问系统

- **🖥️ 前端界面**: http://localhost:8000
- **📡 API 服务**: http://localhost:8000
- **📚 API 文档**: http://localhost:8000/docs
- **💚 健康检查**: http://localhost:8000/health

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite（开发环境）
- **ORM**: SQLAlchemy
- **数据源**: Yahoo Finance, Alpha Vantage
- **AI**: OCI Generative AI (xAI Grok)

### 前端
- **形态**: FastAPI 同源托管的静态产品界面
- **技术**: 原生 HTML / CSS / JavaScript，无需额外构建
- **特点**: 单服务、无跨域配置、支持离线加载基础界面

## 显示异常排查

如果页面突然没有样式或操作失效，重新执行：

```bash
./start-ui.sh
```

脚本会识别并平滑替换本工程占用 8000 端口的旧进程；若端口属于其他程序，
脚本会停止启动并给出提示，不会误杀其他服务。运行状态可通过
`http://localhost:8000/api/v1/status` 查看，其中包含当前运行版本与静态资源挂载状态。

## 主要功能

1. **股票查询** - 支持美股、港股、A股等多市场
2. **交易建议** - AI 驱动的买卖建议
3. **模型管理** - 量化模型训练和管理
4. **投资组合** - 组合配置和风险分析
5. **用户配置** - 个性化投资偏好设置
6. **券商接入** - 支持长桥证券等券商 API
7. **Webhook** - 接收 TradingView 等外部信号

## 开放平台模式

系统使用同一产品内核服务三种工作区模板：

- **个人研究**：关注、证券研究、模拟计划和复盘。
- **机构投研**：共享研究资产、角色权限、审批、数据授权和审计。
- **客户化交付**：受限品牌主题、连接器清单、策略包和部署配置。

平台清单位于 `GET /api/v1/platform/manifest`，用于声明工作区模板、RBAC
角色、连接器、扩展契约和部署形态。当前本地版本已经实现工作区上下文、
品牌预览和平台管理界面；机构空间与客户化空间仍是模板预览。生产多租户启用前，
必须完成数据库、缓存、对象存储、后台任务和租户密钥的服务端强制隔离，并接入
SSO/SCIM 与持久成员目录。

## API 端点

### 股票相关
- `GET /api/v1/stocks/{symbol}/info` - 获取股票信息
- `GET /api/v1/stocks/{symbol}/technical` - 技术分析
- `GET /api/v1/stocks/{symbol}/news` - 相关新闻
- `GET /api/v1/stocks/{symbol}/sentiment` - 市场情绪

### 交易建议
- `POST /api/v1/recommendations/generate` - 生成交易建议
- `GET /api/v1/recommendations/quick/{symbol}` - 快速建议
- `POST /api/v1/recommendations/generate-plan` - 生成交易计划

### 模型管理
- `GET /api/v1/models/` - 模型列表
- `POST /api/v1/models/` - 创建模型
- `POST /api/v1/models/{id}/approve` - 审批模型
- `POST /api/v1/models/{id}/deploy` - 部署模型

### 用户配置
- `GET /api/v1/user/profile` - 获取用户配置
- `PUT /api/v1/user/goals` - 更新投资目标
- `PUT /api/v1/user/risk-profile` - 更新风险偏好

### 券商接口 (长桥证券)
- `GET /api/v1/broker/brokers` - 列出支持的券商
- `GET /api/v1/broker/quote/{symbol}` - 获取报价
- `GET /api/v1/broker/account/balance` - 账户余额
- `GET /api/v1/broker/account/positions` - 持仓信息
- `POST /api/v1/broker/order` - 下单
- `POST /api/v1/broker/order/cancel` - 撤单

### Webhook
- `POST /api/v1/webhooks/` - 创建 Webhook
- `GET /api/v1/webhooks/` - 列出所有 Webhook
- `DELETE /api/v1/webhooks/{id}` - 删除 Webhook
- `POST /api/v1/webhooks/receive/tradingview` - 接收 TradingView 信号
- `POST /api/v1/webhooks/receive/longport` - 接收长桥证券回调
- `POST /api/v1/webhooks/receive/custom/{source}` - 自定义 Webhook

## 数据库

开发环境使用 SQLite，数据库文件位于：
```
backend/data/quant_advisor.db
```

## 配置

配置文件位于：
```
config/production.env
```

主要配置项：
- `DATABASE_URL` - 数据库连接
- `OCI_GENAI_API_KEY` - OCI Generative AI API Key（Grok 推理与 X Search 共用）
- `OCI_REGION` - OCI 推理区域，默认 `us-chicago-1`
- `OCI_GROK_MODEL_ID` - 常规研究模型，默认 `xai.grok-4.3`
- `OCI_GROK_MULTI_AGENT_MODEL_ID` - 深度研究模型，默认 `xai.grok-4.20-multi-agent`
- `SECRET_KEY` - JWT 密钥

实时新闻、X 趋势和 Grok 综合判断统一通过 OCI Responses API 调用；
不再把 xAI 密钥复用为 X API Bearer Token。未配置 OCI Key 时，界面会明确显示
“待配置/部分数据”，不会用静态示例冒充实时结果。

## 开发

### 运行测试

```bash
cd backend
source venv/bin/activate
pytest tests/
```

### 代码格式化

```bash
black app/
isort app/
```

## 部署

### 使用 Docker

```bash
docker-compose up -d
```

### 手动部署

参见 `scripts/` 目录下的部署脚本。

## 文档

- [用户指南](docs/user-guide.md)
- [API 文档](http://localhost:8000/docs)
- [合规评估](docs/compliance-assessment.md)
- [法律评估](docs/legal-assessment.md)

## 许可证

MIT License
