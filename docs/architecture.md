# 🏗️ 架构设计文档

## 1. 系统概览

Quant Trading Advisor（QTA）是一个面向机构研究场景的实时决策情报分析平台，核心能力包括：

- **多源实时信息检索**：通过 OCI Generative AI Responses API 调用 xAI Grok 模型，结合 X Search、Web Search、Code Interpreter 三类工具，生成带引用、可审计的结构化研究判断。
- **项目风险情报**：对成员国/项目维度进行政治、社会、债务、环境、声誉五维实时风险扫描。
- **地缘融资推演**：针对复杂地缘事件进行多情景（基准/压力/机会）因果链推理。
- **量化模型实验**：Random Forest / XGBoost 等量化因子模型的训练、回测、影子跟踪与治理审阅。
- **模拟交易计划**：从证据快照到分阶段模拟计划的完整研究闭环。

---

## 2. 整体架构

```
┌──────────────────────────────────────────────────────────────┐
│                     浏览器 (SPA)                              │
│  index.html + app.js (Vanilla JS, 无构建步骤)                │
└──────────────────────┬───────────────────────────────────────┘
                       │  HTTP / SSE
                       ▼
┌──────────────────────────────────────────────────────────────┐
│              FastAPI (uvicorn --reload)                       │
│  ┌─────────────┐ ┌──────────────┐ ┌───────────────────────┐ │
│  │  API Routers │ │ Auth Middleware│ │ Static File Serving  │ │
│  │  /api/v1/*   │ │ (JWT Session) │ │ /login, /assets/*    │ │
│  └──────┬──────┘ └──────────────┘ └───────────────────────┘ │
│         │                                                     │
│  ┌──────▼──────────────────────────────────────────────────┐ │
│  │                  Services Layer                         │ │
│  │  ┌───────────────┐  ┌──────────────────────────────┐   │ │
│  │  │ OCI Responses  │  │ Institutional Intelligence   │   │ │
│  │  │ Service        │──│ Service                      │   │ │
│  │  └───────┬───────┘  └──────────────────────────────┘   │ │
│  │          │                                               │ │
│  │  ┌───────▼───────┐  ┌────────────┐  ┌──────────────┐   │ │
│  │  │ Cache (Memory) │  │ Audit Trail│  │ PDF Reports  │   │ │
│  │  └───────────────┘  └────────────┘  └──────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
│         │                                                     │
│  ┌──────▼──────────────────────────────────────────────────┐ │
│  │              Data Layer (SQLite)                        │ │
│  │  intelligence_history · monitors · models · audit_log   │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│           OCI Generative AI Responses API                    │
│  https://inference.generativeai.{region}.oci.oraclecloud.com │
│  ┌──────────┐ ┌────────────┐ ┌──────────────────┐           │
│  │ X Search │ │ Web Search │ │ Code Interpreter │           │
│  └──────────┘ └────────────┘ └──────────────────┘           │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 核心模块说明

### 3.1 后端 (`backend/app/`)

| 目录 | 职责 |
|------|------|
| `api/` | FastAPI Router，定义 HTTP 端点和请求/响应模型 |
| `core/` | 配置加载 (`config.py`)、数据库连接、缓存、认证 |
| `services/` | 业务逻辑：OCI 调用、情报编排、PDF 生成、审计、模型训练 |
| `models/` | SQLAlchemy ORM 模型定义 |

#### 关键服务

- **`OCIResponsesService`** (`services/oci_responses_service.py`)
  封装 OCI Generative AI Responses API 的 HTTP 调用，处理认证、缓存、错误重试和工具兼容性降级（当服务端不支持某工具时自动移除并重试）。

- **`InstitutionalIntelligenceService`** (`services/institutional_intelligence_service.py`)
  情报编排层，负责构造 system prompt、组织工具组合、解析返回结果、提取引用、生成审计记录，并调用中文规范化后处理。

- **`IntelligenceMonitoringService`** (`services/intelligence_monitoring_service.py`)
  定时情报监控调度器，支持按间隔重复执行检索/风险扫描任务，自动保存 PDF 报告。

### 3.2 前端 (`frontend/public/`)

- **`index.html`**：单页应用主入口，所有页面视图（今日、发现、证券研究、实时检索、项目风险、地缘推演、策略实验室、平台管理）均在此文件内以 `<section class="view">` 形式组织。
- **`assets/app.js`**：约 2800 行的 Vanilla JS 应用逻辑，无构建步骤，直接由浏览器加载。采用模块化函数组织，通过 `state` 对象管理全局状态。

### 3.3 数据存储

使用 SQLite 作为本地开发数据库，主要表包括：

- `intelligence_history`：情报分析历史记录（完整快照，支持不重新调用 Grok 即导出 PDF）
- `intelligence_monitors` / `intelligence_monitor_runs`：定时监控任务与执行记录
- `intelligence_reports`：生成的 PDF 报告元数据
- `models` / `model_versions`：量化实验模型与版本
- `audit_events`：操作审计日志

---

## 4. OCI Grok 情报工作流

### 4.1 实时信息检索 (`realtime-research`)

```
用户输入主题/关键词/日期范围/信息通道
        │
        ▼
