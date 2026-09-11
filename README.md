# 📊 量化洞察系统 — 实时决策情报分析 (AIIB 专版)

基于 OCI Generative AI + xAI Grok 的多源实时情报分析平台，面向 AIIB（亚洲基础设施投资银行）五类核心场景。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心特性

- 🔍 **实时信息检索** — X Search + Web Search + Code Interpreter 多源检索
- 🎯 **项目风险情报** — 政治/社会/债务/环境/声誉五维实时风险扫描
- 🌍 **地缘融资推演** — 基准/压力/机会三情景因果链推理
- ⚖️ **制裁与负面新闻** — KYC/CDD 合规审查公共信息线索
- 📈 **市场与资金环境** — 利率/汇率/信用利差/商品价格/融资条件研究
- 🤖 **研究与数据 Agent** — 连接白名单 SQL、知识库与计算工具生成可核验分析
- 📄 **PDF 报告导出** — 所有情报结果可导出带引用的审计级 PDF
- 🔁 **定时监控** — 按间隔重复执行情报任务，自动保存报告

## 🏗️ 架构概览

```
浏览器 (SPA) → FastAPI → OCI Generative AI Responses API → xAI Grok 模型
                    ↓
              SQLite (历史/监控/审计)
```

Grok 负责全球公开信息研究与工具调用，本地平台负责敏感数据与最终决策。

## 🚀 快速开始

```bash
git clone https://github.com/popolong-tx/REALTIME_INTELLIGENCE.git
cd REALTIME_INTELLIGENCE
./start-ui.sh
# 访问 http://localhost:8000
```

### 配置 `.env`

```env
OCI_GENAI_API_KEY=your_key
OCI_REGION=us-chicago-1
OCI_GENAI_BASE_URL=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/v1
OCI_GROK_MODEL_ID=xai.grok-4.3
OCI_GROK_MULTI_AGENT_MODEL_ID=xai.grok-4.20-multi-agent
AVAILABLE_LLM_MODELS=xai.grok-4.3,xai.grok-4.6,xai.grok-4.20-multi-agent
```

## 📁 项目结构

```
REALTIME_INTELLIGENCE/
├── backend/
│   ├── app/
│   │   ├── api/           # intelligence.py (六类情报端点)
│   │   ├── core/          # config.py, database, cache, auth
│   │   ├── models/        # SQLAlchemy ORM
│   │   └── services/      # OCI 调用、情报编排、PDF、审计
│   └── data/              # SQLite 数据库
├── frontend/
│   └── public/            # index.html + app.js (SPA)
├── docs/                  # 架构文档、用户指南
├── config/                # 环境配置
└── start-ui.sh            # 启动脚本
```

## 🔌 API 端点

### 情报分析（AIIB 五类场景 + 实时检索）

| 端点 | 场景 | 说明 |
|------|------|------|
| `POST /api/v1/intelligence/realtime/search` | 00 实时信息检索 | X + 公共网页多源检索 |
| `POST /api/v1/intelligence/project-risk/analyze` | 01 项目风险情报 | 五维风险扫描 |
| `POST /api/v1/intelligence/geopolitical-impact/analyze` | 02 地缘融资推演 | 多情景因果推理 |
| `POST /api/v1/intelligence/sanctions-news/analyze` | 03 制裁与负面新闻 | KYC/CDD 合规审查 |
| `POST /api/v1/intelligence/market-funding/analyze` | 04 市场与资金环境 | 利率/汇率/融资条件 |
| `POST /api/v1/intelligence/research-agent/run` | 05 研究与数据 Agent | 可核验数据分析 |

### 通用端点

```bash
GET  /api/v1/intelligence/capabilities    # 能力与可用模型列表
GET  /api/v1/intelligence/history         # 分析历史
GET  /api/v1/intelligence/reports         # PDF 报告列表
POST /api/v1/intelligence/export/pdf      # 导出 PDF
```

## 📚 文档

- [架构设计](docs/architecture.md) — 系统架构、模块职责、OCI Grok 情报工作流
- [用户指南](docs/user-guide.md)

## ⚠️ 当前边界

Grok 当前通过 OCI 仅在美国三地可用（模型部署于 OCI 美国数据中心的 xAI tenancy 并由 xAI 管理）。建议按美国 Grok 服务区规划，并与新加坡/中东本地数据域分层。

**建议治理流程**：本地敏感数据处理 → 脱敏/聚合 → 美国 Grok 研究 → 引用与事实校验 → 人工复核 → 结果回流

---

**⚠️ 免责声明**

本系统提供的所有信息仅供参考，不构成任何投资建议或合规结论。在做出任何投资、融资或合规决策之前，请咨询专业顾问。
