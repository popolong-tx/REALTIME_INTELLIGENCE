# Learnings

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
