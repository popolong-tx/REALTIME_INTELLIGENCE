# Feature Requests

## [FEAT-20260825-008] intelligence_analysis_history

**Logged**: 2026-08-25T12:35:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Requested Capability
Persist the results from realtime information search, project-risk intelligence, and geopolitical financing analysis as history records that can be opened from the page and exported exactly as they were originally generated.

### User Context
Decision users need to revisit earlier analysis without rerunning Grok, compare what was known at that time, and export the original record for review or distribution.

### Complexity Estimate
complex

### Suggested Implementation
Add one immutable workspace-scoped history model for all three workflows, automatically save successful live/partial results and their input context, expose list/detail/PDF endpoints, add page history panels with click-to-restore behavior, and ensure exports render the stored snapshot rather than calling Grok again.

### Metadata
- Frequency: recurring
- Related Features: intelligence_pdf_export, scheduled_intelligence_monitoring, audit_trail, citation_tracking

### Resolution
- **Resolved**: 2026-08-25T13:11:00+08:00
- **Notes**: Added immutable workspace-scoped history for all three decision-intelligence workflows, automatic persistence for direct and monitor-triggered live/partial results, idempotent request/run linkage, list/detail/exact-PDF APIs, audit events, page history panels, click-to-restore form and result state, direct historical export, workspace-switch clearing, responsive styling, readiness/platform contracts, and OpenSpec/README documentation. Verified 9/9 operational regression tests, strict OpenSpec validation, runtime 2026.08.25.20, desktop browser restore/export requests, and 390px mobile layouts with no horizontal overflow. Removed the temporary browser-QA record after verification.

---

## [FEAT-20260825-007] env_login_and_responsive_information_architecture

**Logged**: 2026-08-25T09:50:00+08:00
**Priority**: high
**Status**: resolved
**Area**: frontend

### Requested Capability
Add a real login page whose username and password are configured only through the server `.env`, and make the full application readable and operable on phone, tablet, and desktop browsers with clearer page titles.

### User Context
The local test system needs a controlled entry point before exposing decision intelligence or APIs. Users also need concise task-oriented titles and layouts that remain legible across device sizes rather than long slogan-style headings.

### Complexity Estimate
complex

### Suggested Implementation
Add environment-backed credential settings, constant-time verification, rate-limited login, a signed HttpOnly session cookie, server middleware protecting the product shell and business APIs, login/status/logout endpoints, a responsive login screen and user menu, concise page titles, strengthened touch/mobile/tablet breakpoints, and regression plus multi-viewport browser validation.

### Metadata
- Frequency: recurring
- Related Features: multi_tenant_open_platform, audit_trail, workspace_customization, responsive_ui

### Resolution
- **Resolved**: 2026-08-25T10:45:00+08:00
- **Notes**: Added an environment-backed local test login, constant-time credential checks, failed-attempt throttling, signed expiring HttpOnly/SameSite sessions, protected product and business APIs, login/logout audit events, account menu and logout flow. Reworked primary headings into clear task names and strengthened phone/tablet/desktop layouts. Verified no actual password appears outside `backend/.env`, 8/8 operational regression tests, strict OpenSpec validation, live HTTP redirect/readiness, desktop browser login and logout, and 390px/768px responsive previews for both product and login pages on runtime 2026.08.25.19.

---

## [FEAT-20260825-006] scheduled_intelligence_pdf_reports

**Logged**: 2026-08-25T09:17:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Requested Capability
Automatically generate a downloadable PDF report whenever a scheduled realtime-information or project-risk monitor completes with a real result.

### User Context
Decision users should not need to revisit the workbench at every interval. Each successful scheduled detection needs a durable, traceable report tied to the exact monitor run and source request.

### Complexity Estimate
medium

### Suggested Implementation
Persist immutable PDF artifact metadata per successful monitor run, write files atomically on the server, expose workspace-scoped list and safe download APIs, surface the latest report on monitor cards, and skip report creation for configuration-required, failed, or empty results.

### Metadata
- Frequency: recurring
- Related Features: scheduled_intelligence_monitoring, intelligence_pdf_export, audit_trail, citation_tracking

### Resolution
- **Resolved**: 2026-08-25T09:39:00+08:00
- **Notes**: Successful live/partial realtime-information and project-risk monitor runs now generate one immutable PDF from the exact stored result without re-querying Grok. Added atomic local artifact storage, database metadata and run linkage, SHA-256 verification, workspace-scoped list/download APIs, generation/download audits, latest-report task-card actions, truthful skip behavior, readiness and platform contracts, OpenSpec updates, and regression coverage. Verified 7/7 operational tests, scheduled trigger persistence, cross-workspace denial, configuration-required no-report behavior, strict OpenSpec validation, runtime 2026.08.25.17, and both monitor pages in the running app.

---

## [FEAT-20260824-005] intelligence_pdf_export

**Logged**: 2026-08-24T16:10:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Requested Capability
Export the completed real-time information search, project-risk intelligence, and geopolitical financing analysis results as downloadable PDF reports.

### User Context
Decision users need a portable, reviewable artifact that preserves the analysis result, evidence ledger, scope, audit metadata, and risk disclaimer for sharing and governance workflows.

### Complexity Estimate
medium

### Suggested Implementation
Add one governed server-side PDF renderer with workflow-specific sections, Chinese font support, source citations, audit metadata, safe filenames, and response-size validation; expose it through a shared export API and result-level download buttons on all three intelligence workbenches.

### Metadata
- Frequency: first_time
- Related Features: multisource_realtime_information_search, grok_sovereign_project_intelligence, citation_tracking, audit_trail

