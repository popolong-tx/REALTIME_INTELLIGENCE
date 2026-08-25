# Errors

## [ERR-20260825-095] in_app_tab_viewport_method_unavailable

**Logged**: 2026-08-25T18:33:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend-qa

### Summary
The in-app browser tab wrapper does not expose Playwright's `setViewportSize` method directly.

### Error
```
localTab.setViewportSize is not a function
```

### Context
- Desktop visual QA had already succeeded.
- This affected only an optional mobile-size browser inspection.

### Suggested Fix
Use the in-app browser's supported resize/emulation operation instead of assuming a raw Playwright page method.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.css

### Resolution
- **Resolved**: 2026-08-25T18:34:00+08:00
- **Notes**: Continued responsive validation through source breakpoint checks and the browser wrapper's supported capabilities.

---

## [ERR-20260825-094] prestartup_route_count_assumption_invalid

**Logged**: 2026-08-25T18:30:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
The import-only smoke-check expected standard FastAPI routes to be materialized before the application's startup router initialization.

### Error
```
AssertionError: overseas_routes=0
```

### Context
- The application uses an internal included-router registration mechanism, so an import-only `app.routes` count is not a valid endpoint check.
- Static source inspection and a live HTTP request are the appropriate checks for this application.

### Suggested Fix
Verify router inclusion in source, then exercise `/api/v1/overseas-securities/providers` against the running application.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py, backend/app/api/overseas_securities.py

### Resolution
- **Resolved**: 2026-08-25T18:31:00+08:00
- **Notes**: Replaced the invalid pre-start route-count assertion with source wiring and live HTTP verification.

---

## [ERR-20260825-093] fastapi_route_table_contains_pathless_entry

**Logged**: 2026-08-25T18:28:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
The route smoke-check assumed every application route entry exposes a `path` attribute, but the application also contains an internal included-router entry.

### Error
```
AttributeError: '_IncludedRouter' object has no attribute 'path'
```

### Context
- Importing the application succeeded.
- The failure occurred only while formatting the diagnostic route list.

### Suggested Fix
Filter route entries with `getattr(route, "path", "")`.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-25T18:29:00+08:00
- **Notes**: Re-ran the route check using a safe attribute lookup.

---

## [ERR-20260825-092] backend_venv_relative_path_mismatch

**Logged**: 2026-08-25T18:26:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
The application import check used a project-root virtual-environment path while its working directory was already `backend`.

### Error
```
zsh: no such file or directory: backend/venv/bin/python
```

### Context
- The application code had not started; this was only a command path mismatch.

### Suggested Fix
Use `venv/bin/python` from the backend working directory or run the root-relative path from the project root.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-25T18:27:00+08:00
- **Notes**: Re-ran the import check with the correct working-directory-relative interpreter path.

---

## [ERR-20260825-091] readonly_shell_heredoc_tempfile_denied

**Logged**: 2026-08-25T18:24:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
The read-only execution environment rejected shell here-documents used for static checks because the shell could not create temporary files.

### Error
```
zsh: can't create temp file for here document: operation not permitted
```

### Context
- The attempted checks were read-only Python AST and CSS balance checks.
- No application file was changed and no application test failed.

### Suggested Fix
Use inline `python3 -c` expressions instead of shell here-documents in read-only execution mode.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/data_sources/twelve_data.py, frontend/public/assets/app.css

### Resolution
- **Resolved**: 2026-08-25T18:25:00+08:00
- **Notes**: Re-ran the checks with inline expressions that do not create temporary shell files.

---

## [ERR-20260825-090] overseas_openspec_patch_context_mismatch

**Logged**: 2026-08-25T18:18:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
The combined overseas-securities documentation patch assumed wording that did not exactly match the open-platform specification.

### Error
```
apply_patch verification failed: expected open-platform provider validation scenario was not found
```

### Context
- The patch combined data-search, open-platform, tasks, design, and README updates.
- Verification failed before the documentation files were changed.

### Suggested Fix
Read the exact open-platform requirement and update each document independently.

### Metadata
- Reproducible: yes
- Related Files: openspec/changes/quant-trading-advisor/specs/open-platform/spec.md

### Resolution
- **Resolved**: 2026-08-25T18:19:00+08:00
- **Notes**: Split the documentation updates and anchored them to exact current headings.

---

## [ERR-20260825-089] overseas_api_multi_file_patch_context_mismatch

**Logged**: 2026-08-25T18:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
The first multi-file overseas-securities integration patch used an outdated import line for the legacy application entrypoint.

### Error
```
apply_patch verification failed: Failed to find expected lines in backend/app/main.py
```

### Context
- The patch included new service/API files plus current and legacy application wiring.
- Patch verification failed before any part of the patch was applied.

### Suggested Fix
Inspect the exact legacy entrypoint imports and apply the integration in smaller verified patches.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main.py, backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-25T18:06:00+08:00
- **Notes**: Split the change into focused patches and used the exact current import contexts.

---

## [ERR-20260825-088] browser_locator_scroll_helper_unavailable

**Logged**: 2026-08-25T17:29:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The in-app browser locator API does not expose `scrollIntoViewIfNeeded` in this runtime.

### Error
```
localTab.playwright.getByRole(...).scrollIntoViewIfNeeded is not a function
```

### Context
- The operation was only intended to position the geopolitical scenario section for visual QA.
- No application state or source code changed.

### Suggested Fix
Use the browser tab's supported page-scrolling operation or a visible navigation flow instead of locator scrolling.

### Metadata
- Reproducible: yes
- Related Files: none

### Resolution
- **Resolved**: 2026-08-25T17:30:00+08:00
- **Notes**: Continued diagnosis from the rendered DOM and source layout rules; the unsupported helper is not required for the fix.

---

## [ERR-20260825-087] browser_qa_redeclared_binding

**Logged**: 2026-08-25T17:08:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The persistent browser QA session rejected a reused constant name from an earlier turn.

### Error
```
Identifier 'geoSnap' has already been declared
```

### Context
- The script failed before clicking or changing page state.
- Persistent browser bindings can survive across turns.

### Suggested Fix
Use fresh uniquely named bindings, or declare reusable QA values with `var`.

### Metadata
- Reproducible: yes
- Related Files: none

### Resolution
- **Resolved**: 2026-08-25T17:09:00+08:00
- **Notes**: Continued the browser check with a unique variable name.

---

## [ERR-20260825-086] browser_domcontentloaded_helper_unavailable

**Logged**: 2026-08-25T17:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The browser QA script called a page-load helper that is not available in the current in-app browser API.

### Error
```
localTab.playwright.domcontentloaded is not a function
```

### Context
- The application page was reloaded, but the unsupported wait call stopped the QA script before inspection.
- No application data or source code was changed by the failed call.

### Suggested Fix
Use a short bounded wait after reload and confirm readiness from the visible DOM snapshot.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html, frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-25T17:06:00+08:00
- **Notes**: Replaced the unsupported helper with a bounded wait and DOM-based readiness check.

---

## [ERR-20260825-085] browser_realtime_nav_accessible_name

**Logged**: 2026-08-25T16:44:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The initial browser QA locator could not find the realtime-information navigation button by the assumed exact accessible name.

### Error
```
Playwright selector deadline exceeded: role=button, name="实时信息检索"
```

### Context
- The page loaded successfully at localhost and displayed the signed-in application shell.
- No page state was changed by the failed click.

### Suggested Fix
Inspect the fresh visible DOM for the rendered navigation label, then use the observed locator instead of an assumed accessible name.

### Metadata
- Reproducible: unknown
- Related Files: frontend/public/index.html, frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-25T16:46:00+08:00
- **Notes**: Used the observed accessible name `实时信息检索 X + WEB`, opened the target page, and confirmed runtime `2026.08.25.21` with the new asset versions.

---

## [ERR-20260825-084] py_compile_read_only_workspace

**Logged**: 2026-08-25T16:32:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
Python bytecode compilation attempted to create a `__pycache__` file in the read-only workspace.

### Error
```
Operation not permitted: backend/app/services/__pycache__/institutional_intelligence_service...
```

### Context
- No source file was modified by the failed check.
- JavaScript syntax checking did not run because the preceding command failed.

### Suggested Fix
Use in-memory `ast.parse` for Python syntax validation and run JavaScript syntax checking separately.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/institutional_intelligence_service.py

### Resolution
- **Resolved**: 2026-08-25T16:33:00+08:00
- **Notes**: Replaced bytecode compilation with read-only AST parsing.

---

## [ERR-20260825-083] duplicate_provider_translation_rejected

**Logged**: 2026-08-25T16:20:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
A proposed fallback would have resent a complete institutional analysis result to OCI Grok for translation, creating an unnecessary second outbound transfer.

### Error
```
apply_patch rejected: duplicate provider translation carries unacceptable data-egress risk
```

### Context
- The user requested Chinese presentation, but did not separately authorize retransmitting the full result for translation.
- The rejected patch was not applied.

### Suggested Fix
Enforce Simplified Chinese in the original inference request, localize fixed labels and enums locally, and reject residual English prose before it reaches the UI.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/institutional_intelligence_service.py

### Resolution
- **Resolved**: 2026-08-25T16:21:00+08:00
- **Notes**: Switched to single-pass Chinese generation plus local validation; no duplicate provider call or additional data egress is used.

---

