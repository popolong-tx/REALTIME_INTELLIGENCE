# 变更日志

本文件记录项目的重要变更和修复。

## [2025-09-16] 代码质量与 UI 优化

### UI 调整

- **移除页面模型标识**：删除所有5个情报分析页面（实时信息检索、项目风险情报、地缘融资推演、制裁与负面新闻、市场与资金环境）右上角的 Grok 4.3 模型信息栏，简化页面头部布局

### 布局修复

- **情报输出面板内边距统一**：为 `.intelligence-output` 内的所有 `.panel` 元素添加22px统一内边距，修复"风险发现"和"关键指标"面板文字位置与"来源账本"不一致的问题

### 稳定性修复（Null Safety）

#### 应用初始化
- 为 `init()` 函数添加 try/catch 错误处理，捕获并显示初始化错误
- 为 `today-date` 元素引用添加空守卫

#### 向导与计划模块
- 为 `wizardData()` 所有表单字段（plan-symbol、plan-horizon、plan-target、plan-drawdown、plan-risk、plan-capital、plan-thesis、plan-catalyst、plan-invalidation、stage1-3-trigger、stage2-3-weight、stage-exit）添加可选链空值保护
- 为 `renderPlanReview()` 的 plan-review 元素引用添加空守卫
- 为 `startPlanVersion()` 8个 plan 表单字段填充添加空守卫
- 为 `generatePlan()` 的 plan-ack、wizard-next、wizard-message 引用添加空守卫
- 为 `renderWizardStep()` 的 plan-wizard、plan-library、wizard-message 引用添加空守卫
- 为 `closeWizard()` 的 plan-wizard、plan-library 引用添加空守卫

#### Grok 实时查询
- 为 `runGrok()` 的 grok-synthesis innerHTML 赋值添加空守卫

#### 预警模块
- 为 `renderAlerts()` 的 alert-list 元素引用添加空守卫
- 为 `updateAlertFields()` 的 alert-threshold、alert-symbol-field 元素引用添加空守卫
- 为所有 `$('#alert-symbol')` 引用添加空守卫

#### 海外证券模块
- 为 `overseasRequestParams()` 函数参数提取添加空守卫
- 为 `renderOverseasError()` 的 error-overseas 元素引用添加空守卫
- 为 `queryOverseasQuote()` 的 overseas-quote-result 元素引用添加空守卫
- 为 `searchOverseasSecurities()` 的 overseas-search-result 元素引用添加空守卫
- 为 `loadOverseasHistory()` 的 overseas-history-result 元素引用添加空守卫
- 为 `loadOverseasProviderStatus()` 的 overseas-provider 元素引用添加空守卫

#### 计划详情模块
- 为 `openPlanDetail()` 的 plan-drawer、plan-drawer-content、plan-drawer-title 元素引用添加空守卫

#### 模型详情模块
- 为 `renderModelDetail()` 的 lab-view 相关元素引用添加空守卫（已删除视图的死代码路径）

#### 研究模块
- 为 `openResearch()` 的 research 相关元素引用添加空守卫
- 为 `resetResearchUI()` 的 price-chart、chart-metrics、metric-grid、technical-content、financial-content、evidence-cards、grok-synthesis、source-list 元素引用添加空守卫

#### 品牌配置模块
- 为 `saveBrandConfig()` 和 `applyBrandConfig()` 的品牌配置元素引用添加空守卫

#### Broker 模块
- 为 `checkBroker()` 和 `checkHealth()` 的 broker-summary 元素引用添加空守卫

#### 其他修复
- 为 `openWizard()` 的 plan-library、plan-wizard 元素引用添加空守卫
- 为 `runPlanEvidence()` 的 plan-symbol、run-plan-evidence 按钮引用添加空守卫
- 为 `nextWizardStep()` 的 wizard-message 元素引用添加空守卫
- 为海外证券搜索结果点击处理器添加空守卫

### 代码清理

- 移除已删除页面（discover、plans、portfolio、lab）的死代码条目
- 为制裁与负面新闻、市场与资金环境页面添加 PAGE_COPY 标签

### 模型选择器修复

- 将 `#sanctions-model` 和 `#market-model` 添加到 `populateModelSelectors` 数组，修复制裁和市场页面模型下拉框无选项的问题

### 历史记录恢复修复

- 为 `restoreIntelligenceHistoryContext()` 添加 `sanctions-news` 和 `market-funding` 分支，正确恢复对应表单字段

### 表单布局修复

- 为 `.intelligence-query-panel` 添加 `overflow: hidden`，修复输入框溢出330px面板边界的问题

### SVG 图标修复

- 添加缺失的 `#i-chart` SVG 符号定义（柱状图图标）

### 无障碍访问改进

- 将全局搜索的 `aria-labelledby` 从 `<label>` 改为 `<h2>` 元素
- 为关闭按钮（close-jobs、close-alerts）添加 `aria-label` 属性
- 为预警表单字段（alert-symbol、alert-threshold）添加 `required` 和 `for` 属性

---

## [2025-09-14] 架构审查文档

- 添加 `docs/realtime-intelligence-review.md` 架构审查与优化建议文档

---

## [2025-09-10] 初始版本

- 实现实时情报分析系统六类场景
- 集成 OCI Generative AI + xAI Grok
- 支持 X Search、Web Search、Code Interpreter
- 实现 PDF 报告导出和审计功能
