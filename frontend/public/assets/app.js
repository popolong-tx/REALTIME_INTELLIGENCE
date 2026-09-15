(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const API_BASE = window.location.origin;
  const DEFAULT_WATCHLIST = ['AAPL', 'NVDA', '0700.HK'];
  const MONITOR_INTERVAL_LABELS = { 30: '每 30 分钟', 60: '每 1 小时', 120: '每 2 小时', 240: '每 4 小时', 360: '每 6 小时', 480: '每 8 小时', 720: '每 12 小时', 1440: '每 24 小时' };
  const WIZARD_TITLES = ['目标与范围', '证据快照', '策略与情景', '阶段与门控', '审阅与确认'];
  const NEXT_LABELS = ['继续：证据快照', '继续：策略与情景', '继续：阶段与门控', '继续：审阅确认', '生成模拟计划'];
  const DEFAULT_BRAND = { name: '实时决策情报分析', subtitle: 'REALTIME INTELLIGENCE', mark: 'RI', theme: 'emerald' };
  const PAGE_COPY = {
    today: ['决策情报概览', '集中查看实时风险、复杂推理与金融研究状态。'],
    discover: ['发现研究机会', '用主题、条件和已有关注列表建立研究候选池。'],
    'realtime-research': ['检索实时公开信息', '按关键词和日期范围搜索，分别展示 X 原文、公共网页、证据状态和来源链接。'],
    'project-risk': ['监测项目实时风险', '持续监测政治、社会、债务、环境和声誉变化，并保留引用与审计信息。'],
    geopolitics: ['分析地缘政治融资影响', '跟踪公开表态，推演项目管道、联合融资、借贷意愿、可行性和风险转移。'],
    plans: ['管理模拟交易计划', '把研究结论转化为可复核的行动条件，不提交任何实盘订单。'],
    portfolio: ['跟踪模拟组合', '记录阶段状态、触发器和待复核事项，不连接实盘账户。'],
    lab: ['管理策略实验', '按研究、回测、影子跟踪和治理审阅阶段管理模型。'],
    settings: ['管理平台与工作区', '配置个人、机构与客户化工作区，以及策略、模型、数据和情报扩展。'],
  };
  const THEME_PALETTES = {
    emerald: { green: '#0da678', deep: '#087c5b', pale: '#dff5ec', lime: '#bcf26d' },
    navy: { green: '#3977b8', deep: '#24598d', pale: '#e4eff9', lime: '#8ec5ff' },
    violet: { green: '#7356b8', deep: '#563c93', pale: '#eee8fa', lime: '#c7afff' },
  };
  const FALLBACK_WORKSPACES = [
    { id: 'personal', name: '我的研究空间', short_name: '个人', type: 'personal', role: 'owner', status: 'active', provisioning: 'local_active', description: '面向个人的研究、模拟计划和复盘空间。', member_slots: ['所有者'], policy_pack: '个人研究默认策略' },
    { id: 'institution', name: '机构投研工作区', short_name: '机构', type: 'institution', role: 'researcher', status: 'template', provisioning: 'template_preview', description: '共享研究资产，使用审批、角色、数据授权与审计门禁。', member_slots: ['研究负责人', '量化研究员', '风险复核人', '只读访客'], policy_pack: '机构双人复核策略' },
    { id: 'custom', name: '客户化交付沙箱', short_name: '客户化', type: 'custom', role: 'admin', status: 'template', provisioning: 'template_preview', description: '独立品牌、连接器清单和交付配置的客户化预览。', member_slots: ['客户管理员', '平台运维', '合规负责人'], policy_pack: '客户专属策略草案' },
  ];

  const state = {
    view: 'today',
    symbol: '',
    stock: null,
    historical: null,
    technical: null,
    financials: null,
    intel: null,
    wizardStep: 1,
    evidenceChecked: false,
    watchlist: readStorage('nexus-watchlist', DEFAULT_WATCHLIST),
    savedCandidates: readStorage('nexus-candidates', []),
    alerts: readStorage('nexus-alerts', []),
    plans: [],
    recent: readStorage('nexus-recent', ['AAPL', 'NVDA', '0700.HK']),
    screenerResults: [],
    screenerTab: 'results',
    planFilter: 'all',
    selectedPlanId: '',
    models: [],
    selectedModelId: '',
    modelTab: 'overview',
    jobs: [],
    workspaceId: readStorage('nexus-workspace', 'personal'),
    brand: readStorage('nexus-brand', DEFAULT_BRAND),
    platformManifest: null,
    intelligenceCapabilities: null,
    realtimeResearch: null,
    materialSessionId: '',
    materials: [],
    projectMaterials: [],
    projectMaterialSessionId: '',
    geoMaterials: [],
    geoMaterialSessionId: '',
    sanctionsMaterials: [],
    sanctionsMaterialSessionId: '',
    marketMaterials: [],
    marketMaterialSessionId: '',
    realtimeFilter: 'all',
    projectRisk: null,
    geopoliticalImpact: null,
    intelligenceMonitors: [],
    intelligenceHistory: {
      'realtime-research': [],
      'project-risk': [],
      'geopolitical-impact': [],
    },
    activeIntelligenceHistory: {
      'realtime-research': '',
      'project-risk': '',
      'geopolitical-impact': '',
    },
    settingsSection: 'overview',
  };

  function readStorage(key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key));
      return value ?? fallback;
    } catch (_) {
      return fallback;
    }
  }

  function writeStorage(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (_) { /* private mode */ }
  }

  function escapeHtml(value) {
    const original = String(value ?? '');
    const cleaned = original
      .replaceAll('该字段未按要求返回简体中文，请重新运行分析。', '')
      .replaceAll('该条内容未按要求返回简体中文，请重新运行分析。', '')
      .replaceAll('该来源未返回可用的中文摘要，请通过来源链接核验原文。', '')
      .replaceAll('模型未按要求返回简体中文，本次英文回复已被拦截，请重新运行。', '')
      .replace(/发现\s*\d+\s*个未按要求返回中文的字段，系统已阻止其直接展示；请重新运行分析。/g, '')
      .replace(/^[；;\s]+|[；;\s]+$/g, '')
      .replace(/[；;]{2,}/g, '；');
    return (cleaned || (original ? '—' : ''))
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#039;');
  }

  function safeUrl(value) {
    try {
      const url = new URL(value);
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch (_) { return ''; }
  }

  function asNumber(value) {
    if (value === null || value === undefined || value === '') return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function formatNumber(value, options = {}) {
    const number = asNumber(value);
    if (number === null) return '—';
    return new Intl.NumberFormat('zh-CN', options).format(number);
  }

  function formatPrice(value, currency = '$') {
    const number = asNumber(value);
    return number === null ? '—' : `${currency}${formatNumber(number, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function formatCompact(value) {
    const number = asNumber(value);
    if (number === null) return '—';
    return new Intl.NumberFormat('zh-CN', { notation: 'compact', maximumFractionDigits: 1 }).format(number);
  }

  function formatPercent(value, scale = 1) {
    const number = asNumber(value);
    if (number === null) return '—';
    return `${number >= 0 ? '+' : ''}${(number * scale).toFixed(2)}%`;
  }

  function timestamp(date = new Date()) {
    return new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false, timeZone: 'Asia/Shanghai',
    }).format(date);
  }

  async function api(path, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), options.timeout || 45000);
    try {
      const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
      const headers = { ...(options.body && !isFormData ? { 'Content-Type': 'application/json' } : {}), ...(options.headers || {}) };
      const response = await fetch(`${API_BASE}${path}`, { ...options, headers, signal: controller.signal });
      if (response.status === 401 && !path.startsWith('/api/v1/auth/')) {
        const next = `${window.location.pathname}${window.location.search}`;
        window.location.replace(`/login?next=${encodeURIComponent(next)}`);
        throw new Error('登录状态已失效，正在返回登录页');
      }
      const type = response.headers.get('content-type') || '';
      const payload = type.includes('application/json') ? await response.json() : await response.text();
      if (!response.ok) {
        const detail = typeof payload === 'object' ? (payload.detail || payload.error) : payload;
        throw new Error(detail || `请求失败（${response.status}）`);
      }
      if (payload && typeof payload === 'object' && payload.error) throw new Error(payload.error);
      return payload;
    } catch (error) {
      if (error.name === 'AbortError') throw new Error('数据服务响应超时');
      throw error;
    } finally {
      clearTimeout(timeout);
    }
  }

  function renderMaterials() {
    const container = $('#material-list');
    const analyze = $('#analyze-materials');
    if (!container) return;
    if (!state.materials.length) {
      container.innerHTML = '<div class="empty-state small"><strong>尚未添加资料</strong><span>上传后将在当前资料集内联合分析。</span></div>';
      if (analyze) analyze.disabled = true;
      return;
    }
    container.innerHTML = state.materials.map((item) => `<div class="material-row"><span class="material-type">${escapeHtml((item.content_type || 'file').split('/').pop().toUpperCase())}</span><div><strong>${escapeHtml(item.filename)}</strong><small>${formatNumber(item.byte_size)} bytes · ${escapeHtml(item.extraction_status)}${item.text_characters ? ` · ${formatNumber(item.text_characters)} 字` : ''}</small></div><span class="status-chip ${item.extraction_status === 'extraction_failed' ? 'partial' : 'healthy'}">${item.extraction_status === 'image_ready' ? '截图就绪' : item.extraction_status === 'ready' ? '已解析' : '需复核'}</span></div>`).join('');
    if (analyze) analyze.disabled = false;
  }

  async function ensureMaterialSession() {
    if (state.materialSessionId) return state.materialSessionId;
    const result = await api(`/api/v1/intelligence/materials/sessions?workspace_id=${encodeURIComponent(state.workspaceId)}`, { method: 'POST' });
    state.materialSessionId = result.session_id;
    return state.materialSessionId;
  }

  async function uploadPageMaterials(page, files) {
    if (!files?.length) return;
    const sessionKey = `${page}MaterialSessionId`;
    const listKey = `${page}Materials`;
    if (!state[sessionKey]) {
      try {
        const session = await api(`/api/v1/intelligence/materials/sessions?workspace_id=${encodeURIComponent(state.workspaceId)}`, { method: 'POST' });
        state[sessionKey] = session.session_id;
      } catch (error) { toast('创建资料会话失败', error.message, 'error'); return; }
    }
    const picker = $(`#${page}-material-upload`);
    if (picker) picker.disabled = true;
    try {
      for (const file of Array.from(files)) {
        const body = new FormData();
        body.append('file', file);
        await api(`/api/v1/intelligence/materials/sessions/${encodeURIComponent(state[sessionKey])}/upload?workspace_id=${encodeURIComponent(state.workspaceId)}`, { method: 'POST', body, timeout: 90000 });
      }
      const data = await api(`/api/v1/intelligence/materials/sessions/${encodeURIComponent(state[sessionKey])}?workspace_id=${encodeURIComponent(state.workspaceId)}`);
      state[listKey] = data.items || [];
      renderPageMaterials(page);
      toast('文档已上传', `${state[listKey].length} 份文档将与检索结果联合分析`);
    } catch (error) {
      toast('文档上传失败', error.message, 'error');
    } finally {
      if (picker) { picker.disabled = false; picker.value = ''; }
    }
  }

  function renderPageMaterials(page) {
    const container = $(`#${page}-material-list`);
    const items = state[`${page}Materials`] || [];
    if (!container) return;
    if (!items.length) { container.innerHTML = ''; return; }
    container.innerHTML = items.map((item) => `<div class="material-row"><span class="material-type">${escapeHtml((item.content_type || 'file').split('/').pop().toUpperCase())}</span><strong>${escapeHtml(item.filename)}</strong><small>${formatNumber(item.byte_size)} bytes</small></div>`).join('');
  }

  async function uploadMaterials(files) {
    if (!files?.length) return;
    const sessionId = await ensureMaterialSession();
    const picker = $('#material-upload');
    if (picker) picker.disabled = true;
    try {
      for (const file of Array.from(files)) {
        const body = new FormData();
        body.append('file', file);
        await api(`/api/v1/intelligence/materials/sessions/${encodeURIComponent(sessionId)}/upload?workspace_id=${encodeURIComponent(state.workspaceId)}`, { method: 'POST', body, timeout: 90000 });
      }
      const data = await api(`/api/v1/intelligence/materials/sessions/${encodeURIComponent(sessionId)}?workspace_id=${encodeURIComponent(state.workspaceId)}`);
      state.materials = data.items || [];
      renderMaterials();
      toast('资料已加入当前资料集', `${state.materials.length} 份资料保持会话隔离`);
    } catch (error) {
      toast('资料上传失败', error.message, 'error');
    } finally {
      if (picker) { picker.disabled = false; picker.value = ''; }
    }
  }

  async function analyzeMaterials() {
    const question = $('#material-question')?.value.trim();
    if (!state.materialSessionId || !state.materials.length || !question) {
      toast('请补充联合分析问题', '先上传资料并填写要比较或核查的问题', 'error');
      return;
    }
    if (!$('#material-consent')?.checked) {
      toast('需要确认资料处理授权', '联合分析会将当前资料集发送至已配置的 OCI/Grok', 'error');
      return;
    }
    const button = $('#analyze-materials');
    if (button) { button.disabled = true; button.innerHTML = '<span class="spinner"></span>联合分析中'; }
    try {
      const result = await api(`/api/v1/intelligence/materials/sessions/${encodeURIComponent(state.materialSessionId)}/analyze?workspace_id=${encodeURIComponent(state.workspaceId)}`, { method: 'POST', body: JSON.stringify({ question, external_processing_consent: true, model_id: $('#realtime-model')?.value || null }), timeout: 120000 });
      state.realtimeResearch = result;
      renderRealtimeResearchResult(result);
      toast('联合分析完成', '结果仅基于当前资料集，并已标注会话范围');
    } catch (error) {
      toast('联合分析失败', error.message, 'error');
    } finally {
      if (button) { button.disabled = false; button.innerHTML = '<svg><use href="#i-lab"/></svg>联合分析当前资料集'; }
    }
  }

  function applyClearPageTitles() {
    Object.entries(PAGE_COPY).forEach(([view, copy]) => {
      const heading = $(`#view-${view} .page-heading h1`);
      const description = $(`#view-${view} .page-heading p:not(.eyebrow)`);
      if (heading) heading.textContent = copy[0];
      if (description) description.textContent = copy[1];
    });
    const researchHeading = $('#research-empty h1');
    const researchDescription = $('#research-empty > p:not(.eyebrow)');
    if (researchHeading) researchHeading.textContent = '开始证券研究';
    if (researchDescription) researchDescription.textContent = '输入证券代码，集中查看行情、技术指标、财务数据、实时新闻与 X 趋势。';
    const realtimeAudit = $('#realtime-audit');
    const projectAudit = $('#project-risk-audit');
    const geoAudit = $('#geo-audit');
    if (realtimeAudit) realtimeAudit.innerHTML = '<span>模型 —</span><span>工具 —</span><span>请求 —</span>';
    if (projectAudit) projectAudit.innerHTML = '<span>模型 —</span><span>来源 0</span><span>请求 —</span>';
    if (geoAudit) geoAudit.innerHTML = '<span>模型 —</span><span>来源 0</span><span>请求 —</span>';
    const projectDirectLabel = $('#project-risk-direct span');
    const geoDirectLabel = $('#geo-direct span');
    if (projectDirectLabel) projectDirectLabel.textContent = '直接判断';
    if (geoDirectLabel) geoDirectLabel.textContent = '重点关注';
  }

  function userInitials(username) {
    const normalized = String(username || 'AD').trim();
    return normalized.slice(0, 2).toUpperCase() || 'AD';
  }

  function closeUserMenu() {
    $('#user-menu-popover')?.classList.add('hidden');
    $('#user-menu-trigger')?.setAttribute('aria-expanded', 'false');
  }

  function toggleUserMenu() {
    const menu = $('#user-menu-popover');
    const trigger = $('#user-menu-trigger');
    if (!menu || !trigger) return;
    const opening = menu.classList.contains('hidden');
    menu.classList.toggle('hidden', !opening);
    trigger.setAttribute('aria-expanded', String(opening));
  }

  async function loadAuthSession() {
    try {
      const session = await api('/api/v1/auth/status', { timeout: 10000 });
      if (!session.authenticated) {
        window.location.replace(`/login?next=${encodeURIComponent(`${window.location.pathname}${window.location.search}`)}`);
        return false;
      }
      const mark = userInitials(session.username);
      $('#user-menu-trigger').textContent = mark;
      $('#session-user-mark').textContent = mark;
      $('#session-username').textContent = session.username || '管理员';
      return true;
    } catch (_) {
      window.location.replace('/login');
      return false;
    }
  }

  async function logout() {
    const button = $('#logout-button');
    if (button) button.disabled = true;
    try {
      await fetch('/api/v1/auth/logout', { method: 'POST', headers: { Accept: 'application/json' } });
    } finally {
      window.location.replace('/login');
    }
  }

  function toast(title, detail = '', type = 'success') {
    const region = $('#toast-region');
    const item = document.createElement('div');
    item.className = `toast ${type}`;
    item.innerHTML = `<div><strong>${escapeHtml(title)}</strong>${detail ? `<small>${escapeHtml(detail)}</small>` : ''}</div><button aria-label="关闭">×</button>`;
    item.querySelector('button').addEventListener('click', () => item.remove());
    region.appendChild(item);
    setTimeout(() => item.remove(), 5000);
  }

  function setChip(element, label, status = 'neutral') {
    if (!element) return;
    element.textContent = label;
    element.className = `status-chip ${status}`;
  }

  function updateClock() {
    const clock = $('#market-clock');
    if (clock) clock.textContent = `${new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZone: 'Asia/Shanghai' }).format(new Date())} CST`;
  }

  function renderCapabilityStatus(modules = {}) {
    const container = $('#module-readiness');
    if (!container) return;
    const labels = {
      authentication: '登录与会话保护',
      market_research: '行情与证券研究',
      overseas_market_data: '海外证券 API',
      grok_intelligence: 'Grok 实时情报',
      intelligence_history: '情报分析历史',
      intelligence_scheduler: '情报定时监控',
      intelligence_pdf_export: '情报 PDF 导出',
      recommendations: '推荐与计划生成',
      saved_plans: '计划服务端存储',
      model_training: '模型训练 / 评估 / 微调',
      model_xgboost: 'XGBoost 可选模型',
      audit_trail: '审计留痕',
      webhooks: 'Webhook',
      broker_execution: '券商执行边界',
      workspace_customization: '工作区与客户化',
    };
    const entries = Object.entries(modules);
    if (!entries.length) {
      container.innerHTML = '<div class="empty-state small"><strong>尚未返回模块状态</strong><span>重新检查后由服务端返回真实成熟度。</span></div>';
      return;
    }
    container.innerHTML = entries.map(([id, item]) => {
      const [label, tone] = connectorStatus(item.status);
      return `<article class="readiness-card"><header><strong>${escapeHtml(labels[id] || id)}</strong><span class="status-chip ${tone}">${escapeHtml(label)}</span></header><p>${escapeHtml(item.reason || '未提供状态说明')}</p><small>${escapeHtml(item.persistence || 'unknown')} · ${escapeHtml((item.dependencies || []).join(' + ') || 'no external dependency')}</small></article>`;
    }).join('');
  }

  function showView(view) {
    if (!document.getElementById(`view-${view}`)) return;
    state.view = view;
    $$('.view').forEach((item) => item.classList.toggle('active', item.id === `view-${view}`));
    $$('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === view));
    document.title = `${$(`#view-${view}`).dataset.title} · ${state.brand.name || DEFAULT_BRAND.name}`;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    $('#main-content').focus({ preventScroll: true });
    closeSidebar();
    if (view === 'lab') loadModels();
    if (view === 'settings') { loadProfile(); loadGovernance(); loadPlatformManifest(); }
    if (view === 'portfolio') renderPlans();
    if (view === 'realtime-research' || view === 'project-risk' || view === 'geopolitics' || view === 'sanctions-news' || view === 'market-funding' || view === 'research-agent') loadIntelligenceCapabilities();
    if (view === 'realtime-research') loadIntelligenceMonitors('realtime_research');
    if (view === 'project-risk') loadIntelligenceMonitors('project_risk');
    if (view === 'realtime-research') loadIntelligenceHistory('realtime-research');
    if (view === 'project-risk') loadIntelligenceHistory('project-risk');
    if (view === 'geopolitics') loadIntelligenceHistory('geopolitical-impact');
    if (view === 'sanctions-news') loadIntelligenceHistory('sanctions-news');
    if (view === 'market-funding') loadIntelligenceHistory('market-funding');
    if (view === 'research-agent') loadIntelligenceHistory('research-agent');
  }

  function openSidebar() {
    $('#sidebar').classList.add('open');
    $('#mobile-overlay').classList.remove('hidden');
  }

  function closeSidebar() {
    $('#sidebar').classList.remove('open');
    $('#mobile-overlay').classList.add('hidden');
  }

  function openDrawer(id) {
    $$('.drawer').forEach((drawer) => drawer.classList.toggle('hidden', drawer.id !== id));
  }

  function closeDrawers() {
    $$('.drawer').forEach((drawer) => drawer.classList.add('hidden'));
  }

  async function checkHealth() {
    const sidebarDot = $('#api-dot');
    const statusDot = $('#status-api-dot');
    try {
      const status = await api('/api/v1/status', { timeout: 10000 });
      const overallTone = status.status === 'healthy' ? 'healthy' : status.status === 'blocked' ? 'partial' : 'error';
      [sidebarDot, statusDot].forEach((dot) => { dot.className = `health-dot ${overallTone}`; });
      $('#api-state').textContent = status.status === 'healthy' ? '服务正常' : status.status === 'blocked' ? '紧急停用中' : '服务降级';
      $('#api-detail').textContent = `API ${status.api_version || 'v1'} · ${status.runtime_version || '当前版本'}`;
      $('#status-api').textContent = `${status.status === 'healthy' ? '正常' : status.status === 'blocked' ? '操作已阻断' : '部分异常'} · 刚刚检查`;
      const market = status.features?.market_research;
      const [marketLabel, marketTone] = connectorStatus(market?.status || 'unavailable');
      setChip($('#conn-market'), marketLabel, marketTone);
      const overseas = status.integrations?.overseas_securities;
      const [overseasLabel, overseasTone] = connectorStatus(overseas?.status || 'configuration_required');
      setChip($('#conn-overseas'), overseasLabel, overseasTone);
      if ($('#overseas-connection-detail')) $('#overseas-connection-detail').textContent = overseas?.configured
        ? 'Twelve Data 已配置 · 全球证券搜索、报价与历史行情'
        : '适配器已接入 · 服务端需配置 TWELVE_DATA_API_KEY';
      renderCapabilityStatus(status.features || {});
      const grok = status.integrations?.oci_grok;
      if (grok?.status === 'operational') {
        $('#grok-status-dot').className = 'health-dot healthy';
        $('#grok-status-detail').textContent = `${grok.model} · ${grok.region}`;
        setChip($('#conn-grok'), '已配置', 'healthy');
      } else {
        $('#grok-status-dot').className = 'health-dot partial';
        $('#grok-status-detail').textContent = '待配置 OCI API Key';
        setChip($('#conn-grok'), '待配置', 'partial');
      }
      const broker = status.integrations?.longport;
      if (broker) $('#broker-summary').textContent = broker.order_mutations_enabled ? '服务端已启用实盘执行' : '服务端强制仅模拟；下单与撤单被拒绝';
      return true;
    } catch (error) {
      [sidebarDot, statusDot].forEach((dot) => { dot.className = 'health-dot error'; });
      $('#api-state').textContent = '服务不可用';
      $('#api-detail').textContent = error.message;
      $('#status-api').textContent = '不可用 · 可稍后重试';
      setChip($('#conn-market'), '不可用', 'error');
      setChip($('#conn-overseas'), '不可用', 'error');
      renderCapabilityStatus({});
      return false;
    }
  }

  function overseasRequestParams() {
    const query = $('#overseas-symbol').value.trim();
    const country = $('#overseas-country').value.trim();
    const exchange = $('#overseas-exchange').value.trim();
    const suffix = `${country ? `&country=${encodeURIComponent(country)}` : ''}${exchange ? `&exchange=${encodeURIComponent(exchange)}` : ''}`;
    return { query, country, exchange, suffix };
  }

  function renderOverseasError(error) {
    $('#overseas-result').innerHTML = `<div class="empty-state small"><strong>海外证券数据暂不可用</strong><span>${escapeHtml(error.message || '请检查服务端供应商配置。')}</span></div>`;
  }

  async function loadOverseasProviderStatus(probe = false) {
    const statusChip = $('#overseas-provider-status');
    const detail = $('#overseas-provider-detail');
    if (!statusChip || !detail) return null;
    setChip(statusChip, probe ? '验证中' : '检查中', 'neutral');
    try {
      const payload = probe
        ? await api(`/api/v1/overseas-securities/health/provider?probe=true&symbol=${encodeURIComponent($('#overseas-symbol').value.trim() || 'AAPL')}`, { timeout: 35000 })
        : await api('/api/v1/overseas-securities/providers');
      const provider = probe ? payload : (payload.providers || [])[0];
      const [label, tone] = connectorStatus(provider?.status || 'configuration_required');
      setChip(statusChip, label, tone);
      setChip($('#conn-overseas'), label, tone);
      detail.textContent = provider?.configured
        ? `${provider.provider === 'twelve_data' ? 'Twelve Data' : provider.provider} · 搜索 / 报价 / 历史行情${probe ? ' · 连接验证通过' : ''}`
        : '适配器已安装，需在服务端配置 TWELVE_DATA_API_KEY';
      if (probe) toast('海外证券 API 连接正常', `${provider.probe_symbol || 'AAPL'} · ${provider.probe_source || 'twelve_data'}`);
      return provider;
    } catch (error) {
      setChip(statusChip, '不可用', 'error');
      setChip($('#conn-overseas'), '不可用', 'error');
      detail.textContent = error.message;
      renderOverseasError(error);
      if (probe) toast('海外证券 API 验证失败', error.message, 'error');
      return null;
    }
  }

  async function queryOverseasQuote(event) {
    event?.preventDefault();
    const { query, suffix } = overseasRequestParams();
    if (!query) { toast('请输入海外证券代码', '', 'error'); return; }
    $('#overseas-result').innerHTML = '<div class="loading-state"><span class="spinner"></span>查询海外证券报价</div>';
    try {
      const quote = await api(`/api/v1/overseas-securities/${encodeURIComponent(query.toUpperCase())}/quote?${suffix.slice(1)}`, { timeout: 35000 });
      const currency = quote.currency || '';
      $('#overseas-result').innerHTML = `<div class="overseas-quote"><div><span>证券</span><strong>${escapeHtml(quote.symbol || query)} · ${escapeHtml(quote.name || '名称未返回')}</strong><small>${escapeHtml([quote.exchange, quote.mic_code, quote.market].filter(Boolean).join(' · ') || '市场未标注')}</small></div><div><span>最新价</span><strong>${escapeHtml(currency)} ${formatNumber(quote.current_price, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</strong><small>${escapeHtml(quote.provider_timestamp || quote.fetched_at || '时间未返回')}</small></div><div><span>涨跌</span><strong>${formatPercent(quote.price_change_percent)}</strong><small>${formatNumber(quote.price_change, { maximumFractionDigits: 4 })}</small></div><div><span>日内范围</span><strong>${formatNumber(quote.day_low, { maximumFractionDigits: 4 })} – ${formatNumber(quote.day_high, { maximumFractionDigits: 4 })}</strong><small>开盘 ${formatNumber(quote.open, { maximumFractionDigits: 4 })}</small></div><div><span>来源</span><strong>Twelve Data</strong><small>${escapeHtml(quote.freshness_note || '时效取决于供应商授权')}</small></div></div>`;
    } catch (error) { renderOverseasError(error); }
  }

  async function searchOverseasSecurities() {
    const { query, suffix } = overseasRequestParams();
    if (!query) { toast('请输入证券代码或公司名称', '', 'error'); return; }
    $('#overseas-result').innerHTML = '<div class="loading-state"><span class="spinner"></span>搜索全球证券目录</div>';
    try {
      const result = await api(`/api/v1/overseas-securities/search?q=${encodeURIComponent(query)}${suffix}`, { timeout: 35000 });
      const items = result.results || [];
      $('#overseas-result').innerHTML = items.length
        ? `<div class="overseas-search-list">${items.map((item) => `<button class="overseas-search-item" type="button" data-overseas-symbol="${escapeHtml(item.symbol || '')}" data-overseas-country="${escapeHtml(item.country || '')}" data-overseas-exchange="${escapeHtml(item.exchange || '')}"><strong>${escapeHtml(item.symbol || '—')}</strong><span>${escapeHtml(item.name || '名称未返回')}</span><small>${escapeHtml([item.exchange, item.mic_code, item.country].filter(Boolean).join(' · ') || '市场未标注')}</small><em class="status-chip neutral">选择</em></button>`).join('')}</div>`
        : '<div class="empty-state small"><strong>没有找到匹配证券</strong><span>请尝试证券代码、英文公司名，或补充国家和交易所。</span></div>';
    } catch (error) { renderOverseasError(error); }
  }

  async function loadOverseasHistory() {
    const { query, suffix } = overseasRequestParams();
    if (!query) { toast('请输入海外证券代码', '', 'error'); return; }
    const period = $('#overseas-period').value;
    $('#overseas-result').innerHTML = '<div class="loading-state"><span class="spinner"></span>加载海外历史行情</div>';
    try {
      const result = await api(`/api/v1/overseas-securities/${encodeURIComponent(query.toUpperCase())}/historical?period=${encodeURIComponent(period)}&interval=1d${suffix}`, { timeout: 35000 });
      const rows = result.data || [];
      const first = rows[0] || {};
      const latest = rows[rows.length - 1] || {};
      $('#overseas-result').innerHTML = `<div class="overseas-history-summary"><div><span>证券 / 市场</span><strong>${escapeHtml(result.symbol || query)} · ${escapeHtml(result.exchange || '—')}</strong><small>${escapeHtml(result.currency || '')} · ${escapeHtml(result.exchange_timezone || '交易所本地时间')}</small></div><div><span>数据点</span><strong>${formatNumber(rows.length)}</strong><small>${escapeHtml(period)} · 日线</small></div><div><span>区间</span><strong>${escapeHtml(first.date || '—')} → ${escapeHtml(latest.date || '—')}</strong><small>按日期升序</small></div><div><span>最新收盘</span><strong>${escapeHtml(result.currency || '')} ${formatNumber(latest.close, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</strong><small>${escapeHtml(result.freshness_note || '时效取决于供应商套餐')}</small></div></div>`;
    } catch (error) { renderOverseasError(error); }
  }

  function getCurrency(symbol) {
    if (symbol.endsWith('.SH') || symbol.endsWith('.SZ')) return '¥';
    if (symbol.endsWith('.HK')) return 'HK$';
    return '$';
  }

  function normalizeMarketResult(item, symbol) {
    const nested = item?.data || item?.info || item || {};
    const price = nested.current_price ?? nested.currentPrice ?? nested.price ?? nested.regularMarketPrice;
    const previous = nested.previous_close ?? nested.previousClose ?? nested.regularMarketPreviousClose;
    let change = nested.price_change_percent ?? nested.priceChangePercent ?? nested.change_percent ?? nested.regularMarketChangePercent;
    if (asNumber(change) === null && asNumber(price) !== null && asNumber(previous) !== null && Number(previous) !== 0) {
      change = ((Number(price) - Number(previous)) / Number(previous)) * 100;
    }
    return {
      symbol: nested.symbol || symbol,
      name: nested.name || nested.longName || nested.shortName || '',
      price,
      change,
      marketCap: nested.market_cap ?? nested.marketCap,
      error: nested.error || item?.error,
    };
  }

  async function loadWatchlist() {
    const body = $('#watchlist-body');
    if (!body) return;
    const symbols = state.watchlist.slice(0, 6);
    if (!symbols.length) {
      body.innerHTML = '<tr><td colspan="5"><div class="empty-state small"><strong>关注列表为空</strong><span>在发现页管理关注标的，或从证券研究工作台直接加入。</span></div></td></tr>';
      return;
    }
    body.innerHTML = symbols.map(() => '<tr><td colspan="5"><div class="skeleton-row"></div></td></tr>').join('');
    try {
      const data = await api(`/api/v1/search/market?symbols=${encodeURIComponent(symbols.join(','))}`);
      const bySymbol = new Map((data.results || []).map((item, index) => [String(item.symbol || symbols[index]).toUpperCase(), item]));
      const rows = symbols.map((symbol) => normalizeMarketResult(bySymbol.get(symbol) || {}, symbol));
      body.innerHTML = rows.map((row) => {
        const change = asNumber(row.change);
        const status = row.error || asNumber(row.price) === null ? ['部分', 'partial'] : ['正常', 'healthy'];
        return `<tr>
          <td><div class="ticker-cell"><div class="ticker-logo">${escapeHtml(row.symbol.slice(0, 2))}</div><div><strong>${escapeHtml(row.symbol)}</strong><small>${escapeHtml(row.name || '证券信息')}</small></div></div></td>
          <td><strong>${formatPrice(row.price, getCurrency(row.symbol))}</strong></td>
          <td class="${change === null ? '' : change >= 0 ? 'positive' : 'negative'}">${formatPercent(change)}</td>
          <td><span class="status-chip ${status[1]}">${status[0]}</span></td>
          <td><button class="text-button" data-research-query="${escapeHtml(row.symbol)}">研究</button></td>
        </tr>`;
      }).join('');
    } catch (error) {
      body.innerHTML = `<tr><td colspan="5"><div class="empty-state small"><strong>关注行情暂时不可用</strong><span>${escapeHtml(error.message)}</span><button class="button ghost" id="watchlist-retry">重试</button></div></td></tr>`;
      $('#watchlist-retry')?.addEventListener('click', loadWatchlist);
    }
  }

  function normalizeSymbol(value) {
    return String(value || '').trim().toUpperCase().replace(/\s+/g, '');
  }

  function validSymbol(value) {
    return /^[A-Z0-9][A-Z0-9.-]{0,14}$/.test(value);
  }

  function openWatchlistManager() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<section class="manager-modal" role="dialog" aria-modal="true" aria-labelledby="watchlist-manager-title">
      <div class="modal-head"><div><p class="section-kicker">WATCHLIST</p><h2 id="watchlist-manager-title">管理关注列表</h2></div><button class="icon-button" type="button" data-close-watchlist aria-label="关闭关注列表管理"><svg><use href="#i-close"/></svg></button></div>
      <form class="inline-add-form" id="watchlist-add-form"><label class="sr-only" for="watchlist-symbol-input">证券代码</label><input id="watchlist-symbol-input" placeholder="输入代码，例如 AAPL、0700.HK"><button class="button primary" type="submit">添加</button></form>
      <div class="manager-note"><span>关注列表同时用于今日行情、发现候选与整组预警。</span><strong id="watchlist-manager-count">${state.watchlist.length} / 30</strong></div>
      <div class="watchlist-manager-list" id="watchlist-manager-list"></div>
    </section>`;
    document.body.appendChild(overlay);
    const render = () => {
      $('#watchlist-manager-count', overlay).textContent = `${state.watchlist.length} / 30`;
      $('#watchlist-manager-list', overlay).innerHTML = state.watchlist.length
        ? state.watchlist.map((symbol, index) => `<div><span class="ticker-logo">${escapeHtml(symbol.slice(0, 2))}</span><span><strong>${escapeHtml(symbol)}</strong><small>${index === 0 ? '主要关注' : '关注标的'}</small></span><button class="text-button danger" type="button" data-remove-watch="${escapeHtml(symbol)}">移除</button></div>`).join('')
        : '<div class="empty-state small"><strong>关注列表为空</strong><span>添加证券后会出现在今日行情与预警范围中。</span></div>';
    };
    render();
    $('[data-close-watchlist]', overlay).addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', (event) => { if (event.target === overlay) overlay.remove(); });
    $('#watchlist-manager-list', overlay).addEventListener('click', (event) => {
      const symbol = event.target.closest('[data-remove-watch]')?.dataset.removeWatch;
      if (!symbol) return;
      state.watchlist = state.watchlist.filter((item) => item !== symbol);
      writeStorage('nexus-watchlist', state.watchlist);
      updateWatchToggle();
      render();
      loadWatchlist();
    });
    $('#watchlist-add-form', overlay).addEventListener('submit', (event) => {
      event.preventDefault();
      const input = $('#watchlist-symbol-input', overlay);
      const symbol = normalizeSymbol(input.value);
      if (!validSymbol(symbol)) { toast('证券代码格式不正确', '请检查代码与市场后缀', 'error'); return; }
      if (state.watchlist.includes(symbol)) { toast('该标的已在关注列表', symbol, 'error'); return; }
      if (state.watchlist.length >= 30) { toast('关注列表已达上限', '请先移除不再关注的标的', 'error'); return; }
      state.watchlist.push(symbol);
      writeStorage('nexus-watchlist', state.watchlist);
      input.value = '';
      render();
      loadWatchlist();
      toast('已加入关注列表', symbol);
    });
    $('#watchlist-symbol-input', overlay).focus();
  }

  function isCandidateSaved(symbol) {
    return state.savedCandidates.some((item) => item.symbol === symbol);
  }

  function renderScreener() {
    const rows = state.screenerTab === 'saved' ? state.savedCandidates : state.screenerResults;
    const body = $('#screener-body');
    const countEl = $('#candidate-count');
    if (countEl) countEl.textContent = rows.length;
    $$('[data-screener-tab]').forEach((button) => button.classList.toggle('active', button.dataset.screenerTab === state.screenerTab));
    if (!rows.length) {
      if (body) body.innerHTML = `<tr><td colspan="6"><div class="empty-state small"><strong>${state.screenerTab === 'saved' ? '候选池为空' : '运行筛选以加载候选'}</strong><span>${state.screenerTab === 'saved' ? '从本次筛选结果中保存值得进一步研究的标的。' : '筛选只构建研究入口，不会直接生成交易信号。'}</span></div></td></tr>`;
      return;
    }
    if (!body) return;
    body.innerHTML = rows.map((row) => {
      const change = asNumber(row.change);
      const ok = !row.error && asNumber(row.price) !== null;
      const saved = isCandidateSaved(row.symbol);
      return `<tr><td><div class="ticker-cell"><div class="ticker-logo">${escapeHtml(row.symbol.slice(0, 2))}</div><div><strong>${escapeHtml(row.symbol)}</strong><small>${escapeHtml(row.name || '—')}</small></div></div></td><td>${formatPrice(row.price, getCurrency(row.symbol))}</td><td class="${change === null ? '' : change >= 0 ? 'positive' : 'negative'}">${formatPercent(change)}</td><td><span class="status-chip neutral">${escapeHtml(row.theme || '研究候选')}</span></td><td><span class="status-chip ${ok ? 'healthy' : 'partial'}">${ok ? '正常' : '部分'}</span></td><td><div class="row-actions"><button class="text-button" data-candidate-action="${saved ? 'remove' : 'save'}" data-candidate-symbol="${escapeHtml(row.symbol)}">${saved ? '移出候选' : '保存候选'}</button><button class="button ghost" data-research-query="${escapeHtml(row.symbol)}">研究</button></div></td></tr>`;
    }).join('');
  }

  function toggleCandidate(symbol, action) {
    const existing = state.savedCandidates.find((item) => item.symbol === symbol);
    if (action === 'remove' || existing) {
      state.savedCandidates = state.savedCandidates.filter((item) => item.symbol !== symbol);
      toast('已移出候选池', symbol);
    } else {
      const source = state.screenerResults.find((item) => item.symbol === symbol) || { symbol, theme: $('#filter-theme').value };
      state.savedCandidates.unshift({ ...source, savedAt: new Date().toISOString() });
      toast('已保存到候选池', `${symbol} · 下一步进入完整研究`);
    }
    writeStorage('nexus-candidates', state.savedCandidates);
    renderScreener();
  }

  function updateRangeOutputs() {
    const ranges = $$('.range-field');
    const capLabels = ['≤ 10 亿', '≤ 100 亿', '≤ 500 亿', '≤ 2,000 亿', '不限'];
    const volatilityLabels = ['很低 ≤ 4%', '较低 ≤ 6%', '中等 ≤ 10%', '较高 ≤ 15%', '不限'];
    if (ranges[0]) $('output', ranges[0]).textContent = capLabels[Number($('input', ranges[0]).value)] || '不限';
    if (ranges[1]) $('output', ranges[1]).textContent = volatilityLabels[Number($('input', ranges[1]).value)] || '不限';
  }

  function extractVolatility(payload) {
    return asNumber(payload?.indicators?.volatility?.bollinger_bands?.bandwidth);
  }

  function applyScreenerFilters(rows) {
    const ranges = $$('.range-field input');
    const capIndex = Number(ranges[0]?.value ?? 4);
    const volatilityIndex = Number(ranges[1]?.value ?? 4);
    const capLimits = [1e9, 1e10, 5e10, 2e11, Infinity];
    const volatilityLimits = [4, 6, 10, 15, Infinity];
    const healthyOnly = $('#filter-healthy').checked;
    return rows.filter((row) => {
      if (healthyOnly && (row.error || asNumber(row.price) === null)) return false;
      const cap = asNumber(row.marketCap);
      if (capIndex < 4 && (cap === null || cap > capLimits[capIndex])) return false;
      const volatility = asNumber(row.volatility);
      if (volatilityIndex < 4 && (volatility === null || volatility > volatilityLimits[volatilityIndex])) return false;
      return true;
    });
  }

  async function runScreener() {
    const market = $('#filter-market').value;
    const theme = $('#filter-theme').value;
    const universes = {
      US: ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META'],
      HK: ['0700.HK', '9988.HK', '3690.HK', '1810.HK'],
      CN: ['600519.SH', '300750.SZ', '601318.SH', '000858.SZ'],
    };
    const symbols = universes[market] || universes.US;
    const body = $('#screener-body');
    body.innerHTML = '<tr><td colspan="6"><div class="loading-state"><span class="spinner"></span>正在加载行情并计算 20 日波动</div></td></tr>';
    try {
      const data = await api(`/api/v1/search/market?symbols=${encodeURIComponent(symbols.join(','))}`);
      const baseRows = (data.results || []).map((item, index) => normalizeMarketResult(item, symbols[index]));
      if (!baseRows.length) throw new Error('市场接口没有返回候选数据');
      const technicals = await Promise.allSettled(baseRows.map((row) => api(`/api/v1/stocks/${encodeURIComponent(row.symbol)}/technical?period=1mo`)));
      const grokReview = $('#filter-grok-review').checked;
      const rows = baseRows.map((row, index) => ({ ...row, volatility: technicals[index].status === 'fulfilled' ? extractVolatility(technicals[index].value) : null, theme: grokReview ? `${theme} · Grok待核验` : theme, market }));
      state.screenerResults = applyScreenerFilters(rows);
      state.screenerTab = 'results';
      renderScreener();
      if (!state.screenerResults.length) toast('没有符合条件的候选', '可放宽市值或波动上限后重新运行', 'error');
    } catch (error) {
      body.innerHTML = `<tr><td colspan="6"><div class="empty-state small"><strong>筛选数据暂不可用</strong><span>${escapeHtml(error.message)}</span></div></td></tr>`;
    }
  }

  function renderRecent() {
    const container = $('#recent-symbols');
    if (!container) return;
    container.innerHTML = `<span>最近：</span>${state.recent.slice(0, 4).map((symbol) => `<button data-research-query="${escapeHtml(symbol)}">${escapeHtml(symbol)}</button>`).join('')}`;
  }

  async function openResearch(symbol) {
    symbol = String(symbol || '').trim().toUpperCase();
    if (!symbol) { toast('请输入证券代码', '例如 AAPL、0700.HK 或 600519.SH', 'error'); return; }
    state.symbol = symbol;
    state.stock = null;
    state.historical = null;
    state.technical = null;
    state.financials = null;
    state.intel = null;
    state.recent = [symbol, ...state.recent.filter((item) => item !== symbol)].slice(0, 6);
    writeStorage('nexus-recent', state.recent);
    renderRecent();
    showView('research');
    $('#research-symbol').value = symbol;
    $('#research-empty').classList.add('hidden');
    $('#research-workbench').classList.remove('hidden');
    resetResearchUI(symbol);
    addJob(`加载 ${symbol} 证券研究`, '行情、历史、技术与财务数据');

    const requests = await Promise.allSettled([
      api(`/api/v1/stocks/${encodeURIComponent(symbol)}/info`),
      api(`/api/v1/stocks/${encodeURIComponent(symbol)}/historical?period=6mo&interval=1d`),
      api(`/api/v1/stocks/${encodeURIComponent(symbol)}/technical?period=1y`),
      api(`/api/v1/stocks/${encodeURIComponent(symbol)}/financials`),
    ]);
    [state.stock, state.historical, state.technical, state.financials] = requests.map((result) => result.status === 'fulfilled' ? result.value : null);
    completeLatestJob();
    renderResearch(requests);
  }

  function resetResearchUI(symbol) {
    $('#security-logo').textContent = symbol.slice(0, 2);
    $('#security-name').textContent = symbol;
    $('#security-symbol').textContent = symbol;
    $('#security-market').textContent = '载入中';
    $('#security-sector').textContent = '正在汇集证券数据';
    $('#security-price').textContent = '—';
    $('#security-change').textContent = '—';
    $('#security-change').className = '';
    $('#security-time').textContent = '等待实时数据';
    $('#price-chart').innerHTML = '<div class="loading-state"><span class="spinner"></span>加载历史行情</div>';
    $('#chart-metrics').innerHTML = '';
    $('#metric-grid').innerHTML = '';
    $('#technical-content').innerHTML = '<div class="loading-state"><span class="spinner"></span>加载技术指标</div>';
    $('#financial-content').innerHTML = '<div class="loading-state"><span class="spinner"></span>加载财务数据</div>';
    $('#evidence-cards').innerHTML = '<div class="signal-row skeleton-block"></div><div class="signal-row skeleton-block"></div><div class="signal-row skeleton-block"></div>';
    setChip($('#evidence-status'), '收集中', 'partial');
    setChip($('#grok-model'), '待查询', 'neutral');
    setChip($('#intel-quality'), '尚未运行', 'neutral');
    $('#grok-synthesis').innerHTML = '<div class="empty-state small"><strong>按需运行实时查询</strong><span>结果会保留模型、来源和生成时间。</span></div>';
    $('#source-list').innerHTML = '<div class="empty-state small"><strong>暂无来源</strong><span>查询完成后，新闻与 X 来源会在此逐条展示。</span></div>';
    updateWatchToggle();
  }

  function renderResearch(results) {
    const stock = state.stock || { symbol: state.symbol };
    const currency = getCurrency(state.symbol);
    $('#security-name').textContent = stock.name || state.symbol;
    $('#security-symbol').textContent = stock.symbol || state.symbol;
    $('#security-market').textContent = stock.market || stock.exchange || marketLabel(state.symbol);
    $('#security-sector').textContent = [stock.sector, stock.industry].filter(Boolean).join(' · ') || '行业信息暂不可用';
    $('#security-price').textContent = formatPrice(stock.current_price, currency);
    const change = asNumber(stock.price_change_percent);
    $('#security-change').textContent = formatPercent(change);
    $('#security-change').className = change === null ? '' : change >= 0 ? 'positive' : 'negative';
    $('#security-time').textContent = `更新于 ${timestamp()} · ${state.stock ? '正常' : '部分数据'}`;
    renderChart(state.historical);
    renderMetrics(stock, state.financials);
    renderTechnical(state.technical);
    renderFinancials(state.financials);
    renderEvidence(results);
  }

  function marketLabel(symbol) {
    if (symbol.endsWith('.HK')) return 'HK';
    if (symbol.endsWith('.SH') || symbol.endsWith('.SZ')) return 'CN';
    return 'US';
  }

  function extractDataPoints(payload) {
    return (payload?.data || []).map((item) => ({
      date: item.date || item.timestamp,
      close: asNumber(item.close ?? item.Close),
      volume: asNumber(item.volume ?? item.Volume),
    })).filter((item) => item.close !== null);
  }

  function renderChart(payload) {
    const container = $('#price-chart');
    const data = extractDataPoints(payload);
    if (data.length < 2) {
      container.innerHTML = '<div class="empty-state small"><strong>历史行情不可用</strong><span>图表不会用示例曲线代替真实数据。</span></div>';
      $('#chart-metrics').innerHTML = '';
      return;
    }
    const width = 760, height = 250, left = 8, right = 54, top = 12, bottom = 28;
    const prices = data.map((item) => item.close);
    const min = Math.min(...prices), max = Math.max(...prices);
    const range = max - min || 1;
    const x = (index) => left + index * ((width - left - right) / (data.length - 1));
    const y = (value) => top + (max - value) * ((height - top - bottom) / range);
    const path = data.map((item, index) => `${index ? 'L' : 'M'}${x(index).toFixed(1)},${y(item.close).toFixed(1)}`).join(' ');
    const area = `${path} L${x(data.length - 1)},${height - bottom} L${left},${height - bottom} Z`;
    const ticks = [0, .25, .5, .75, 1].map((ratio) => {
      const value = max - ratio * range;
      const yy = y(value);
      return `<line class="chart-grid-line" x1="${left}" y1="${yy}" x2="${width - right}" y2="${yy}"/><text class="chart-axis" x="${width - right + 8}" y="${yy + 3}">${value.toFixed(2)}</text>`;
    }).join('');
    const dateLabels = [0, Math.floor((data.length - 1) / 2), data.length - 1].map((index) => `<text class="chart-axis" x="${x(index)}" y="${height - 7}" text-anchor="${index === 0 ? 'start' : index === data.length - 1 ? 'end' : 'middle'}">${escapeHtml(String(data[index].date || '').slice(0, 10))}</text>`).join('');
    container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(state.symbol)} 历史收盘价格走势"><defs><linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0da678" stop-opacity=".22"/><stop offset="1" stop-color="#0da678" stop-opacity="0"/></linearGradient></defs>${ticks}<path class="chart-area" d="${area}"/><path class="chart-line" d="${path}"/>${dateLabels}</svg>`;
    const start = prices[0], end = prices[prices.length - 1];
    const periodChange = ((end - start) / start) * 100;
    const quality = payload?.data_quality || {};
    $('#chart-metrics').innerHTML = `<div><span>区间变化</span><strong class="${periodChange >= 0 ? 'positive' : 'negative'}">${formatPercent(periodChange)}</strong></div><div><span>区间高点</span><strong>${formatPrice(max, getCurrency(state.symbol))}</strong></div><div><span>区间低点</span><strong>${formatPrice(min, getCurrency(state.symbol))}</strong></div><div><span>数据完整度</span><strong>${quality.completeness != null ? `${quality.completeness}%` : '—'}</strong></div>`;
  }

  function flattenMetrics(payload) {
    const groups = ['valuation_metrics', 'profitability_metrics', 'growth_metrics', 'liquidity_metrics'];
    const result = {};
    groups.forEach((group) => Object.assign(result, payload?.key_metrics?.[group] || payload?.[group] || {}));
    return result;
  }

  function renderMetrics(stock, financials) {
    const flat = flattenMetrics(financials);
    const items = [
      ['市值', formatCompact(stock.market_cap)],
      ['市盈率', formatNumber(stock.pe_ratio ?? flat.pe_ratio, { maximumFractionDigits: 2 })],
      ['市净率', formatNumber(flat.pb_ratio, { maximumFractionDigits: 2 })],
      ['股息率', flat.dividend_yield == null ? '—' : formatPercent(flat.dividend_yield, 100)],
      ['营收增长', flat.revenue_growth == null ? '—' : formatPercent(flat.revenue_growth, 100)],
      ['盈利增长', flat.earnings_growth == null ? '—' : formatPercent(flat.earnings_growth, 100)],
      ['净利率', flat.net_margin == null ? '—' : formatPercent(flat.net_margin, 100)],
      ['ROE', flat.roe == null ? '—' : formatPercent(flat.roe, 100)],
    ];
    $('#metric-grid').innerHTML = items.map(([label, value]) => `<div><span>${label}</span><strong>${escapeHtml(value)}</strong></div>`).join('');
    $('#metric-asof').textContent = `AS OF ${timestamp()}`;
  }

  function flattenObject(object, prefix = '') {
    const output = [];
    if (!object || typeof object !== 'object') return output;
    Object.entries(object).forEach(([key, value]) => {
      const label = prefix ? `${prefix} · ${key}` : key;
      if (value && typeof value === 'object' && !Array.isArray(value)) output.push(...flattenObject(value, label));
      else if (!Array.isArray(value)) output.push([label, value]);
    });
    return output;
  }

  function humanizeKey(key) {
    const map = { rsi: 'RSI', macd: 'MACD', sma_20: 'SMA 20', sma_50: 'SMA 50', pe_ratio: '市盈率', pb_ratio: '市净率', revenue_growth: '营收增长', earnings_growth: '盈利增长', gross_margin: '毛利率', net_margin: '净利率', roe: 'ROE', roa: 'ROA' };
    const tail = key.split(' · ').pop();
    return map[tail] || tail.replaceAll('_', ' ');
  }

  function displayValue(value) {
    if (value == null || value === '') return '—';
    if (typeof value === 'number') return formatNumber(value, { maximumFractionDigits: 4 });
    if (typeof value === 'boolean') return value ? '是' : '否';
    return String(value).replaceAll('_', ' ');
  }

  function renderTechnical(payload) {
    const content = $('#technical-content');
    if (!payload) { content.innerHTML = '<div class="empty-state small"><strong>技术指标不可用</strong><span>该数据源当前返回失败。</span></div>'; return; }
    const items = flattenObject(payload.indicators).filter(([, value]) => value == null || typeof value !== 'object').slice(0, 12);
    const signals = flattenObject(payload.signals).filter(([, value]) => typeof value !== 'object').slice(0, 4);
    const all = [...signals, ...items].slice(0, 14);
    content.innerHTML = all.length ? `<div class="data-list">${all.map(([key, value]) => `<div><span>${escapeHtml(humanizeKey(key))}</span><strong>${escapeHtml(displayValue(value))}</strong></div>`).join('')}</div>` : '<div class="empty-state small"><strong>没有可展示的技术指标</strong></div>';
  }

  function renderFinancials(payload) {
    const content = $('#financial-content');
    if (!payload) { content.innerHTML = '<div class="empty-state small"><strong>财务数据不可用</strong><span>该数据源当前返回失败。</span></div>'; return; }
    const items = flattenObject(payload.key_metrics || payload).filter(([, value]) => value == null || typeof value !== 'object').slice(0, 14);
    content.innerHTML = items.length ? `<div class="data-list">${items.map(([key, value]) => `<div><span>${escapeHtml(humanizeKey(key))}</span><strong>${escapeHtml(displayValue(value))}</strong></div>`).join('')}</div>` : '<div class="empty-state small"><strong>没有可展示的财务指标</strong></div>';
  }

  function renderEvidence(results) {
    const cards = [
      { title: '市场身份与报价', ok: results[0].status === 'fulfilled', detail: results[0].status === 'fulfilled' ? '证券身份、价格与交易市场已载入' : '行情接口未返回完整结果' },
      { title: '价格与技术证据', ok: results[1].status === 'fulfilled' && results[2].status === 'fulfilled', detail: results[1].status === 'fulfilled' ? '历史价格已冻结，技术指标状态可追踪' : '历史或技术数据缺失' },
      { title: 'Grok 实时情报', ok: false, partial: true, detail: '尚未运行；进入实时情报页按需查询' },
    ];
    $('#evidence-cards').innerHTML = cards.map((card) => `<div class="signal-row"><span class="signal-bar ${card.ok ? 'positive' : card.partial ? 'partial' : ''}"></span><div><strong>${card.title}</strong><small>${card.detail}</small></div><span class="status-chip ${card.ok ? 'healthy' : card.partial ? 'partial' : 'error'}">${card.ok ? '正常' : card.partial ? '待查询' : '缺失'}</span></div>`).join('');
    const fulfilled = results.filter((result) => result.status === 'fulfilled').length;
    setChip($('#evidence-status'), fulfilled === results.length ? '基础数据正常' : fulfilled ? '部分数据' : '不可用', fulfilled === results.length ? 'healthy' : fulfilled ? 'partial' : 'error');
    const gates = $$('#gate-checks .gate-dot');
    if (gates[0]) gates[0].className = `gate-dot ${fulfilled >= 2 ? 'ok' : 'partial'}`;
    if (gates[1]) gates[1].className = 'gate-dot pending';
    if (gates[2]) gates[2].className = 'gate-dot ok';
  }

  function updateWatchToggle() {
    const button = $('#watch-toggle');
    if (!button) return;
    const watched = state.watchlist.includes(state.symbol);
    button.textContent = watched ? '✓ 已关注' : '＋ 关注';
  }

  function toggleWatchlist() {
    if (!state.symbol) return;
    if (state.watchlist.includes(state.symbol)) {
      state.watchlist = state.watchlist.filter((item) => item !== state.symbol);
      toast('已移出关注列表', state.symbol);
    } else {
      if (state.watchlist.length >= 30) { toast('关注列表已达上限', '请先在发现页移除不再关注的标的', 'error'); return; }
      state.watchlist = [state.symbol, ...state.watchlist];
      toast('已加入关注列表', state.symbol);
    }
    writeStorage('nexus-watchlist', state.watchlist);
    updateWatchToggle();
    loadWatchlist();
  }

  async function changeChartPeriod(period) {
    if (!state.symbol) return;
    $('#price-chart').innerHTML = '<div class="loading-state"><span class="spinner"></span>更新历史行情</div>';
    try {
      state.historical = await api(`/api/v1/stocks/${encodeURIComponent(state.symbol)}/historical?period=${encodeURIComponent(period)}&interval=1d`);
      renderChart(state.historical);
    } catch (error) {
      renderChart(null);
      toast('历史行情加载失败', error.message, 'error');
    }
  }

  function selectResearchTab(tab) {
    $$('[data-research-tab]').forEach((button) => button.setAttribute('aria-selected', button.dataset.researchTab === tab ? 'true' : 'false'));
    $$('.research-tab-panel').forEach((panel) => panel.classList.toggle('active', panel.id === `research-panel-${tab}`));
  }

  async function runGrok(options = {}) {
    const symbol = options.symbol || state.symbol || $('#plan-symbol')?.value.trim().toUpperCase();
    if (!symbol) { toast('请先选择证券', '', 'error'); return null; }
    const days = Number($('#intel-window')?.value || 7);
    const button = $('#run-grok');
    if (button) { button.disabled = true; button.innerHTML = '<span class="spinner small"></span>查询中'; }
    setChip($('#grok-model'), '运行中', 'partial');
    setChip($('#intel-quality'), '收集中', 'partial');
    addJob(`${symbol} · Grok 实时查询`, `新闻、X 趋势与综合判断 · ${days} 天`);
    const query = `${symbol} stock latest earnings guidance material events market trend influential investors public statements`;
    const [sourcesResult, synthesisResult] = await Promise.allSettled([
      api('/api/v1/search/global', { method: 'POST', body: JSON.stringify({ query, sources: ['news', 'x'], limit: 20 }) }),
      api(`/api/v1/search/semantic?query=${encodeURIComponent(`${symbol} 最新重要新闻、趋势变化、风险与公开市场观点；区分事实、观点和未验证操作声明`)}&context=${encodeURIComponent('为量化研究生成可追溯摘要，不给出收益承诺或直接下单指令')}`, { method: 'POST', timeout: 60000 }),
    ]);
    completeLatestJob();
    if (button) { button.disabled = false; button.innerHTML = '<svg><use href="#i-refresh"/></svg>运行实时查询'; }
    const sources = sourcesResult.status === 'fulfilled' ? (sourcesResult.value.results || []) : [];
    const synthesis = synthesisResult.status === 'fulfilled' ? synthesisResult.value : null;
    if (!sources.length && !synthesis) {
      const message = [sourcesResult, synthesisResult].map((result) => result.reason?.message).filter(Boolean).join('；') || '实时情报服务未返回结果';
      setChip($('#grok-model'), '不可用', 'error');
      setChip($('#intel-quality'), '查询失败', 'error');
      if (!options.silent) toast('Grok 实时查询失败', message, 'error');
      $('#grok-synthesis').innerHTML = `<div class="empty-state small"><strong>实时查询暂不可用</strong><span>${escapeHtml(message)}</span></div>`;
      return null;
    }
    const model = synthesis?.model || 'OCI Grok';
    state.intel = { symbol, sources, synthesis: synthesis?.result || '', model, time: new Date().toISOString(), sourcesUsed: sourcesResult.status === 'fulfilled' ? sourcesResult.value.sources_used || [] : [] };
    renderIntelligence(state.intel);
    if (!options.silent) toast('实时情报已更新', `${sources.length} 条可追溯来源 · ${model}`);
    return state.intel;
  }

  function renderIntelligence(intel) {
    const sources = intel.sources || [];
    const newsCount = sources.filter((item) => item.source === 'news').length;
    const xCount = sources.filter((item) => item.source === 'x').length;
    const quality = sources.length >= 5 ? ['来源较完整', 'healthy'] : sources.length ? ['来源有限', 'partial'] : ['仅模型摘要', 'partial'];
    setChip($('#grok-model'), intel.model || 'OCI Grok', 'healthy');
    setChip($('#intel-quality'), quality[0], quality[1]);
    $('#intel-time').textContent = `AS OF ${timestamp(new Date(intel.time))}`;
    const copy = intel.synthesis || `模型未返回综合文本。已保留 ${sources.length} 条来源，请逐条核验后再形成研究判断。`;
    $('#grok-synthesis').innerHTML = `<div class="synthesis-copy"><p>${escapeHtml(copy)}</p><div class="synthesis-meta"><span>MODEL ${escapeHtml(intel.model || 'OCI Grok')}</span><span>SOURCES ${sources.length}</span><span>GENERATED ${escapeHtml(timestamp(new Date(intel.time)))}</span></div></div>`;
    $('#trend-content').innerHTML = `<div class="trend-stat"><div><strong>新闻覆盖</strong><small>返回的可追溯新闻来源</small></div><em>${newsCount} 条</em></div><div class="trend-stat"><div><strong>X 公开内容</strong><small>观点与操作声明默认未验证</small></div><em>${xCount} 条</em></div><div class="trend-stat"><div><strong>跨源状态</strong><small>新闻与 X 是否同时返回</small></div><em>${newsCount && xCount ? '双源' : '单源/部分'}</em></div>`;
    if (!sources.length) {
      $('#source-list').innerHTML = '<div class="empty-state small"><strong>没有可打开的来源</strong><span>该次结果仅包含模型摘要，应视为“部分证据”。</span></div>';
    } else {
      $('#source-list').innerHTML = sources.map((item) => {
        const link = safeUrl(item.url);
        const isX = item.source === 'x';
        return `<div class="source-item"><span class="source-kind ${isX ? 'unverified' : ''}"><i></i>${isX ? 'X · 未验证观点' : 'NEWS · 来源'}</span><div><strong>${escapeHtml(item.title || (isX ? 'X 公开内容' : '新闻来源'))}</strong><p>${escapeHtml(item.content || '无摘要')}</p></div>${link ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">打开来源 ↗</a>` : '<span class="status-chip partial">无链接</span>'}</div>`;
      }).join('');
    }
    const gate = $$('#gate-checks .gate-dot')[1];
    if (gate) gate.className = `gate-dot ${sources.length ? 'ok' : 'partial'}`;
    const cards = $('#evidence-cards');
    if (cards) {
      const rows = $$('.signal-row', cards);
      if (rows[2]) rows[2].outerHTML = `<div class="signal-row"><span class="signal-bar ${sources.length ? 'positive' : 'partial'}"></span><div><strong>Grok 实时情报</strong><small>${sources.length ? `${sources.length} 条来源已保留；X 观点仍需核验` : '仅模型摘要，来源证据不足'}</small></div><span class="status-chip ${sources.length ? 'healthy' : 'partial'}">${sources.length ? '已查询' : '部分'}</span></div>`;
    }
  }

  const PROJECT_RISK_LABELS = {
    political: '政治与政策',
    social: '社会与社区',
    debt: '债务与偿付',
    environment: '环境与许可',
    reputation: '声誉与利益相关方',
  };

  const PROJECT_ACTION_LABELS = {
    continue: '继续并保持监测',
    adjust_terms: '调整融资条款',
    pause_for_review: '暂停并专项复核',
    accelerate: '满足条件后加速',
    escalate: '升级至管理层',
  };

  const URGENCY_LABELS = {
    now: '立即',
    '7_days': '7 天内',
    '30_days': '30 天内',
    monitor: '持续监控',
  };

  const SCENARIO_LABELS = {
    baseline: '基准情景',
    stress: '压力情景',
    opportunity: '机会情景',
  };

  const TIMING_LABELS = {
    now: '立即',
    '30_days': '30 天内',
    quarter: '本季度',
  };

  const INTELLIGENCE_PDF_META = {
    'realtime-research': { stateKey: 'realtimeResearch', button: '#export-realtime-pdf', label: '实时信息检索' },
    'project-risk': { stateKey: 'projectRisk', button: '#export-project-risk-pdf', label: '项目风险情报' },
    'geopolitical-impact': { stateKey: 'geopoliticalImpact', button: '#export-geo-pdf', label: '地缘融资推演' },
    'sanctions-news': { stateKey: 'sanctionsNews', button: '#export-sanctions-pdf', label: '制裁与负面新闻' },
    'market-funding': { stateKey: 'marketFunding', button: '#export-market-pdf', label: '市场与资金环境' },
    'research-agent': { stateKey: 'researchAgent', button: '#export-agent-pdf', label: '研究与数据 Agent' },
  };

  const INTELLIGENCE_HISTORY_META = {
    'realtime-research': { list: '#realtime-history-list', count: '#realtime-history-count', label: '实时信息检索', render: renderRealtimeResearchResult },
    'project-risk': { list: '#project-history-list', count: '#project-history-count', label: '项目风险情报', render: renderProjectRiskResult },
    'geopolitical-impact': { list: '#geo-history-list', count: '#geo-history-count', label: '地缘融资推演', render: renderGeopoliticalResult },
    'sanctions-news': { list: '#sanctions-history-list', count: '#sanctions-history-count', label: '制裁与负面新闻', render: renderSanctionsResult },
    'market-funding': { list: '#market-history-list', count: '#market-history-count', label: '市场与资金环境', render: renderMarketResult },
    'research-agent': { list: '#agent-history-list', count: '#agent-history-count', label: '研究与数据 Agent', render: renderAgentResult },
  };

  function splitList(value) {
    return String(value || '').split(/[,，;；\n]/).map((item) => item.trim()).filter(Boolean);
  }

  function renderSourceList(selector, evidence) {
    const container = $(selector);
    if (!container) return;
    if (!evidence || !evidence.length) {
      container.innerHTML = '<div class="empty-state small"><strong>暂无来源</strong><span>完成后显示可访问链接与证据状态。</span></div>';
      return;
    }
    container.innerHTML = evidence.map((item) => {
      const link = safeUrl(item.url);
      const title = escapeHtml(item.title || item.source || '来源');
      const text = escapeHtml(item.text || item.excerpt || item.content || '');
      return `<div class="source-item"><div><strong>${title}</strong><p>${text}</p></div>${link ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">打开来源 ↗</a>` : ''}</div>`;
    }).join('');
  }

  function riskLevelMeta(level, score) {
    const normalized = String(level || '').toLowerCase();
    if (normalized === 'critical' || Number(score) >= 80) return ['严重', 'error'];
    if (normalized === 'high' || Number(score) >= 60) return ['高', 'error'];
    if (normalized === 'moderate' || Number(score) >= 35) return ['中等', 'partial'];
    if (normalized === 'low' || (score !== null && score !== undefined && Number(score) < 35)) return ['低', 'healthy'];
    return ['待评估', 'neutral'];
  }

  function trendLabel(value) {
    return { rising: '上升', stable: '稳定', falling: '下降', unknown: '未知' }[String(value || '').toLowerCase()] || '未知';
  }

  function evidenceStatusMeta(value) {
    const normalized = String(value || '').toLowerCase();
    if (['verified_source', 'official', 'sourced', 'source_available'].includes(normalized)) return ['有来源', 'healthy'];
    if (['reported_claim', 'reported'].includes(normalized)) return ['媒体转述', 'partial'];
    if (['opinion', 'inference', 'inferred'].includes(normalized)) return ['观点 / 推断', 'partial'];
    return ['未验证', 'error'];
  }

  function renderInstitutionalSources(selector, sources, emptyCopy = '实时检索完成后逐条展示链接与证据状态。') {
    const container = $(selector);
    if (!container) return;
    if (!sources?.length) {
      container.innerHTML = `<div class="empty-state small"><strong>暂无可访问来源</strong><span>${escapeHtml(emptyCopy)}</span></div>`;
      return;
    }
    container.innerHTML = sources.map((item) => {
      const link = safeUrl(item.url);
      const isX = item.source_type === 'x';
      return `<div class="source-item"><span class="source-kind ${isX ? 'unverified' : ''}"><i></i>${escapeHtml(item.id || '来源')} · ${isX ? 'X 公开内容' : '公开来源'}</span><div><strong>${escapeHtml(item.title || '未命名来源')}</strong><p>${escapeHtml(item.excerpt || (isX ? '公开观点或声明，需独立核验。' : '来源可访问，事实仍需交叉验证。'))}</p></div>${link ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">打开来源 ↗</a>` : '<span class="status-chip partial">无链接</span>'}</div>`;
    }).join('');
  }

  function renderRiskDimensions(dimensions = [], framework = []) {
    const container = $('#project-risk-dimensions');
    if (!container) return;
    const rows = dimensions.length ? dimensions : framework.map((item) => ({ dimension: item.id, label: item.label, score: null, level: 'unrated', trend: 'unknown', rationale: '等待实时证据后评估。' }));
    container.innerHTML = rows.map((item) => {
      const score = asNumber(item.score);
      const [levelLabel, status] = riskLevelMeta(item.level, score);
      const width = score === null ? 0 : Math.min(100, Math.max(0, score));
      return `<div class="risk-dimension"><div class="risk-dimension-head"><div><strong>${escapeHtml(item.label || PROJECT_RISK_LABELS[item.dimension] || item.dimension || '风险维度')}</strong><small>${escapeHtml(item.rationale || '暂无解释')}</small></div><div><em class="status-chip ${status}">${escapeHtml(levelLabel)}</em><span>${score === null ? '—' : Math.round(score)}</span></div></div><div class="risk-meter ${status}"><i style="width:${width}%"></i></div><small class="risk-trend">趋势：${escapeHtml(trendLabel(item.trend))}</small></div>`;
    }).join('');
  }

  function renderAuditRibbon(selector, result) {
    const audit = result?.audit || {};
    const sourceCount = result?.evidence?.length || 0;
    const requestId = audit.request_id ? String(audit.request_id).slice(0, 12) : '—';
    const windowLabel = audit.query_window_days
      ? `${audit.query_window_days}D`
      : [audit.date_from, audit.date_to].filter(Boolean).join(' → ') || '—';
    const usedTools = (audit.tools || []).join(' + ');
    const requestedTools = (audit.requested_tools || []).join(' + ');
    const tools = usedTools || (requestedTools ? `计划使用 ${requestedTools}` : '—');
    const element = $(selector);
    if (element) element.innerHTML = `<span>模型 ${escapeHtml(audit.model || '—')}</span><span>来源 ${sourceCount}</span><span>窗口 ${escapeHtml(windowLabel)}</span><span>工具 ${escapeHtml(tools)}</span><span>请求 ${escapeHtml(requestId)}</span>`;
  }

  async function loadIntelligenceCapabilities(force = false) {
    if (state.intelligenceCapabilities && !force) return state.intelligenceCapabilities;
    try {
      state.intelligenceCapabilities = await api('/api/v1/intelligence/capabilities', { timeout: 10000 });
    } catch (_) {
      state.intelligenceCapabilities = { configured: false, models: {} };
    }
    const configured = Boolean(state.intelligenceCapabilities.configured);
    setChip($('#today-intelligence-status'), configured ? 'OCI 已连接' : 'OCI 待配置', configured ? 'healthy' : 'partial');
    setChip($('#realtime-form-status'), configured ? '多源检索可用' : 'OCI 待配置', configured ? 'healthy' : 'partial');
    setChip($('#project-risk-form-status'), configured ? '实时可用' : '框架预览', configured ? 'healthy' : 'partial');
    setChip($('#geo-form-status'), configured ? '实时可用' : '框架预览', configured ? 'healthy' : 'partial');
    populateModelSelectors(state.intelligenceCapabilities.available_models || []);
    return state.intelligenceCapabilities;
  }

  function populateModelSelectors(models) {
    if (!models.length) return;
    const options = models.map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join('');
    ['#intel-model', '#realtime-model', '#project-risk-model', '#geo-model'].forEach((selector) => {
      const el = $(selector);
      if (!el) return;
      const current = el.value;
      el.innerHTML = '<option value="">默认模型</option>' + options;
      if (current && models.includes(current)) el.value = current;
    });
  }

  function intelligencePdfContext(workflow) {
    if (workflow === 'realtime-research') return realtimeResearchPayload();
    if (workflow === 'project-risk') return projectRiskPayload();
    if (workflow === 'geopolitical-impact') return geopoliticalPayload();
    if (workflow === 'sanctions-news') return sanctionsPayload();
    if (workflow === 'market-funding') return marketPayload();
    if (workflow === 'research-agent') return agentPayload();
    return {};
  }

  function updateIntelligencePdfButton(workflow, result) {
    const meta = INTELLIGENCE_PDF_META[workflow];
    const button = meta ? $(meta.button) : null;
    if (!button) return;
    const exportable = ['live', 'partial'].includes(result?.status)
      && result?.workflow === workflow
      && result?.analysis
      && Object.keys(result.analysis).length > 0;
    button.disabled = !exportable;
    button.title = exportable ? `将${meta.label}结果导出为 PDF` : '完成真实分析后可导出 PDF';
  }

  function trackActiveIntelligenceHistory(workflow, result) {
    state.activeIntelligenceHistory[workflow] = result?.history_record?.id || '';
    renderIntelligenceHistory(workflow);
  }

  function historyTriggerLabel(item) {
    if (item.trigger === 'schedule') return '定时监控';
    if (item.monitor_id) return '监控手动执行';
    return '手动分析';
  }

  function renderIntelligenceHistory(workflow) {
    const meta = INTELLIGENCE_HISTORY_META[workflow];
    if (!meta) return;
    const list = $(meta.list);
    const count = $(meta.count);
    const items = state.intelligenceHistory[workflow] || [];
    if (count) count.textContent = items.length;
    if (!list) return;
    if (!items.length) {
      list.innerHTML = '<div class="empty-state small"><strong>还没有分析记录</strong><span>真实或部分成功的分析会自动保存在这里。</span></div>';
      return;
    }
    list.innerHTML = items.map((item) => {
      const selected = state.activeIntelligenceHistory[workflow] === item.id;
      const created = item.created_at ? timestamp(new Date(item.created_at)) : '时间未知';
      const status = item.status === 'partial' ? '部分完成' : '已完成';
      return `<article class="analysis-history-item ${selected ? 'selected' : ''}"><button class="history-primary" type="button" data-history-action="open" data-history-id="${escapeHtml(item.id)}" data-history-workflow="${escapeHtml(workflow)}"><strong>${escapeHtml(item.title || meta.label)}</strong><small>${escapeHtml(created)} · ${escapeHtml(status)}</small><p>${escapeHtml(item.summary || '点击查看当时保存的完整分析结果。')}</p></button><em class="history-source-count">${Number(item.source_count || 0)} 源</em><div class="history-actions"><span>${escapeHtml(historyTriggerLabel(item))}</span><button class="text-button" type="button" data-history-action="export" data-history-id="${escapeHtml(item.id)}" data-history-workflow="${escapeHtml(workflow)}">导出当时记录</button></div></article>`;
    }).join('');
  }

  async function loadIntelligenceHistory(workflow) {
    const meta = INTELLIGENCE_HISTORY_META[workflow];
    if (!meta) return;
    const list = $(meta.list);
    if (list) list.innerHTML = '<div class="loading-state"><span class="spinner"></span>加载历史记录</div>';
    try {
      const data = await api(`/api/v1/intelligence/history?workspace_id=${encodeURIComponent(state.workspaceId)}&workflow=${encodeURIComponent(workflow)}&limit=50`, { timeout: 15000 });
      state.intelligenceHistory[workflow] = data.items || [];
      renderIntelligenceHistory(workflow);
    } catch (error) {
      if (list) list.innerHTML = `<div class="empty-state small"><strong>历史记录暂不可用</strong><span>${escapeHtml(error.message)}</span></div>`;
    }
  }

  function restoreIntelligenceHistoryContext(workflow, context = {}) {
    if (workflow === 'realtime-research') {
      $('#realtime-query').value = context.query || '';
      $('#realtime-keywords').value = (context.keywords || []).join(', ');
      if (context.window_days) { const w = $('#realtime-window'); if (w) w.value = String(context.window_days); }
      $$('input[name="realtime-source"]').forEach((input) => { input.checked = (context.source_channels || []).includes(input.value); });
      $('#realtime-use-code').checked = context.use_code_interpreter !== false;
      $('#realtime-preserve-original').checked = context.preserve_x_original !== false;
      return;
    }
    if (workflow === 'project-risk') {
      $('#project-country').value = context.country || '';
      $('#project-name').value = context.project_name || '';
      $('#project-product').value = context.product_type || 'sovereign_loan';
      $('#project-window').value = String(context.window_days || 7);
      $('#project-question').value = context.monitoring_question || '';
      $$('input[name="project-risk-focus"]').forEach((input) => { input.checked = (context.risk_focus || []).includes(input.value); });
      return;
    }
    $('#geo-issue').value = context.issue || '';
    $('#geo-regions').value = (context.regions || []).join(', ');
    $('#geo-actors').value = (context.actors || []).join(', ');
    const products = context.product_types || [];
    const product = products.length > 1 ? '全部产品' : products[0];
    if (product && Array.from($('#geo-product').options).some((option) => option.value === product)) $('#geo-product').value = product;
    $('#geo-horizon').value = context.horizon || 'one_year';
    $('#geo-window').value = String(context.window_days || 30);
    $('#geo-question').value = context.decision_question || '';
  }

  async function openIntelligenceHistory(recordId, workflow) {
    const meta = INTELLIGENCE_HISTORY_META[workflow];
    if (!meta) return;
    try {
      const detail = await api(`/api/v1/intelligence/history/${encodeURIComponent(recordId)}?workspace_id=${encodeURIComponent(state.workspaceId)}`, { timeout: 15000 });
      const historyRecord = { ...detail };
      delete historyRecord.result;
      delete historyRecord.query_context;
      const result = { ...(detail.result || {}), history_record: historyRecord };
      restoreIntelligenceHistoryContext(workflow, detail.query_context || {});
      state.activeIntelligenceHistory[workflow] = recordId;
      meta.render(result);
      renderIntelligenceHistory(workflow);
      document.querySelector(meta.list)?.closest('.intelligence-query-panel')?.nextElementSibling?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      toast('已打开历史分析', `${meta.label} · ${detail.created_at ? timestamp(new Date(detail.created_at)) : '已保存记录'}`);
    } catch (error) {
      toast('打开历史记录失败', error.message, 'error');
    }
  }

  async function downloadIntelligenceHistoryPdf(recordId, workflow, button = null) {
    const meta = INTELLIGENCE_HISTORY_META[workflow];
    if (!meta) return;
    const original = button?.innerHTML;
    if (button) {
      button.disabled = true;
      button.innerHTML = '<span class="spinner small"></span>生成 PDF';
    }
    try {
      const response = await fetch(`${API_BASE}/api/v1/intelligence/history/${encodeURIComponent(recordId)}/pdf?workspace_id=${encodeURIComponent(state.workspaceId)}`);
      if (response.status === 401) {
        window.location.replace(`/login?next=${encodeURIComponent(`${window.location.pathname}${window.location.search}`)}`);
        return;
      }
      if (!response.ok) {
        const type = response.headers.get('content-type') || '';
        const payload = type.includes('application/json') ? await response.json() : await response.text();
        throw new Error(typeof payload === 'object' ? (payload.detail || '历史记录导出失败') : payload);
      }
      const blob = await response.blob();
      if (blob.type !== 'application/pdf' || blob.size < 1000) throw new Error('服务端没有返回有效 PDF');
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = objectUrl;
      anchor.download = pdfDownloadFilename(response, workflow);
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 30000);
      toast('历史记录 PDF 已生成', `${meta.label} · ${(blob.size / 1024).toFixed(1)} KB`);
    } catch (error) {
      toast('历史记录导出失败', error.message, 'error');
    } finally {
      if (button) {
        button.innerHTML = original;
        button.disabled = false;
        const meta2 = INTELLIGENCE_PDF_META[workflow];
        if (meta2 && button.matches('.intelligence-pdf-button')) updateIntelligencePdfButton(workflow, state[meta2.stateKey]);
      }
    }
  }

  function pdfDownloadFilename(response, workflow) {
    const disposition = response.headers.get('content-disposition') || '';
    const encoded = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
    if (encoded) {
      try { return decodeURIComponent(encoded); } catch (_) { /* use fallback */ }
    }
    return `${INTELLIGENCE_PDF_META[workflow]?.label || '情报分析'}-${new Date().toISOString().slice(0, 10)}.pdf`;
  }

  async function downloadIntelligencePdf(workflow) {
    const meta = INTELLIGENCE_PDF_META[workflow];
    const result = meta ? state[meta.stateKey] : null;
    const button = meta ? $(meta.button) : null;
    if (!meta || !button || !['live', 'partial'].includes(result?.status)) {
      toast('暂无可导出的真实分析结果', '请先完成对应的实时检索或推演', 'error');
      return;
    }
    const historyId = result.history_record?.id || state.activeIntelligenceHistory[workflow];
    if (historyId) {
      await downloadIntelligenceHistoryPdf(historyId, workflow, button);
      return;
    }
    const original = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>生成 PDF';
    try {
      const response = await fetch(`${API_BASE}/api/v1/intelligence/export/pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflow, result, query_context: intelligencePdfContext(workflow) }),
      });
      if (!response.ok) {
        const type = response.headers.get('content-type') || '';
        const payload = type.includes('application/json') ? await response.json() : await response.text();
        throw new Error(typeof payload === 'object' ? (payload.detail || 'PDF 生成失败') : payload);
      }
      const blob = await response.blob();
      if (blob.type !== 'application/pdf' || blob.size < 1000) throw new Error('服务端没有返回有效 PDF');
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = objectUrl;
      anchor.download = pdfDownloadFilename(response, workflow);
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 30000);
      toast('PDF 已生成', `${meta.label} · ${(blob.size / 1024).toFixed(1)} KB`, 'success');
    } catch (error) {
      toast('PDF 导出失败', error.message, 'error');
    } finally {
      button.innerHTML = original;
      updateIntelligencePdfButton(workflow, result);
    }
  }

  async function downloadScheduledMonitorReport(item) {
    const report = item?.latest_report;
    if (!report?.id) {
      toast('尚无定时报告', '真实监控成功运行后会自动生成 PDF', 'error');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/v1/intelligence/reports/${encodeURIComponent(report.id)}/download?workspace_id=${encodeURIComponent(state.workspaceId)}`);
      if (!response.ok) {
        const type = response.headers.get('content-type') || '';
        const payload = type.includes('application/json') ? await response.json() : await response.text();
        throw new Error(typeof payload === 'object' ? (payload.detail || '报告下载失败') : payload);
      }
      const blob = await response.blob();
      if (blob.type !== 'application/pdf' || blob.size < 1000) throw new Error('服务端没有返回有效 PDF');
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = objectUrl;
      anchor.download = report.filename || 'intelligence-monitor-report.pdf';
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(objectUrl), 30000);
      toast('定时报告已下载', `${item.name} · ${(blob.size / 1024).toFixed(1)} KB`, 'success');
    } catch (error) {
      toast('定时报告下载失败', error.message, 'error');
    }
  }

  function realtimeResearchPayload() {
    const days = Number($('#realtime-window')?.value || 7);
    const to = new Date();
    const from = new Date(to);
    from.setDate(from.getDate() - days);
    return {
      query: $('#realtime-query').value.trim(),
      keywords: splitList($('#realtime-keywords').value),
      date_from: from.toISOString().slice(0, 10),
      date_to: to.toISOString().slice(0, 10),
      source_channels: $$('input[name="realtime-source"]:checked').map((input) => input.value),
      use_code_interpreter: $('#realtime-use-code').checked,
      preserve_x_original: $('#realtime-preserve-original').checked,
      max_results: 30,
      window_days: days,
      workspace_id: state.workspaceId,
      model_id: $('#realtime-model')?.value || null,
    };
  }

  function renderRealtimeItems() {
    const container = $('#realtime-items');
    if (!container) return;
    const allItems = state.realtimeResearch?.items || [];
    const items = state.realtimeFilter === 'all'
      ? allItems
      : allItems.filter((item) => item.source_type === state.realtimeFilter);
    $('#realtime-item-count').textContent = allItems.length;
    if (!items.length) {
      container.innerHTML = `<div class="empty-state small"><strong>${allItems.length ? '当前通道没有结果' : '尚无可展示结果'}</strong><span>${allItems.length ? '切换到“全部”查看其他来源。' : '未运行、未配置或证据不足时不会生成占位内容。'}</span></div>`;
      return;
    }
    container.innerHTML = items.map((item) => {
      const isX = item.source_type === 'x';
      const [evidenceLabel, evidenceClass] = evidenceStatusMeta(item.evidence_status);
      const link = safeUrl(item.url);
      const original = isX ? item.original_text : '';
      const summary = item.content_excerpt || '';
      const body = isX ? original : summary;
      const chineseContext = isX && summary
        ? `<div class="item-chinese-translation"><strong>中文说明</strong><p>${escapeHtml(summary)}</p></div>`
        : '';
      return `<article class="realtime-item ${isX ? 'x-item' : 'web-item'}"><div class="realtime-item-meta"><span class="source-channel ${isX ? 'x' : 'web'}">${isX ? 'X' : '网页'}</span><span>${escapeHtml(item.author || '未知发布者')}</span><time>${escapeHtml(item.published_at || '时间未知')}</time><em class="status-chip ${evidenceClass}">${escapeHtml(evidenceLabel)}</em></div><h3>${escapeHtml(item.title || (isX ? 'X 公开内容' : '公共开放来源'))}</h3>${body ? `<blockquote class="${isX ? 'original-post' : ''}">${escapeHtml(body)}</blockquote>` : '<p class="missing-content">来源没有返回可验证的正文摘录。</p>'}${chineseContext}<div class="realtime-item-foot"><span>${escapeHtml((item.matched_keywords || []).join(' · ') || '未标注匹配词')}</span>${link ? `<a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer">打开原始来源 ↗</a>` : '<span class="status-chip partial">无可访问链接</span>'}</div></article>`;
    }).join('');
  }

  function renderRealtimeResearchResult(result) {
    const analysis = result?.analysis || {};
    const hasLiveResult = ['live', 'partial'].includes(result?.status);
    const partial = result?.status === 'partial';
    const counts = result?.counts || {};
    setChip($('#realtime-status'), hasLiveResult ? (partial ? '部分检索完成' : '检索完成') : 'OCI 待配置', hasLiveResult ? (partial ? 'partial' : 'healthy') : 'partial');
    $('#realtime-asof').textContent = hasLiveResult ? `截至 ${timestamp(new Date(result.audit?.generated_at || Date.now()))}` : '未查询外部信息';
    $('#realtime-summary').className = hasLiveResult ? 'brief-copy' : 'brief-placeholder';
    $('#realtime-summary').innerHTML = hasLiveResult
      ? `<p>${escapeHtml(analysis.executive_summary || '本次没有返回可解析的综述，请检查来源账本。')}</p>`
      : `<strong>实时检索尚未运行</strong><span>${escapeHtml(result?.configuration?.message || '配置服务端 OCI 凭证后才能查询 X 和公共网页。')}</span>`;
    $('#realtime-coverage').innerHTML = `<span>覆盖说明</span><p>${escapeHtml(analysis.coverage_note || result?.warnings?.[0] || '结果为尽力覆盖，不代表 X 或公共网络的全量数据。')}</p>`;
    renderAuditRibbon('#realtime-audit', result);
    $('#realtime-x-count').textContent = counts.x || 0;
    $('#realtime-web-count').textContent = counts.public || 0;
    $('#realtime-citation-count').textContent = counts.citations || 0;
    $('#realtime-coverage-state').textContent = hasLiveResult ? (partial ? '部分' : '尽力覆盖') : '未运行';

    const trends = analysis.trends || [];
    $('#realtime-trend-count').textContent = `${trends.length} 个`;
    $('#realtime-trends').innerHTML = trends.length ? trends.map((item) => `<div class="realtime-trend"><span>${escapeHtml({ rising: '↑', falling: '↓', stable: '→', unclear: '?' }[item.direction] || '?')}</span><div><strong>${escapeHtml(item.label || '未命名趋势')}</strong><p>${escapeHtml(item.evidence || '没有提供证据说明。')}</p><small>${escapeHtml((item.source_refs || []).join(' · ') || '未映射具体来源')}</small></div></div>`).join('') : '<div class="empty-state small"><strong>没有可验证趋势</strong><span>没有足够证据时不会生成趋势占位值。</span></div>';
    state.realtimeResearch = result;
    updateIntelligencePdfButton('realtime-research', result);
    renderRealtimeItems();
    renderInstitutionalSources('#realtime-sources', result?.evidence || []);
    const warnings = result?.warnings || [];
    $('#realtime-warning').innerHTML = `<svg><use href="#i-shield"/></svg><span>${escapeHtml(warnings.join('；') || '公开内容是研究证据；观点、转述和交易声明不会自动升级为事实。')}</span>`;
    trackActiveIntelligenceHistory('realtime-research', result);
  }

  async function runRealtimeResearch(event) {
    event?.preventDefault();
    const payload = realtimeResearchPayload();
    if (!payload.query) { toast('请输入检索主题', '说明希望查询的对象、事件或问题', 'error'); return; }
    if (!payload.source_channels.length) { toast('至少选择一个信息通道', '可选择 X 或公共开放网页', 'error'); return; }
    if (payload.date_from && payload.date_to && payload.date_from > payload.date_to) { toast('日期范围不正确', '开始日期不能晚于结束日期', 'error'); return; }
    const button = $('#run-realtime-research');
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>检索 X 与公共信息';
    addJob('实时多源信息检索', `${payload.source_channels.join(' + ')} · ${payload.keywords.join(' / ') || payload.query.slice(0, 24)}`);
    try {
      const result = await api('/api/v1/intelligence/realtime/search', { method: 'POST', body: JSON.stringify(payload), timeout: 120000 });
      renderRealtimeResearchResult(result);
      if (result.history_record?.id) loadIntelligenceHistory('realtime-research');
      const complete = ['live', 'partial'].includes(result.status);
      toast(complete ? '实时信息检索完成' : 'OCI Grok 尚未配置', complete ? `X ${result.counts?.x || 0} 条 · 公共网页 ${result.counts?.public || 0} 条 · 引用 ${result.counts?.citations || 0} 条` : '没有查询外部信息，也没有生成模拟结果', complete ? 'success' : 'error');
    } catch (error) {
      setChip($('#realtime-status'), '检索失败', 'error');
      toast('实时信息检索失败', error.message, 'error');
    } finally {
      completeLatestJob();
      button.disabled = false;
      button.innerHTML = '<svg><use href="#i-search"/></svg>运行实时检索';
    }
  }

  function projectRiskPayload() {
    return {
      country: $('#project-country').value.trim(),
      project_name: $('#project-name').value.trim(),
      product_type: $('#project-product').value,
      risk_focus: $$('input[name="project-risk-focus"]:checked').map((input) => input.value),
      window_days: Number($('#project-window').value),
      monitoring_question: $('#project-question').value.trim() || null,
      workspace_id: state.workspaceId,
      model_id: $('#project-risk-model')?.value || null,
      material_session_id: state.projectMaterialSessionId || null,
    };
  }

  function renderProjectRiskResult(result) {
    state.projectRisk = result;
    const analysis = result?.analysis || {};
    const live = ['live', 'partial'].includes(result?.status);
    const configuredMessage = result?.configuration?.message;
    const overall = riskLevelMeta(analysis.overall_risk, null);
    setChip($('#project-risk-status'), live ? `${overall[0]}风险` : 'OCI 待配置', live ? overall[1] : 'partial');
    $('#project-risk-asof').textContent = live ? `截至 ${timestamp(new Date(result.audit?.generated_at || Date.now()))}` : '未生成实时事实';
    $('#project-risk-summary').className = live ? 'brief-copy' : 'brief-placeholder';
    $('#project-risk-summary').innerHTML = live
      ? `<p>${escapeHtml(analysis.executive_summary || '模型未返回管理层摘要。')}</p>`
      : `<strong>实时分析尚未运行</strong><span>${escapeHtml(configuredMessage || '配置 OCI Grok 后生成带引用的风险简报。')}</span>`;
    $('#project-risk-direct').innerHTML = `<span>直接判断</span><p>${escapeHtml(live ? (analysis.direct_assessment || '本次没有形成直接判断，需人工检查来源账本。') : '当前仅展示分析框架；没有调用模型，也没有生成或伪造实时风险结论。')}</p>`;
    renderAuditRibbon('#project-risk-audit', result);
    renderRiskDimensions(analysis.risk_dimensions || [], result?.analysis_framework || []);

    const actions = analysis.decision_options || [];
    $('#project-risk-actions').innerHTML = actions.length ? actions.map((item, index) => `<div class="decision-option"><span>${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHtml(PROJECT_ACTION_LABELS[item.action] || item.action || '复核动作')}</strong><p>${escapeHtml(item.rationale || '等待人工补充判断依据。')}</p><small>${escapeHtml(item.owner || '待指定负责人')} · ${escapeHtml(URGENCY_LABELS[item.urgency] || item.urgency || '持续监控')} · 触发：${escapeHtml(item.trigger || '待定义')}</small></div></div>`).join('') : '<div class="empty-state small"><strong>尚无动作建议</strong><span>每个动作必须包含负责人、时限和可观察触发条件。</span></div>';

    const events = analysis.events || [];
    $('#project-event-count').textContent = `${events.length} 条`;
    $('#project-risk-events').innerHTML = events.length ? events.map((item) => {
      const [label, status] = evidenceStatusMeta(item.evidence_status);
      return `<div class="ground-signal"><span class="signal-time">${escapeHtml(item.observed_at || '时间未知')}</span><div><div class="signal-title"><strong>${escapeHtml(item.title || '未命名事件')}</strong><em class="status-chip ${status}">${escapeHtml(label)}</em></div><p>${escapeHtml(item.impact || '影响尚未评估。')}</p><small>${escapeHtml((item.source_refs || []).join(' · ') || '未映射具体来源')}</small></div></div>`;
    }).join('') : '<div class="empty-state small"><strong>没有可展示的实时事件</strong><span>未运行或证据不足时不会生成占位事件。</span></div>';
    renderInstitutionalSources('#project-risk-sources', result?.evidence || []);
    updateIntelligencePdfButton('project-risk', result);
    trackActiveIntelligenceHistory('project-risk', result);
  }

  async function runProjectRisk(event) {
    event?.preventDefault();
    const payload = projectRiskPayload();
    if (!payload.country || !payload.project_name) { toast('请填写国家/地区和项目名称', '两项信息用于限定实时检索范围', 'error'); return; }
    if (!payload.risk_focus.length) { toast('至少选择一个风险维度', '', 'error'); return; }
    const button = $('#run-project-risk');
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>扫描实时地面信号';
    addJob(`${payload.project_name} · 项目风险扫描`, `${payload.country} · ${payload.window_days} 天 · Grok 4.3`);
    try {
      const result = await api('/api/v1/intelligence/project-risk/analyze', { method: 'POST', body: JSON.stringify(payload), timeout: 100000 });
      state.projectRisk = result;
      renderProjectRiskResult(result);
      if (result.history_record?.id) loadIntelligenceHistory('project-risk');
      const complete = ['live', 'partial'].includes(result.status);
      toast(complete ? '项目风险简报已生成' : 'OCI Grok 尚未配置', complete ? `${result.evidence?.length || 0} 条来源进入证据账本` : '已展示完整分析框架，没有生成实时事实', complete ? 'success' : 'error');
    } catch (error) {
      setChip($('#project-risk-status'), '查询失败', 'error');
      toast('项目风险扫描失败', error.message, 'error');
    } finally {
      completeLatestJob();
      button.disabled = false;
      button.innerHTML = '<svg><use href="#i-radar"/></svg>运行 Grok 风险扫描';
    }
  }

  function monitorStatusMeta(item) {
    if (!item.is_active) return ['已暂停', 'neutral'];
    return {
      scheduled: ['等待执行', 'healthy'],
      running: ['运行中', 'partial'],
      live: ['实时完成', 'healthy'],
      partial: ['部分完成', 'partial'],
      configuration_required: ['OCI 待配置', 'partial'],
      failed: ['执行失败', 'error'],
    }[item.last_status] || [item.last_status || '等待执行', 'neutral'];
  }

  function monitorListMeta(type) {
    return type === 'realtime_research'
      ? { list: $('#realtime-monitor-list'), count: $('#realtime-monitor-count'), scheduler: $('#realtime-scheduler-status'), empty: '尚无实时信息监控', hint: '填写主题并选择间隔后，可由服务端按计划重复检索。' }
      : { list: $('#project-monitor-list'), count: $('#project-monitor-count'), scheduler: $('#project-scheduler-status'), empty: '尚无项目风险监控', hint: '填写国家/地区和项目后，可由服务端按计划重复扫描。' };
  }

  function monitorIntervalOptions(selected) {
    return Object.entries(MONITOR_INTERVAL_LABELS).map(([value, label]) => `<option value="${value}" ${Number(value) === Number(selected) ? 'selected' : ''}>${escapeHtml(label)}</option>`).join('');
  }

  function renderIntelligenceMonitors(type) {
    const meta = monitorListMeta(type);
    if (!meta.list) return;
    const monitors = state.intelligenceMonitors.filter((item) => item.monitor_type === type);
    meta.count.textContent = monitors.length;
    if (!monitors.length) {
      meta.list.innerHTML = `<div class="empty-state small"><strong>${meta.empty}</strong><span>${meta.hint}</span></div>`;
      return;
    }
    meta.list.innerHTML = monitors.map((item) => {
      const payload = item.request_payload || {};
      const realtime = type === 'realtime_research';
      const mark = realtime ? 'RT' : String(payload.country || 'PR').slice(0, 2).toUpperCase();
      const detail = realtime
        ? `${(payload.keywords || []).join(' · ') || 'X + 公共网页'} · ${payload.max_results || 30} 条上限`
        : `${payload.country || '未指定地区'} · ${payload.window_days || 7} 天证据窗口`;
      const [statusLabel, statusClass] = monitorStatusMeta(item);
      const next = item.is_active && item.next_run_at ? `下次 ${timestamp(new Date(item.next_run_at))}` : '定时执行已暂停';
      const report = item.latest_report;
      const reportLine = report
        ? `<small class="monitor-next monitor-report">${escapeHtml(timestamp(new Date(report.generated_at)))} 自动生成 · ${(Number(report.byte_size || 0) / 1024).toFixed(1)} KB</small>`
        : '<small class="monitor-next">真实结果完成后自动生成 PDF</small>';
      const reportAction = report
        ? `<button class="text-button" data-intelligence-monitor-action="download-report" data-monitor-id="${escapeHtml(item.id)}">下载最新报告</button>`
        : '';
      return `<article class="monitor-item ${item.is_active ? '' : 'paused'}"><button class="monitor-primary" data-intelligence-monitor-action="open" data-monitor-id="${escapeHtml(item.id)}"><span class="monitor-mark">${escapeHtml(mark)}</span><div><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(detail)}</small></div></button><div class="monitor-schedule"><span class="status-chip ${statusClass}">${escapeHtml(statusLabel)}</span><label class="monitor-interval-control"><span>间隔</span><select data-monitor-interval data-monitor-id="${escapeHtml(item.id)}" aria-label="调整 ${escapeHtml(item.name)} 的监控间隔">${monitorIntervalOptions(item.schedule_minutes)}</select></label></div><small class="monitor-next">${escapeHtml(next)}</small>${reportLine}<div class="monitor-actions"><button class="text-button" data-intelligence-monitor-action="run" data-monitor-id="${escapeHtml(item.id)}">立即运行</button>${reportAction}<button class="text-button" data-intelligence-monitor-action="toggle" data-monitor-id="${escapeHtml(item.id)}">${item.is_active ? '暂停' : '恢复'}</button><button class="text-button danger" data-intelligence-monitor-action="delete" data-monitor-id="${escapeHtml(item.id)}">移除</button></div></article>`;
    }).join('');
  }

  async function loadIntelligenceMonitors(type) {
    const meta = monitorListMeta(type);
    if (meta.list) meta.list.innerHTML = '<div class="loading-state"><span class="spinner"></span>加载监控任务</div>';
    try {
      const data = await api(`/api/v1/intelligence/monitors?workspace_id=${encodeURIComponent(state.workspaceId)}&monitor_type=${encodeURIComponent(type)}`);
      state.intelligenceMonitors = [
        ...state.intelligenceMonitors.filter((item) => item.monitor_type !== type),
        ...(data.items || []),
      ];
      setChip(meta.scheduler, data.scheduler?.running ? '调度运行中' : '调度未运行', data.scheduler?.running ? 'healthy' : 'error');
      renderIntelligenceMonitors(type);
    } catch (error) {
      setChip(meta.scheduler, '调度不可用', 'error');
      if (meta.list) meta.list.innerHTML = `<div class="empty-state small"><strong>监控任务暂不可用</strong><span>${escapeHtml(error.message)}</span></div>`;
    }
  }

  function replaceIntelligenceMonitor(next) {
    state.intelligenceMonitors = [next, ...state.intelligenceMonitors.filter((item) => item.id !== next.id)];
    renderIntelligenceMonitors(next.monitor_type);
  }

  async function createIntelligenceMonitor(type) {
    const realtime = type === 'realtime_research';
    const payload = realtime ? realtimeResearchPayload() : projectRiskPayload();
    if (realtime && !payload.query) { toast('请输入检索主题', '保存监控前需要定义查询对象', 'error'); return; }
    if (realtime && !payload.source_channels.length) { toast('至少选择一个信息通道', '', 'error'); return; }
    if (realtime && payload.date_from && payload.date_to && payload.date_from > payload.date_to) { toast('日期范围不正确', '开始日期不能晚于结束日期', 'error'); return; }
    if (!realtime && (!payload.country || !payload.project_name)) { toast('请先填写监测对象', '需要国家/地区和项目名称', 'error'); return; }
    if (!realtime && !payload.risk_focus.length) { toast('至少选择一个风险维度', '', 'error'); return; }
    const intervalSelector = realtime ? $('#realtime-monitor-interval') : $('#project-monitor-interval');
    const button = realtime ? $('#save-realtime-monitor') : $('#save-project-monitor');
    const scheduleMinutes = Number(intervalSelector.value);
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>保存监控';
    try {
      const monitor = await api('/api/v1/intelligence/monitors', {
        method: 'POST',
        body: JSON.stringify({
          monitor_type: type,
          name: realtime ? payload.query.slice(0, 80) : `${payload.country} · ${payload.project_name}`,
          schedule_minutes: scheduleMinutes,
          request_payload: payload,
          workspace_id: state.workspaceId,
          is_active: true,
        }),
      });
      replaceIntelligenceMonitor(monitor);
      toast('定时监控已启用', `${MONITOR_INTERVAL_LABELS[scheduleMinutes]} · 首次运行可等待计划或点击立即运行`);
    } catch (error) {
      toast('保存定时监控失败', error.message, 'error');
    } finally {
      button.disabled = false;
      button.innerHTML = '<svg><use href="#i-bell"/></svg>保存定时监控';
    }
  }

  function openIntelligenceMonitor(item) {
    const payload = item.request_payload || {};
    if (item.monitor_type === 'realtime_research') {
      showView('realtime-research');
      $('#realtime-query').value = payload.query || '';
      $('#realtime-keywords').value = (payload.keywords || []).join(', ');
      if (payload.window_days) { const w = $('#realtime-window'); if (w) w.value = String(payload.window_days); }
      $$('input[name="realtime-source"]').forEach((input) => { input.checked = (payload.source_channels || []).includes(input.value); });
      $('#realtime-use-code').checked = payload.use_code_interpreter !== false;
      $('#realtime-preserve-original').checked = payload.preserve_x_original !== false;
      $('#realtime-monitor-interval').value = String(item.schedule_minutes);
      if (item.last_result) renderRealtimeResearchResult(item.last_result);
      return;
    }
    showView('project-risk');
    $('#project-country').value = payload.country || '';
    $('#project-name').value = payload.project_name || '';
    $('#project-product').value = payload.product_type || 'sovereign_loan';
    $('#project-window').value = String(payload.window_days || 7);
    $('#project-question').value = payload.monitoring_question || '';
    $('#project-monitor-interval').value = String(item.schedule_minutes);
    $$('input[name="project-risk-focus"]').forEach((input) => { input.checked = (payload.risk_focus || []).includes(input.value); });
    if (item.last_result) renderProjectRiskResult(item.last_result);
  }

  async function handleIntelligenceMonitor(id, action) {
    const item = state.intelligenceMonitors.find((monitor) => monitor.id === id);
    if (!item) return;
    if (action === 'open') { openIntelligenceMonitor(item); return; }
    if (action === 'download-report') { downloadScheduledMonitorReport(item); return; }
    if (action === 'delete') {
      try {
        await api(`/api/v1/intelligence/monitors/${encodeURIComponent(id)}`, { method: 'DELETE' });
        state.intelligenceMonitors = state.intelligenceMonitors.filter((monitor) => monitor.id !== id);
        renderIntelligenceMonitors(item.monitor_type);
        toast('定时监控已移除', item.name);
      } catch (error) { toast('移除监控失败', error.message, 'error'); }
      return;
    }
    if (action === 'toggle') {
      try {
        const updated = await api(`/api/v1/intelligence/monitors/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ is_active: !item.is_active }) });
        replaceIntelligenceMonitor(updated);
        toast(updated.is_active ? '定时监控已恢复' : '定时监控已暂停', updated.schedule_label);
      } catch (error) { toast('更新监控失败', error.message, 'error'); }
      return;
    }
    if (action === 'run') {
      addJob(`${item.name} · 定时情报`, '手动触发服务端监控任务');
      try {
        const execution = await api(`/api/v1/intelligence/monitors/${encodeURIComponent(id)}/run`, { method: 'POST', timeout: 120000 });
        if (execution.monitor) replaceIntelligenceMonitor(execution.monitor);
        const result = execution.run?.result;
        if (result && execution.history_record) result.history_record = execution.history_record;
        if (result && item.monitor_type === 'realtime_research') renderRealtimeResearchResult(result);
        if (result && item.monitor_type === 'project_risk') renderProjectRiskResult(result);
        if (execution.history_record?.workflow) loadIntelligenceHistory(execution.history_record.workflow);
        const configured = result && ['live', 'partial'].includes(result.status);
        const reportStatus = execution.report_generation?.status;
        const detail = configured
          ? reportStatus === 'generated'
            ? '最新结果已载入工作台，PDF 已自动保存'
            : reportStatus === 'failed'
              ? '结果已载入，但 PDF 保存失败，请查看服务状态'
              : '最新结果已载入工作台'
          : 'OCI 未配置，没有查询外部信息，也未生成报告';
        toast(configured ? '监控任务执行完成' : '监控任务已记录', detail, configured && reportStatus !== 'failed' ? 'success' : 'error');
      } catch (error) {
        toast('立即运行失败', error.message, 'error');
      } finally { completeLatestJob(); }
    }
  }

  async function updateIntelligenceMonitorInterval(id, scheduleMinutes) {
    const item = state.intelligenceMonitors.find((monitor) => monitor.id === id);
    if (!item || !MONITOR_INTERVAL_LABELS[scheduleMinutes]) return;
    try {
      const updated = await api(`/api/v1/intelligence/monitors/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify({ schedule_minutes: scheduleMinutes }) });
      replaceIntelligenceMonitor(updated);
      toast('监控间隔已更新', updated.schedule_label);
    } catch (error) {
      renderIntelligenceMonitors(item.monitor_type);
      toast('更新监控间隔失败', error.message, 'error');
    }
  }

  function geopoliticalPayload() {
    const product = $('#geo-product').value;
    return {
      issue: $('#geo-issue').value.trim(),
      regions: splitList($('#geo-regions').value),
      actors: splitList($('#geo-actors').value),
      product_types: product === '全部产品' ? ['主权贷款', '非主权融资', '担保', '联合融资'] : [product],
      horizon: $('#geo-horizon').value,
      window_days: Number($('#geo-window').value),
      decision_question: $('#geo-question').value.trim() || null,
      workspace_id: state.workspaceId,
      model_id: $('#geo-model')?.value || null,
      material_session_id: state.geoMaterialSessionId || null,
    };
  }

  function scenarioClass(name, index) {
    const normalized = String(name || '').toLowerCase();
    if (normalized.includes('stress') || normalized.includes('压力')) return 'bear';
    if (normalized.includes('opportunity') || normalized.includes('机会')) return 'bull';
    return index === 1 ? 'bear' : index === 2 ? 'bull' : 'base';
  }

  function renderGeopoliticalResult(result) {
    state.geopoliticalImpact = result;
    const analysis = result?.analysis || {};
    const live = ['live', 'partial'].includes(result?.status);
    setChip($('#geo-status'), live ? '推演完成' : 'OCI 待配置', live ? 'healthy' : 'partial');
    $('#geo-asof').textContent = live ? `截至 ${timestamp(new Date(result.audit?.generated_at || Date.now()))}` : '未生成实时事实';
    $('#geo-summary').className = live ? 'brief-copy' : 'brief-placeholder';
    $('#geo-summary').innerHTML = live
      ? `<p>${escapeHtml(analysis.executive_summary || '模型未返回战略摘要。')}</p>`
      : `<strong>实时推演尚未运行</strong><span>${escapeHtml(result?.configuration?.message || '配置 OCI Grok 后生成多情景融资影响分析。')}</span>`;
    $('#geo-direct').innerHTML = `<span>重点关注</span><p>${escapeHtml(live ? (analysis.direct_assessment || '本次没有形成直接判断，需人工检查来源和假设。') : '当前仅展示分析框架；没有调用模型，也没有生成或伪造实时政策结论。')}</p>`;
    renderAuditRibbon('#geo-audit', result);

    const paths = analysis.transmission_paths || [];
    $('#geo-transmission').innerHTML = paths.length ? paths.map((item, index) => {
      const [label, status] = evidenceStatusMeta(item.evidence_status);
      return `<div class="transmission-step"><span>${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHtml(item.driver || '驱动因素')}</strong><p>${escapeHtml(item.mechanism || '传导机制待补充')}</p><small>${escapeHtml(item.financing_effect || '融资影响待评估')} · ${escapeHtml((item.affected_parties || []).join('、') || '相关方待识别')}</small></div><em class="status-chip ${status}">${escapeHtml(label)}</em></div>`;
    }).join('') : '<div class="empty-state small"><strong>等待推理链</strong><span>未运行或证据不足时不会生成占位因果关系。</span></div>';

    const scenarios = analysis.scenarios || [];
    $('#geo-scenarios').innerHTML = scenarios.length ? scenarios.slice(0, 3).map((item, index) => `<article class="panel scenario ${scenarioClass(item.name, index)}"><span>${escapeHtml(SCENARIO_LABELS[item.name] || item.name || `情景 ${index + 1}`)} · ${escapeHtml(item.probability || '概率未量化')}</span><h2>${escapeHtml(item.pipeline_impact || '项目管道影响待评估')}</h2><dl><div><dt>联合融资</dt><dd>${escapeHtml(item.cofinancing_impact || '—')}</dd></div><div><dt>借贷意愿</dt><dd>${escapeHtml(item.borrowing_appetite || '—')}</dd></div><div><dt>可行性</dt><dd>${escapeHtml(item.feasibility || '—')}</dd></div><div><dt>风险转移</dt><dd>${escapeHtml(item.risk_transfer || '—')}</dd></div></dl><strong>早期信号：${escapeHtml((item.early_signals || []).join('；') || '尚未识别')}</strong></article>`).join('') : '<article class="panel scenario base"><span>基准情景</span><h2>等待推演</h2><p>配置并运行 Grok 后展示融资影响。</p><strong>没有生成演示结论</strong></article><article class="panel scenario bear"><span>压力情景</span><h2>等待推演</h2><p>识别可行性恶化与风险转移。</p><strong>没有生成演示结论</strong></article><article class="panel scenario bull"><span>机会情景</span><h2>等待推演</h2><p>识别合作窗口与替代路径。</p><strong>没有生成演示结论</strong></article>';

    const actions = analysis.decision_options || [];
    $('#geo-actions').innerHTML = actions.length ? actions.map((item, index) => `<div class="decision-option"><span>${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHtml(item.action || '策略选项')}</strong><p><b>收益：</b>${escapeHtml(item.upside || '待评估')} · <b>代价：</b>${escapeHtml(item.downside || '待评估')}</p><small>${escapeHtml(item.owner || '待指定负责人')} · ${escapeHtml(TIMING_LABELS[item.timing] || item.timing || '待确定时机')} · 触发：${escapeHtml(item.trigger || '待定义')}</small></div></div>`).join('') : '<div class="empty-state small"><strong>尚无策略选项</strong><span>推演后展示时机、收益、代价和触发条件。</span></div>';

    const assumptions = [...(analysis.assumptions || []).map((item) => ({ type: '假设', copy: item })), ...(analysis.unknowns || []).map((item) => ({ type: '未知', copy: item }))];
    $('#geo-assumptions').innerHTML = assumptions.length ? assumptions.map((item) => `<div><span>${escapeHtml(item.type)}</span><p>${escapeHtml(item.copy)}</p></div>`).join('') : '<div class="empty-state small"><strong>尚无假设</strong><span>关键不确定性必须显式呈现。</span></div>';
    renderInstitutionalSources('#geo-sources', result?.evidence || []);
    updateIntelligencePdfButton('geopolitical-impact', result);
    trackActiveIntelligenceHistory('geopolitical-impact', result);
  }

  async function runGeopoliticalAnalysis(event) {
    event?.preventDefault();
    const payload = geopoliticalPayload();
    if (!payload.issue) { toast('请填写地缘事件或政策变化', '需要明确分析对象', 'error'); return; }
    const button = $('#run-geo-analysis');
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>运行多情景推演';
    addJob('地缘融资影响推演', `${payload.horizon} · ${payload.window_days} 天实时证据 · Multi-Agent`);
    try {
      const result = await api('/api/v1/intelligence/geopolitical-impact/analyze', { method: 'POST', body: JSON.stringify(payload), timeout: 120000 });
      state.geopoliticalImpact = result;
      renderGeopoliticalResult(result);
      if (result.history_record?.id) loadIntelligenceHistory('geopolitical-impact');
      const complete = ['live', 'partial'].includes(result.status);
      toast(complete ? '地缘融资推演已生成' : 'OCI Grok 尚未配置', complete ? `${result.evidence?.length || 0} 条来源进入证据账本` : '已展示完整推演框架，没有生成实时事实', complete ? 'success' : 'error');
    } catch (error) {
      setChip($('#geo-status'), '推演失败', 'error');
      toast('地缘融资推演失败', error.message, 'error');
    } finally {
      completeLatestJob();
      button.disabled = false;
      button.innerHTML = '<svg><use href="#i-globe"/></svg>运行多情景推演';
    }
  }

  // ── 场景 03：制裁与负面新闻 ──────────────────────────────────────

  function sanctionsPayload() {
    return {
      entity_name: $('#sanctions-entity').value.trim(),
      entity_type: $('#sanctions-entity-type').value,
      jurisdictions: splitList($('#sanctions-jurisdictions').value),
      risk_focus: $$('input[name="sanctions-risk"]:checked').map((input) => input.value),
      window_days: Number($('#sanctions-window').value),
      additional_context: $('#sanctions-context').value.trim() || null,
      model_id: $('#sanctions-model')?.value || null,
      workspace_id: state.workspaceId,
      material_session_id: state.sanctionsMaterialSessionId || null,
    };
  }

  async function runSanctionsNews(event) {
    event?.preventDefault();
    const payload = sanctionsPayload();
    if (!payload.entity_name) { toast('请填写审查对象名称', '例如公司名称或个人姓名', 'error'); return; }
    const button = $('#run-sanctions');
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>运行合规审查';
    addJob('制裁与负面新闻审查', `${payload.entity_type} · ${payload.window_days} 天`);
    try {
      const result = await api('/api/v1/intelligence/sanctions-news/analyze', { method: 'POST', body: JSON.stringify(payload), timeout: 120000 });
      state.sanctionsNews = result;
      renderSanctionsResult(result);
      if (result.history_record?.id) loadIntelligenceHistory('sanctions-news');
      const complete = ['live', 'partial'].includes(result.status);
      toast(complete ? '合规审查完成' : 'OCI Grok 尚未配置', complete ? `${result.evidence?.length || 0} 条来源` : '已展示审查框架', complete ? 'success' : 'error');
    } catch (error) {
      setChip($('#sanctions-status'), '审查失败', 'error');
      toast('制裁与负面新闻审查失败', error.message, 'error');
    } finally {
      completeLatestJob();
      button.disabled = false;
      button.innerHTML = '<svg><use href="#i-shield"/></svg>运行合规审查';
    }
  }

  function renderSanctionsResult(result) {
    const hasLiveResult = ['live', 'partial'].includes(result?.status);
    const partial = result?.status === 'partial';
    const analysis = result?.analysis || {};
    setChip($('#sanctions-status'), hasLiveResult ? (partial ? '部分完成' : '已完成') : '尚未运行', hasLiveResult ? (partial ? 'partial' : 'healthy') : 'neutral');
    $('#sanctions-asof').textContent = hasLiveResult ? `截至 ${timestamp(new Date(result.audit?.generated_at || Date.now()))}` : '等待查询';
    $('#sanctions-summary').className = hasLiveResult ? 'brief-copy' : 'brief-placeholder';
    $('#sanctions-summary').innerHTML = hasLiveResult
      ? `<p>${escapeHtml(analysis.executive_summary || result?.output_text || '本次没有返回可解析的综述。')}</p>`
      : '<strong>输入审查对象后运行合规检索</strong><span>将检索制裁名单、负面媒体、监管行动和诉讼信息。</span>';
    renderAuditRibbon('#sanctions-audit', result);
    const findings = analysis.findings || [];
    const findingsContainer = $('#sanctions-findings');
    if (findingsContainer) {
      if (findings.length) {
        findingsContainer.innerHTML = findings.map((f) => `<div class="synthesis-copy"><strong>${escapeHtml(f.label || f.category || '发现')}</strong><p>${escapeHtml(f.finding || '')}</p><small>${escapeHtml(f.evidence_status || '')} · ${escapeHtml((f.source_refs || []).join(', ') || '无来源')}</small></div>`).join('');
      } else if (hasLiveResult) {
        findingsContainer.innerHTML = '<div class="empty-state small"><strong>没有风险发现</strong><span>本次审查未发现匹配的风险线索。</span></div>';
      }
    }
    renderInstitutionalSources('#sanctions-sources', result?.evidence || [], '合规审查完成后逐条展示来源与证据状态。');
    updateIntelligencePdfButton('sanctions-news', result);
    trackActiveIntelligenceHistory('sanctions-news', result);
  }

  // ── 场景 04：市场与资金环境 ──────────────────────────────────────

  function marketPayload() {
    return {
      topic: $('#market-topic').value.trim(),
      regions: splitList($('#market-regions').value),
      indicators: $$('input[name="market-indicator"]:checked').map((input) => input.value),
      horizon: $('#market-horizon').value,
      window_days: Number($('#market-window').value),
      decision_context: $('#market-context').value.trim() || null,
      model_id: $('#market-model')?.value || null,
      workspace_id: state.workspaceId,
      material_session_id: state.marketMaterialSessionId || null,
    };
  }

  async function runMarketFunding(event) {
    event?.preventDefault();
    const payload = marketPayload();
    if (!payload.topic) { toast('请填写研究主题', '例如利率环境或汇率走势', 'error'); return; }
    const button = $('#run-market');
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>运行市场分析';
    addJob('市场与资金环境分析', `${payload.horizon} · ${payload.window_days} 天`);
    try {
      const result = await api('/api/v1/intelligence/market-funding/analyze', { method: 'POST', body: JSON.stringify(payload), timeout: 120000 });
      state.marketFunding = result;
      renderMarketResult(result);
      if (result.history_record?.id) loadIntelligenceHistory('market-funding');
      const complete = ['live', 'partial'].includes(result.status);
      toast(complete ? '市场分析完成' : 'OCI Grok 尚未配置', complete ? `${result.evidence?.length || 0} 条来源` : '已展示分析框架', complete ? 'success' : 'error');
    } catch (error) {
      setChip($('#market-status'), '分析失败', 'error');
      toast('市场与资金环境分析失败', error.message, 'error');
    } finally {
      completeLatestJob();
      button.disabled = false;
      button.innerHTML = '<svg><use href="#i-chart"/></svg>运行市场分析';
    }
  }

  function renderMarketResult(result) {
    const hasLiveResult = ['live', 'partial'].includes(result?.status);
    const partial = result?.status === 'partial';
    const analysis = result?.analysis || {};
    setChip($('#market-status'), hasLiveResult ? (partial ? '部分完成' : '已完成') : '尚未运行', hasLiveResult ? (partial ? 'partial' : 'healthy') : 'neutral');
    $('#market-asof').textContent = hasLiveResult ? `截至 ${timestamp(new Date(result.audit?.generated_at || Date.now()))}` : '等待查询';
    $('#market-summary').className = hasLiveResult ? 'brief-copy' : 'brief-placeholder';
    $('#market-summary').innerHTML = hasLiveResult
      ? `<p>${escapeHtml(analysis.executive_summary || result?.output_text || '本次没有返回可解析的综述。')}</p>`
      : '<strong>输入研究主题后运行市场分析</strong><span>将分析利率、汇率、信用利差、商品价格和融资条件。</span>';
    renderAuditRibbon('#market-audit', result);
    const indicators = analysis.key_findings || [];
    const indContainer = $('#market-indicators');
    if (indContainer) {
      if (indicators.length) {
        indContainer.innerHTML = indicators.map((f) => `<div class="synthesis-copy"><strong>${escapeHtml(f.label || f.indicator || '指标')}</strong><p>${escapeHtml(f.current_assessment || '')}</p><small>趋势: ${escapeHtml(f.trend || '—')} · 影响: ${escapeHtml(f.impact_on_aiib || '—')}</small></div>`).join('');
      } else if (hasLiveResult) {
        indContainer.innerHTML = '<div class="empty-state small"><strong>没有指标数据</strong><span>本次分析未返回结构化指标。</span></div>';
      }
    }
    renderInstitutionalSources('#market-sources', result?.evidence || [], '市场分析完成后逐条展示来源与数据引用。');
    updateIntelligencePdfButton('market-funding', result);
    trackActiveIntelligenceHistory('market-funding', result);
  }

  // ── 场景 05：研究与数据 Agent ──────────────────────────────────────

  function agentPayload() {
    return {
      query: $('#agent-query').value.trim(),
      data_sources: $$('input[name="agent-tool"]:checked').map((input) => input.value),
      calculation_required: $('#agent-calculation').checked,
      verification_level: $('#agent-verification').value,
      max_results: Number($('#agent-max').value),
      model_id: $('#agent-model')?.value || null,
      workspace_id: state.workspaceId,
    };
  }

  async function runResearchAgent(event) {
    event?.preventDefault();
    const payload = agentPayload();
    if (!payload.query) { toast('请填写研究问题', '例如分析投资趋势或计算增长率', 'error'); return; }
    const button = $('#run-agent');
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>运行研究 Agent';
    addJob('研究与数据 Agent', `${payload.verification_level} 校验 · ${payload.data_sources.join(' + ')}`);
    try {
      const result = await api('/api/v1/intelligence/research-agent/run', { method: 'POST', body: JSON.stringify(payload), timeout: 120000 });
      state.researchAgent = result;
      renderAgentResult(result);
      if (result.history_record?.id) loadIntelligenceHistory('research-agent');
      const complete = ['live', 'partial'].includes(result.status);
      toast(complete ? '研究 Agent 完成' : 'OCI Grok 尚未配置', complete ? `${result.evidence?.length || 0} 条来源` : '已展示研究框架', complete ? 'success' : 'error');
    } catch (error) {
      setChip($('#agent-status'), '执行失败', 'error');
      toast('研究与数据 Agent 执行失败', error.message, 'error');
    } finally {
      completeLatestJob();
      button.disabled = false;
      button.innerHTML = '<svg><use href="#i-lab"/></svg>运行研究 Agent';
    }
  }

  function renderAgentResult(result) {
    const hasLiveResult = ['live', 'partial'].includes(result?.status);
    const partial = result?.status === 'partial';
    const analysis = result?.analysis || {};
    setChip($('#agent-status'), hasLiveResult ? (partial ? '部分完成' : '已完成') : '尚未运行', hasLiveResult ? (partial ? 'partial' : 'healthy') : 'neutral');
    $('#agent-asof').textContent = hasLiveResult ? `截至 ${timestamp(new Date(result.audit?.generated_at || Date.now()))}` : '等待执行';
    $('#agent-summary').className = hasLiveResult ? 'brief-copy' : 'brief-placeholder';
    $('#agent-summary').innerHTML = hasLiveResult
      ? `<p>${escapeHtml(analysis.executive_summary || result?.output_text || '本次没有返回可解析的综述。')}</p>`
      : '<strong>输入研究问题后运行数据 Agent</strong><span>将使用代码解释器进行数据处理、统计分析和趋势计算。</span>';
    renderAuditRibbon('#agent-audit', result);
    const computation = analysis.computation_results || [];
    const compContainer = $('#agent-computation');
    if (compContainer) {
      if (computation.length) {
        compContainer.innerHTML = computation.map((c) => `<div class="synthesis-copy"><strong>${escapeHtml(c.description || '计算')}</strong><p>方法: ${escapeHtml(c.method || '—')}</p><p>结果: ${escapeHtml(String(c.result || '—'))}</p><small>可复现: ${c.reproducible ? '是' : '否'}</small></div>`).join('');
      } else if (hasLiveResult) {
        compContainer.innerHTML = '<div class="empty-state small"><strong>没有计算结果</strong><span>本次分析未包含代码计算步骤。</span></div>';
      }
    }
    renderInstitutionalSources('#agent-sources', result?.evidence || [], '研究 Agent 执行完成后逐条展示数据来源与交叉验证结果。');
    updateIntelligencePdfButton('research-agent', result);
    trackActiveIntelligenceHistory('research-agent', result);
  }

  const ALERT_CONDITIONS = {
    price_above: '价格高于',
    price_below: '价格低于',
    move: '日涨跌幅超过',
    grok_event: 'Grok 重大事件',
    plan_review: '计划到期复核',
  };

  function alertNeedsThreshold(condition) {
    return ['price_above', 'price_below', 'move'].includes(condition);
  }

  function updateAlertFields() {
    const watchlistScope = $('#alert-scope').value === 'watchlist';
    $('#alert-symbol-field').classList.toggle('hidden', watchlistScope);
    $('#alert-threshold-field').classList.toggle('hidden', !alertNeedsThreshold($('#alert-condition').value));
  }

  function renderAlerts() {
    const list = $('#alert-list');
    const active = state.alerts.filter((item) => item.status !== 'paused').length;
    $('#alert-count').textContent = state.alerts.length;
    $('#notification-pip').classList.toggle('hidden', active === 0);
    if (!state.alerts.length) {
      list.innerHTML = '<div class="empty-state small"><strong>还没有预警规则</strong><span>为单一证券或整个关注列表设置价格、波动、重大事件或计划复核条件。</span></div>';
      return;
    }
    list.innerHTML = state.alerts.map((item) => {
      const scope = item.scope === 'watchlist' ? `关注列表 · ${state.watchlist.length} 个标的` : item.symbol;
      const threshold = alertNeedsThreshold(item.condition) ? ` · ${item.condition === 'move' ? `${item.threshold}%` : formatNumber(item.threshold)}` : '';
      const paused = item.status === 'paused';
      return `<article class="alert-rule ${paused ? 'paused' : ''}"><div class="alert-rule-head"><div><strong>${escapeHtml(scope || '未指定')}</strong><small>${escapeHtml(ALERT_CONDITIONS[item.condition] || item.condition)}${escapeHtml(threshold)}</small></div><span class="status-chip ${paused ? 'neutral' : 'partial'}">${paused ? '已暂停' : '待调度'}</span></div><p>${paused ? '规则已暂停。' : '规则已保存；后台定时触发器配置后开始监测。'}触发后仅进入人工复核。</p><div class="alert-actions"><button class="text-button" data-alert-action="toggle" data-alert-id="${escapeHtml(item.id)}">${paused ? '启用' : '暂停'}</button><button class="text-button danger" data-alert-action="delete" data-alert-id="${escapeHtml(item.id)}">删除</button></div></article>`;
    }).join('');
  }

  function saveAlert(event) {
    event.preventDefault();
    const scope = $('#alert-scope').value;
    const condition = $('#alert-condition').value;
    const symbol = normalizeSymbol($('#alert-symbol').value || state.symbol);
    const thresholdText = $('#alert-threshold').value.trim();
    const threshold = Number(thresholdText);
    if (scope === 'symbol' && !validSymbol(symbol)) { toast('请输入有效证券代码', '例如 AAPL、0700.HK 或 600519.SH', 'error'); return; }
    if (scope === 'watchlist' && !state.watchlist.length) { toast('关注列表为空', '请先添加至少一个证券', 'error'); return; }
    if (alertNeedsThreshold(condition) && (!thresholdText || !Number.isFinite(threshold))) { toast('请输入有效阈值', '', 'error'); return; }
    state.alerts.unshift({ id: `alert-${Date.now()}`, scope, symbol: scope === 'symbol' ? symbol : '', condition, threshold: alertNeedsThreshold(condition) ? threshold : null, status: 'armed', createdAt: new Date().toISOString() });
    writeStorage('nexus-alerts', state.alerts);
    $('#alert-form').reset();
    $('#alert-symbol').value = state.symbol || '';
    updateAlertFields();
    renderAlerts();
    toast('预警规则已保存', '触发器未配置时会保持“待调度”状态');
  }

  function handleAlertAction(id, action) {
    if (action === 'delete') state.alerts = state.alerts.filter((item) => item.id !== id);
    if (action === 'toggle') state.alerts = state.alerts.map((item) => item.id === id ? { ...item, status: item.status === 'paused' ? 'armed' : 'paused' } : item);
    writeStorage('nexus-alerts', state.alerts);
    renderAlerts();
  }

  function addJob(title, detail) {
    const id = Date.now();
    state.jobs.unshift({ id, title, detail, status: 'running' });
    renderJobs();
    return id;
  }

  function completeLatestJob() {
    const job = state.jobs.find((item) => item.status === 'running');
    if (job) { job.status = 'complete'; job.completedAt = new Date().toISOString(); }
    renderJobs();
    setTimeout(() => { state.jobs = state.jobs.filter((item) => item.status === 'running'); renderJobs(); }, 5000);
  }

  function renderJobs() {
    const running = state.jobs.filter((job) => job.status === 'running');
    const badge = $('#job-badge');
    badge.textContent = running.length;
    badge.classList.toggle('hidden', !running.length);
    const list = $('#job-list');
    if (!state.jobs.length) { list.innerHTML = '<div class="empty-state small"><strong>当前没有运行中的任务</strong><span>Grok 查询和计划生成会在这里显示进度。</span></div>'; return; }
    list.innerHTML = state.jobs.map((job) => `<div class="job-item"><div class="job-item-head"><div><strong>${escapeHtml(job.title)}</strong><small>${escapeHtml(job.detail)}</small></div><span class="status-chip ${job.status === 'running' ? 'partial' : 'healthy'}">${job.status === 'running' ? '运行中' : '已完成'}</span></div>${job.status === 'running' ? '<div class="job-progress"><span></span></div>' : ''}</div>`).join('');
  }

  function startPlan(symbol = '') {
    showView('plans');
    $('#plan-library').classList.add('hidden');
    $('#plan-wizard').classList.remove('hidden');
    state.wizardStep = 1;
    state.evidenceChecked = false;
    const planSymbol = String(symbol || state.symbol || '').toUpperCase();
    if (planSymbol) $('#plan-symbol').value = planSymbol;
    $('#plan-ack').checked = false;
    $('#wizard-message').textContent = '';
    renderWizardStep();
  }

  function closeWizard() {
    $('#plan-wizard').classList.add('hidden');
    $('#plan-library').classList.remove('hidden');
    renderPlans();
  }

  function renderWizardStep() {
    $$('.wizard-pane').forEach((pane) => pane.classList.toggle('active', Number(pane.dataset.step) === state.wizardStep));
    $$('[data-step-indicator]').forEach((item) => {
      const step = Number(item.dataset.stepIndicator);
      item.classList.toggle('active', step === state.wizardStep);
      item.classList.toggle('complete', step < state.wizardStep);
      const circle = item.querySelector(':scope > span');
      if (circle) circle.innerHTML = step < state.wizardStep ? '<svg><use href="#i-check"/></svg>' : String(step);
    });
    $('#wizard-title').textContent = `第 ${state.wizardStep} 步 · ${WIZARD_TITLES[state.wizardStep - 1]}`;
    $('#wizard-back').disabled = state.wizardStep === 1;
    $('#wizard-next').textContent = NEXT_LABELS[state.wizardStep - 1];
    $('#wizard-message').textContent = '';
    if (state.wizardStep === 2 && !state.evidenceChecked) runPlanEvidence();
    if (state.wizardStep === 5) renderPlanReview();
  }

  function wizardData() {
    return {
      symbol: $('#plan-symbol').value.trim().toUpperCase(),
      horizon: $('#plan-horizon').value,
      target: Number($('#plan-target').value),
      drawdown: Number($('#plan-drawdown').value),
      risk: $('#plan-risk').value,
      capital: Number($('#plan-capital').value),
      thesis: $('#plan-thesis').value.trim(),
      catalyst: $('#plan-catalyst').value.trim(),
      invalidation: $('#plan-invalidation').value.trim(),
      stages: [
        { name: '观察', trigger: $('#stage1-trigger').value.trim(), weight: '0%' },
        { name: '验证', trigger: $('#stage2-trigger').value.trim(), weight: $('#stage2-weight').value.trim() },
        { name: '扩展', trigger: $('#stage3-trigger').value.trim(), weight: $('#stage3-weight').value.trim() },
      ],
      exit: $('#stage-exit').value.trim(),
    };
  }

  function validateWizardStep() {
    const data = wizardData();
    if (state.wizardStep === 1) {
      if (!data.symbol) return '请输入证券代码。';
      if (!(data.target > 0) || !(data.drawdown > 0) || !(data.capital > 0)) return '请填写有效的收益假设、最大回撤和模拟资金。';
    }
    if (state.wizardStep === 3 && (!data.thesis || !data.invalidation)) return '至少填写核心研究假设和逻辑失效条件。';
    if (state.wizardStep === 4 && (!data.stages[1].trigger || !data.exit)) return '请填写验证阶段触发条件和退出规则。';
    return '';
  }

  async function nextWizardStep() {
    const message = validateWizardStep();
    if (message) { $('#wizard-message').textContent = message; return; }
    if (state.wizardStep < 5) { state.wizardStep += 1; renderWizardStep(); return; }
    await generatePlan();
  }

  function previousWizardStep() {
    if (state.wizardStep > 1) { state.wizardStep -= 1; renderWizardStep(); }
  }

  async function runPlanEvidence() {
    const symbol = $('#plan-symbol').value.trim().toUpperCase();
    if (!symbol) return;
    const button = $('#run-plan-evidence');
    button.disabled = true;
    button.innerHTML = '<span class="spinner small"></span>检查中';
    ['market', 'technical', 'news'].forEach((name) => updateEvidenceCheck(name, '检查中', '正在连接数据源', 'partial'));
    const results = await Promise.allSettled([
      api(`/api/v1/stocks/${encodeURIComponent(symbol)}/info`),
      api(`/api/v1/stocks/${encodeURIComponent(symbol)}/technical?period=1y`),
      api('/api/v1/search/global', { method: 'POST', body: JSON.stringify({ query: `${symbol} latest material news market trend`, sources: ['news', 'x'], limit: 10 }) }),
    ]);
    updateEvidenceCheck('market', results[0].status === 'fulfilled' ? '正常' : '不可用', results[0].status === 'fulfilled' ? '证券身份与报价已冻结' : results[0].reason.message, results[0].status === 'fulfilled' ? 'healthy' : 'error');
    updateEvidenceCheck('technical', results[1].status === 'fulfilled' ? '正常' : '不可用', results[1].status === 'fulfilled' ? '技术指标已冻结' : results[1].reason.message, results[1].status === 'fulfilled' ? 'healthy' : 'error');
    const sourceCount = results[2].status === 'fulfilled' ? (results[2].value.results || []).length : 0;
    updateEvidenceCheck('news', sourceCount ? '已查询' : results[2].status === 'fulfilled' ? '来源有限' : '不可用', sourceCount ? `${sourceCount} 条新闻/X 来源已保留` : results[2].status === 'fulfilled' ? '未返回可追溯来源' : results[2].reason.message, sourceCount ? 'healthy' : 'partial');
    state.evidenceChecked = true;
    button.disabled = false;
    button.innerHTML = '<svg><use href="#i-refresh"/></svg>重新运行证据检查';
  }

  function updateEvidenceCheck(name, label, detail, status) {
    const item = $(`[data-check="${name}"]`);
    if (!item) return;
    item.querySelector('small').textContent = detail;
    setChip(item.querySelector('em'), label, status);
    item.querySelector('.check-icon').innerHTML = status === 'healthy' ? '<svg><use href="#i-check"/></svg>' : status === 'error' ? '!' : '<span class="spinner small"></span>';
  }

  function horizonLabel(value) { return { short: '1–4 周', medium: '1–3 个月', long: '3–12 个月' }[value] || value; }
  function riskLabel(value) { return { conservative: '保守', moderate: '稳健', aggressive: '进取' }[value] || value; }

  function renderPlanReview() {
    const data = wizardData();
    $('#plan-review').innerHTML = `<div><span>证券 / 期限</span><strong>${escapeHtml(data.symbol)} · ${escapeHtml(horizonLabel(data.horizon))}</strong></div><div><span>收益假设 / 最大回撤</span><strong>${data.target}% / ${data.drawdown}%</strong></div><div><span>风险 / 模拟资金</span><strong>${escapeHtml(riskLabel(data.risk))} · ¥${formatNumber(data.capital)}</strong></div><div><span>证据状态</span><strong>${state.evidenceChecked ? '已运行检查；异常来源显式保留' : '未运行完整检查 · 部分证据'}</strong></div><div class="wide"><span>核心研究假设</span><strong>${escapeHtml(data.thesis || '未填写')}</strong></div><div class="wide"><span>失效与退出</span><strong>${escapeHtml(data.invalidation || '未填写')} · ${escapeHtml(data.exit || '未填写')}</strong></div>`;
  }

  async function generatePlan() {
    if (!$('#plan-ack').checked) { $('#wizard-message').textContent = '请先确认“仅研究与模拟”的说明。'; return; }
    const data = wizardData();
    const next = $('#wizard-next');
    next.disabled = true;
    next.innerHTML = '<span class="spinner small"></span>生成中';
    addJob(`${data.symbol} · 生成模拟计划`, '阶段、风险门控与版本快照');
    try {
      const result = await api('/api/v1/recommendations/generate-plan', {
        method: 'POST',
        timeout: 90000,
        body: JSON.stringify({
          symbol: data.symbol,
          workspace_id: state.workspaceId,
          evidence_status: state.evidenceChecked ? 'checked' : 'partial',
          plan_context: data,
          user_profile: { target_return: data.target / 100, investment_horizon: data.horizon, risk_tolerance: data.risk, available_capital: data.capital, max_drawdown: data.drawdown / 100 },
        }),
      });
      const plan = result.record;
      if (!plan?.id) throw new Error('服务端未返回已持久化的计划记录');
      state.plans.unshift(plan);
      completeLatestJob();
      closeWizard();
      renderPlans();
      toast('模拟计划已生成', `${data.symbol} · ${plan.version} · 保留证据时间点`);
    } catch (error) {
      completeLatestJob();
      $('#wizard-message').textContent = `生成失败：${error.message}`;
      toast('计划生成失败', error.message, 'error');
    } finally {
      next.disabled = false;
      next.textContent = NEXT_LABELS[4];
    }
  }

  async function loadPlans() {
    // Plans API removed in intelligence-only build
    state.plans = [];
    renderPlans();
  }

  function renderPlans() {
    const count = state.plans.length;
    const frozenCount = state.plans.filter((plan) => plan.status === 'frozen').length;
    const reviewCount = state.plans.filter((plan) => plan.status !== 'frozen').length;
    const pc = $('#plan-count'); if (pc) pc.textContent = count;
    const ppc = $('#portfolio-plan-count'); if (ppc) ppc.textContent = count;
    const ptc = $('#portfolio-trigger-count'); if (ptc) ptc.textContent = reviewCount;
    const pfc = $('#portfolio-frozen-count'); if (pfc) pfc.textContent = frozenCount;
    if (!count) {
      const pl = $('#plan-library'); if (pl) pl.innerHTML = '<div class="empty-state large"><div class="empty-icon"><svg><use href="#i-plan"/></svg></div><strong>还没有模拟计划</strong><span>从证券工作台开始，或直接使用五步向导定义目标、证据和风险边界。</span><button class="button primary" data-action="start-plan">开始五步向导</button></div>';
      const tpl = $('#today-plan-list'); if (tpl) { tpl.className = 'empty-compact'; tpl.innerHTML = '<span>尚无模拟计划</span><small>完成证券研究后，可将证据快照带入五步向导。</small>'; }
      const pl2 = $('#portfolio-ledger'); if (pl2) { pl2.className = 'empty-state large'; pl2.innerHTML = '<div class="empty-icon"><svg><use href="#i-portfolio"/></svg></div><strong>暂无跟踪中的计划</strong><span>生成模拟计划后，阶段、触发条件和证据时间点会出现在这里。</span>'; }
      return;
    }
    const pl3 = $('#plan-library'); if (pl3) pl3.innerHTML = `<div class="plan-card-grid">${state.plans.map(planCardHtml).join('')}</div>`;
    const latest = state.plans[0];
    $('#today-plan-list').className = '';
    $('#today-plan-list').innerHTML = `<button class="signal-row row-button" data-plan-id="${escapeHtml(latest.id)}"><span class="signal-bar ${latest.status === 'frozen' ? 'partial' : 'positive'}"></span><div><strong>${escapeHtml(latest.userPlan.symbol)} · ${latest.status === 'frozen' ? '已冻结' : '观察阶段'}</strong><small>${escapeHtml(latest.version)} · ${escapeHtml(new Date(latest.createdAt).toLocaleString('zh-CN'))}</small></div><span class="status-chip ${latest.status === 'frozen' ? 'neutral' : 'partial'}">${latest.status === 'frozen' ? '待重评' : '待复核'}</span></button>`;
    renderPortfolioLedger();
  }

  function planCardHtml(plan) {
    const frozen = plan.status === 'frozen';
    return `<article class="plan-card ${frozen ? 'frozen' : ''}"><div class="plan-card-head"><span class="status-chip ${frozen ? 'neutral' : 'partial'}">${frozen ? '已冻结' : '模拟草稿'}</span><span class="as-of">${escapeHtml(plan.version)}</span></div><h3>${escapeHtml(plan.userPlan.symbol)}</h3><p>${escapeHtml(plan.userPlan.thesis || '分阶段研究计划')}</p><div class="plan-card-meta"><div><span>期限</span><strong>${escapeHtml(horizonLabel(plan.userPlan.horizon))}</strong></div><div><span>风险风格</span><strong>${escapeHtml(riskLabel(plan.userPlan.risk))}</strong></div><div><span>最大回撤</span><strong>${plan.userPlan.drawdown}%</strong></div><div><span>证据</span><strong>${plan.evidenceStatus === 'checked' ? '已检查' : '部分'}</strong></div></div><button class="button ghost" data-plan-id="${escapeHtml(plan.id)}">查看计划与复核</button></article>`;
  }

  function renderPortfolioLedger() {
    const filtered = state.plans.filter((plan) => state.planFilter === 'all' || (state.planFilter === 'frozen' ? plan.status === 'frozen' : plan.status !== 'frozen'));
    $$('[data-plan-filter]').forEach((button) => button.classList.toggle('active', button.dataset.planFilter === state.planFilter));
    if (!filtered.length) {
      const pl = $('#portfolio-ledger');
      if (pl) { pl.className = 'empty-state large'; pl.innerHTML = `<div class="empty-icon"><svg><use href="#i-portfolio"/></svg></div><strong>当前筛选下没有计划</strong><span>${state.planFilter === 'frozen' ? '冻结计划会保留原证据与版本，等待重新评估。' : '生成模拟计划后会进入人工复核队列。'}</span>`; }
      return;
    }
    const pl = $('#portfolio-ledger');
    if (!pl) return;
    pl.className = 'table-wrap portfolio-table';
    pl.innerHTML = `<table><thead><tr><th>计划</th><th>当前阶段</th><th>风险上限</th><th>证据快照</th><th>状态</th><th></th></tr></thead><tbody>${filtered.map((plan) => {
      const frozen = plan.status === 'frozen';
      return `<tr><td><div class="ticker-cell"><div class="ticker-logo">${escapeHtml(plan.userPlan.symbol.slice(0, 2))}</div><div><strong>${escapeHtml(plan.userPlan.symbol)}</strong><small>${escapeHtml(plan.version)} · ${escapeHtml(horizonLabel(plan.userPlan.horizon))}</small></div></div></td><td><span class="plan-stage">${frozen ? '冻结' : '观察'}</span></td><td>${plan.userPlan.drawdown}% 最大回撤</td><td>${plan.evidenceStatus === 'checked' ? '<span class="status-chip healthy">已检查</span>' : '<span class="status-chip partial">部分</span>'}</td><td><span class="status-chip ${frozen ? 'neutral' : 'partial'}">${frozen ? '待重评' : '待复核'}</span></td><td><button class="text-button" data-plan-id="${escapeHtml(plan.id)}">详情</button></td></tr>`;
    }).join('')}</tbody></table>`;
  }

  function planSummary(plan) {
    const generated = plan.generatedPlan;
    if (typeof generated === 'string') return generated;
    if (!generated || typeof generated !== 'object') return '服务端未返回额外摘要，用户定义的阶段与门控仍已保存。';
    return generated.summary || generated.recommendation || generated.rationale || generated.analysis || '服务端计划对象已保存；当前版本以用户确认的阶段、风险与失效条件为准。';
  }

  function openPlanDetail(id) {
    const plan = state.plans.find((item) => item.id === id);
    if (!plan) return;
    state.selectedPlanId = id;
    const frozen = plan.status === 'frozen';
    $('#plan-drawer-title').textContent = `${plan.userPlan.symbol} · ${plan.version}`;
    $('#plan-drawer-content').innerHTML = `<div class="plan-detail-hero"><div><span class="status-chip ${frozen ? 'neutral' : 'partial'}">${frozen ? '已冻结 · 待重评' : '模拟草稿 · 待复核'}</span><h3>${escapeHtml(plan.userPlan.symbol)}</h3><p>${escapeHtml(plan.userPlan.thesis || '分阶段研究计划')}</p></div><div class="version-stamp"><span>证据版本</span><strong>${escapeHtml(plan.version)}</strong><small>${escapeHtml(new Date(plan.createdAt).toLocaleString('zh-CN'))}</small></div></div>
      <div class="detail-metrics"><div><span>期限</span><strong>${escapeHtml(horizonLabel(plan.userPlan.horizon))}</strong></div><div><span>收益假设</span><strong>${formatNumber(plan.userPlan.target)}%</strong></div><div><span>最大回撤</span><strong>${formatNumber(plan.userPlan.drawdown)}%</strong></div><div><span>证据状态</span><strong>${plan.evidenceStatus === 'checked' ? '已检查' : '部分'}</strong></div></div>
      <section class="detail-section"><p class="section-kicker">STAGED PLAN</p><h4>阶段与触发条件</h4><ol class="plan-timeline">${(plan.userPlan.stages || []).map((stage, index) => `<li><span>${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHtml(stage.name)} · 上限 ${escapeHtml(stage.weight)}</strong><small>${escapeHtml(stage.trigger || (index === 0 ? '仅观察，不建立模拟仓位' : '触发条件未填写'))}</small></div></li>`).join('')}<li class="danger"><span>×</span><div><strong>冻结与退出</strong><small>${escapeHtml(plan.userPlan.exit || plan.userPlan.invalidation || '失效条件待补充')}</small></div></li></ol></section>
      <section class="detail-section"><p class="section-kicker">MODEL OUTPUT</p><h4>服务端计划摘要</h4><p class="detail-copy">${escapeHtml(planSummary(plan))}</p></section>
      <div class="drawer-callout"><svg><use href="#i-shield"/></svg><span>查看或冻结不会提交订单。新证据需要创建新版本，原版本保持不变。</span></div>
      <div class="drawer-actions"><button class="button ghost" data-plan-research="${escapeHtml(plan.userPlan.symbol)}">重新研究</button><button class="button secondary" data-plan-freeze="${escapeHtml(plan.id)}">${frozen ? '恢复复核' : '冻结计划'}</button><button class="button primary" data-plan-version="${escapeHtml(plan.id)}">基于此计划建新版本</button></div>`;
    openDrawer('plan-drawer');
  }

  async function togglePlanFrozen(id) {
    const current = state.plans.find((plan) => plan.id === id);
    if (!current) return;
    const status = current.status === 'frozen' ? 'draft' : 'frozen';
    try {
      const result = await api(`/api/v1/recommendations/plans/${encodeURIComponent(id)}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status, workspace_id: state.workspaceId }),
      });
      state.plans = state.plans.map((plan) => plan.id === id ? result.plan : plan);
      renderPlans();
      openPlanDetail(id);
    } catch (error) {
      toast('计划状态更新失败', error.message, 'error');
    }
  }

  function startPlanVersion(id) {
    const plan = state.plans.find((item) => item.id === id);
    if (!plan) return;
    closeDrawers();
    startPlan(plan.userPlan.symbol);
    $('#plan-horizon').value = plan.userPlan.horizon;
    $('#plan-target').value = plan.userPlan.target;
    $('#plan-drawdown').value = plan.userPlan.drawdown;
    $('#plan-risk').value = plan.userPlan.risk;
    $('#plan-capital').value = plan.userPlan.capital;
    $('#plan-thesis').value = plan.userPlan.thesis;
    $('#plan-catalyst').value = plan.userPlan.catalyst;
    $('#plan-invalidation').value = plan.userPlan.invalidation;
    (plan.userPlan.stages || []).forEach((stage, index) => {
      const trigger = $(`#stage${index + 1}-trigger`);
      const weight = $(`#stage${index + 1}-weight`);
      if (trigger) trigger.value = stage.trigger || '';
      if (weight) weight.value = stage.weight || '';
    });
    $('#stage-exit').value = plan.userPlan.exit || '';
    toast('已复制为新版本草稿', '重新运行证据检查后再生成，原版本不会被覆盖');
  }

  async function loadModels() {
    const list = $('#lab-model-list');
    if (!list) return;
    list.innerHTML = '<div class="loading-state"><span class="spinner"></span>加载实验</div>';
    try {
      const models = await api('/api/v1/models/');
      state.models = Array.isArray(models) ? models : [];
      if (!state.models.length) {
        state.selectedModelId = '';
        list.innerHTML = '<div class="empty-state small"><strong>还没有模型实验</strong><span>新建实验后先进入研究阶段，不会直接部署。</span></div>';
        renderModelDetail();
        return;
      }
      if (!state.models.some((model) => model.id === state.selectedModelId)) state.selectedModelId = state.models[0].id;
      list.innerHTML = state.models.map((model) => `<button class="model-item ${model.id === state.selectedModelId ? 'active' : ''}" data-model-id="${escapeHtml(model.id)}"><span class="model-icon">${escapeHtml(String(model.model_type || 'M').slice(0, 2).toUpperCase())}</span><span><strong>${escapeHtml(model.name)}</strong><small>${escapeHtml(model.model_type)} · ${escapeHtml(model.version || 'v1')}</small></span><em class="status-chip ${modelStatusClass(model.status)}">${escapeHtml(modelStatusLabel(model.status))}</em></button>`).join('');
      renderModelDetail();
    } catch (error) {
      state.models = [];
      list.innerHTML = `<div class="empty-state small"><strong>模型列表暂不可用</strong><span>${escapeHtml(error.message)}</span></div>`;
    }
  }

  function modelStatusClass(status) {
    if (['approved', 'deployed'].includes(status)) return 'healthy';
    if (status === 'rejected') return 'error';
    if (['training', 'evaluating', 'pending_review'].includes(status)) return 'partial';
    return 'neutral';
  }

  function modelStatusLabel(status) {
    return { draft: '研究草稿', training: '训练中', trained: '待评估', evaluating: '评估中', pending_review: '待治理审阅', approved: '已批准', deployed: '影子/部署', rejected: '已拒绝', archived: '已归档' }[status] || status || '研究草稿';
  }

  function metricCard(label, value) {
    const number = asNumber(value);
    return `<div><span>${escapeHtml(label)}</span><strong>${number === null ? '—' : `${(number * 100).toFixed(1)}%`}</strong><small>${number === null ? '尚无正式评估结果' : '来自当前模型版本'}</small></div>`;
  }

  function renderModelDetail() {
    const model = state.models.find((item) => item.id === state.selectedModelId);
    const content = $('#model-result-content');
    $$('[data-model-id]').forEach((button) => button.classList.toggle('active', button.dataset.modelId === state.selectedModelId));
    $$('[data-model-tab]').forEach((button) => button.classList.toggle('active', button.dataset.modelTab === state.modelTab));
    if (!model) {
      $('#model-detail-title').textContent = '结果工作区';
      setChip($('#model-detail-status'), '选择实验', 'neutral');
      content.className = 'empty-state';
      content.innerHTML = '<strong>选择一个实验查看结果</strong><span>结果区只展示真实返回的评估指标；缺失数据不会被示例曲线替代。</span>';
      return;
    }
    $('#model-detail-title').textContent = model.name;
    setChip($('#model-detail-status'), modelStatusLabel(model.status), modelStatusClass(model.status));
    content.className = 'model-result-content';
    const hasMetrics = [model.accuracy, model.precision, model.recall, model.f1_score].some((value) => asNumber(value) !== null);
    if (state.modelTab === 'overview') {
      content.innerHTML = `<div class="model-summary"><div><span class="model-icon large">${escapeHtml(String(model.model_type || 'M').slice(0, 2).toUpperCase())}</span><div><strong>${escapeHtml(model.model_type)}</strong><small>${escapeHtml(model.version || 'v1')} · 更新于 ${escapeHtml(new Date(model.updated_at).toLocaleString('zh-CN'))}</small></div></div><p>${escapeHtml(model.description || '尚未填写研究假设与数据范围。')}</p></div><div class="model-metrics">${metricCard('Accuracy', model.accuracy)}${metricCard('Precision', model.precision)}${metricCard('Recall', model.recall)}${metricCard('F1 Score', model.f1_score)}</div><div class="model-gate"><div><p class="section-kicker">NEXT GATE</p><h3>${hasMetrics ? '评估结果已返回，仍需检查回测与风险证据。' : '先训练并评估，再进入正式回测。'}</h3><p>当前接口没有收益曲线、回撤、订单和日志数据时，相应页签保持空状态，不推导虚假指标。</p></div><div><button class="button secondary" data-model-action="train" data-model-id="${escapeHtml(model.id)}">准备训练</button><button class="button primary" data-model-action="evaluate" data-model-id="${escapeHtml(model.id)}">运行评估</button></div></div>`;
      return;
    }
    const emptyByTab = {
      returns: ['尚无收益与基准曲线', '完成带成本、滑点和样本外区间的正式回测后再展示 CAGR、Sharpe、Alpha 与基准对比。'],
      risk: ['尚无风险证据', '需要最大回撤、波动、压力情景和容量结果；分类准确率不能替代策略风险。'],
      orders: ['尚无模拟订单账本', '进入影子跟踪后记录每次信号、订单、成交、费用与滑点。'],
      logs: ['尚无运行日志', '训练、回测和评估任务开始后，在这里保留参数、数据版本与错误记录。'],
    };
    const [title, detail] = emptyByTab[state.modelTab] || emptyByTab.returns;
    content.innerHTML = `<div class="honest-empty"><span class="empty-icon"><svg><use href="#i-shield"/></svg></span><strong>${title}</strong><p>${detail}</p><small>数据状态：NOT_RUN / NOT_AVAILABLE</small></div>`;
  }

  async function evaluateModel(id) {
    const model = state.models.find((item) => item.id === id);
    if (!model) return;
    addJob(`${model.name} · 模型评估`, '提交评估任务并等待正式结果');
    try {
      const result = await api(`/api/v1/models/${encodeURIComponent(id)}/evaluate`, { method: 'POST', timeout: 60000 });
      completeLatestJob();
      toast('评估任务已提交', result.message || '结果返回前不会展示推测指标');
      loadModels();
    } catch (error) {
      completeLatestJob();
      toast('评估任务提交失败', error.message, 'error');
    }
  }

  function openTrainModelDialog(id) {
    const model = state.models.find((item) => item.id === id);
    if (!model) return;
    const overlay = document.createElement('div');
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<form class="manager-modal compact-modal" id="train-model-form"><div class="modal-head"><div><p class="section-kicker">TRAINING JOB</p><h2>准备训练 · ${escapeHtml(model.name)}</h2></div><button type="button" class="icon-button" data-close-train aria-label="关闭训练任务"><svg><use href="#i-close"/></svg></button></div><div class="form-stack compact"><label class="field-label">训练标的<input id="train-symbol" required value="${escapeHtml(state.symbol || 'AAPL')}" placeholder="例如 AAPL"></label><div class="form-grid compact"><label class="field-label">开始日期（可选）<input id="train-start" type="date"></label><label class="field-label">结束日期（可选）<input id="train-end" type="date"></label></div><label class="field-label">预测周期（交易日）<input id="train-horizon" type="number" min="1" max="60" value="5"></label><div class="screening-note"><svg><use href="#i-shield"/></svg><span>训练完成仍不等于策略可用；必须继续检查正式回测、风险、样本外表现和影子跟踪。</span></div><button class="button primary" type="submit">提交训练任务</button></div></form>`;
    document.body.appendChild(overlay);
    $('[data-close-train]', overlay).addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', (event) => { if (event.target === overlay) overlay.remove(); });
    $('#train-model-form', overlay).addEventListener('submit', async (event) => {
      event.preventDefault();
      const symbol = normalizeSymbol($('#train-symbol', overlay).value);
      if (!validSymbol(symbol)) { toast('训练标的格式不正确', '', 'error'); return; }
      const submit = event.submitter;
      submit.disabled = true;
      addJob(`${model.name} · 训练`, `${symbol} · 数据准备与验证`);
      try {
        const payload = { symbol, prediction_horizon: Number($('#train-horizon', overlay).value), target_column: 'close' };
        if ($('#train-start', overlay).value) payload.start_date = $('#train-start', overlay).value;
        if ($('#train-end', overlay).value) payload.end_date = $('#train-end', overlay).value;
        await api(`/api/v1/models/${encodeURIComponent(id)}/train`, { method: 'POST', timeout: 90000, body: JSON.stringify(payload) });
        overlay.remove();
        completeLatestJob();
        toast('训练任务已完成', '请运行评估，并继续正式回测与风险检查');
        loadModels();
      } catch (error) {
        completeLatestJob();
        submit.disabled = false;
        toast('训练失败', error.message, 'error');
      }
    });
  }

  function openNewModelDialog() {
    const overlay = document.createElement('div');
    overlay.className = 'modal-backdrop';
    overlay.innerHTML = `<form class="command-palette" id="model-form"><div class="command-input"><strong>新建研究实验</strong><button type="button" class="icon-button" data-close-model aria-label="关闭新建实验"><svg><use href="#i-close"/></svg></button></div><div style="padding:20px;display:grid;gap:16px"><label class="field-label">实验名称<input id="new-model-name" required placeholder="例如：质量因子候选模型"></label><label class="field-label">模型类型<select id="new-model-type"><option value="random_forest">Random Forest</option><option value="xgboost">XGBoost</option><option value="linear_regression">Linear Regression</option></select></label><label class="field-label">研究说明<textarea id="new-model-description" rows="3" placeholder="记录研究假设、数据范围和验证目标"></textarea></label><div class="screening-note"><svg><use href="#i-shield"/></svg><span>新模型从 Draft 开始，需经过训练、回测、影子跟踪与治理审阅。</span></div><button class="button primary" type="submit">创建 Draft 实验</button></div></form>`;
    document.body.appendChild(overlay);
    $('[data-close-model]', overlay).addEventListener('click', () => overlay.remove());
    overlay.addEventListener('click', (event) => { if (event.target === overlay) overlay.remove(); });
    $('#model-form', overlay).addEventListener('submit', async (event) => {
      event.preventDefault();
      const submit = event.submitter;
      submit.disabled = true;
      try {
        await api('/api/v1/models/', { method: 'POST', body: JSON.stringify({ name: $('#new-model-name', overlay).value.trim(), model_type: $('#new-model-type', overlay).value, description: $('#new-model-description', overlay).value.trim() || undefined }) });
        overlay.remove();
        toast('Draft 实验已创建', '下一步：准备训练数据与正式回测');
        loadModels();
      } catch (error) {
        toast('创建实验失败', error.message, 'error');
        submit.disabled = false;
      }
    });
    $('#new-model-name', overlay).focus();
  }

  async function loadProfile() {
    try {
      const profile = await api('/api/v1/user/profile');
      if (profile && profile.status !== 'not_configured') {
        if (profile.target_return != null) $('#setting-return').value = profile.target_return;
        if (profile.investment_horizon) $('#setting-horizon').value = profile.investment_horizon;
        if (profile.risk_tolerance) $('#setting-risk').value = profile.risk_tolerance;
        if (profile.available_capital != null) $('#setting-capital').value = profile.available_capital;
        if (profile.max_position_size != null) $('#setting-position').value = profile.max_position_size;
        if (profile.max_loss_per_trade != null) $('#setting-loss').value = profile.max_loss_per_trade;
        setChip($('#profile-status'), '已载入', 'healthy');
      } else setChip($('#profile-status'), '使用默认值', 'neutral');
    } catch (error) {
      setChip($('#profile-status'), '载入失败', 'error');
    }
  }

  async function saveSettings() {
    const button = $('#save-settings');
    button.disabled = true;
    $('#settings-message').textContent = '';
    try {
      await api('/api/v1/user/goals', { method: 'PUT', body: JSON.stringify({ target_return: Number($('#setting-return').value), investment_horizon: $('#setting-horizon').value, risk_tolerance: $('#setting-risk').value, available_capital: Number($('#setting-capital').value), max_position_size: Number($('#setting-position').value), max_loss_per_trade: Number($('#setting-loss').value), preferred_sectors: [], excluded_sectors: [] }) });
      setChip($('#profile-status'), '已保存', 'healthy');
      $('#settings-message').textContent = `已保存 · ${timestamp()}`;
      toast('研究偏好已保存', '新计划会默认使用这些边界');
    } catch (error) {
      setChip($('#profile-status'), '保存失败', 'error');
      $('#settings-message').textContent = error.message;
      toast('保存失败', error.message, 'error');
    } finally { button.disabled = false; }
  }

  async function loadGovernance() {
    try {
      const data = await api('/api/v1/governance/stats');
      const values = [data.pending ?? data.pending_count ?? 0, data.approved ?? data.approved_count ?? 0, data.rejected ?? data.rejected_count ?? 0, data.total ?? data.total_models ?? '—'];
      $$('#governance-stats strong').forEach((element, index) => { element.textContent = values[index]; });
    } catch (_) { $$('#governance-stats strong').forEach((element) => { element.textContent = '—'; }); }
  }

  async function checkBroker() {
    const summary = $('#broker-summary');
    summary.textContent = '正在检查服务状态';
    try {
      const data = await api('/api/v1/broker/brokers');
      const brokers = data.brokers || [];
      const active = brokers.filter((broker) => broker.status === 'active').length;
      summary.textContent = data.order_mutations_enabled
        ? `${brokers.length} 个适配器 · ${active} 个已连接；服务端已启用实盘变更`
        : `${brokers.length} 个适配器 · ${active} 个已连接；服务端强制 ${data.execution_mode || 'simulation_only'}，下单与撤单被拒绝`;
    } catch (error) { summary.textContent = `检查失败：${error.message}`; }
  }

  function getWorkspaces() {
    return state.platformManifest?.workspaces?.length ? state.platformManifest.workspaces : FALLBACK_WORKSPACES;
  }

  function currentWorkspace() {
    return getWorkspaces().find((workspace) => workspace.id === state.workspaceId) || getWorkspaces()[0];
  }

  function workspaceTypeLabel(type) {
    return { personal: '个人空间', institution: '机构空间', custom: '客户化空间' }[type] || type;
  }

  function workspaceRoleLabel(role) {
    return { owner: '所有者', researcher: '量化研究员', admin: '平台管理员' }[role] || role;
  }

  function workspaceMark(workspace) {
    if (workspace.id === 'personal') return 'MY';
    if (workspace.id === 'institution') return 'IR';
    return String(state.brand.mark || 'GD').slice(0, 3).toUpperCase();
  }

  function applyBrandConfig(candidate = state.brand) {
    if (candidate?.name === 'Nexus Quant' && candidate?.mark === 'NQ') candidate = DEFAULT_BRAND;
    const theme = THEME_PALETTES[candidate?.theme] ? candidate.theme : DEFAULT_BRAND.theme;
    const brand = {
      name: String(candidate?.name || DEFAULT_BRAND.name).trim().slice(0, 30),
      subtitle: String(candidate?.subtitle || DEFAULT_BRAND.subtitle).trim().slice(0, 32),
      mark: String(candidate?.mark || DEFAULT_BRAND.mark).trim().slice(0, 3).toUpperCase(),
      theme,
    };
    state.brand = brand;
    const palette = THEME_PALETTES[theme];
    const root = document.documentElement;
    root.style.setProperty('--green', palette.green);
    root.style.setProperty('--green-deep', palette.deep);
    root.style.setProperty('--green-pale', palette.pale);
    root.style.setProperty('--lime', palette.lime);
    $('#brand-name').textContent = brand.name || DEFAULT_BRAND.name;
    $('#brand-subtitle').textContent = brand.subtitle.toUpperCase();
    $('#brand-preview-name').textContent = brand.name;
    $('#brand-preview-subtitle').textContent = brand.subtitle.toUpperCase();
    $('#brand-preview-mark').textContent = brand.mark;
    $('#platform-brand-name').value = brand.name;
    $('#platform-brand-subtitle').value = brand.subtitle;
    $('#platform-brand-mark').value = brand.mark;
    $('#platform-brand-theme').value = brand.theme;
    document.title = `${$(`#view-${state.view}`)?.dataset.title || '今日'} · ${brand.name}`;
  }

  function renderWorkspaceContext() {
    const workspace = currentWorkspace();
    const type = workspaceTypeLabel(workspace.type);
    const role = workspaceRoleLabel(workspace.role);
    const mark = workspaceMark(workspace);
    document.body.dataset.workspaceType = workspace.type;
    $('#sidebar-workspace-mark').textContent = mark;
    $('#top-workspace-mark').textContent = mark;
    $('#sidebar-workspace-name').textContent = workspace.name;
    $('#top-workspace-name').textContent = workspace.name;
    $('#sidebar-workspace-meta').textContent = `${workspace.short_name || type} · ${role}`;
    $('#top-workspace-type').textContent = workspaceTypeLabel(workspace.type);
    const pw = $('#platform-current-workspace');
    if (pw) pw.textContent = workspace.name;
    const pr = $('#platform-current-role');
    if (pr) pr.textContent = `${type} · ${role}`;
    $$('[data-workspace-select]').forEach((button) => {
      const active = button.dataset.workspaceSelect === workspace.id;
      button.classList.toggle('active', active);
      const status = button.querySelector('em');
      if (status) status.textContent = active ? (workspace.provisioning === 'local_active' ? '当前空间' : '正在预览') : '切换预览';
    });
    renderWorkspaceDetail(workspace);
    renderWorkspaceOptions();
  }

  function renderWorkspaceDetail(workspace = currentWorkspace()) {
    const container = $('#workspace-detail');
    if (!container) return;
    const memberSlots = (workspace.member_slots || []).map((slot, index) => `<div><span>${String(index + 1).padStart(2, '0')}</span><strong>${escapeHtml(slot)}</strong><small>${workspace.provisioning === 'local_active' ? '当前成员' : '角色席位'}</small></div>`).join('');
    const readiness = workspace.provisioning === 'local_active' ? '本地已激活' : '模板预览';
    container.innerHTML = `<div class="workspace-summary-card"><header><span class="workspace-avatar">${escapeHtml(workspaceMark(workspace))}</span><div><h3>${escapeHtml(workspace.name)}</h3><small>${escapeHtml(workspaceTypeLabel(workspace.type))} · ${escapeHtml(readiness)}</small></div></header><p>${escapeHtml(workspace.description)}</p><div class="workspace-facts"><div><span>默认角色</span><strong>${escapeHtml(workspaceRoleLabel(workspace.role))}</strong></div><div><span>策略包</span><strong>${escapeHtml(workspace.policy_pack || '默认策略')}</strong></div><div><span>资源归属</span><strong>${workspace.type === 'personal' ? '个人所有' : '工作区所有'}</strong></div><div><span>服务端隔离</span><strong>${workspace.provisioning === 'local_active' ? '单实例边界' : '待生产实现'}</strong></div></div></div><div class="member-slot-card"><strong>成员与职责模板</strong><div class="member-slot-list">${memberSlots || '<div><span>01</span><strong>尚未配置</strong><small>身份目录待接入</small></div>'}</div></div>`;
  }

  function renderWorkspaceOptions() {
    const container = $('#workspace-option-list');
    if (!container) return;
    const selected = currentWorkspace();
    container.innerHTML = getWorkspaces().map((workspace) => `<button class="workspace-option ${workspace.id === selected.id ? 'active' : ''}" data-workspace-select="${escapeHtml(workspace.id)}"><span>${escapeHtml(workspaceMark(workspace))}</span><span><strong>${escapeHtml(workspace.name)}</strong><small>${escapeHtml(workspace.description)}</small></span><em>${workspace.id === selected.id ? '当前' : workspace.provisioning === 'local_active' ? '可用' : '模板预览'}</em></button>`).join('');
  }

  function renderRoleMatrix() {
    const container = $('#role-matrix');
    if (!container) return;
    const roles = state.platformManifest?.roles || [];
    if (!roles.length) {
      container.innerHTML = '<div class="empty-state small"><strong>角色清单待载入</strong><span>平台清单连接后显示后端 RBAC 权限。</span></div>';
      return;
    }
    const permissionLabels = {
      view_stock: '查看证券', search_stock: '搜索证券', view_recommendation: '查看计划', generate_recommendation: '生成计划', manage_recommendation: '管理计划', view_model: '查看模型', train_model: '训练模型', approve_model: '批准模型', deploy_model: '部署模型', view_portfolio: '查看组合', manage_portfolio: '管理组合', view_users: '查看成员', manage_users: '管理成员', view_audit: '查看审计', manage_system: '管理平台',
    };
    container.innerHTML = roles.map((role) => {
      const visible = role.permissions.slice(0, 5);
      const tags = visible.map((permission) => `<span>${escapeHtml(permissionLabels[permission] || permission)}</span>`).join('');
      const extra = role.permissions.length > visible.length ? `<span>+${role.permissions.length - visible.length}</span>` : '';
      return `<div class="role-card"><header><strong>${escapeHtml(role.name)}</strong><span class="status-chip neutral">${escapeHtml(role.id)}</span></header><p>${role.id === 'admin' ? '治理、成员和平台配置的最高权限模板。' : '权限按工作区分配，并在资源操作前校验。'}</p><div class="permission-tags">${tags}${extra}</div></div>`;
    }).join('');
  }

  function connectorStatus(status) {
    if (status === 'available' || status === 'configured' || status === 'operational') return ['可用', 'healthy'];
    if (status === 'simulation_only') return ['仅模拟', 'partial'];
    if (status === 'needs_configuration' || status === 'configuration_required') return ['待配置', 'partial'];
    if (status === 'local_only') return ['仅本地', 'partial'];
    if (status === 'blocked') return ['已阻断', 'error'];
    if (status === 'unavailable') return ['不可用', 'error'];
    return ['规划中', 'neutral'];
  }

  function renderPlatformCatalog() {
    const connectorContainer = $('#connector-catalog');
    const extensionContainer = $('#extension-grid');
    const connectors = state.platformManifest?.connectors || [];
    const extensions = state.platformManifest?.extension_points || [];
    if (connectorContainer) connectorContainer.innerHTML = connectors.length ? connectors.map((connector) => {
      const [label, status] = connectorStatus(connector.status);
      return `<div class="connector-card"><header><strong>${escapeHtml(connector.name)}</strong><span class="status-chip ${status}">${escapeHtml(label)}</span></header><p>${escapeHtml(connector.contract)}</p><small>${escapeHtml(connector.category)} · ${escapeHtml(connector.scope)}</small></div>`;
    }).join('') : '<div class="empty-state small"><strong>扩展清单待载入</strong><span>连接平台 API 后显示数据、模型和事件适配器。</span></div>';
    if (extensionContainer) extensionContainer.innerHTML = extensions.map((extension, index) => `<div class="extension-card"><span>${String(index + 1).padStart(2, '0')}</span><div><strong>${escapeHtml(extension.name)}</strong><p>${escapeHtml(extension.artifact)}</p><small>${escapeHtml(extension.interface)}</small></div></div>`).join('');
  }

  async function loadPlatformManifest(force = false) {
    if (state.platformManifest && !force) {
      renderWorkspaceContext();
      renderRoleMatrix();
      renderPlatformCatalog();
      return state.platformManifest;
    }
    try {
      state.platformManifest = await api('/api/v1/platform/manifest', { timeout: 10000 });
    } catch (_) {
      state.platformManifest = { workspaces: FALLBACK_WORKSPACES, roles: [], connectors: [], extension_points: [] };
    }
    if (!getWorkspaces().some((workspace) => workspace.id === state.workspaceId)) state.workspaceId = 'personal';
    renderWorkspaceContext();
    renderRoleMatrix();
    renderPlatformCatalog();
    return state.platformManifest;
  }

  function selectWorkspace(id) {
    const workspace = getWorkspaces().find((item) => item.id === id);
    if (!workspace) return;
    state.workspaceId = workspace.id;
    writeStorage('nexus-workspace', workspace.id);
    Object.keys(state.intelligenceHistory).forEach((workflow) => {
      state.intelligenceHistory[workflow] = [];
      state.activeIntelligenceHistory[workflow] = '';
    });
    state.realtimeResearch = null;
    state.projectRisk = null;
    state.geopoliticalImpact = null;
    renderWorkspaceContext();
    loadPlans();
    if (state.view === 'realtime-research') {
      renderRealtimeResearchResult({ status: 'idle', workflow: 'realtime-research', analysis: {} });
      loadIntelligenceMonitors('realtime_research');
      loadIntelligenceHistory('realtime-research');
    }
    if (state.view === 'project-risk') {
      renderProjectRiskResult({ status: 'idle', workflow: 'project-risk', analysis: {} });
      loadIntelligenceMonitors('project_risk');
      loadIntelligenceHistory('project-risk');
    }
    if (state.view === 'geopolitics') {
      renderGeopoliticalResult({ status: 'idle', workflow: 'geopolitical-impact', analysis: {} });
      loadIntelligenceHistory('geopolitical-impact');
    }
    closeWorkspaceModal();
    toast(workspace.provisioning === 'local_active' ? '已切换工作区' : '已进入模板预览', `${workspace.name} · ${workspace.policy_pack}`);
  }

  function openWorkspaceModal() {
    renderWorkspaceOptions();
    $('#workspace-modal').classList.remove('hidden');
  }

  function closeWorkspaceModal() { $('#workspace-modal').classList.add('hidden'); }

  function saveBrandConfig() {
    const brand = {
      name: $('#platform-brand-name').value.trim() || DEFAULT_BRAND.name,
      subtitle: $('#platform-brand-subtitle').value.trim() || DEFAULT_BRAND.subtitle,
      mark: $('#platform-brand-mark').value.trim() || DEFAULT_BRAND.mark,
      theme: $('#platform-brand-theme').value,
    };
    applyBrandConfig(brand);
    writeStorage('nexus-brand', state.brand);
    renderWorkspaceContext();
    toast('品牌配置已应用', `${state.brand.name} · ${state.brand.theme}`);
  }

  function resetBrandConfig() {
    applyBrandConfig(DEFAULT_BRAND);
    writeStorage('nexus-brand', state.brand);
    renderWorkspaceContext();
    toast('已恢复默认品牌', '实时决策情报分析 · 研究绿');
  }

  function switchSettingsSection(section) {
    state.settingsSection = section;
    $$('[data-settings-section]').forEach((item) => item.classList.toggle('active', item.dataset.settingsSection === section));
    $$('.settings-section').forEach((item) => item.classList.toggle('active', item.id === `settings-${section}`));
    const button = $('#save-settings');
    button.textContent = section === 'profile' ? '保存研究偏好' : section === 'brand' ? '保存品牌配置' : '保存配置草案';
    if (section === 'connectors') { checkHealth(); checkBroker(); loadOverseasProviderStatus(); }
    if (section === 'governance') loadGovernance();
    if (section === 'workspace') loadPlatformManifest();
  }

  function saveCurrentSettings() {
    if (state.settingsSection === 'profile') return saveSettings();
    if (state.settingsSection === 'brand') return saveBrandConfig();
    writeStorage('nexus-platform-draft', { workspace_id: state.workspaceId, section: state.settingsSection, saved_at: new Date().toISOString() });
    toast('配置草案已保存', '生产环境启用前仍需管理员审批和服务端持久化');
  }

  function openCommand() {
    $('#command-modal').classList.remove('hidden');
    $('#command-search').value = '';
    renderCommandResults('');
    setTimeout(() => $('#command-search').focus(), 0);
  }

  function closeCommand() { $('#command-modal').classList.add('hidden'); }

  function renderCommandResults(query) {
    const raw = query.trim();
    const q = raw.toUpperCase();
    const result = $('#command-results');
    if (q) {
      const pages = [
        { view: 'realtime-research', label: '实时信息检索', detail: '分开获取 X 原文与公共开放信息', keywords: '实时 信息 X 原文 公共 网页 新闻 搜索 GROK WEB SEARCH X SEARCH' },
        { view: 'project-risk', label: '项目风险情报', detail: '国家/地区、项目和金融产品的实时风险监测', keywords: '项目 风险 国家/地区 舆情 政治 社会 债务 环境 声誉 GROK PROJECT RISK' },
        { view: 'geopolitics', label: '地缘融资推演', detail: '地缘政治对管道、联合融资和借贷意愿的影响', keywords: '地缘 政策 区域 融资 联合融资 一带一路 中美 GEO FINANCING GROK' },
        { view: 'discover', label: '发现与候选池', detail: '筛选、保存候选并进入研究', keywords: '发现 筛选 候选 DISCOVER' },
        { view: 'plans', label: '模拟计划', detail: '创建或复核分阶段计划', keywords: '计划 模拟 PLAN' },
        { view: 'portfolio', label: '模拟组合', detail: '查看触发、冻结与版本状态', keywords: '组合 跟踪 复核 PORTFOLIO' },
        { view: 'lab', label: '策略实验室', detail: '研究、训练、评估与治理', keywords: '模型 回测 策略 实验 LAB' },
        { view: 'settings', label: '平台管理', detail: '工作区、品牌、连接器、权限与治理', keywords: '平台 工作区 机构 客户化 设置 数据 GROK OCI PLATFORM TENANT' },
      ].filter((page) => page.keywords.toUpperCase().includes(q));
      const plans = state.plans.filter((plan) => `${plan.userPlan.symbol} ${plan.userPlan.thesis}`.toUpperCase().includes(q)).slice(0, 3);
      const symbolResult = validSymbol(q) ? `<button data-command-symbol="${escapeHtml(q)}"><svg><use href="#i-search"/></svg><span><strong>研究 ${escapeHtml(q)}</strong><small>打开证券工作台并加载实时证据</small></span><kbd>↵</kbd></button>` : '';
      const pageResults = pages.map((page) => `<button data-command-view="${page.view}"><svg><use href="#i-arrow"/></svg><span><strong>${page.label}</strong><small>${page.detail}</small></span></button>`).join('');
      const planResults = plans.map((plan) => `<button data-command-plan="${escapeHtml(plan.id)}"><svg><use href="#i-plan"/></svg><span><strong>${escapeHtml(plan.userPlan.symbol)} · ${escapeHtml(plan.version)}</strong><small>${escapeHtml(plan.userPlan.thesis || '模拟计划')}</small></span></button>`).join('');
      result.innerHTML = `<p>搜索结果</p>${symbolResult}${pageResults}${planResults || (!symbolResult && !pageResults ? '<div class="command-empty">没有匹配页面或计划；股票代码请包含正确市场后缀。</div>' : '')}`;
      return;
    }
    result.innerHTML = '<p>快速前往</p><button data-command-view="realtime-research"><svg><use href="#i-search"/></svg><span><strong>实时信息检索</strong><small>X 原文、公共网页、趋势与来源账本</small></span><kbd>↵</kbd></button><button data-command-view="project-risk"><svg><use href="#i-radar"/></svg><span><strong>项目风险情报</strong><small>国家/地区、项目与金融产品实时监测</small></span></button><button data-command-view="geopolitics"><svg><use href="#i-globe"/></svg><span><strong>地缘融资推演</strong><small>复杂政策与区域竞争情景分析</small></span></button><button data-command-view="research"><svg><use href="#i-search"/></svg><span><strong>证券研究</strong><small>输入代码打开完整工作台</small></span></button><button data-command-view="settings"><svg><use href="#i-settings"/></svg><span><strong>平台管理</strong><small>工作区、客户化、连接器与权限</small></span></button>';
  }

  function bindEvents() {
    document.addEventListener('click', (event) => {
      const viewButton = event.target.closest('[data-view], [data-view-target]');
      if (viewButton) showView(viewButton.dataset.view || viewButton.dataset.viewTarget);
      const researchButton = event.target.closest('[data-research-query]');
      if (researchButton) openResearch(researchButton.dataset.researchQuery || researchButton.textContent.trim());
      const tabButton = event.target.closest('[data-research-tab], [data-research-tab-target]');
      if (tabButton) selectResearchTab(tabButton.dataset.researchTab || tabButton.dataset.researchTabTarget);
      const action = event.target.closest('[data-action]')?.dataset.action;
      if (action === 'open-research') showView('research');
      if (action === 'start-plan') startPlan();
      if (action === 'start-plan-current') startPlan(state.symbol);
      const workspaceButton = event.target.closest('[data-workspace-select]');
      if (workspaceButton) selectWorkspace(workspaceButton.dataset.workspaceSelect);
      if (event.target.closest('#run-screener')) runScreener();
      const candidateButton = event.target.closest('[data-candidate-action]');
      if (candidateButton) toggleCandidate(candidateButton.dataset.candidateSymbol, candidateButton.dataset.candidateAction);
      const alertButton = event.target.closest('[data-alert-action]');
      if (alertButton) handleAlertAction(alertButton.dataset.alertId, alertButton.dataset.alertAction);
      const monitorAction = event.target.closest('[data-intelligence-monitor-action]');
      if (monitorAction) handleIntelligenceMonitor(monitorAction.dataset.monitorId, monitorAction.dataset.intelligenceMonitorAction);
      const historyAction = event.target.closest('[data-history-action]');
      if (historyAction?.dataset.historyAction === 'open') openIntelligenceHistory(historyAction.dataset.historyId, historyAction.dataset.historyWorkflow);
      if (historyAction?.dataset.historyAction === 'export') downloadIntelligenceHistoryPdf(historyAction.dataset.historyId, historyAction.dataset.historyWorkflow, historyAction);
      const historyRefresh = event.target.closest('[data-history-refresh]');
      if (historyRefresh) loadIntelligenceHistory(historyRefresh.dataset.historyRefresh);
      const planButton = event.target.closest('[data-plan-id]');
      if (planButton && !event.target.closest('[data-model-id]')) openPlanDetail(planButton.dataset.planId);
      const planFreeze = event.target.closest('[data-plan-freeze]');
      if (planFreeze) togglePlanFrozen(planFreeze.dataset.planFreeze);
      const planVersion = event.target.closest('[data-plan-version]');
      if (planVersion) startPlanVersion(planVersion.dataset.planVersion);
      const planResearch = event.target.closest('[data-plan-research]');
      if (planResearch) { closeDrawers(); openResearch(planResearch.dataset.planResearch); }
      const modelAction = event.target.closest('[data-model-action]');
      if (modelAction?.dataset.modelAction === 'train') openTrainModelDialog(modelAction.dataset.modelId);
      if (modelAction?.dataset.modelAction === 'evaluate') evaluateModel(modelAction.dataset.modelId);
      const modelButton = event.target.closest('.model-item[data-model-id]');
      if (modelButton) { state.selectedModelId = modelButton.dataset.modelId; state.modelTab = 'overview'; renderModelDetail(); }
    });
    document.addEventListener('change', (event) => {
      const interval = event.target.closest('[data-monitor-interval]');
      if (interval) updateIntelligenceMonitorInterval(interval.dataset.monitorId, Number(interval.value));
    });
    $('[data-open-sidebar]').addEventListener('click', openSidebar);
    $('[data-close-sidebar]').addEventListener('click', closeSidebar);
    $('#mobile-overlay').addEventListener('click', closeSidebar);
    $('#global-search-trigger').addEventListener('click', openCommand);
    $('#workspace-switcher').addEventListener('click', openWorkspaceModal);
    $('#workspace-switcher-top').addEventListener('click', openWorkspaceModal);
    $('#close-workspace-modal').addEventListener('click', closeWorkspaceModal);
    $('#workspace-modal').addEventListener('click', (event) => { if (event.target === $('#workspace-modal')) closeWorkspaceModal(); });
    $('#manage-platform')?.addEventListener('click', () => { closeWorkspaceModal(); showView('settings'); switchSettingsSection('overview'); });
    $('#open-workspace-manager')?.addEventListener('click', openWorkspaceModal);
    $('#command-modal').addEventListener('click', (event) => { if (event.target === $('#command-modal')) closeCommand(); });
    $('#command-search').addEventListener('input', (event) => renderCommandResults(event.target.value));
    $('#command-search').addEventListener('keydown', (event) => { if (event.key === 'Enter') { event.preventDefault(); const first = $('#command-results button'); if (first) first.click(); else { closeCommand(); showView('research'); } } });
    $('#command-results').addEventListener('click', (event) => { const view = event.target.closest('[data-command-view]')?.dataset.commandView; const symbol = event.target.closest('[data-command-symbol]')?.dataset.commandSymbol; const plan = event.target.closest('[data-command-plan]')?.dataset.commandPlan; if (view) { closeCommand(); showView(view); } if (symbol) { closeCommand(); openResearch(symbol); } if (plan) { closeCommand(); openPlanDetail(plan); } });
    document.addEventListener('keydown', (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); openCommand(); } if (event.key === 'Escape') { closeCommand(); closeWorkspaceModal(); closeDrawers(); closeSidebar(); closeUserMenu(); } });
    document.addEventListener('click', (event) => { if (!event.target.closest('.user-menu-wrap')) closeUserMenu(); });
    $('#user-menu-trigger').addEventListener('click', toggleUserMenu);
    $('#logout-button').addEventListener('click', logout);
    $('#jobs-trigger').addEventListener('click', () => openDrawer('jobs-drawer'));
    $('#close-jobs').addEventListener('click', closeDrawers);
    $('#notifications-trigger').addEventListener('click', () => { $('#alert-symbol').value = state.symbol || ''; updateAlertFields(); renderAlerts(); openDrawer('alerts-drawer'); });
    $('#close-alerts').addEventListener('click', closeDrawers);
    $('#close-plan-drawer')?.addEventListener('click', closeDrawers);
    $('#alert-form').addEventListener('submit', saveAlert);
    $('#alert-scope').addEventListener('change', updateAlertFields);
    $('#alert-condition').addEventListener('change', updateAlertFields);
    $('#refresh-watchlist')?.addEventListener('click', loadWatchlist);
    $('#edit-watchlist')?.addEventListener('click', openWatchlistManager);
    $('#screener-tabs')?.addEventListener('click', (event) => { const button = event.target.closest('[data-screener-tab]'); if (!button) return; state.screenerTab = button.dataset.screenerTab; renderScreener(); });
    $('#reset-filters')?.addEventListener('click', () => { $('#filter-market').value = 'US'; $('#filter-theme').selectedIndex = 0; $('#filter-healthy').checked = true; $('#filter-grok-review').checked = false; const ranges = $$('.range-field input'); if (ranges[0]) ranges[0].value = 4; if (ranges[1]) ranges[1].value = 2; updateRangeOutputs(); });
    $$('.range-field input').forEach((input) => input.addEventListener('input', updateRangeOutputs));
    $('#ticker-search-form')?.addEventListener('submit', (event) => { event.preventDefault(); openResearch($('#research-symbol')?.value); });
    $('#watch-toggle')?.addEventListener('click', toggleWatchlist);
    $('#chart-periods')?.addEventListener('click', (event) => { const button = event.target.closest('[data-period]'); if (!button) return; $$('[data-period]').forEach((item) => item.classList.toggle('active', item === button)); changeChartPeriod(button.dataset.period); });
    $('#refresh-technical')?.addEventListener('click', async () => { if (!state.symbol) return; $('#technical-content').innerHTML = '<div class="loading-state"><span class="spinner"></span>更新技术指标</div>'; try { state.technical = await api(`/api/v1/stocks/${encodeURIComponent(state.symbol)}/technical?period=1y`); renderTechnical(state.technical); } catch (error) { renderTechnical(null); } });
    $('#run-grok')?.addEventListener('click', () => runGrok());
    $('#realtime-research-form')?.addEventListener('submit', runRealtimeResearch);
    $('#material-upload')?.addEventListener('change', (event) => uploadMaterials(event.target.files));
    $('#analyze-materials')?.addEventListener('click', analyzeMaterials);
    $('#project-material-upload')?.addEventListener('change', (event) => uploadPageMaterials('project', event.target.files));
    $('#geo-material-upload')?.addEventListener('change', (event) => uploadPageMaterials('geo', event.target.files));
    $('#sanctions-material-upload')?.addEventListener('change', (event) => uploadPageMaterials('sanctions', event.target.files));
    $('#market-material-upload')?.addEventListener('change', (event) => uploadPageMaterials('market', event.target.files));
    $('#new-material-session')?.addEventListener('click', () => {
      state.materialSessionId = '';
      state.materials = [];
      renderMaterials();
      $('#material-question').value = '';
      $('#material-consent').checked = false;
      toast('已新建资料集', '后续上传的文件不会与之前的资料混合');
    });
    $$('.query-template').forEach((button) => button.addEventListener('click', () => {
      const query = $('#realtime-query');
      if (!query) return;
      query.value = button.dataset.queryTemplate || '';
      query.focus();
      const status = $('#realtime-form-status');
      if (status) setChip(status, '已载入模板', 'healthy');
    }));
    $('#save-realtime-monitor')?.addEventListener('click', () => createIntelligenceMonitor('realtime_research'));
    $('#realtime-item-filters')?.addEventListener('click', (event) => { const button = event.target.closest('[data-realtime-filter]'); if (!button) return; state.realtimeFilter = button.dataset.realtimeFilter; $$('[data-realtime-filter]').forEach((item) => item.classList.toggle('active', item === button)); renderRealtimeItems(); });
    $('#project-risk-form')?.addEventListener('submit', runProjectRisk);
    $('#save-project-monitor')?.addEventListener('click', () => createIntelligenceMonitor('project_risk'));
    $('#geo-form')?.addEventListener('submit', runGeopoliticalAnalysis);
    $('#sanctions-form').addEventListener('submit', runSanctionsNews);
    $('#market-form').addEventListener('submit', runMarketFunding);
    $('#agent-form').addEventListener('submit', runResearchAgent);
    $('#export-realtime-pdf')?.addEventListener('click', () => downloadIntelligencePdf('realtime-research'));
    $('#export-project-risk-pdf')?.addEventListener('click', () => downloadIntelligencePdf('project-risk'));
    $('#export-geo-pdf')?.addEventListener('click', () => downloadIntelligencePdf('geopolitical-impact'));
    $('#export-sanctions-pdf')?.addEventListener('click', () => downloadIntelligencePdf('sanctions-news'));
    $('#export-market-pdf')?.addEventListener('click', () => downloadIntelligencePdf('market-funding'));
    $('#export-agent-pdf')?.addEventListener('click', () => downloadIntelligencePdf('research-agent'));
    $('#close-wizard')?.addEventListener('click', closeWizard);
    $('#wizard-next')?.addEventListener('click', nextWizardStep);
    $('#wizard-back')?.addEventListener('click', previousWizardStep);
    $('#run-plan-evidence')?.addEventListener('click', runPlanEvidence);
    $('#refresh-models')?.addEventListener('click', loadModels);
    $('#model-result-tabs')?.addEventListener('click', (event) => { const button = event.target.closest('[data-model-tab]'); if (!button) return; state.modelTab = button.dataset.modelTab; renderModelDetail(); });
    $('#new-model-button')?.addEventListener('click', openNewModelDialog);
    $('#portfolio-filters')?.addEventListener('click', (event) => { const button = event.target.closest('[data-plan-filter]'); if (!button) return; state.planFilter = button.dataset.planFilter; renderPortfolioLedger(); });
    $('#save-settings')?.addEventListener('click', saveCurrentSettings);
    $('#save-brand')?.addEventListener('click', saveBrandConfig);
    $('#reset-brand')?.addEventListener('click', resetBrandConfig);
    $('#check-health')?.addEventListener('click', async () => { const ok = await checkHealth(); toast(ok ? '数据服务正常' : '数据服务不可用', ok ? '行情与接口通过健康检查' : '请检查后端服务', ok ? 'success' : 'error'); });
    $('#overseas-api-form')?.addEventListener('submit', queryOverseasQuote);
    $('#search-overseas')?.addEventListener('click', searchOverseasSecurities);
    $('#history-overseas')?.addEventListener('click', loadOverseasHistory);
    $('#probe-overseas')?.addEventListener('click', () => loadOverseasProviderStatus(true));
    $('#overseas-result')?.addEventListener('click', (event) => {
      const item = event.target.closest('[data-overseas-symbol]');
      if (!item) return;
      $('#overseas-symbol').value = item.dataset.overseasSymbol || '';
      $('#overseas-country').value = item.dataset.overseasCountry || '';
      $('#overseas-exchange').value = item.dataset.overseasExchange || '';
      queryOverseasQuote();
    });
    $('#check-broker')?.addEventListener('click', checkBroker);
    $('#refresh-governance')?.addEventListener('click', loadGovernance);
    $$('[data-settings-section]').forEach((button) => button.addEventListener('click', () => switchSettingsSection(button.dataset.settingsSection)));
    $$('.mode-switch button').forEach((button) => button.addEventListener('click', () => { $$('.mode-switch button').forEach((item) => item.classList.toggle('active', item === button)); if (button.dataset.mode === 'admin') { showView('settings'); switchSettingsSection('overview'); toast('已进入平台视图', '管理工作区、客户化、连接器和治理策略'); } else showView('today'); }));
  }

  async function init() {
    applyClearPageTitles();
    if (!await loadAuthSession()) return;
    applyBrandConfig(state.brand);
    renderWorkspaceContext();
    const today = new Date();
    $('#today-date').textContent = new Intl.DateTimeFormat('zh-CN', { month: 'long', day: 'numeric', weekday: 'long', timeZone: 'Asia/Shanghai' }).format(new Date()).toUpperCase();
    updateClock();
    setInterval(updateClock, 1000);
    [['#refresh-technical', '刷新技术指标'], ['#refresh-models', '刷新模型列表'], ['#close-jobs', '关闭后台任务'], ['#close-alerts', '关闭预警中心'], ['#close-plan-drawer', '关闭计划详情']].forEach(([selector, label]) => $(selector)?.setAttribute('aria-label', label));
    bindEvents();
    updateRangeOutputs();
    renderRecent();
    renderScreener();
    renderAlerts();
    renderPlans();
    renderIntelligenceMonitors('realtime_research');
    renderIntelligenceMonitors('project_risk');
    await loadPlatformManifest();
    await loadPlans();
    const intelligence = await loadIntelligenceCapabilities();
    const projectWorkflow = intelligence?.workflows?.find((item) => item.id === 'project-risk');
    renderRiskDimensions([], projectWorkflow?.dimensions || Object.entries(PROJECT_RISK_LABELS).map(([id, label]) => ({ id, label })));
    const healthy = await checkHealth();
    if (healthy) loadWatchlist();
    else { const wb = $('#watchlist-body'); if (wb) wb.innerHTML = '<tr><td colspan="5"><div class="empty-state small"><strong>等待数据服务</strong><span>启动后端后可重新加载实时行情。</span><button class="button ghost" id="watchlist-retry">重试</button></div></td></tr>'; }
    $('#watchlist-retry')?.addEventListener('click', async () => { if (await checkHealth()) loadWatchlist(); });
  }

  init();
})();