## [ERR-20260825-068] compressed_html_title_patch_mismatch

**Logged**: 2026-08-25T10:03:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
A bulk title patch failed because several complete page sections are compressed onto single very long HTML lines.

### Error
```
apply_patch verification failed while matching the portfolio page heading line
```

### Context
- The intended copy changes were not applied by the failed patch.

### Suggested Fix
Use a single declarative page-copy map in the frontend initialization so all page headings are updated consistently without rewriting compressed section markup.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html, frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-25T10:04:00+08:00
- **Notes**: Moved concise heading and subtitle copy into one initialization map and kept only structural user-menu edits in HTML.

---

## [ERR-20260825-067] python_secrets_entropy_hang

**Logged**: 2026-08-25T09:53:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The isolated Python process unexpectedly hung while generating a session signing secret with `secrets.token_urlsafe`.

### Error
```
Process produced no output for more than 30 seconds and required termination.
```

### Context
- The command only requested cryptographically secure random bytes and did not touch project files.

### Suggested Fix
Use the system OpenSSL random generator for the local `.env` session secret.

### Metadata
- Reproducible: unknown
- Related Files: backend/.env

### Resolution
- **Resolved**: 2026-08-25T09:54:00+08:00
- **Notes**: Replaced the hanging generator with `openssl rand` and continued without reusing an application password as a signing secret.

---

## [ERR-20260825-066] sandbox_localhost_connect_denied

**Logged**: 2026-08-25T09:35:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The default sandbox could not connect to the local UI service for read-only endpoint verification.

### Error
```
curl: (7) Failed to connect to localhost port 8000
```

### Context
- The in-app browser remained connected and displayed the running application; the failure was isolated to the restricted shell network context.

### Suggested Fix
Repeat the scoped localhost read-only checks with approved network permissions.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-25T09:36:00+08:00
- **Notes**: Re-ran the same localhost health, readiness, report-list, and monitor-list checks with scoped approval.

---

## [ERR-20260825-065] brand_patch_context_mismatch

**Logged**: 2026-08-25T09:33:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The first brand consistency patch targeted a helper name that does not exist in the current frontend.

### Error
```
apply_patch verification failed: Failed to find expected lines ... function sanitizeBrand(candidate)
```

### Context
- The existing brand normalization is implemented inside `applyBrandConfig`.

### Suggested Fix
Inspect the current brand configuration function and patch its actual context.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.js, frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-25T09:34:00+08:00
- **Notes**: Retargeted the update to `applyBrandConfig` and the current static defaults.

---

## [ERR-20260825-064] browser_tab_wait_method_unavailable

**Logged**: 2026-08-25T09:32:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The current in-app browser tab wrapper does not expose a direct `waitForTimeout` method.

### Error
```
platformTab.waitForTimeout is not a function
```

### Context
- Navigation completed before the unsupported convenience wait was called.

### Suggested Fix
Use the supported page snapshot or accessibility inspection operation, which waits for the document state needed by the validation.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-25T09:33:00+08:00
- **Notes**: Continued with supported Playwright-backed page inspection instead of a tab-level timeout helper.

---

## [ERR-20260825-063] stale_browser_tab_after_restart

**Logged**: 2026-08-25T09:30:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The persisted in-app browser tab binding became stale after the local UI service restart.

### Error
```
Unknown tab: 7
```

### Context
- The browser connection remained available; only the old tab handle was no longer part of the current browser session.

### Suggested Fix
Discard the stale tab binding and obtain a fresh tab from the existing browser binding.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html
- See Also: ERR-20260825-060

### Resolution
- **Resolved**: 2026-08-25T09:31:00+08:00
- **Notes**: Recovered by listing current tabs and rebinding a current or newly created in-app tab.

---

## [ERR-20260825-062] py_compile_read_only_cache

**Logged**: 2026-08-25T09:23:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
Python bytecode compilation attempted to write a cache file in the managed read-only workspace.

### Error
```
[Errno 1] Operation not permitted: backend/app/models/__pycache__/intelligence_monitoring...
```

### Context
- The validation command used `py_compile`, which writes `.pyc` artifacts even though only syntax validation was needed.

### Suggested Fix
Parse the source with `ast.parse` for read-only syntax validation and reserve bytecode compilation for an approved writable run.

### Metadata
- Reproducible: yes
- Related Files: backend/app/models/intelligence_monitoring.py, backend/app/services/intelligence_monitoring_service.py

### Resolution
- **Resolved**: 2026-08-25T09:24:00+08:00
- **Notes**: Switched subsequent static checks to read-only AST parsing.

---

## [ERR-20260825-061] process_list_sandbox_denied

**Logged**: 2026-08-25T09:15:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The default read-only environment denied process-list inspection before the local UI restart.

### Error
```
zsh: operation not permitted: ps
```

### Context
- The startup script was inspected successfully and already validates listener ownership, working directory, reload parent, and graceful termination.

### Suggested Fix
Run the scoped project startup script with approved process permissions instead of probing the process list separately.

### Metadata
- Reproducible: yes
- Related Files: start-ui.sh
- See Also: ERR-20260824-049

### Resolution
- **Resolved**: 2026-08-25T09:16:00+08:00
- **Notes**: Continued through the verified project-scoped restart guard.

---

## [ERR-20260825-060] browser_tabs_open_method

**Logged**: 2026-08-25T09:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The reused browser binding did not expose `browser.tabs.open` after its prior tabs had been cleaned up.

### Error
```
browser.tabs.open is not a function
```

### Context
- Browser binding was reused as required.
- `browser.tabs.list()` returned an empty collection.
- Attempted to open the local UI with an assumed tabs method.

### Suggested Fix
Inspect the already-connected binding's public tab methods and use the documented creation method.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html
- See Also: ERR-20260824-032, ERR-20260824-033

### Resolution
- **Resolved**: 2026-08-25T09:12:00+08:00
- **Notes**: The binding exposes `tabs.new(...)`; using it created the target local-app tab successfully.

---

## [ERR-20260825-059] pdf_text_case_assertion

**Logged**: 2026-08-25T09:03:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The PDF regression test expected title-case branding while the rendered header intentionally uses uppercase branding.

### Error
```
AssertionError: 'Grok Demo' not found in 'GROK DEMO / 实时决策情报分析 ...'
```

### Context
- PDF generation, page count, Chinese text extraction, tables, sources, and audit sections all succeeded.
- Only the case-sensitive string assertion failed.

### Suggested Fix
Assert the exact rendered brand string or normalize case before comparison.

### Metadata
- Reproducible: yes
- Related Files: backend/tests/run_operational_hardening.py

### Resolution
- **Resolved**: 2026-08-25T09:04:00+08:00
- **Notes**: Updated the assertion to the intentional `GROK DEMO` page-header text.

---

## [ERR-20260825-058] standalone_test_import_path

**Logged**: 2026-08-25T00:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The dependency-free test runner still required an external Python module path when invoked as a file.

### Error
```
ModuleNotFoundError: No module named 'app'
```

### Context
- Executing `tests/run_operational_hardening.py` makes `tests/` the first import root.
- The runner imports the sibling `app/` package.

### Suggested Fix
Insert the resolved backend root into `sys.path` before application imports.

### Metadata
- Reproducible: yes
- Related Files: backend/tests/run_operational_hardening.py
- See Also: ERR-20260824-047, ERR-20260825-057

### Resolution
- **Resolved**: 2026-08-25T00:21:00+08:00
- **Notes**: Made the standalone runner initialize its backend import root directly.

---

## [ERR-20260825-057] backend_import_workdir

**Logged**: 2026-08-25T00:14:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The PDF service import probe ran from the repository root instead of the backend package root.

### Error
```
ModuleNotFoundError: No module named 'app'
```

### Context
- Backend modules use `app.*` imports and expect `backend/` on the Python import path.

### Suggested Fix
Run backend import and test commands with `backend/` as their working directory.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/intelligence_pdf_service.py
- See Also: ERR-20260824-029

### Resolution
- **Resolved**: 2026-08-25T00:15:00+08:00
- **Notes**: Re-ran the import probe from the backend directory.

---

## [ERR-20260825-056] compileall_read_only_bytecode

**Logged**: 2026-08-25T00:12:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Python `compileall` attempted to update bytecode caches in a read-only workspace.

### Error
```
PermissionError: [Errno 1] Operation not permitted: '__pycache__/...pyc'
```

### Context
- Ran a broad backend syntax check after adding the PDF export service.
- Source files are readable, but the command writes `.pyc` files by default.

### Suggested Fix
Parse source files with `ast.parse` or run imports with `PYTHONDONTWRITEBYTECODE=1`.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/intelligence.py, backend/app/services/intelligence_pdf_service.py
- See Also: ERR-20260824-014

### Resolution
- **Resolved**: 2026-08-25T00:13:00+08:00
- **Notes**: Replaced compileall with read-only AST parsing and disabled bytecode writes for runtime imports.

---

## [ERR-20260825-055] apply_patch_permission_review_timeout

**Logged**: 2026-08-25T00:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
A multi-hunk frontend patch was not applied because the automatic permission review timed out.

### Error
```
The automatic permission approval review did not finish before its deadline.
```

### Context
- The patch added PDF export state, download handling, and three button bindings in one JavaScript file.
- A read-only follow-up confirmed none of the target symbols were written.

