# 📊 量化交易建议系统 (Quant Trading Advisor)

基于人工智能的股票分析和交易建议平台，集成 Grok 实时情报分析。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心特性

- 🔍 **智能股票搜索** - 支持美股、港股、A股等多市场
- 💡 **AI 交易建议** - 基于量化模型的买卖建议
- 🤖 **Grok 情报分析** - 实时 X/Web 信息检索与风险监测
- 📈 **模型训练管理** - 量化模型训练、回测与版本管理
- 🔗 **Webhook 集成** - 支持 TradingView 等外部信号
- 🏦 **券商接入** - 长桥证券 API 集成（模拟模式）
- 🛡️ **合规治理** - 审计留痕、紧急停用、风险控制

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/popolong-tx/Grok_Quant_Demo.git
cd Grok_Quant_Demo
```

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，配置 Grok API Key
```

### 3. 启动服务

```bash
# 方式一：使用启动脚本（推荐）
./start-ui.sh

# 方式二：手动启动
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-ui.txt
python -m uvicorn app.main_ui:app --host 0.0.0.0 --port 8000
```

### 4. 访问系统

| 服务 | 地址 |
|------|------|
| 🖥️ 前端界面 | http://localhost:8000 |
| 📚 API 文档 | http://localhost:8000/docs |
| 💚 健康检查 | http://localhost:8000/health |
| 📊 系统状态 | http://localhost:8000/api/v1/status |

## ⚙️ 配置说明

### Grok API 配置

在 `backend/.env` 中配置：

```env
# OCI Generative AI / xAI Grok
OCI_GENAI_API_KEY=your_api_key_here
OCI_REGION=us-ashburn-1
OCI_GENAI_BASE_URL=https://inference.generativeai.us-ashburn-1.oci.oraclecloud.com/20231130/actions/v1
OCI_GROK_MODEL_ID=xai.grok-4.3
OCI_GROK_MULTI_AGENT_MODEL_ID=xai.grok-4.20-multi-agent
```

### 执行模式配置

```env
# simulation_only: 模拟模式（默认，阻止真实交易）
# live: 实盘模式（需要额外配置）
EXECUTION_MODE=simulation_only
BROKER_LIVE_TRADING_ENABLED=false
```

## 📁 项目结构

```
Grok_Quant_Demo/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── api/               # API 端点
│   │   │   ├── broker.py      # 券商接口
│   │   │   ├── intelligence.py # Grok 情报
│   │   │   ├── models.py      # 模型管理
│   │   │   ├── recommendations.py # 交易建议
│   │   │   ├── webhooks.py    # Webhook
│   │   │   └── ...
│   │   ├── core/              # 核心配置
│   │   ├── models/            # 数据模型
│   │   └── services/          # 业务逻辑
│   ├── data/                  # SQLite 数据库
│   └── tests/                 # 测试
├── frontend/
│   └── public/                # 前端界面
├── docs/                      # 文档
├── config/                    # 配置文件
└── scripts/                   # 部署脚本
```

## 🔌 API 端点

### 股票查询
```bash
GET /api/v1/stocks/{symbol}/info        # 获取股票信息
GET /api/v1/stocks/{symbol}/technical   # 技术分析
GET /api/v1/stocks/{symbol}/news        # 相关新闻
```

### 交易建议
```bash
POST /api/v1/recommendations/generate   # 生成交易建议
POST /api/v1/recommendations/generate-plan  # 生成交易计划
```

### Grok 情报
```bash
POST /api/v1/intelligence/realtime/search   # 实时信息检索
POST /api/v1/intelligence/project-risk/analyze  # 项目风险分析
POST /api/v1/intelligence/geopolitical-impact/analyze  # 地缘融资推演
```

### 模型管理
```bash
GET  /api/v1/models/                    # 模型列表
POST /api/v1/models/                    # 创建模型
POST /api/v1/models/{id}/fine-tune      # 微调模型
POST /api/v1/models/{id}/evaluate       # 评估模型
```

### Webhook
```bash
POST /api/v1/webhooks/                  # 创建 Webhook
POST /api/v1/webhooks/receive/tradingview  # 接收 TradingView 信号
```

### 券商接口
```bash
GET  /api/v1/broker/quote/{symbol}      # 获取报价
POST /api/v1/broker/order               # 下单（模拟模式会被阻止）
```

## 🛡️ 安全特性

### 模拟模式保护

系统默认运行在 `simulation_only` 模式，所有真实交易请求会被阻止：

```json
{
  "detail": {
    "code": "simulation_only",
    "message": "Live broker order mutations are disabled by server policy."
  }
}
```

### 紧急停用

支持紧急停用功能，可立即阻断所有敏感操作：

```bash
# 触发紧急停用
POST /api/v1/governance/shutdown/initiate

# 恢复系统
POST /api/v1/governance/shutdown/recover
```

### 审计追踪

所有关键操作都会记录到审计日志：

```bash
GET /api/v1/governance/audit/events     # 查看审计事件
```

## 📊 系统状态

访问 `/api/v1/status` 查看模块成熟度：

```json
{
  "status": "healthy",
  "modules": {
    "market_research": {"status": "operational"},
    "grok_intelligence": {"status": "operational"},
    "model_training": {"status": "operational"},
    "broker_execution": {"status": "simulation_only"}
  }
}
```

## 🧪 测试

```bash
cd backend
source venv/bin/activate

# 运行单元测试
pytest tests/

# 运行集成测试
pytest tests/test_integration.py

# 运行性能测试
pytest tests/test_performance.py
```

## 📚 文档

- [用户指南](docs/user-guide.md)
- [合规评估](docs/compliance-assessment.md)
- [法律评估](docs/legal-assessment.md)
- [无障碍测试](docs/accessibility-tests.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🔗 相关链接

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [OCI Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [xAI Grok](https://x.ai/)
- [长桥证券 API](https://open.longportapp.com/)

---

**⚠️ 免责声明**

本系统提供的所有信息仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。在做出任何投资决策之前，请咨询专业的投资顾问。本系统不对任何投资损失承担责任。
