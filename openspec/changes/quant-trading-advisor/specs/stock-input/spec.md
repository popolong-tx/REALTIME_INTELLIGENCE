## ADDED Requirements

### Requirement: Unique instrument resolution
The system SHALL resolve a query to an internal instrument identifier with exchange, asset type and currency, and SHALL require confirmation when the query is ambiguous.

#### Scenario: Same ticker exists on multiple venues
- **WHEN** a user searches a code that maps to more than one active instrument
- **THEN** the system presents the candidates and does not select one implicitly

#### Scenario: Code format is valid but instrument is inactive or unknown
- **WHEN** the code cannot be resolved for the selected market and date
- **THEN** the system explains the status, may suggest close matches, and does not start analysis

### Requirement: Assisted and batch input
The system SHALL provide name/code auto-completion and batch validation while preserving an independent result for every input.

#### Scenario: Batch contains invalid and ambiguous items
- **WHEN** a user submits multiple codes with mixed resolution states
- **THEN** the system identifies each valid, invalid and ambiguous item and requires correction without discarding valid items

### Requirement: Search history control
The system SHALL maintain user-scoped recent searches only with configured consent and retention, and SHALL allow the user to clear them.

#### Scenario: User clears recent searches
- **WHEN** the user requests history deletion
- **THEN** the user-visible history is removed according to the retention policy and the privacy action is audited