### Suggested Fix
Retry once using smaller, independently verifiable patches.

### Metadata
- Reproducible: unknown
- Related Files: frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-25T00:06:00+08:00
- **Notes**: Confirmed no partial write and split the frontend update into smaller patches.

---

## [ERR-20260824-053] live_broker_mutation_probe_rejected

**Logged**: 2026-08-24T15:37:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
A live-service POST intended to confirm the broker simulation gate was rejected because any broker mutation probe could place a real order if the guard were misconfigured.

### Error
```
The command includes a POST to the running broker order endpoint; a bug or misconfiguration could place a real order.
```

### Context
- The same route and server policy were already validated in an isolated TestClient environment with no broker credentials.
- The running service must be verified using read-only endpoints only.

### Suggested Fix
Keep mutation-gate tests isolated and restrict live runtime verification to readiness metadata showing `simulation_only`, `order_mutations_enabled: false`, and `server_policy_enforced: true`.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/broker.py, backend/tests/run_operational_hardening.py

### Resolution
- **Resolved**: 2026-08-24T15:37:00+08:00
- **Notes**: Did not retry the live mutation; retained isolated regression coverage and proceeded with read-only runtime checks.

---

## [ERR-20260824-052] sandbox_localhost_probe_isolated

**Logged**: 2026-08-24T15:34:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An unprivileged shell probe could not connect to the freshly started localhost service even though the authorized server session reported successful startup.

### Error
```
curl: (7) Failed to connect to localhost port 8000
```

### Context
- The service was started outside the restricted sandbox and logged application startup complete.
- The follow-up curl ran in the default restricted environment.

### Suggested Fix
Run localhost verification in the same authorized environment and confirm the server session remains alive before classifying this as an application failure.

### Metadata
- Reproducible: unknown
- Related Files: start-ui.sh, backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-24T15:42:00+08:00
- **Notes**: Authorized read-only probes returned version 2026.08.24.14 and HTTP 200 for the status and static assets.

---

## [ERR-20260824-051] startup_guard_rejects_uvicorn_reload_worker

**Logged**: 2026-08-24T15:31:00+08:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
The canonical startup script refused to restart the project because it inspected the Uvicorn reload worker rather than the parent command.

### Error
```
端口 8000 已被其他程序占用
命令: Python -c from multiprocessing.spawn import spawn_main ... --multiprocessing-fork
```

### Context
- The listener working directory is the project backend directory.
- Uvicorn `--reload` uses a parent process plus a multiprocessing child whose command line does not contain the original module target.

### Suggested Fix
Teach the guarded restart to recognize a project-owned multiprocessing worker only when its parent is the project Uvicorn reload process; terminate the parent so the process group shuts down cleanly.

### Metadata
- Reproducible: yes
- Related Files: start-ui.sh
- See Also: LRN-20260824-001

### Resolution
- **Resolved**: 2026-08-24T15:42:00+08:00
- **Notes**: The guard now verifies the worker's direct parent and cleanly restarted the project Uvicorn reload process.

---

## [ERR-20260824-050] ui_server_unavailable_after_hot_reload

**Logged**: 2026-08-24T15:28:00+08:00
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
The localhost UI/API stopped accepting connections after backend module changes triggered the existing reload process.

### Error
```
curl: (7) Failed to connect to localhost port 8000
```

### Context
- Port inspection immediately beforehand showed project-owned Python reload/worker listeners.
- The new version adds database models and changes imported runtime modules, which can require a clean process restart.

### Suggested Fix
Restart through `start-ui.sh`, then verify runtime version, HTML, CSS/JS assets, health payload, and the browser page before marking resolved.

### Metadata
- Reproducible: unknown
- Related Files: start-ui.sh, backend/app/main_ui.py, backend/app/models/platform_operations.py
- See Also: LRN-20260824-001

### Resolution
- **Resolved**: 2026-08-24T15:42:00+08:00
- **Notes**: Restarted through the canonical startup script and verified runtime, API, static assets, and browser-rendered module readiness.

---

## [ERR-20260824-049] process_command_inspection_sandbox_denied

**Logged**: 2026-08-24T15:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: infra

### Summary
The sandbox denied reading full process command lines for the two Python listeners on port 8000.

### Error
```
zsh: operation not permitted: ps
```

### Context
- Read-only socket and working-directory inspection succeeded.
- Both listeners have the project backend directory as their current working directory and share the same port, consistent with the Uvicorn reload parent/worker pattern.

### Suggested Fix
Use the project's guarded startup script for restart, or request elevated read access when exact command-line confirmation is required.

### Metadata
- Reproducible: yes
- Related Files: start-ui.sh, backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-24T15:25:00+08:00
- **Notes**: Continued with the canonical guarded restart flow after confirming both listener working directories.

---

## [ERR-20260824-048] eager_xgboost_import_breaks_other_models

**Logged**: 2026-08-24T15:18:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
Linear-regression training failed because model factories imported the optional XGBoost package before selecting the requested model type.

### Error
```
POST /api/v1/models/{id}/train -> 500
No module named 'xgboost'
```

### Context
- The requested model type was `linear_regression` and did not require XGBoost.
- Both training and fine-tuning factories used eager imports.

### Suggested Fix
Import optional model libraries only inside the selected model branch and return a clear configuration error when that specific model type is unavailable.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/model_training_service.py, backend/app/services/model_fine_tuning_service.py

### Resolution
- **Resolved**: 2026-08-24T15:18:00+08:00
- **Notes**: Changed XGBoost to a branch-local optional import and reran the regression suite.

---

## [ERR-20260824-047] standard_test_runner_environment_setup

**Logged**: 2026-08-24T15:12:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The first standard-library regression run used an incompatible macOS `mktemp` template and omitted the backend module path.

### Error
```
mktemp: mkstemp failed on /tmp/quant-demo-validation.XXXXXX.db: File exists
ModuleNotFoundError: No module named 'app'
```

### Context
- macOS `mktemp` expects the trailing template characters at the end of the path.
- Application imports resolve from the `backend` directory.

### Suggested Fix
Use a template ending in `XXXXXX` and run with `PYTHONPATH=backend` while keeping the isolated database URL.

### Metadata
- Reproducible: yes
- Related Files: backend/tests/run_operational_hardening.py

### Resolution
- **Resolved**: 2026-08-24T15:12:00+08:00
- **Notes**: Corrected the local validation command and reran the suite.

---

## [ERR-20260824-046] pytest_not_installed_in_project_venv

**Logged**: 2026-08-24T15:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The isolated regression test command could not start because the project virtual environment does not include pytest.

### Error
```
backend/venv/bin/python: No module named pytest
```

### Context
- The application dependencies and FastAPI test client are already installed.
- Adding a network dependency is unnecessary for the requested runtime verification.

### Suggested Fix
Use Python's built-in `unittest` and `unittest.mock`, or add pytest to the documented development dependencies in a separate dependency-management change.

### Metadata
- Reproducible: yes
- Related Files: backend/tests/test_operational_hardening.py, backend/requirements.txt

### Resolution
- **Resolved**: 2026-08-24T15:05:00+08:00
- **Notes**: Added a dependency-free standard-library regression runner without changing application dependencies.

---

## [ERR-20260824-045] readiness_css_anchor_mismatch

**Logged**: 2026-08-24T14:53:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
The module-readiness UI patch used a CSS anchor whose exact declaration did not exist in the current stylesheet.

### Error
```
apply_patch verification failed: Failed to find expected lines: .connector-catalog { ... }
```

### Context
- The combined patch was atomic and no partial changes were applied.
- The UI already has connector styles, but their formatting differs from the assumed single-line declaration.

### Suggested Fix
Locate the actual selector block before inserting adjacent styles, and keep backend and frontend patch anchors separate.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.css, frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T14:53:00+08:00
- **Notes**: Retried after inspecting the exact CSS section.

---

## [ERR-20260824-044] local_plan_migration_delete_rejected

**Logged**: 2026-08-24T14:45:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
The first browser-to-server plan migration attempted to remove the legacy local plan list immediately after import and was rejected as a data-loss risk.

### Error
```
The migration deletes the browser’s local plan store after POSTing records, but a later reload failure or partial migration could cause irreversible local data loss.
```

### Context
- The active plan store is being moved from localStorage to SQLite.
- User-created local plans must remain recoverable during migration.

### Suggested Fix
Keep the legacy list as a read-only backup, set a separate migration marker only after all imports and a confirming server reload succeed, and never use the backup as the active store afterward.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.js, backend/app/api/recommendations.py

### Resolution
- **Resolved**: 2026-08-24T14:45:00+08:00
- **Notes**: Reworked migration to preserve legacy data and switch active reads/writes to the server.

---

## [ERR-20260824-043] standalone_service_file_delete_rejected

**Logged**: 2026-08-24T14:22:00+08:00
**Priority**: low
**Status**: resolved
**Area**: workflow

### Summary
Deleting an imported service file before recreating it was rejected because the intermediate state could break the running application.

### Error
```
Deleting the audit service file as a standalone mutation can immediately break imports and governance functionality.
```

### Context
- The intended result was a full replacement of the audit implementation.
- The safer approach is an in-place patch that never removes the module path.

### Suggested Fix
Use one or more `Update File` hunks for imported runtime modules rather than delete/add replacement steps.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/audit_trail_service.py

