## ADDED Requirements

### Requirement: Simplified Chinese intelligence presentation

The system SHALL request and present all user-facing intelligence analysis in Simplified Chinese while preserving evidence identifiers and exact source material that must not be altered.

#### Scenario: Generate a Chinese intelligence result

- **WHEN** Grok runs realtime research, project-risk analysis, geopolitical-financing analysis, semantic research, stock analysis, a trading plan, or a news summary
- **THEN** the initial inference request explicitly requires Simplified Chinese for summaries, trends, judgments, reasons, events, scenarios, recommendations, assumptions, unknowns, and source explanations
- **AND** JSON keys, governed enum codes, URLs, dates, stock symbols, model/tool identifiers, citation identifiers, and necessary proper names may remain unchanged
- **AND** cached responses created before the Chinese-output contract do not override a new Chinese request

#### Scenario: Preserve a non-Chinese X original

- **WHEN** cited X content is returned in a language other than Chinese
- **THEN** `original_text` remains an exact source quotation and is never translated or reconstructed
- **AND** `content_excerpt` provides a separate Simplified Chinese explanation that the UI and PDF display under an explicit Chinese label

#### Scenario: Provider violates the language contract

- **WHEN** the provider still returns English-heavy prose in a user-facing structured field
- **THEN** the server preserves the actual returned content, records the detected-field count and language-compliance state in audit metadata, and does not replace useful analysis with a generic language-error or rerun placeholder
- **AND** language compliance alone does not downgrade an otherwise successful result or instruct the user to repeat an expensive live retrieval
- **AND** the server does not resend the complete analysis to a separate translation request or add facts that were not present in the original result

### Requirement: Multi-source realtime open-information research

The system SHALL accept a topic, keywords and aliases, date range, source channels, result limit, workspace, and X-original-text preference, then query approved Grok research tools while keeping X and public-web results distinguishable.

#### Scenario: Retrieve X and public open information

- **WHEN** an authorized user submits a valid request with both source channels and OCI Grok is configured
- **THEN** the system first requests Web Search, X Search, and Code Interpreter
- **AND** returns a cited executive summary, trend signals, X/public item counts, a source-typed item stream, source ledger, coverage notice, and audit metadata
- **AND** verbatim X text is preserved only when it is returned with a corresponding source rather than reconstructed by the model
- **AND** the result is labelled `best_effort` and never represented as an exhaustive X or web export

#### Scenario: One research tool is incompatible

- **WHEN** the provider explicitly rejects a requested tool with a 400/422 tool-validation error
- **THEN** the system retries with the remaining approved retrieval tools
- **AND** returns `partial` with requested, used, and degraded tools in the audit record
- **AND** does not apply this fallback to authentication, quota, network, or timeout failures

#### Scenario: OCI is not configured for realtime research

- **WHEN** the user submits a realtime research request without a server-side OCI credential
- **THEN** the system returns `configuration_required` with zero X, public, and citation counts
- **AND** does not query external sources or generate placeholder posts, pages, trends, or summaries

### Requirement: Cited project-level risk intelligence

The system SHALL accept a member country, project, financial product, monitoring window, risk dimensions, and decision question, then use the configured OCI Grok real-time model with X and public-web research to produce a project-risk brief.

#### Scenario: Generate a live project-risk brief

- **WHEN** an authorized workspace user submits a valid project-risk request and OCI Grok is configured
- **THEN** the system returns a direct executive assessment, overall risk, political/social/debt/environment/reputation dimensions, cited ground-signal events, review actions, watch items, assumptions, and audit metadata
- **AND** each action states an owner, urgency, observable trigger, and rationale
- **AND** the system does not automatically approve, pause, accelerate, or modify financing

#### Scenario: OCI is not configured

- **WHEN** the user submits the request without a configured OCI credential
- **THEN** the system returns `configuration_required`
- **AND** displays the analysis framework and required configuration
- **AND** does not generate placeholder facts, events, scores, citations, or conclusions

### Requirement: Evidence-status separation

The system SHALL distinguish source-backed facts, reported claims, public opinions, and model inference in all institutional-intelligence outputs.

#### Scenario: X content is returned

- **WHEN** a result is derived from a public X post
- **THEN** it is marked as public and unverified unless independently confirmed
- **AND** it cannot independently trigger a financing action

#### Scenario: No accessible citation is returned

- **WHEN** Grok provides a current factual statement without an accessible source URL
- **THEN** the result evidence quality is `unverified`
- **AND** the UI warns that the fact requires independent verification

### Requirement: Geopolitical financing scenario analysis

The system SHALL analyze geopolitical events and policy changes through explicit causal transmission paths and financing scenarios.

#### Scenario: Generate a structured financing impact analysis

- **WHEN** an authorized user submits an issue, regions, actors, product scope, realtime window, and decision horizon
- **THEN** the system uses the configured Multi-Agent model to produce a direct conclusion, causal paths, baseline/stress/opportunity scenarios, strategy options, stakeholder positions, assumptions, unknowns, and citations
- **AND** each scenario covers project pipeline, co-financing, member borrowing appetite, project feasibility, and risk transfer
- **AND** inference is not represented as an official country or institution position

### Requirement: Auditable workspace boundary

Each institutional-intelligence result SHALL record provider, model, region, query window, tools, generated time, request identifier, and workspace identifier.

#### Scenario: Review a saved brief

- **WHEN** a reviewer opens a project-risk or geopolitical brief
- **THEN** the evidence ledger and audit metadata remain attached to the same immutable analysis version
- **AND** production access is enforced by tenant, workspace, role, source entitlement, and retention policy

