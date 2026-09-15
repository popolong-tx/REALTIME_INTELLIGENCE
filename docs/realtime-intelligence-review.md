# realtime-intelligence-only 分支审查与优化建议

## 1. 审查范围

本文把仓库中的架构、合规、验收和用户指南视为项目背景材料，不把其中的旧量化交易描述自动当成当前分支的实现要求。当前用户目标是：利用 Grok 的实时舆情与公开信息能力，为投资机构提供可追溯的信息、事件理解和受治理的推理预测。

当前审查基线：`realtime-intelligence-only` 分支。

## 2. 当前实现判断

当前系统已经具备一条较完整的研究闭环：

```text
用户问题
  -> FastAPI 请求模型
  -> InstitutionalIntelligenceService
  -> OCI Responses / Grok + X Search + Web Search + Code Interpreter
  -> JSON 解析与中文规范化
  -> 引用、审计、历史快照
  -> 监控调度 / PDF 产物 / 前端展示
```

已经形成的优势：

- 把 X 原文、公共网页和模型推断分层，避免把社交媒体观点直接当成事实。
- provider 降级信息会进入审计元数据，能够解释“为什么结果是 partial”。
- 历史记录保存输入与输出快照，PDF 导出不必再次调用模型。
- 未配置 OCI 时返回 `configuration_required`，不会用假数据冒充实时结果。
- 监控执行、历史记录和报告产物已有持久化基础。

## 3. 本轮已完成的代码优化

### 3.4 机构第三方资料与隔离联合分析

新增独立资料集能力。前端先创建 `session_id`，之后上传的 PDF、DOCX、TXT、Markdown、CSV、JSON、HTML 和 PNG/JPEG/WebP 都绑定到该会话。资料列表、解析文本、截图和联合分析接口同时按 `workspace_id + session_id` 过滤，联合分析不会读取其他会话的资料。

处理规则：

- 单文件默认上限 25 MB，单资料集默认最多 30 份；
- PDF、DOCX、文本类文件在服务端解析；
- 截图不伪造 OCR 结果，而是作为当前会话的图像输入交给已配置的多模态 Grok；
- 联合分析必须由用户显式勾选外部处理授权；
- 上传图片不进入通用缓存；
- 分析请求写入资料 ID、会话 ID、工作区、授权状态和来源范围审计记录；
- 分析提示明确禁止读取或假设其他任务的资料。

### 3.1 监控工作区越权边界

监控的更新、删除、立即执行和运行列表接口此前只按 `monitor_id` 定位资源。现在这些路径均支持并校验 `workspace_id`，服务层也支持按工作区读取监控，跨工作区访问表现为“监控任务不存在”。立即执行在进入异步执行前即完成工作区校验，避免执行一个不属于当前工作区的任务。

### 3.2 制裁/负面新闻枚举修正

修复了 `adverse_media` 默认值前多余空格的问题。此前接口 Literal 与默认提示词值不一致，容易造成请求校验、提示词和下游结构化结果不一致。

### 3.3 预测治理元数据

实时结果新增 `forecast_governance`，包含：

- 是否包含情景/展望类推理；
- `calibration_status=not_calibrated`；
- `probability_semantics=qualitative_only`；
- 历史回测是否可用；
- 自动化使用前必须完成的预测定义、信息集快照、概率校准和 Brier 分数评估。

这不是给模型预测增加虚假的置信度，而是把“当前只能用于研究与人工复核”的边界结构化返回。

## 4. 关键设计缺口

### P0：身份与工作区仍是演示级

当前会话认证是单账号本地登录，`workspace_id` 仍来自请求参数。即使资源接口已加强工作区过滤，生产环境仍需要把工作区绑定到身份、角色和成员关系，禁止客户端任意声明工作区。

建议引入：

- `user_id -> workspace_membership -> workspace_id` 数据模型；
- 所有情报读取、写入、导出和监控操作从服务端会话推导工作区；
- workspace 管理员、研究员、审阅者、只读用户四类最小权限；
- 审计事件同时记录 `user_id`、`workspace_id`、`request_id` 和 `source_snapshot_id`。