### Resolution
- **Resolved**: 2026-08-24T14:22:00+08:00
- **Notes**: Continued with in-place import and class-method replacement.

---

## [ERR-20260824-042] apply_patch_same_file_delete_add

**Logged**: 2026-08-24T14:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: workflow

### Summary
An `apply_patch` operation attempted to delete and add the same file in one patch and was rejected by the patch verifier.

### Error
```
apply_patch verification failed: invalid patch: multiple operations target audit_trail_service.py
```

### Context
- The operation was replacing an in-memory audit service with a database-backed implementation.
- No file content was changed by the rejected patch.

### Suggested Fix
Replace the file with a single update hunk, or separate the delete and add into distinct patch calls.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/audit_trail_service.py

### Resolution
- **Resolved**: 2026-08-24T14:20:00+08:00
- **Notes**: Retried using a single full-file update operation.

---

## [ERR-20260824-041] simulation_mode_not_enforced_at_broker_api

**Logged**: 2026-08-24T13:52:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
The UI and platform manifest declare simulation-only execution, but mounted broker endpoints still call the real Longport order and cancellation service without a separate execution-mode guard.

### Error
```
POST /api/v1/broker/order and POST /api/v1/broker/order/cancel remain mounted while execution_mode is advertised as simulation_only.
```

### Context
- The current runtime has zero configured broker connections, so no order was attempted.
- If credentials are later configured, the API layer does not visibly enforce the product's simulation-only declaration.

### Suggested Fix
Add a server-side execution policy gate that rejects live order mutations unless an explicitly approved workspace-level live mode is enabled, with actor authorization and durable audit logging.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/broker.py, backend/app/api/platform.py, backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-24T15:42:00+08:00
- **Notes**: Added a server-side dual execution gate, persistent blocked-attempt audit, truthful readiness metadata, and isolated regression coverage proving the broker adapter is not called in simulation mode.

---

## [ERR-20260824-040] audit_event_table_assumption

**Logged**: 2026-08-24T13:49:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
The persistence audit assumed governance audit events had a SQLite table, but the database contains no `audit_events` table.

### Error
```
Error: in prepare, no such table: audit_events
```

### Context
- The UI displayed one audit event through the governance service.
- Database introspection showed models and user/intelligence tables but no audit-event persistence table.

### Suggested Fix
Persist audit events in an append-only datastore before treating governance audit counts as durable evidence.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/audit_trail_service.py, backend/app/api/governance.py

### Resolution
- **Resolved**: 2026-08-24T13:49:00+08:00
- **Notes**: Removed the nonexistent table from the read-only count query and classified governance audit history as process-local.

---

## [ERR-20260824-039] hidden_research_grok_button_probe

**Logged**: 2026-08-24T13:47:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The securities Grok validation attempted to click its button before selecting the hidden intelligence tab.

### Error
```
Element is not visible: #run-grok
```

### Context
- The research workbench uses separate tab panels.
- The button exists in the DOM but is intentionally hidden until its tab is selected.

### Suggested Fix
Activate the relevant research tab before interacting with its controls.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html, frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-24T13:47:00+08:00
- **Notes**: Switched to the intelligence research tab before retrying.

---

## [ERR-20260824-038] persisted_model_evaluation_probe_rejected

**Logged**: 2026-08-24T13:44:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A proposed live call to the evaluation endpoint for an existing persisted model was rejected because it could mutate user-owned model state.

### Error
```
The POST evaluation targets an existing persisted model and may mutate its status or metrics; read-only inspection is sufficient.
```

### Context
- The audit was intended to confirm whether the endpoint performs real evaluation.
- Source inspection already shows the endpoint returns a fixed `evaluation_started` payload without invoking the evaluation service.

### Suggested Fix
Use a disposable isolated database or dedicated test fixture when mutation testing is needed.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/models.py

### Resolution
- **Resolved**: 2026-08-24T13:44:00+08:00
- **Notes**: Did not retry or circumvent the rejection; used read-only source and database inspection instead.

---

## [ERR-20260824-037] browser_element_info_argument_mismatch

**Logged**: 2026-08-24T13:38:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The Browser plugin `elementInfo` helper was called with a selector although it requires numeric screen coordinates.

### Error
```
playwright.elementInfo requires numeric x and y coordinates
```

### Context
- The check was diagnostic only and did not affect the application.
- Locator inspection and browser console APIs are sufficient for this audit.

### Suggested Fix
Use locator methods for selector-based inspection and reserve `elementInfo(x, y)` for coordinate-based UI analysis.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T13:38:00+08:00
- **Notes**: Continued with locator and console-based diagnostics.

---

## [ERR-20260824-036] discover_screener_click_no_effect

**Logged**: 2026-08-24T13:37:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
Clicking the visible Discover-page screener button during browser validation left the result area in its untouched initial state.

### Error
```
candidate count remained 0 and the body still read "运行筛选以加载候选"
```

### Context
- The API-backed market watchlist and AAPL research workflow worked immediately beforehand.
- The screener should replace the body with a loading row before fetching market and technical data.

### Suggested Fix
Inspect the click handler, button identity, browser console, and filter control availability; then rerun the workflow.

### Metadata
- Reproducible: unknown
- Related Files: frontend/public/assets/app.js, frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T13:40:00+08:00
- **Notes**: Server logs proved the click executed one market request and five technical-analysis requests. The default volatility filter excluded every row, and the shared zero-row copy resembled the untouched state. With the limit set to unrestricted, five live candidates rendered successfully. The feature works; its no-match copy should be made less ambiguous.

---

## [ERR-20260824-035] shell_quote_in_api_extraction

**Logged**: 2026-08-24T12:43:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
An API-call extraction command mixed shell quotes and a backtick inside a regex, causing zsh parsing to fail.

### Error
```
zsh:1: unmatched '
zsh:1: parse error in command substitution
```

### Context
- The command attempted to extract frontend `api(...)` calls with a single regex.
- Static file inspection itself was unaffected.

### Suggested Fix
Use fixed-string searches or separate safely quoted expressions for source extraction.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-24T12:43:00+08:00
- **Notes**: Continued with fixed-string route searches and targeted function reads.

---

## [ERR-20260824-034] repository_status_unavailable

**Logged**: 2026-08-24T12:31:00+08:00
**Priority**: low
**Status**: resolved
**Area**: workflow

### Summary
The final change-summary check assumed the project directory was a Git worktree.

### Error
```
fatal: not a git repository (or any of the parent directories): .git
```

### Context
- The application files and runtime are valid, but this directory has no Git metadata.
- File-level verification is sufficient for this local delivery.

### Suggested Fix
Check for `.git` before requesting repository status; otherwise report verified file paths directly.

### Metadata
- Reproducible: yes
- Related Files: /Users/juxiaobing/dev-work/claude_workspace/QuantitativeTradingDemo

### Resolution
- **Resolved**: 2026-08-24T12:31:00+08:00
- **Notes**: Used direct file and runtime checks for the final delivery summary.

---

## [ERR-20260824-033] browser_tab_wrapper_timeout_assumption

**Logged**: 2026-08-24T12:29:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The persisted in-app browser tab was treated as a Playwright Page and called with `waitForTimeout`.

### Error
```
platformTab.waitForTimeout is not a function
```

### Context
- The Browser plugin persists a tab wrapper, not a raw Playwright Page.
- Earlier semantic DOM validation already completed through the wrapper's native interfaces.

### Suggested Fix
Use the Browser plugin tab wrapper APIs and polling helpers instead of raw Playwright page methods.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T12:29:00+08:00
- **Notes**: Returned to the plugin-native browser interaction pattern.

---

## [ERR-20260824-032] browser_context_shape_assumption

**Logged**: 2026-08-24T12:28:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The final browser positioning check treated the persisted browser handle as a Playwright Browser instead of reusing the persisted page handle.

### Error
```
browser.pages is not a function
```

### Context
- The existing browser validation session already exposed `globalThis.platformTab` as the active page.
- Reinitializing or enumerating pages was unnecessary.

### Suggested Fix
Reuse the persisted `platformTab` page handle for follow-up browser checks.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T12:28:00+08:00
- **Notes**: Switched the final positioning check to the existing `platformTab` page handle.

---

## [ERR-20260824-031] fastapi_route_list_not_flattened

**Logged**: 2026-08-24T12:18:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Direct route-list traversal did not expose paths registered through included routers in the installed FastAPI version.

### Error
```
AssertionError: expected monitor paths were not present in the direct app.routes set
```

### Context
- Live monitor endpoints already returned successful 200/201 responses.
- The application can generate a flattened OpenAPI path map for contract inspection.

### Suggested Fix
Assert included API contracts against `app.openapi()['paths']` rather than internal route-list representation.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py, backend/app/api/intelligence.py

### Resolution
- **Resolved**: 2026-08-24T12:18:00+08:00
- **Notes**: Use the public OpenAPI contract as the route source of truth.

---

## [ERR-20260824-030] fastapi_included_router_path_check

**Logged**: 2026-08-24T12:16:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The route-contract assertion assumed every FastAPI route-list item exposes a `path` attribute.

### Error
```
AttributeError: '_IncludedRouter' object has no attribute 'path'
```

### Context
- This FastAPI version includes internal router markers in `app.routes`.
- Actual API routes still expose `path` normally.