### Requirement: Continuous monitoring lifecycle

The system SHALL allow a user to persist workspace-scoped realtime-research and project-risk requests as recurring monitoring tasks.

#### Scenario: Create an interval monitor

- **WHEN** a user saves a valid realtime-information or project-risk scope with an interval of 30 minutes, 1, 2, 4, 6, 8, 12, or 24 hours
- **THEN** the server persists the workspace, workflow, complete request payload, active state, and next-run time
- **AND** the application scheduler executes the saved workflow when it becomes due
- **AND** service restarts do not remove the monitoring definition or its run history

#### Scenario: Operate a saved monitor

- **WHEN** a user opens a saved monitor
- **THEN** the original scope, interval, last status, last result, last-run time, and next-run time are available
- **AND** the user can run it immediately, pause it, resume it, or remove it
- **AND** pausing a task clears its next execution until it is resumed

#### Scenario: OCI is not configured during a scheduled run

- **WHEN** a due monitor executes without a server-side OCI credential
- **THEN** the run is recorded as `configuration_required`
- **AND** its next run remains scheduled
- **AND** no external query, placeholder evidence, or simulated conclusion is generated

#### Scenario: Generate a report for a completed monitor run

- **WHEN** a scheduled or user-triggered saved monitor completes with a `live` or `partial` result and a non-empty analysis
- **THEN** the server generates exactly one immutable PDF artifact from that same stored result without calling Grok again
- **AND** the artifact metadata records the workspace, monitor, run, trigger, workflow, source request identifier, query context, filename, byte size, SHA-256 digest, and generated time
- **AND** the monitor exposes its latest report, run history exposes the report bound to each run, and a workspace-scoped report API lists and downloads the stored artifacts
- **AND** the download verifies the server path, file size, and SHA-256 digest before returning `application/pdf` with no-store caching and an append-only download audit event

#### Scenario: Do not create a misleading scheduled report

- **WHEN** a monitor result is `configuration_required`, failed, empty, or not a supported workflow
- **THEN** the execution status remains truthful and no PDF artifact is created
- **AND** a PDF storage failure does not replace or falsify the already stored intelligence result

#### Scenario: Production scheduler is configured

- **WHEN** the monitoring schedule runs in a multi-worker production workspace
- **THEN** execution uses a distributed lease or equivalent single-run guarantee rather than one independent loop per worker
- **AND** the system deduplicates events, compares the new evidence snapshot to the prior version, applies workspace thresholds, and routes material changes to human review

### Requirement: Governed PDF report export

The system SHALL export completed realtime-research, project-risk, and geopolitical-financing results as server-generated PDF reports without re-running or altering the source analysis.

#### Scenario: Export a completed intelligence result

- **WHEN** a user exports a result whose status is `live` or `partial`
- **THEN** the PDF includes the original query scope, generated time, workflow-specific analysis, evidence ledger, provider/model/tools/request identifier, workspace, limitations, and human-review disclaimer
- **AND** Chinese text, long source links, tables, repeated table headers, section transitions, page numbers, and A4 pagination render legibly
- **AND** the response uses `application/pdf`, a safe download filename, no-store caching, and an append-only export audit event

#### Scenario: Reject a non-result placeholder

- **WHEN** the result is `configuration_required`, empty, oversized, or belongs to a different workflow
- **THEN** the server rejects the export instead of creating a PDF that could be mistaken for completed analysis
- **AND** the page keeps the export action disabled until a real result is available

#### Scenario: Retain scheduled reports in production

- **WHEN** scheduled reports are deployed for institution or custom workspaces
- **THEN** production uses tenant-scoped object storage, retention and legal-hold policies, encryption, backup, lifecycle management, and role-based download authorization
- **AND** the local filesystem artifact store remains explicitly identified as the single-node foundation rather than production-grade archive storage

### Requirement: Immutable analysis history

The system SHALL retain workspace-scoped input and output snapshots for usable realtime-research, project-risk, and geopolitical-impact analyses so a reviewer can reopen or export the exact historical result without re-running Grok.

#### Scenario: Save a completed manual analysis

- **WHEN** an authorized user receives a `live` or `partial` result with a non-empty analysis from any of the three decision-intelligence workflows
- **THEN** the server stores one immutable record containing workflow, workspace, title, trigger, source request identifier, complete query context, complete result, source count, and created time
- **AND** repeated processing of the same workspace/workflow/request identifier does not create a duplicate record
- **AND** `configuration_required`, failed, empty, or oversized results are not stored as completed history

#### Scenario: Save a completed monitor analysis

- **WHEN** a realtime-research or project-risk monitor run returns a usable result
- **THEN** the same history store records its monitor, run, and schedule/manual trigger identifiers in addition to the exact input/output snapshot
- **AND** removing the monitor does not erase its historical analysis record

#### Scenario: Browse and reopen history

- **WHEN** a user opens one of the three intelligence pages
- **THEN** the page lists only that workspace and workflow's recent records without returning the full result in the list payload
- **AND** selecting a record restores its saved form context and complete result into the page without an external query
- **AND** another workspace cannot read the detail by guessing its record identifier

#### Scenario: Export an exact historical snapshot

- **WHEN** a user exports a history item
- **THEN** the server generates the PDF exclusively from that record's stored query context and result
- **AND** the response and append-only audit event identify the historical record and original Grok request
- **AND** no Grok, X Search, Web Search, or Code Interpreter request is made during export