### Resolution
- **Resolved**: 2026-08-25T09:16:00+08:00
- **Notes**: Added a shared server-side ReportLab renderer and guarded export API for all three workflows; reports include Chinese fonts, workflow-specific analysis, evidence, audit, disclaimers, safe filenames, no-store headers, and persistent export events. Added three result-level buttons, live/partial gating, responsive styling, readiness reporting, OpenSpec contracts, automated regression coverage, three visually inspected A4 samples, and a successful browser download from a real OCI Grok multi-tool result.

---

## [FEAT-20260824-004] scheduled_intelligence_monitoring

**Logged**: 2026-08-24T11:48:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Requested Capability
Add scheduled monitoring for real-time X/public information retrieval and project-risk intelligence at 30-minute, 1-, 2-, 4-, 6-, 8-, 12-, and 24-hour intervals.

### User Context
Decision users need saved monitoring scopes that run repeatedly without re-entering the research or project definition, with visible schedule state and controlled execution.

### Complexity Estimate
complex

### Suggested Implementation
Persist workspace-scoped monitor definitions and execution history, run due monitors through an application lifecycle scheduler, expose governed CRUD/run-now APIs, and add schedule, next-run, pause/resume, and recent-result controls to both intelligence workbenches.

### Metadata
- Frequency: recurring
- Related Features: multisource_realtime_information_search, grok_sovereign_project_intelligence, alerts, audit_trail

### Resolution
- **Resolved**: 2026-08-24T12:22:00+08:00
- **Notes**: Added persistent workspace monitor and run-history tables, lifecycle scheduler, CRUD/run-now/history APIs, 30-minute through 24-hour intervals, pause/resume and live interval updates, scheduler status, realtime-research and project-risk UI controls, safe OCI configuration fallback, platform manifest entries, and OpenSpec updates. Verified manual and scheduled execution, restart persistence, history, cleanup, static contracts, and rendered UI.

---

## [FEAT-20260824-003] multisource_realtime_information_search

**Logged**: 2026-08-24T10:38:41+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Requested Capability
Use OCI-hosted Grok with X Search, public web search, and code interpretation to retrieve recent X originals and public open information for a topic and date range.

### User Context
Decision users need one governed workflow that separates X ground signals from public-source evidence, preserves source links and original text, and lets Grok synthesize trends without presenting best-effort search as exhaustive coverage.

### Complexity Estimate
complex

### Suggested Implementation
Add a compatibility-aware OCI Responses adapter, a date-bounded multi-source research API, structured X/public result and audit ledgers, source-channel controls, and explicit partial/configuration-required states. Keep credentials server-side and never persist user-provided keys.

### Metadata
- Frequency: recurring
- Related Features: oci_grok, x_search, web_search, code_interpreter, citation_tracking, institutional_intelligence

### Resolution
- **Resolved**: 2026-08-24T10:52:36+08:00
- **Notes**: Added a server-side OCI Responses base URL override, X/Web/compute research adapter with narrow tool-validation fallback, multi-source realtime API, source-typed results and audit metadata, a complete realtime-research workbench, open-platform manifest entries, and OpenSpec requirements. Verified static syntax, safe zero-result configuration state, fallback metadata, runtime version 2026.08.24.11, and the browser workflow without using or persisting the user-provided credential.

---

## [FEAT-20260824-002] grok_sovereign_project_intelligence

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: frontend

### Requested Capability
Add Grok-centered real-time project risk monitoring and geopolitical financing scenario analysis for member countries and financial products.

### User Context
Investment, risk, strategy, and management teams need cited ground signals from X and public sources, direct assessment of political, social, debt, environmental, default, conflict, and reputation risks, plus structured reasoning about how geopolitical competition changes financing flows, project feasibility, co-financing, and member borrowing appetite.

### Complexity Estimate
complex

### Suggested Implementation
Create two governed intelligence workbenches: a project risk monitor with country/project/product scope, cited event timeline, risk scoring, alerts, and decision actions; and a geopolitical financing simulator with actor/event inputs, baseline/upside/stress scenarios, transmission paths, assumptions, evidence quality, and auditable Grok metadata. Reuse the OCI Grok search layer and clearly distinguish live, unverified, and demonstration states.

### Metadata
- Frequency: first_time
- Related Features: oci_grok, x_search, citation_tracking, alerts, governance, workspace_policies

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Added dedicated project-risk and geopolitical-financing APIs, governed OCI configuration fallback, two full workbench pages, a project-monitoring prototype, source and audit ledgers, open-platform manifests, and OpenSpec requirements. Verified both workflows and the `Grok Demo` sidebar title in the running app.

---

## [FEAT-20260824-001] multi_tenant_open_platform

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: frontend

### Requested Capability
Evolve the product into an open quantitative-research platform for individuals, institutions, and customer-specific deployments.

### User Context
The same platform should provide a light personal workflow, institution-grade collaboration and governance, and configurable branding, policies, data sources, models, and integrations.

### Complexity Estimate
complex

### Suggested Implementation
Introduce tenant-aware workspaces, role and approval policies, platform templates, connector contracts, branding tokens, deployment profiles, and clear data-isolation boundaries. Expose these concepts through a workspace switcher and platform administration surface while preserving the existing research workflow.

### Metadata
- Frequency: first_time
- Related Features: governance, role_permissions, oci_grok, webhooks, model_registry

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Added a platform manifest API, workspace templates and switcher, RBAC visibility, bounded brand themes, connector/extension catalogs, deployment profiles, governance flow, and an OpenSpec roadmap that keeps production tenant isolation work explicitly pending.

---