### Suggested Fix
Collect paths with `getattr(route, 'path', None)` and ignore internal markers.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py, backend/app/api/intelligence.py

### Resolution
- **Resolved**: 2026-08-24T12:16:00+08:00
- **Notes**: Re-run the assertion against path-bearing route entries only.

---

## [ERR-20260824-029] backend_route_check_workdir

**Logged**: 2026-08-24T12:14:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The final route-contract check imported `app.main_ui` from the repository root instead of the backend package directory.

### Error
```
ModuleNotFoundError: No module named 'app'
```

### Context
- The project package root is `backend/`.
- The running application was unaffected; only the standalone import check used the wrong working directory.

### Suggested Fix
Run backend import checks with `backend/` as the working directory and adjust AST paths accordingly.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-24T12:14:00+08:00
- **Notes**: Re-run the contract check from the backend directory.

---

## [ERR-20260824-028] browser_direct_local_json_blocked

**Logged**: 2026-08-24T12:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The in-app browser client blocked direct navigation from the product shell to a localhost JSON history endpoint.

### Error
```
net::ERR_BLOCKED_BY_CLIENT
```

### Context
- Normal same-origin API calls made by the application are working.
- The failure occurred only when using the browser tab as a raw JSON viewer.

### Suggested Fix
Use an approved localhost command for read-only API contract inspection and keep browser checks focused on rendered UI workflows.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/intelligence.py

### Resolution
- **Resolved**: 2026-08-24T12:05:00+08:00
- **Notes**: Continue with localhost API inspection plus browser-rendered workflow checks.

---

## [ERR-20260824-027] browser_evaluate_fetch_unavailable

**Logged**: 2026-08-24T12:03:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The in-page browser evaluation sandbox does not expose the native `fetch` function for direct API contract checks.

### Error
```
TypeError: fetch is not a function
```

### Context
- The user-facing application itself can call the API normally through its loaded script.
- Only the restricted validation callback lacks general network primitives.

### Suggested Fix
Navigate the test tab to the read-only JSON endpoint, inspect the rendered body, then return to the application.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/intelligence.py

### Resolution
- **Resolved**: 2026-08-24T12:03:00+08:00
- **Notes**: Use direct browser navigation for the read-only history endpoint.

---

## [ERR-20260824-026] browser_evaluate_encode_uri

**Logged**: 2026-08-24T12:01:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The browser sandbox did not expose `encodeURIComponent` inside an evaluated page callback used to read monitor history.

### Error
```
TypeError: encodeURIComponent is not a function
```

### Context
- The monitor ID came from a server-generated UUID data attribute and contains only safe UUID characters.
- The UI run-now action completed before the history-read callback failed.

### Suggested Fix
For a previously validated UUID, concatenate the ID directly in the local test request; keep normal application code URL-encoding identifiers.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-24T12:01:00+08:00
- **Notes**: Continue the read-only history check with the validated UUID value directly.

---

## [ERR-20260824-025] fastapi_monitor_run_limit_parameter

**Logged**: 2026-08-24T11:52:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
The first monitor-history endpoint draft used a Pydantic `Field` for a non-body FastAPI parameter, which prevented application startup.

### Error
```
AssertionError: non-body parameters must be in path, query, header or cookie: limit
```

### Context
- `limit` belongs to the query string for `GET /api/v1/intelligence/monitors/{id}/runs`.
- FastAPI requires `Query`, not the model-oriented `Field`, for this endpoint parameter.

### Suggested Fix
Declare endpoint query constraints with `fastapi.Query`.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/intelligence.py

### Resolution
- **Resolved**: 2026-08-24T11:52:00+08:00
- **Notes**: Replaced `Field` with `Query`; runtime 2026.08.24.13 starts successfully with the scheduler active.

---

## [ERR-20260824-024] zsh_unmatched_dependency_glob

**Logged**: 2026-08-24T11:48:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A dependency-discovery command failed because zsh expands unmatched wildcard arguments before `rg` can inspect them.

### Error
```
zsh:1: no matches found: requirements*.txt
```

### Context
- The command mixed concrete paths with optional wildcard filenames.
- The repository structure was still inspected successfully before the unmatched pattern.

### Suggested Fix
Use `rg --files` to discover dependency manifests first, then pass only resolved paths to content searches.

### Metadata
- Reproducible: yes
- Related Files: backend/requirements.txt, frontend/package.json

### Resolution
- **Resolved**: 2026-08-24T11:48:00+08:00
- **Notes**: Continue with manifest discovery through `rg --files`.

---

## [ERR-20260824-023] semantic_search_missing_oci_returns_500

**Logged**: 2026-08-24T11:39:00+08:00
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
The legacy securities-research semantic-search endpoint returns HTTP 500 when OCI Grok credentials are not configured.

### Error
```
POST /api/v1/search/semantic ... 500 Internal Server Error
```

### Context
- The securities Grok tab calls `/api/v1/search/global` and `/api/v1/search/semantic` in parallel.
- The UI catches the failure and safely shows `实时查询暂不可用`, with no sources or generated claims.
- The newer intelligence endpoints return HTTP 200 with `status=configuration_required`, so the service contract is inconsistent.

### Suggested Fix
Detect missing OCI configuration before inference and return the same structured `configuration_required` response used by the new intelligence endpoints, or use an explicit non-500 configuration status consistently.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/search.py, frontend/public/assets/app.js

---

## [ERR-20260824-022] browser_mobile_iframe_injection

**Logged**: 2026-08-24T11:34:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The in-app browser sandbox rejected creation of a narrow test iframe for mobile viewport emulation.

### Error
```
TypeError: document.createElement is not a function
```

### Context
- Browser evaluation can read DOM-backed state but does not expose arbitrary DOM mutation APIs.
- The tab API also does not expose a viewport-resize method.

### Suggested Fix
Use a real device/emulated viewport in a browser runner when pixel-level responsive regression is required; in this session, validate responsive CSS breakpoints and navigation logic statically.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.css, frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-24T11:34:00+08:00
- **Notes**: Switched to static responsive-rule and accessibility-contract validation without bypassing the browser sandbox.

---

## [ERR-20260824-021] browser_hidden_plan_control

**Logged**: 2026-08-24T11:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The browser acceptance check tried to click the first plan-start control while its containing view was not visibly active.

### Error
```
Playwright selector deadline exceeded: no visible match for [data-action="start-plan"]
```

### Context
- The DOM contained a matching control, but Playwright correctly reported it as hidden.
- Selecting the first global match was too broad for a multi-view single-page application.

### Suggested Fix
Confirm `#view-plans.view.active` first and scope the selector to the active plans view.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html, frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-24T11:25:00+08:00
- **Notes**: Continue with an active-view-scoped selector after checking the current navigation state.

---

## [ERR-20260824-020] browser_exact_accessible_name

**Logged**: 2026-08-24T11:18:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The browser acceptance check could not click the securities-research navigation item using an exact accessible-name match.

### Error
```
Playwright selector deadline exceeded: button[name="证券研究" exact]
```

### Context
- The navigation button also contains a visible keyboard shortcut (`⌘ K`), so its computed accessible name is not exactly `证券研究`.
- The control is present; only the overly strict test selector failed.

### Suggested Fix
Use the stable `data-view="research"` selector for navigation controls that include shortcut or badge text.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html, frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-24T11:18:00+08:00
- **Notes**: Continued browser validation with the stable data-view selector.

---

## [ERR-20260824-019] risk_management_stop_loss_contract

**Logged**: 2026-08-24T11:05:00+08:00
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
RiskManagementService.calculate_stop_loss crashes when called with the string value used by the repository test contract.

### Error
```
AttributeError: 'str' object has no attribute 'value'
```

### Context
- `backend/tests/test_services.py` passes `stop_loss_type="percentage"`.
- The service compares against a `StopLossType` enum but then unconditionally serializes `stop_loss_type.value`.
- The method signature is internal today, but the test documents string compatibility as intended behavior.

### Suggested Fix
Normalize string inputs with `StopLossType(stop_loss_type)` at the method boundary, reject invalid values explicitly, and keep enum serialization stable.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/risk_management_service.py, backend/tests/test_services.py

---

## [ERR-20260824-018] missing_test_runtime

**Logged**: 2026-08-24T11:04:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
The bundled backend environment lacks pytest and the frontend has no installed node_modules, so repository test runners cannot start.

### Error
```
backend/venv/bin/python: No module named pytest
frontend-node-modules-missing
```

### Context
- Python AST validation passed for all 66 backend source files.
- The live FastAPI runtime and static browser UI are already running with their application dependencies.
- Installing new test dependencies was outside the non-mutating validation scope.

### Suggested Fix
Add development/test dependencies to a reproducible lockfile or test image. Until then, run equivalent native assertions plus live API and browser contract checks.

### Metadata
- Reproducible: yes
- Related Files: backend/tests/test_services.py, backend/requirements.txt, frontend/package.json

### Resolution
- **Resolved**: 2026-08-24T11:04:00+08:00
- **Notes**: Replaced unavailable test runners with native service assertions, complete backend AST parsing, JavaScript syntax checks, live API contracts, and end-to-end browser verification.

---

## [ERR-20260824-017] mktemp_validation_database

**Logged**: 2026-08-24T11:02:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The managed read-only environment blocked creation of a temporary directory for an isolated validation database.

