# Learnings

## [LRN-20260826-001] correction

**Logged**: 2026-08-26T09:20:00+08:00
**Priority**: high
**Status**: resolved
**Area**: frontend

### Summary
The product's typography is undersized overall, with card titles, descriptions, metadata, and status content requiring a clearer readable scale.

### Details
The user reported that the interface text is generally slightly too small and that card content is especially difficult to read. The existing stylesheet frequently uses 7–10px text inside cards, which is visually dense on desktop and becomes harder to scan on tablets and phones.

### Suggested Action
Raise the global base size modestly, establish a larger minimum type scale for card titles/body/metadata/status labels, retain the existing hierarchy, and verify that denser dashboards and responsive layouts do not clip or overlap.

### Metadata
- Source: user_feedback
- Related Files: frontend/public/assets/app.css, frontend/public/index.html, backend/app/main_ui.py
- Tags: accessibility, typography, cards, readability, responsive, visual-qa
- Pattern-Key: improve.product_typography_readability
- Recurrence-Count: 1
- First-Seen: 2026-08-26
- Last-Seen: 2026-08-26

### Resolution
- **Resolved**: 2026-08-26T09:40:00+08:00
- **Notes**: Raised the global base from 14px to 15px, increased 7–13px interface text by 2px and 14–16px text by 1px, lifted the remaining 6px PDF badge to 9px, retained existing hierarchy and responsive structure, and updated the runtime to 2026.08.26.1. Verified that all 295 stylesheet line changes are font-size-only, the minimum explicit size is now 9px, CSS braces and application syntax are valid, and strict OpenSpec validation passes. Automated live-page refresh was blocked by browser URL policy, so the existing tab requires a manual refresh to load the cache-busted stylesheet.

---

## [LRN-20260825-005] correction

**Logged**: 2026-08-25T17:25:00+08:00
**Priority**: high
**Status**: resolved
**Area**: frontend

### Summary
Geopolitical financing analysis content must remain readable without text overlapping adjacent labels or cards at any supported viewport.

### Details
The user reported that text in the geopolitical financing scenario view is visually covering other text. Dense model output, long mixed-language strings, metadata rows, and responsive grid columns must wrap and grow naturally instead of overflowing their containers or relying on fixed heights.

### Suggested Action
Reproduce the overlap at desktop, tablet, and mobile widths; identify the responsible layout constraints; add resilient wrapping, intrinsic-size, and responsive rules; then verify the real historical analysis visually.

### Metadata
- Source: user_feedback
- Related Files: frontend/public/assets/styles.css, frontend/public/assets/app.js, frontend/public/index.html
- Tags: responsive, typography, overflow, geopolitical-analysis, visual-qa
- Pattern-Key: harden.dense_analysis_text_layout
- Recurrence-Count: 1
- First-Seen: 2026-08-25
- Last-Seen: 2026-08-25

### Resolution
- **Resolved**: 2026-08-25T17:35:00+08:00
- **Notes**: Replaced the geopolitical scenario card's absolutely positioned early-signal text with natural document flow, added shrink/wrap safeguards for transmission paths, decisions, assumptions, and sources, and introduced compact-layout header/source behavior. Verified the real saved analysis visually at the active viewport, confirmed zero browser errors, and passed all 10 regression tests.

---

## [LRN-20260825-004] correction

**Logged**: 2026-08-25T14:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
Language-compliance checks must never replace useful model analysis with repetitive “未按要求返回简体中文，请重新运行” placeholders.

### Details
The user explicitly rejected the placeholder message introduced by the previous Chinese-output guard. A language audit may record residual English, but the application should preserve the actual result and rely on the original Chinese generation contract rather than destroying content or instructing the user to rerun.

### Suggested Action
Convert the language guard to non-destructive auditing, remove rerun placeholders and status downgrades, preserve actual model/source text, and suppress the old placeholder strings when rendering immutable historical snapshots.

### Metadata
- Source: user_feedback
- Related Files: backend/app/services/institutional_intelligence_service.py, backend/app/services/xai_grok_service.py, frontend/public/assets/app.js
- Tags: grok, localization, non-destructive, history, user-experience
- See Also: LRN-20260825-003
- Pattern-Key: harden.non_destructive_language_compliance
- Recurrence-Count: 1
- First-Seen: 2026-08-25
- Last-Seen: 2026-08-25

