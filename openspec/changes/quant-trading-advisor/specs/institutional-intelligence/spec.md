## ADDED Requirements

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

#### Scenario: Production scheduler is configured

- **WHEN** the monitoring schedule runs in a multi-worker production workspace
- **THEN** execution uses a distributed lease or equivalent single-run guarantee rather than one independent loop per worker
- **AND** the system deduplicates events, compares the new evidence snapshot to the prior version, applies workspace thresholds, and routes material changes to human review