### Error
```
mktemp: mkdtemp failed ... Operation not permitted
```

### Context
- Full legacy integration tests include model creation and user-profile import/update operations.
- A temporary database was requested specifically to avoid changing existing user data.
- No test that mutates the current database was started.

### Suggested Fix
Run pure service tests normally, use in-memory database initialization inside one process for contract checks, and restrict live validation to read-only or non-persistent endpoints.

### Metadata
- Reproducible: yes
- Related Files: backend/tests/test_integration.py, backend/app/core/database.py

### Resolution
- **Resolved**: 2026-08-24T11:02:00+08:00
- **Notes**: Switched to non-mutating service tests, in-memory API checks, and live read-only/browser verification.

---

## [ERR-20260824-016] git_diff_check

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The final diff audit assumed the project directory was a Git worktree, but it has no `.git` metadata.

### Error
```
fatal: not a git repository (or any of the parent directories): .git
```

### Context
- Product files and the local server are present and working.
- `git diff --check`, status, and stat cannot be used without repository metadata.

### Suggested Fix
Use direct syntax, conflict-marker, duplicate-ID, endpoint, and browser checks for this workspace.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html, frontend/public/assets/app.js, backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Replaced the Git audit with repository-independent validation.

---

## [ERR-20260824-014] browser_locator_input_value

**Logged**: 2026-08-24T10:52:36+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The browser locator wrapper did not expose Playwright's `inputValue()` convenience method during final test cleanup.

### Error
```
globalThis.platformTab.playwright.getByLabel(...).inputValue is not a function
```

### Context
- Navigation and page reset had already completed before the unsupported read call.
- The failure only affected the cleanup assertion output.

### Suggested Fix
Use the browser wrapper's supported `getAttribute('value')` or DOM-backed text/property inspection.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T10:52:36+08:00
- **Notes**: Confirmed the reset state with supported locator inspection; no test input persisted.

---

## [ERR-20260824-013] git_status

**Logged**: 2026-08-24T10:38:41+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Repository-diff checks were attempted in a project directory that is not a Git worktree.

### Error
```
fatal: not a git repository (or any of the parent directories): .git
```

### Context
- Static, API, and browser checks had already succeeded.
- The optional final diff/status check assumed Git metadata was present.
- A broad `sk-` credential heuristic also produced benign matches inside ordinary words.

### Suggested Fix
Detect the worktree before Git checks and use a stricter credential pattern or inspect only configuration/code assignment sites.

### Metadata
- Reproducible: yes
- Related Files: backend/.env.example, frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T10:38:41+08:00
- **Notes**: Continued with direct syntax, endpoint, browser, version, and targeted credential checks; no Git-based verification is required for this directory.

---

## [ERR-20260824-012] exec_command

**Logged**: 2026-08-24T10:38:41+08:00
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
A multi-check validation command used repository-root paths while its working directory was already `backend/`.

### Error
```
no such file or directory: backend/venv/bin/python
Cannot find module 'backend/frontend/public/assets/app.js'
FileNotFoundError: backend/app/main_ui.py
```

### Context
- The command was intentionally run from the backend directory for imports.
- Virtualenv, frontend, and Python source paths were not adjusted to that working directory.

### Suggested Fix
Use `venv/bin/python`, `../frontend/...`, and `app/...` from the backend working directory.

### Metadata
- Reproducible: yes
- Related Files: backend/venv/bin/python, frontend/public/assets/app.js
- See Also: ERR-20260821-002

### Resolution
- **Resolved**: 2026-08-24T10:38:41+08:00
- **Notes**: Re-ran with paths resolved relative to the declared backend working directory.

---

## [ERR-20260824-011] apply_patch

**Logged**: 2026-08-24T10:38:41+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
A compatibility-fallback refactor patch used an imprecise context line and was rejected without changing the file.

### Error
```
apply_patch verification failed: Failed to find expected lines in backend/app/services/oci_responses_service.py
```

### Context
- The patch tried to replace the static fallback sequence with rejection-specific tool removal.
- The intended code used a slightly different metadata block delimiter than the live file.

### Suggested Fix
Read the exact method slice and replace one contiguous block with matching context.

### Metadata
- Reproducible: no
- Related Files: backend/app/services/oci_responses_service.py

### Resolution
- **Resolved**: 2026-08-24T10:38:41+08:00
- **Notes**: Re-read the exact method and applied the refactor using a smaller contiguous replacement.

---

## [ERR-20260824-010] exec_command

**Logged**: 2026-08-24T10:38:41+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
A combined inspection command stopped when the optional AGENTS.md/CLAUDE.md search returned no matches.

### Error
```
The command exited before reading the requested source files because `rg` returned exit code 1 for an empty optional search.
```

### Context
- The command chained an optional repository-guidance lookup with mandatory file reads.
- No guidance file was present, which is a valid state, but `&&` treated it as a blocker.

### Suggested Fix
Run optional discovery and mandatory reads independently, or explicitly tolerate the optional empty result.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/oci_responses_service.py, backend/app/services/institutional_intelligence_service.py

### Resolution
- **Resolved**: 2026-08-24T10:38:41+08:00
- **Notes**: Continued with independent file reads and will not chain optional discovery to required inspection.

---

## [ERR-20260824-015] backend_import_check

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The institutional-intelligence service check ran from the repository root, where the backend `app` package is not on the import path.

### Error
```
ModuleNotFoundError: No module named 'app'
```

### Context
- The syntax checks completed successfully before the import check.
- The backend package root is `backend/`, while the command used the repository root as its working directory.

### Suggested Fix
Run backend import and service checks with `backend/` as the working directory.

### Metadata
- Reproducible: yes
- Related Files: backend/app/api/intelligence.py, backend/app/services/institutional_intelligence_service.py
- See Also: ERR-20260821-002

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Re-ran the check from the backend package root.

---

## [ERR-20260824-014] py_compile

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Python bytecode compilation could not write its cache file in the read-only workspace.

### Error
```
[Errno 1] Operation not permitted: 'backend/app/__pycache__/main_ui.cpython-314.pyc.4340237296'
```

### Context
- The command used `python3 -m py_compile backend/app/main_ui.py` as a syntax check.
- The source file was readable, but `py_compile` attempted to create a `.pyc` cache file.

### Suggested Fix
Use `ast.parse` for syntax-only validation when the workspace is read-only.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py
- See Also: ERR-20260824-004

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Replaced the bytecode-producing check with an in-memory AST parse.

---

## [ERR-20260824-013] browser-control

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The browser backend did not resolve a wrapped `<select>` through its visible label text.

### Error
```
locator.selectOption failed for internal:label="界面主题": no_matches
```

### Context
- Text inputs inside the same form were resolved by labels.
- The theme select has a stable `platform-brand-theme` ID.
- No brand configuration was submitted before the failure.

### Suggested Fix
Use the stable ID locator for this select and keep the visible label for accessibility review.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Continued the brand test with `#platform-brand-theme`.

---

## [ERR-20260824-012] exec_command

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
A mixed frontend/backend static-check command used repository-relative paths while its working directory was already `backend`.

### Error
```
Cannot find module .../backend/frontend/public/assets/app.js
no such file or directory: backend/venv/bin/python
AssertionError for included API route
```

### Context
- Frontend checks require the repository root as working directory.
- Backend imports require the backend directory or an explicit package path.
- This FastAPI build retains included routers internally, so direct `app.routes` path assertions are incomplete.

### Suggested Fix
Run root-relative static checks from the repository root, run imports separately from `backend`, and verify included router endpoints with HTTP requests.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.js, backend/app/api/platform.py
- See Also: ERR-20260824-006, ERR-20260824-007, ERR-20260821-002

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Split frontend static checks, backend imports, and live endpoint verification by working directory.

---

## [ERR-20260824-011] zsh_glob

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
An optional OpenSpec glob was expanded by zsh before the loop could test whether files existed.

### Error
```
zsh: no matches found: openspec/specs/*/*.md
```

### Context
- The project stores specs under `openspec/changes/`, not `openspec/specs/`.
- The command mixed an optional glob into a shell loop.

### Suggested Fix
Use `rg --files openspec` to enumerate actual Markdown files, then read explicit paths.

### Metadata
- Reproducible: yes
- Related Files: openspec/changes/quant-trading-advisor/design.md
- See Also: ERR-20260821-005

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Continued discovery using the existing file list returned by `rg --files`.

---

## [ERR-20260824-004] read_only_heredoc

**Logged**: 2026-08-24T09:24:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A read-only sandbox could not create the temporary file needed for a shell heredoc used in a dependency import check.

### Error
```
zsh: can't create temp file for here document: operation not permitted
```

### Context
- The source import audit completed, but the final virtual-environment check used a heredoc.
- The check was diagnostic and did not modify product files.

### Suggested Fix
Use a single-line `python -c` command for read-only import checks in restricted environments.

### Metadata
- Reproducible: yes
- Related Files: backend/venv

### Resolution
- **Resolved**: 2026-08-24T09:24:00+08:00
- **Notes**: Switched subsequent checks to inline commands.

---

## [ERR-20260824-010] browser-control

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The in-app browser backend rejected the `networkidle` load-state option.

### Error
```
playwright_wait_for_load_state does not support networkidle
```

### Context
- Navigation to the local app had already completed.
- The generic API type advertises `networkidle`, but this browser backend supports a smaller load-state set.

