## ADDED Requirements

### Requirement: Point-in-time research data
The system SHALL store and query market, fundamental, corporate-action and news data by event time, availability time, ingestion time, source and revision so that an as-of result contains only information available at that decision time.

#### Scenario: Financial statement was revised later
- **WHEN** an as-of query predates a revision
- **THEN** the system returns the version available at the requested time and excludes the later revision

### Requirement: Data quality and provenance
The system SHALL show source, as-of time, freshness, license class and quality state for material evidence and SHALL block dependent action plans when required data is stale, conflicting or unlicensed.

#### Scenario: Primary and backup sources exceed tolerance
- **WHEN** a required field differs beyond its configured tolerance
- **THEN** the field is marked degraded, the discrepancy is audited, and dependent advice is not actionable

### Requirement: Normalized research view
The system SHALL present raw and adjusted price context, financial metrics, corporate actions and licensed news or announcements with explicit units, currency, trading calendar and source references.

#### Scenario: Corporate action changes price comparability
- **WHEN** a split, dividend or symbol change affects a requested period
- **THEN** the system identifies the event and distinguishes raw from adjusted values

### Requirement: Governed overseas-securities provider
The system SHALL provide a server-configured overseas-securities adapter that supports global instrument search, normalized quote retrieval and OHLCV history, SHALL keep provider credentials outside browser assets and responses, and SHALL label provider, exchange/MIC, currency, provider time, ingestion time and freshness or entitlement limitations.

#### Scenario: Overseas provider is configured
- **WHEN** an authenticated user searches or requests a supported overseas security
- **THEN** the system calls the configured Twelve Data API, normalizes the response, preserves source provenance, and returns no API credential to the client

#### Scenario: Overseas provider is not configured
- **WHEN** an authenticated user opens provider status or requests overseas market data without `TWELVE_DATA_API_KEY`
- **THEN** status reports `configuration_required`, data endpoints return an explicit configuration error, and no static quote or historical series is substituted

#### Scenario: Provider plan has delayed or unavailable market data
- **WHEN** the configured plan or exchange entitlement cannot provide the requested freshness or market
- **THEN** the system exposes the provider failure or returned freshness limitation and does not label the data as exchange-real-time by default

### Requirement: Derived indicators are reproducible
The system SHALL bind every technical, fundamental or sentiment-derived indicator to its input snapshot, formula/model version and parameters, and SHALL NOT present a single indicator as a guaranteed buy or sell signal.

#### Scenario: User changes an indicator parameter
- **WHEN** the system recalculates the indicator
- **THEN** the result records the new parameter set and preserves the prior result's lineage

### Requirement: Point-in-time instrument universe
The system SHALL version the eligible instrument universe by decision time and SHALL include inactive, delisted, suspended and renamed instruments according to their historical state.

#### Scenario: Current index membership differs from historical membership
- **WHEN** a backtest requests the universe for a past decision time
- **THEN** the system returns the membership known at that time instead of applying today's constituents retroactively

### Requirement: Governed feature definitions
The system SHALL register each formal feature's entity keys, event and availability times, transformation version, window, TTL, missing-value policy and owner, and SHALL build training datasets with point-in-time joins.

#### Scenario: Feature value is newer than the training row
- **WHEN** historical retrieval encounters a value whose availability time is after the row's decision time
- **THEN** the value is excluded and the dataset lineage records the join decision

### Requirement: Training and simulation feature parity
The system SHALL derive formal training, backtest and paper-trading features from the same versioned definitions and SHALL block dependent workflows when critical schema, freshness or skew checks fail.

#### Scenario: Paper feature exceeds its TTL
- **WHEN** a critical feature is older than its registered TTL
- **THEN** the system marks it unavailable and does not silently reuse the last value

### Requirement: OCI Grok real-time intelligence
The system SHALL query approved xAI Grok models through the OCI Generative AI Responses API for real-time social information and SHALL bind each result to the actual model, region, prompt, tool parameters, query window, OCI request/response identifiers and source citations.

#### Scenario: Interactive stock intelligence query
- **WHEN** a user requests current information for a resolved instrument
- **THEN** the system uses the configured Grok real-time capability, returns cited results with publication and retrieval times, and labels the actual model used

#### Scenario: Deep multi-topic research is requested
- **WHEN** the query requires multiple themes, accounts or a long time window
- **THEN** the system may route it to the approved Grok multi-agent capability as a background job that can be retrieved or cancelled

### Requirement: Versioned public-figure tracking
The system SHALL track only explicitly configured public X handles in a versioned watchlist with identity verification, rationale, applicable instruments, approval and validity period.

#### Scenario: User asks to follow a display name with ambiguous accounts
- **WHEN** more than one X handle may belong to the named person or organization
- **THEN** the system requires an approved exact handle and does not infer the identity from the display name alone

### Requirement: Public statement is not a verified trade
The system SHALL classify social claims about buying, selling or holding as `claimed_action` unless an approved authoritative disclosure verifies them, and SHALL preserve post type, citation, publication time and uncertainty.

#### Scenario: Public figure says they bought a stock
- **WHEN** X Search finds the statement but no regulatory filing or other approved disclosure confirms it
- **THEN** the system displays the original citation as an unverified claimed action and does not represent it as an executed trade

### Requirement: Evidence-based trend snapshots
The system SHALL calculate versioned trend snapshots from cited evidence using volume, velocity, independent-source diversity, concentration, novelty, disagreement and suspected coordination indicators instead of a sentiment label alone.

#### Scenario: Apparent trend comes from one repeated post
- **WHEN** most mentions are reposts or near-duplicates from a single origin
- **THEN** the system reduces source-diversity confidence and identifies the concentration in the trend explanation

### Requirement: Real-time intelligence degradation
The system SHALL mark Grok intelligence as `partial`, `unverified` or `unavailable` when citations, entity resolution, freshness, model/region availability, rate limit or quota requirements fail, and SHALL not present expired cached results as current.

#### Scenario: Target Grok model is unavailable in the configured region
- **WHEN** runtime capability discovery cannot resolve the preferred model
- **THEN** the system either uses an approved fallback and discloses its actual identity or returns unavailable without fabricating real-time coverage
