## ADDED Requirements

### Requirement: Portfolio-aware conditional plan
The system SHALL transform approved signals into portfolio-aware stages subject to current holdings, cash, concentration, correlation, turnover, liquidity and risk-budget constraints.

#### Scenario: Signal conflicts with concentration limit
- **WHEN** a positive signal would breach a hard concentration limit
- **THEN** the proposed size is reduced or rejected, and the violated rule is shown

### Requirement: Explainable immutable recommendation
The system SHALL bind each recommendation version to its as-of snapshot, profile, portfolio, strategy, concrete immutable model version, feature set, risk policy and evidence, and SHALL include assumptions, confidence, counter-evidence, validity and invalidation conditions.

#### Scenario: New information changes the recommendation
- **WHEN** reevaluation produces a different plan
- **THEN** the system creates a linked new version and does not overwrite the previous plan

#### Scenario: Model routing alias changes during generation
- **WHEN** a mutable champion or rollback alias is reassigned after a plan job starts
- **THEN** the job continues with the concrete version resolved at start and records that version in the plan

### Requirement: Safe abstention
The system SHALL return `abstain` instead of an actionable stage when required inputs are missing, data or models are unhealthy, compliance mode disallows personalization or a hard risk rule fails.

#### Scenario: Approved model becomes unhealthy
- **WHEN** drift or runtime monitoring disables the model and no approved baseline applies
- **THEN** plan generation stops, the reason is explained and the event is audited

### Requirement: Social evidence cannot independently drive action
The system SHALL treat Grok/X Search trends and public statements as supporting evidence and SHALL NOT create or size an actionable stage solely from social sentiment, a single account or an unverified claimed trade.

#### Scenario: Influential account posts a strong buy statement
- **WHEN** no approved independent market, issuer, regulatory or licensed-news evidence supports the statement
- **THEN** the system may show it in research context but does not create an actionable stage from it

### Requirement: Advice-only execution boundary
The MVP SHALL require user acknowledgement for paper tracking and SHALL NOT transmit an order to a broker.

#### Scenario: Stage trigger is met
- **WHEN** a price or time event satisfies an active stage
- **THEN** the system records and notifies a pending paper action without placing a real order