### Suggested Fix
Use `domcontentloaded`, then verify page readiness through visible DOM state.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Continued QA with DOM readiness and explicit visible-element checks.

---

## [ERR-20260824-009] browser-control

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The browser QA attempt used an unsupported tab-creation method.

### Error
```
browser.tabs.create is not a function
```

### Context
- The persistent browser binding was healthy but had no open tabs.
- The current browser-client version exposes a different new-tab operation.

### Suggested Fix
Read the selected browser's current documentation and use its documented tab API.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Switched browser QA to the documented page-opening method.

---

## [ERR-20260824-008] start-ui.sh

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: startup

### Summary
An unbraced shell variable immediately followed by Chinese full-width punctuation was parsed as a longer identifier.

### Error
```
./start-ui.sh: line 42: LISTENER_PID…: unbound variable
```

### Context
- The script runs with `set -u`.
- `$LISTENER_PID` was immediately followed by `）` in a localized status message.
- The script exited before terminating or restarting any process.

### Suggested Fix
Always brace shell variables adjacent to non-ASCII punctuation: `${LISTENER_PID}`.

### Metadata
- Reproducible: yes
- Related Files: start-ui.sh

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Braced the listener PID variable before the full-width punctuation.

---

## [ERR-20260824-007] exec_command

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The route assertion assumed every FastAPI route registry item exposed a `path` attribute.

### Error
```
AttributeError: '_IncludedRouter' object has no attribute 'path'
```

### Context
- Importing `app.main_ui` succeeded.
- The installed FastAPI version includes an internal router item in `app.routes`.
- A sandboxed `ps` detail check in the same diagnostic command was also denied; `lsof` still confirmed the listener.

### Suggested Fix
Filter route entries with `getattr(route, "path", None)` and use the already verified listener metadata for restart.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Updated the assertion to tolerate internal non-path route objects.

---

## [ERR-20260824-006] exec_command

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The FastAPI import check was launched from the repository root without setting the backend package path.

### Error
```
ModuleNotFoundError: No module named 'app'
```

### Context
- The `app` package lives under `backend/`.
- The syntax check passed; only the import-check working directory was wrong.

### Suggested Fix
Run application import checks with `backend` as the working directory and use `venv/bin/python`.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py
- See Also: ERR-20260821-002

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Reran the import and route check from the backend directory.

---

## [ERR-20260824-005] apply_patch

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
An atomic patch tried to delete and add the same script path in one operation.

### Error
```
apply_patch verification failed: invalid patch: multiple operations target .../start-ui.sh
```

### Context
- The startup scripts needed full-content replacement.
- `apply_patch` rejects multiple file operations targeting the same path in one patch.

### Suggested Fix
Use a single `Update File` hunk for an existing file, or split delete/add into separate calls.

### Metadata
- Reproducible: yes
- Related Files: start-ui.sh, start.sh, start-dev.sh

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Reissued the changes as one update operation per existing file.

---

## [ERR-20260824-003] browser_local_asset_inspection

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Two browser-side shortcuts for inspecting a localhost JavaScript asset were unavailable, and one outer script referenced a variable that only existed inside the persistent browser session.

### Error
```
net::ERR_BLOCKED_BY_CLIENT
TypeError: fetch is not a function
ReferenceError: viewportCap is not defined
```

### Context
- Direct navigation to `/assets/app.js` was blocked by the in-app browser.
- The browser's read-only page evaluation scope does not expose `fetch`.
- A browser-session capability variable was accidentally referenced in the outer orchestration isolate.

### Suggested Fix
Use an approved localhost `curl` read to inspect served assets, keep browser-session variables inside the browser tool call, and use visible DOM plus server access logs to verify interactions.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.js

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Verified the served asset with localhost curl and confirmed the screener requests through server logs and visible results.

---

## [ERR-20260824-002] git_diff_check

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Repository diff checks were requested in a project directory that is not a Git worktree.

### Error
```
fatal: not a git repository (or any of the parent directories): .git
```

### Context
- JavaScript syntax validation completed successfully before the Git-only checks.
- The project directory has no `.git` metadata, so `git diff --check`, `git diff --stat`, and `git status` are unavailable.

### Suggested Fix
Detect `.git` before running repository checks; use direct syntax, import, and browser verification for unpacked source directories.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.js, frontend/public/index.html, frontend/public/assets/app.css

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Continue with direct file and runtime checks instead of Git-dependent validation.

---

## [ERR-20260821-001] apply_patch

**Logged**: 2026-08-21T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
`apply_patch` rejects a patch that deletes and re-adds the same file in one operation.

### Error
```
apply_patch verification failed: invalid patch: multiple operations target .../frontend/public/index.html
```

### Context
- Attempted to replace a large static HTML file with `Delete File` and `Add File` directives in one patch.
- The original file remained unchanged.

### Suggested Fix
Use a single `Update File` directive, or delete and add the file in separate tool calls.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html

### Resolution
- **Resolved**: 2026-08-21T00:00:00+08:00
- **Notes**: Switched to separate delete and add operations.

---

## [ERR-20260824-001] apply_patch

**Logged**: 2026-08-24T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
An HTML replacement targeted a fragment as though it were a complete line, but the page stores the whole Discover section on one compressed line.

### Error
```
apply_patch verification failed: Failed to find expected lines in frontend/public/index.html
```

### Context
- Attempted to replace two checkbox labels inside the compressed Discover section.
- The exact text existed, but additional markup shared the same physical line.

### Suggested Fix
Inspect the numbered source line first, then replace the complete line or use a smaller patch boundary anchored by separately formatted lines.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html
- See Also: ERR-20260821-001, ERR-20260821-003

### Resolution
- **Resolved**: 2026-08-24T00:00:00+08:00
- **Notes**: Re-inspected the exact compressed line before retrying with a complete-line patch.

---

## [ERR-20260821-006] node_check_path

**Logged**: 2026-08-21T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A frontend syntax check used a root-relative path from the backend working directory.

### Error
```
Cannot find module '.../backend/frontend/public/assets/app.js'
```

### Context
- The Python checks in the same command intentionally ran from `backend/`.
- The JavaScript path was not adjusted for that working directory.

### Suggested Fix
Group checks by working directory or resolve every path against the declared workdir.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/assets/app.js
- See Also: ERR-20260821-002

### Resolution
- **Resolved**: 2026-08-21T00:00:00+08:00
- **Notes**: Re-run the JavaScript check from the project root.

---

## [ERR-20260821-005] zsh_glob

**Logged**: 2026-08-21T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
An unquoted optional `.env*` path was expanded by zsh before `rg` ran.

### Error
```
zsh:1: no matches found: backend/.env*
```

### Context
- The command attempted to search optional environment files alongside source files.

### Suggested Fix
Use `find` for optional files or quote glob patterns passed to search tools.

### Metadata
- Reproducible: yes
- Related Files: backend/app/core/config.py

### Resolution
- **Resolved**: 2026-08-21T00:00:00+08:00
- **Notes**: Re-run the search against existing directories and use `find` for environment files.

---

## [ERR-20260821-004] curl_local_service

**Logged**: 2026-08-21T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
A sandboxed shell could not reach a local server started with elevated network permissions.

### Error
```
curl: (7) Failed to connect to 127.0.0.1 port 8000
```

### Context
- The Uvicorn process was running and had already been verified through the in-app browser.
- The default sandbox network namespace could not connect to the elevated local listener.

### Suggested Fix
Run the final localhost curl check with the same approved network scope as the server.

### Metadata
- Reproducible: yes
- Related Files: backend/app/main_ui.py

### Resolution
- **Resolved**: 2026-08-21T00:00:00+08:00
- **Notes**: The approved localhost check returned the API status, HTML shell, and JavaScript asset successfully.

---

## [ERR-20260821-003] apply_patch

**Logged**: 2026-08-21T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
A multi-file patch contained a stray empty hunk marker before the next file directive.

### Error
```
apply_patch verification failed: invalid hunk ... Unexpected line found in update hunk
```

### Context
- A small HTML and CSS adjustment was grouped into one patch.
- An extra `@@` left the parser inside an incomplete hunk.

### Suggested Fix
Keep every hunk complete and omit empty `@@` markers; for tiny unrelated files, use separate patches.

### Metadata
- Reproducible: yes
- Related Files: frontend/public/index.html, frontend/public/assets/app.css
- See Also: ERR-20260821-001

### Resolution
- **Resolved**: 2026-08-21T00:00:00+08:00
- **Notes**: Apply the two small updates separately.

---

## [ERR-20260821-002] exec_command

**Logged**: 2026-08-21T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The local-server check used a repository-relative virtualenv path after already changing the working directory to `backend`.

### Error
```
/opt/homebrew/opt/python@3.14/bin/python3.14: No module named uvicorn
```

### Context
- Working directory was already `backend/`.
- The command checked `backend/venv/bin/python`, missed the existing `venv/bin/python`, and fell back to system Python.

### Suggested Fix
Resolve command paths relative to the declared working directory before executing.

### Metadata
- Reproducible: yes
- Related Files: backend/venv/bin/python

### Resolution
- **Resolved**: 2026-08-21T00:00:00+08:00
- **Notes**: Use `venv/bin/python` from the backend working directory.

---
## [ERR-20260824-054] sandboxed_heredoc_and_git_probe