InstitutionalIntelligenceService.search_realtime_information()
        │
        ├─ 构造 system prompt（中文输出规则 + 来源区分规则）
        ├─ 选择工具：web_search + x_search + code_interpreter
        ├─ 可选 model_id（用户下拉框选择，或使用默认值）
        │
        ▼
OCIResponsesService.generate_realtime_research()
        │
        ├─ 首次请求：全量工具
        ├─ 若工具不兼容 → 自动降级移除不支持的工具 → 重试
        │
        ▼
结果解析 → 来源提取 → 引用去重 → 中文规范化 → 保存历史 → 返回前端
```

### 4.2 工具兼容性降级机制

OCI 不同 region/模型对工具的支持可能不同。`generate_realtime_research` 实现了自动降级：

1. 首次尝试全部选定工具
2. 若返回 400/422 且错误信息包含工具相关关键词，识别被拒绝的工具
3. 移除该工具后重试，直到成功或无可用搜索工具
4. 降级信息记录在 `metadata.degraded_tools` 和 `metadata.tool_warnings` 中

### 4.3 模型选择

系统支持在运行时选择不同的 Grok 模型：

| 模型 | 用途 | 默认场景 |
|------|------|----------|
| `xai.grok-4.3` | 通用实时检索与风险分析 | 实时检索、项目风险 |
| `xai.grok-4.6` | 增强推理能力 | 用户可选 |
| `xai.grok-4.20-multi-agent` | 多智能体复杂推理 | 地缘融资推演 |

前端通过 `/api/v1/intelligence/capabilities` 接口获取 `available_models` 列表，动态填充下拉框。用户选择的 `model_id` 随请求体传递到后端，后端优先使用用户选择，无选择时回退到配置默认值。

---

## 5. 安全架构

### 5.1 认证

- 本地开发：基于 JWT 的会话认证，Cookie 名 `grok_demo_session`
- 密码使用 bcrypt 哈希存储，会话令牌包含过期时间
- 登录失败次数限制（默认 5 次后锁定 5 分钟）

### 5.2 执行安全

- 默认 `simulation_only` 模式，所有真实交易请求被阻止
- 紧急停用门控：`/api/v1/governance/shutdown/*` 可立即阻断所有敏感操作
- 所有关键操作记录审计日志

### 5.3 数据安全

- API Key 仅存在于服务端 `.env` 文件，不进入前端、浏览器存储或 API 响应
- OCI 请求使用 Bearer Token 认证
- PDF 报告包含 SHA256 校验

---

## 6. 部署架构

### 本地开发

```bash
./start-ui.sh
# → uvicorn --reload :8000
# → 前端 + API 同一端口，热重载
```

### Docker 部署

```bash
docker-compose up -d
# → PostgreSQL + Redis + 应用服务
```

### 生产环境注意事项

- 切换 `AUTH_COOKIE_SECURE=true`（HTTPS）
- 配置强密码和随机 `AUTH_SESSION_SECRET`
- 使用 PostgreSQL 替代 SQLite
- 接入 SSO/SCIM/MFA（当前为单账号本地演示）
- 配置 CORS 允许的源

---

## 7. 依赖说明

### 后端核心依赖

| 包 | 用途 |
|----|------|
| `fastapi` + `uvicorn` | Web 框架与 ASGI 服务器 |
| `pydantic-settings` | 配置管理 |
| `sqlalchemy` | ORM |
| `httpx` | 异步 HTTP 客户端（OCI API 调用） |
| `yfinance` | Yahoo Finance 行情数据 |
| `reportlab` | PDF 报告生成 |
| `python-jose` + `passlib` | JWT 与密码哈希 |

### 前端

无构建依赖，纯 Vanilla JS + CSS，通过 CDN 加载图标库。所有逻辑在 `app.js` 中，约 2800 行。
