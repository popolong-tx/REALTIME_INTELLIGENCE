## ADDED Requirements

### Requirement: Workspace-scoped platform context
The system SHALL treat every research asset and operation as belonging to an explicit tenant and workspace context.

#### Scenario: Personal workspace
- **WHEN** an individual enters the platform
- **THEN** the system selects a personal workspace with a lightweight owner policy
- **AND** research, watchlists, plans, models and alerts are attributed to that workspace

#### Scenario: Institution workspace
- **WHEN** a member switches to an institution workspace
- **THEN** the system displays the institution brand, role, policy pack and authorized resources
- **AND** does not expose assets from another workspace

#### Scenario: Missing workspace context
- **WHEN** a protected API request has no trusted `tenant_id`, `workspace_id`, actor and role context
- **THEN** the system rejects the request instead of selecting a permissive default

### Requirement: Server-enforced tenant isolation
The system SHALL enforce tenant isolation in storage, cache, object storage, task execution, secrets and audit records; a client-side workspace selector SHALL NOT be considered an isolation control.

#### Scenario: Cross-tenant identifier reuse
- **WHEN** a user supplies the identifier of a plan, model, snapshot or connector owned by another tenant
- **THEN** the repository layer applies the trusted tenant scope and returns not found or forbidden
- **AND** records a security audit event without leaking the foreign resource metadata

#### Scenario: Cache and asynchronous task isolation
- **WHEN** the system writes cache entries or schedules a background job
- **THEN** all keys, queues, artifacts and callbacks include the trusted tenant and workspace context

### Requirement: Multiple service profiles
The platform SHALL support personal, institution and customer-specific service profiles using one product core and explicit capability flags.

#### Scenario: Personal profile
- **WHEN** a personal profile is active
- **THEN** the primary workflow remains research, simulation plans and review
- **AND** institution administration stays out of the primary navigation

#### Scenario: Institution profile
- **WHEN** an institution profile is active
- **THEN** members, shared research assets, approvals, audit and data entitlements are available according to role

#### Scenario: Customer-specific profile
- **WHEN** a customer-specific profile is provisioned
- **THEN** brand tokens, navigation, allowed connectors, policy pack and deployment settings are versioned configuration
- **AND** core safety and audit controls cannot be removed by branding configuration

### Requirement: Workspace membership and role assignment
The system SHALL separate global identity from workspace membership and allow one identity to hold different roles in different workspaces.

#### Scenario: Role differs by workspace
- **WHEN** a user is an owner in a personal workspace and a viewer in an institution workspace
- **THEN** permissions are evaluated from the active workspace membership, not a global role

#### Scenario: Enterprise identity lifecycle
- **WHEN** an institution enables SSO or SCIM
- **THEN** group membership can map to workspace roles
- **AND** deprovisioning revokes active sessions, connector secrets and workspace access

### Requirement: Versioned extension contracts
The platform SHALL expose versioned contracts for data providers, strategy/model packages, workspace applications and event connectors.

#### Scenario: Provider installation
- **WHEN** an administrator installs a data provider
- **THEN** the platform validates its manifest, normalized schemas, entitlements, secret requirements, health checks and supported markets before activation

#### Scenario: Overseas provider awaits its server-side key
- **WHEN** the Twelve Data connector is installed but `TWELVE_DATA_API_KEY` is absent
- **THEN** the platform manifest and readiness API report `needs_configuration` or `configuration_required`, expose search/quote/history capabilities and the required secret name, and never expose the secret value

#### Scenario: Strategy package installation
- **WHEN** a strategy or model package is registered
- **THEN** it includes an immutable version, required features, evidence schema, risk limits, compatible runtime and governance metadata

#### Scenario: Incompatible extension
- **WHEN** an extension requires an unsupported contract version or forbidden permission
- **THEN** installation is blocked with an actionable compatibility report

### Requirement: Policy packs
The system SHALL support workspace policy packs for approvals, risk limits, permitted data sources, Grok research boundaries, content rules and model lifecycle gates.

#### Scenario: Stricter customer policy
- **WHEN** a customer policy is stricter than the platform default
- **THEN** the stricter effective rule is applied and recorded in the decision audit

#### Scenario: Policy version changes
- **WHEN** a policy pack is updated
- **THEN** existing plans keep the original policy version in their snapshot
- **AND** the system identifies plans that require re-evaluation

### Requirement: White-label configuration
The system SHALL allow safe customer branding through bounded design tokens and content configuration without arbitrary executable code.

#### Scenario: Apply brand configuration
- **WHEN** an authorized administrator changes name, mark, theme or navigation labels
- **THEN** the platform previews and versions the configuration
- **AND** preserves accessibility contrast, risk disclosures and platform safety states

### Requirement: Deployment portability
The platform SHALL define shared-cloud, dedicated-private-cloud and on-premise deployment profiles with explicit responsibility and isolation boundaries.

#### Scenario: Dedicated deployment
- **WHEN** an institution requires a dedicated deployment
- **THEN** database, cache, object storage, network, keys, monitoring and backup ownership are specified before provisioning

#### Scenario: Local platform foundation
- **WHEN** the local demo exposes workspace templates
- **THEN** it labels production isolation, enterprise identity and secret management as pending
- **AND** does not claim those controls are already enforced

### Requirement: Embedded execution remains separately governed
The open platform SHALL keep broker or embedded-investing execution behind a separate licensed, approved and sandbox-first capability boundary.

#### Scenario: Connector is present without execution approval
- **WHEN** a broker adapter is installed but the workspace lacks execution approval
- **THEN** the platform exposes simulation and connectivity health only
- **AND** rejects live order requests

### Requirement: Responsive and task-oriented interface
The product shell and login experience SHALL remain usable in current phone, tablet and desktop browser sizes and SHALL identify each primary page by its user task.

#### Scenario: Phone browser
- **WHEN** the viewport is 680 CSS pixels wide or narrower
- **THEN** navigation moves to an accessible drawer, primary content uses one-column flow, tables remain horizontally reachable and critical controls keep touch-sized targets

#### Scenario: Tablet browser
- **WHEN** the viewport is between phone and desktop breakpoints
- **THEN** the sidebar becomes a drawer and analysis workbenches collapse without clipping forms, results or account controls

#### Scenario: Clear page naming
- **WHEN** a user opens a primary workflow
- **THEN** the first heading names the task, such as “检索实时公开信息” or “监测项目实时风险”
- **AND** supporting copy explains scope and limitations instead of replacing the page name with a slogan

#### Scenario: Readable dense cards
- **WHEN** a dashboard, analysis result, plan, model or connector card displays dense content at default browser zoom
- **THEN** the product applies the shared readable type hierarchy, keeps compact auxiliary labels at or above the platform minimum, and gives titles, primary values and explanatory copy visually distinct sizes
- **AND** increased text size is accommodated through natural card growth, wrapping, responsive stacking or reachable scrolling instead of clipping, overlap or shrinking the content below the minimum
