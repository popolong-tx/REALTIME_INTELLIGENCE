## ADDED Requirements

### Requirement: Approved strategy templates
The system SHALL describe each available template's hypothesis, asset universe, horizon, required data, limitations, baseline and approval state, and SHALL expose only approved templates to recommendation generation.

#### Scenario: User selects an unapproved experiment
- **WHEN** a draft or merely validated model is requested for a plan
- **THEN** the system denies the request and identifies its current governance state

### Requirement: Reproducible experiment
The system SHALL bind every formal experiment to immutable data, feature, code, configuration, environment and random-seed versions.

#### Scenario: Experiment is rerun
- **WHEN** the same bound inputs are rerun in the supported environment
- **THEN** the result is reproducible within documented deterministic tolerances

### Requirement: Preregistered research and complete trial ledger
The system SHALL require a research protocol before formal evaluation and SHALL record every completed, failed, cancelled and manually initiated trial against its declared trial budget.

#### Scenario: Researcher renames an experiment after using the trial budget
- **WHEN** the underlying protocol, hypothesis and test window are unchanged
- **THEN** the trials remain associated with the same research family and the count is not reset

### Requirement: Time-correct and realistic backtest
The system SHALL use an event-driven decision clock, exclude unavailable future information and model configured fees, taxes, spread, slippage, liquidity, partial fills, suspensions, price limits and corporate actions.

#### Scenario: Feature contains future data
- **WHEN** a feature observation has an availability time after the decision time
- **THEN** the backtest rejects or excludes it and records a leakage violation

### Requirement: Out-of-sample promotion gate
The system SHALL require predeclared baselines, time-series validation, out-of-sample evaluation, stress tests, configured multiple-testing correction and independent approval before a model can be used in a plan.

#### Scenario: Model has high in-sample return but fails stress threshold
- **WHEN** a candidate violates a configured drawdown, stability, cost or liquidity threshold
- **THEN** it cannot transition to `approved` regardless of in-sample return

#### Scenario: Many candidates were evaluated
- **WHEN** the recorded trial count exceeds the configured threshold
- **THEN** the promotion report includes Deflated Sharpe Ratio or an approved equivalent and cannot rely on the best raw Sharpe alone

### Requirement: Controlled tuning and model lifecycle
The system SHALL run tuning in an isolated asynchronous environment, prevent users from editing registered artifacts, separate dev, staging and production permissions, use validation tags, and support auditable `champion`, `challenger` and `rollback` aliases.

#### Scenario: Approved model inputs materially change
- **WHEN** data, features, code or applicable universe changes beyond policy tolerance
- **THEN** its validation tag is invalidated and it cannot receive a production routing alias until required validation is repeated

#### Scenario: Champion alias is reassigned
- **WHEN** an authorized approval promotes a challenger
- **THEN** the alias event records old and new immutable versions, approvers and time, and existing recommendations remain bound to their original version

### Requirement: Engine selection evidence
The system SHALL select one formal backtest engine through a time-boxed comparison using the same boundary dataset and acceptance suite for market rules, point-in-time data, determinism, integration, licensing and operations.

#### Scenario: Candidate engine cannot model a hard market rule
- **WHEN** the engine cannot correctly represent a required launch-market constraint through a maintained extension point
- **THEN** it is rejected for formal backtesting even if its basic performance benchmark is faster

### Requirement: Paper reconciliation
The system SHALL publish a versioned simulation fidelity profile and compare paper results with a contemporaneous out-of-sample replay before any future live-trading review.

#### Scenario: Paper fills materially outperform replay assumptions
- **WHEN** fill or cost deviation exceeds the configured tolerance
- **THEN** the model is flagged for review and cannot advance automatically

### Requirement: Deterministic event replay
The system SHALL record ordered inputs, logical clock, seeds, state transitions and simulated fills needed to replay a formal backtest within declared deterministic tolerances.

#### Scenario: Auditor replays an accepted run
- **WHEN** the immutable run artifacts are executed in the declared environment
- **THEN** the replay matches recorded decisions and results within documented tolerances or the run is invalidated