### P0：来源账本需要从“引用列表”升级为“证据对象”

当前 `evidence` 主要是 URL、标题、摘要和来源类型。机构研究还需要保存：抓取/生成时间、原始响应摘要哈希、来源发布时间、作者或机构、事实状态、交叉验证关系、引用所在分析字段。

建议最小结构：

```json
{
  "evidence_id": "S-001",
  "source_type": "x|public|official|dataset",
  "url": "https://...",
  "published_at": "...",
  "observed_at": "...",
  "evidence_status": "verified|reported|opinion|inference|unverified",
  "content_hash": "sha256:...",
  "supports": ["analysis.events[0]", "analysis.scenarios[1]"]
}
```

### P1：预测还缺少“可验证的预测对象”

当前项目风险和地缘推演已经有情景、触发信号和定性概率，但还不能做真正的预测评估。下一步应将每个预测保存为不可变对象：

- 预测事件：例如“30 天内是否出现融资条件收紧”；
- 预测截止时间与评估规则；
- 生成时的信息集和证据快照；
- 当时的概率/区间及其语义；
- 到期后的结果标签；
- Brier 分数、校准曲线、分场景命中率和失效原因。

没有这些字段，不应把模型输出转换为交易信号或自动调整融资条件。

### P1：监控调度需要分布式租约

当前调度器是单进程轮询，适合本地演示，不适合多 worker 或多副本部署。生产版本应使用数据库租约或队列：

```text
due monitor
  -> acquire lease (workspace, monitor, lease_until)
  -> enqueue run
  -> worker executes with idempotency key
  -> persist result / evidence snapshot / report
  -> release lease
```

必须保证同一个 `monitor_id + scheduled_slot` 最多产生一个有效运行结果。

### P1：Grok 输出解析需要 schema 版本与严格校验

当前 JSON 提取失败时会回退到文本，具备可用性但会削弱下游契约。建议：

- 每个 workflow 定义 Pydantic 响应模型和 `schema_version`；
- 解析失败时返回 `partial`，保留原始输出哈希和失败原因；
- 对评分范围、枚举、引用 ID 和事件时间做服务端校验；
- 禁止将未引用事实映射为 `verified`；
- 前端按 `status/evidence_quality/forecast_governance` 展示，而不是仅按是否有摘要判断成功。

### P2：实时数据产品化

当前是“问题驱动查询”。投资机构还需要实体、主题和事件的持续状态：实体别名归一化、事件去重、事件生命周期、情绪变化与影响方向、影响资产/项目映射，以及告警抑制与升级规则。

推荐新增实体层：

```text
Entity -> Alias -> Evidence -> Event -> ImpactAssessment -> DecisionReview
```

其中 `DecisionReview` 只产生待复核事项，不直接产生下单或融资审批动作。

## 5. 建议的迭代顺序

1. 完成身份-工作区绑定和全链路权限测试。
2. 固化证据对象与内容哈希，建立不可变信息快照。
3. 为六类 workflow 增加版本化 Pydantic 响应模型。
4. 建立预测对象、到期评估和校准指标服务。
5. 将单进程调度替换为带租约的队列执行。
6. 增加事件去重、实体归一化和可配置告警策略。
7. 最后再考虑把部分高质量预测接入研究员工作台；在校准数据不足前保持人工复核门控。

## 6. 验证建议

当前环境未安装 `pytest`，因此本轮使用了不落盘的 Python AST 语法校验和 `git diff --check`。在 CI 或开发环境补齐依赖后，至少应增加以下回归测试：

- 工作区 A 无法更新、删除、执行或读取工作区 B 的监控；
- `adverse_media` 默认请求可通过模型校验；
- 工具降级后 `status=partial` 且审计字段完整；
- 无引用结果不会被标为 `cited`；
- 预测治理元数据始终声明未校准；
- 同一监控调度槽位的重复执行具备幂等性。