### Resolution
- **Resolved**: 2026-08-25T17:12:00+08:00
- **Notes**: Replaced destructive language blocking with non-destructive auditing, preserved future model content, suppressed legacy rerun placeholders while rendering immutable history, and passed the 10-test regression suite, browser QA, syntax checks, and strict OpenSpec validation.

---

## [LRN-20260825-003] correction

**Logged**: 2026-08-25T13:20:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
All user-facing Grok analysis prose must be returned in Simplified Chinese rather than relying on the model's default language.

### Details
The user reported that current decision-intelligence responses are in English. Chinese UI labels do not make the analysis usable when executive summaries, trends, risk rationales, events, scenarios, actions, assumptions, unknowns, excerpts, and PDF content remain English.

### Suggested Action
Enforce Simplified Chinese in every workflow prompt and structured-output contract, add a server-side language-compliance guard for English results, preserve names, URLs, tickers, official terms, model/tool identifiers and verbatim X original text, and cover the behavior with regression tests.

### Metadata
- Source: user_feedback
- Related Files: backend/app/services/institutional_intelligence_service.py, backend/app/services/intelligence_pdf_service.py, frontend/public/assets/app.js
- Tags: grok, localization, simplified-chinese, structured-output, pdf
- Pattern-Key: harden.user_facing_output_language
- Recurrence-Count: 1
- First-Seen: 2026-08-25
- Last-Seen: 2026-08-25

### Resolution
- **Resolved**: 2026-08-25T16:52:00+08:00
- **Notes**: Localized all Grok-facing prompts and fixed fallbacks, added a server-side language audit without a second data-egress call, separated X original text from Chinese explanations in UI/PDF, invalidated legacy English caches, and passed the 10-test regression suite plus browser and OpenSpec validation. LRN-20260825-004 later refined this guard to preserve content and never replace it with rerun placeholders.

---

## [LRN-20260824-002] best_practice

**Logged**: 2026-08-24T12:07:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
New scheduler timestamps should use explicit UTC instead of deprecated `datetime.utcnow()`.

### Details
Python 3.14 reports `datetime.utcnow()` as deprecated. The SQLite schema currently stores naive `DateTime` values, so the compatible approach is to obtain an aware UTC timestamp with `datetime.now(timezone.utc)` and remove timezone metadata only at the persistence boundary.

### Suggested Action
Use one UTC helper for scheduler/model timestamps and keep API serialization explicitly suffixed with `Z`.

### Metadata
- Source: error
- Related Files: backend/app/models/intelligence_monitoring.py, backend/app/services/intelligence_monitoring_service.py
- Tags: datetime, utc, scheduler, python-3.14
- Pattern-Key: harden.explicit_utc_timestamps
- Recurrence-Count: 1
- First-Seen: 2026-08-24
- Last-Seen: 2026-08-24

### Resolution
- **Resolved**: 2026-08-24T12:07:00+08:00
- **Notes**: Added an explicit UTC helper for all newly introduced monitoring timestamps.

---

## [LRN-20260824-001] correction

**Logged**: 2026-08-24T09:22:00+08:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
UI verification must include the user's already-running process, not only a freshly started test process.

### Details
The user reported that the interface and system were not displaying correctly after a successful isolated browser test. The existing port 8000 process had been running for more than two days without reload. It served the latest `index.html` from disk, but its in-memory FastAPI application predated the `/assets` mount and newer status payload. The result was a mixed-version deployment: new HTML with missing CSS/JavaScript routes.

### Suggested Action
Before declaring a local UI fixed, inspect the actual listening process, verify GET requests for HTML/CSS/JavaScript and the versioned API status, then restart stale project processes through a single canonical startup script.

### Metadata
- Source: user_feedback
- Related Files: backend/app/main_ui.py, start-ui.sh, start.sh, docker-compose.yml
- Tags: stale-process, split-brain, static-assets, runtime-verification
- Pattern-Key: harden.runtime_version_alignment
- Recurrence-Count: 1
- First-Seen: 2026-08-24
- Last-Seen: 2026-08-24

---