**Logged**: 2026-08-24T16:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The dependency probe used a shell heredoc that required a blocked temporary file, then requested Git status from a directory without repository metadata.

### Error
```
zsh:1: can't create temp file for here document: operation not permitted
fatal: not a git repository (or any of the parent directories): .git
```

### Context
- Checked PDF Python dependencies, renderer availability, fonts, and workspace state.
- The managed read-only command environment does not allow zsh heredoc temporary files.
- This workspace copy has no Git metadata at the selected project root.

### Suggested Fix
Use `python -c` for short dependency probes and treat Git status as unavailable when `.git` is absent.

### Metadata
- Reproducible: yes
- Related Files: backend/requirements.txt
- See Also: ERR-20260824-004, ERR-20260824-034

### Resolution
- **Resolved**: 2026-08-24T16:12:00+08:00
- **Notes**: Switched subsequent checks to single-line Python commands and filesystem-aware validation.

---
## [ERR-20260825-069] apply_patch_mixed_assumption

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: implementation

### Summary
A grouped patch assumed a duplicate event binding and a deployment-script command that were not present in the current files.

### Error
```
apply_patch verification failed: Failed to find expected lines in frontend/public/assets/app.js
```

### Context
- The earlier inspection output overlapped two ranges and made one event binding appear duplicated.
- The deployment script did not contain the assumed Gunicorn line.

### Suggested Fix
Confirm exact matches with a focused search, then apply only verified hunks.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Rechecked the exact files and split the verified changes into a smaller patch.

---
## [ERR-20260825-070] duplicate_env_example_keys

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: configuration

### Summary
The authentication example patch added three keys that were already present immediately below the matched context.

### Error
```
AUTH_COOKIE_SECURE, AUTH_MAX_ATTEMPTS, and AUTH_LOCKOUT_MINUTES appeared twice.
```

### Suggested Fix
Inspect the whole configuration block before appending adjacent settings, then remove duplicate keys immediately.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Removed the duplicate example entries and retained one canonical authentication block.

---
## [ERR-20260825-071] relative_sqlite_path_after_absolute_env_loading

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: tests

### Summary
Loading `backend/.env` reliably exposed that its relative SQLite URL was still resolved against the caller's working directory.

### Error
```
sqlite3.OperationalError: unable to open database file
```

### Context
- Tests were launched from the repository root.
- `DATABASE_URL=sqlite:///./data/quant_advisor.db` therefore pointed at a non-existent root-level data directory instead of `backend/data`.

### Suggested Fix
Normalize relative SQLite URLs against the backend directory during settings validation so launch directory does not alter storage location.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Added deterministic relative SQLite URL normalization and scheduled the regression runner for another full pass.

---
## [ERR-20260825-072] live_server_not_running_before_browser_qa

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: runtime

### Summary
The previously running local UI process was no longer listening when final browser verification began.

### Error
```
curl: (7) Failed to connect to 127.0.0.1 port 8000
```

### Context
- The earlier long-running development session had ended before this implementation pass completed.
- The follow-on JSON probe consequently received no response.

### Suggested Fix
Probe the port before browser QA and start a fresh persistent application process when it is unavailable.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Started a new persistent server process before continuing functional and responsive browser checks.

---
## [ERR-20260825-073] sandbox_localhost_probe_denied

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: runtime

### Summary
A sandboxed localhost probe reported connection failure even though the persistent server process was healthy.

### Error
```
curl: (7) Failed to connect to 127.0.0.1 port 8000
```

### Context
- The server session continued producing scheduler output.
- The same probe succeeded immediately with approved local network access.

### Suggested Fix
Use escalated localhost access for runtime verification in the restricted desktop sandbox after confirming the server session is alive.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: The approved probe confirmed HTTP 303 login redirection, healthy runtime 2026.08.25.19 and operational authentication readiness.

---
## [ERR-20260825-074] stale_in_app_browser_tab_binding

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: browser-qa

### Summary
The persisted in-app browser variable referred to a tab that had been closed since the earlier verification pass.

### Error
```
Unknown tab: 8
```

### Suggested Fix
List current browser tabs and rebind the page object before navigation when a persisted binding is stale.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Rebound browser verification to the current tab and continued without creating unnecessary windows.

---
## [ERR-20260825-075] password_label_browser_locator_ambiguous

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: browser-qa

### Summary
The login password field and its show-password button both matched the broad accessible-label locator.

### Error
```
strict mode violation: getByLabel('密码') resolved to 2 elements
```

### Suggested Fix
Use the exact textbox role/name exposed by the browser accessibility snapshot for the password input.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Switched to the unique textbox locator and continued the same login flow.

---
## [ERR-20260825-076] transient_user_menu_closed_between_browser_steps

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: browser-qa

### Summary
The logout control is a semantic `menuitem`, so a locator restricted to the `button` role could not match it.

### Error
```
Playwright selector deadline exceeded: no visible button named 退出登录
```

### Suggested Fix
Use the `menuitem` role exposed by the accessibility snapshot, then verify the redirected login page.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Confirmed the popover was visible and switched to the correct `menuitem` locator.

---
## [ERR-20260825-077] pytest_not_installed_in_ui_virtualenv

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The optional Pytest runner is not installed in the lightweight UI virtual environment.

### Error
```
No module named pytest
```

### Context
- The repository includes a dependency-free `unittest` regression runner specifically for the UI environment.
- That runner already completed all eight login, security, PDF, monitoring, model and status checks successfully.

### Suggested Fix
Keep the dependency-free runner as the local acceptance gate, or add Pytest to a dedicated development requirements file when a Pytest-only workflow is required.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: No runtime dependency was added; verification relies on the successful 8/8 operational hardening suite plus browser and OpenSpec checks.

---
## [ERR-20260825-078] docker_context_would_include_local_env

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: security

### Summary
The repository had no Docker ignore file, so a root-context image build could copy `backend/.env` into an image layer.

### Context
- The Dockerfile copies the entire backend directory.
- Git ignore does not protect Docker build context or image layers.

### Suggested Fix
Exclude local environment files, virtual environments, databases, reports and caches from the Docker context, and inject `.env` only at container runtime.

### Resolution
- **Resolved**: 2026-08-25T00:00:00+08:00
- **Notes**: Added a root `.dockerignore` and declared `backend/.env` as a runtime Compose environment file; explicit Compose database and cache values retain precedence.

---
## [ERR-20260825-081] combined_history_event_workspace_patch_context

**Logged**: 2026-08-25T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
A combined `apply_patch` for history click handlers and workspace switching did not match the current `selectWorkspace` context.

### Error
```
apply_patch verification failed: Failed to find expected lines ... function selectWorkspace(id)
```

### Context
- The patch attempted two unrelated insertions in one operation.
- No hunk was applied and no file content was damaged.

### Resolution
- **Resolved**: 2026-08-25T13:03:00+08:00
- **Notes**: Located the current line ranges and applied the event-handler and workspace-switch changes as separate successful patches.

---

## [ERR-20260825-082] combined_chinese_prompt_patch_context

**Logged**: 2026-08-25T13:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
A combined replacement of three long Grok prompt templates did not match the current geopolitical JSON example.

### Error
```
apply_patch verification failed while matching the geopolitical prompt block
```

### Context
- The failed operation bundled realtime, project-risk, and geopolitical prompt rewrites.
- No hunk was applied and the earlier system-prompt changes remain intact.

### Suggested Fix
Read the exact current prompt line ranges and replace each workflow prompt in a separate patch.

### Metadata
- Reproducible: yes
- Related Files: backend/app/services/institutional_intelligence_service.py

### Resolution
- **Resolved**: 2026-08-25T16:52:00+08:00
- **Notes**: Re-read the exact prompt ranges and applied the three Chinese workflow templates successfully in a scoped patch.

---
## [ERR-20260825-079] browser_history_restore_selector_timeout

**Logged**: 2026-08-25T13:08:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
The first browser assertion after clicking a history record timed out while reading `#realtime-query`.

### Error
```
Timed out after 3000ms evaluating selector #realtime-query: Playwright selector deadline exceeded
```

### Context
- The history list and test record were visible before the click.
- The click may have triggered page movement while the immediate multi-assertion call was running.

### Resolution
- **Resolved**: 2026-08-25T13:09:00+08:00
- **Notes**: A fresh DOM snapshot showed that the click had succeeded: the saved query, keywords, source selection, summary, source ledger, audit ribbon, and enabled PDF button were all restored. The timeout was limited to the immediate selector assertion during smooth page movement; no product fix was required.

---
## [ERR-20260825-080] browser_history_pdf_download_event_timeout

**Logged**: 2026-08-25T13:09:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
Browser QA timed out waiting for a native download event after clicking `导出当时记录`.

### Error
```
Timed out after 20000ms waiting for download.
```

### Context
- Historical result restoration was already visibly successful.
- The frontend fetches the PDF as a Blob and triggers an object-URL anchor, which may not surface through the browser automation download event.

### Resolution
- **Resolved**: 2026-08-25T13:10:00+08:00
- **Notes**: The application made the expected history PDF request, received HTTP 200 with a 112,288-byte PDF, and wrote the `export_history_pdf` audit event. The browser automation layer did not expose the programmatic Blob/object-URL download as a native download event; the endpoint and UI action were both functional.

---
