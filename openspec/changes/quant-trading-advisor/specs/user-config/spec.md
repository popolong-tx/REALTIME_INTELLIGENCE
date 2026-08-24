## ADDED Requirements

### Requirement: Versioned investor constraints
The system SHALL capture a versioned investor profile containing target, horizon, investable amount, holdings, liquidity needs, experience, maximum tolerable drawdown, prohibited exposures and notification preferences.

#### Scenario: Profile changes after a plan is generated
- **WHEN** a user updates profile information
- **THEN** the system creates a new profile version and the existing plan continues to reference the original version

### Requirement: Suitability and feasibility gate
The system SHALL assess completeness, internal consistency, product scope and target feasibility before producing a personalized plan.

#### Scenario: Target conflicts with drawdown tolerance
- **WHEN** the requested return and horizon are materially inconsistent with the declared loss tolerance under configured scenarios
- **THEN** the system returns `abstain`, explains the conflict and requests revised constraints without promising a return

### Requirement: Portfolio constraint integrity
The system SHALL validate cash, positions, allocation preferences and prohibited exposures and SHALL compile accepted values into versioned risk-policy inputs.

#### Scenario: Existing holdings exceed a new concentration limit
- **WHEN** the profile assessment detects a current breach
- **THEN** the system identifies the breach and prevents a plan from increasing that exposure

### Requirement: Notification control
The system SHALL allow users to select supported event types, channels and frequency, and SHALL not treat a notification as order authorization.

#### Scenario: Plan stage triggers
- **WHEN** the user opted into the relevant notification
- **THEN** the system sends a notice through an approved channel without executing a trade

### Requirement: Privacy lifecycle
The system SHALL minimize profile data, enforce purpose-based access, audit reads and support configured export, correction, deletion and retention workflows.

#### Scenario: Unauthorized researcher requests raw profile data
- **WHEN** a role without profile access requests identifiable answers
- **THEN** access is denied and the attempt is recorded in the audit log

