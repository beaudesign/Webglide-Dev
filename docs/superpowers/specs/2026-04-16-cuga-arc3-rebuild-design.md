# CUGA ARC-3 Rebuild Design Brief

**Date:** 2026-04-16  
**Role Context:** Design Lead / PM  
**Status:** Approved for planning handoff  
**Confidentiality:** Internal planning document

## 1) Goal and Product Intent

Build a new, isolated CUGA-derived project focused on improving **ARC-AGI-3** performance through scaffolded agent design and disciplined evaluation.

Primary objective:

- Maximize **win rate / scorecard performance** on ARC-3.

Secondary objective:

- Make agent behavior legible and steerable through a UI that exposes planning, reasoning, action choice, and reflection in real time.

## 2) Scope and Boundaries

### In Scope (MVP-1)

- ARC-3 online API integration via `ARC_API_KEY`.
- Fixed benchmark slice: **50 games total**.
  - Tier 1: 30 representative core games.
  - Tier 2: 20 hard stress games.
- Phased ablation ladder for scaffold impact attribution:
  - Stage S0: Baseline.
  - Stage S1: + Single-agent cognitive scaffold.
  - Stage S2: + Tool-use scaffold.
  - Stage S3: + Multi-agent scaffold (minimal version in MVP-1).
- Operator UI with a **right-hand panel** showing CUGA planning and reasoning.
- Evaluation harness with reproducible scorecard tracking and stage-by-stage comparisons.

### In Scope (MVP-2)

- Max-impact multi-agent scaling:
  - Planner/executor/critic specialization.
  - Portfolio routing across game families.
  - Action arbitration (vote or policy-based tie-break).
  - Parallel orchestration within ARC rate limits.
- Per-agent attribution metrics for win/loss contribution.

### Out of Scope (for MVP-1)

- Full ARC-3 catalog optimization.
- Cost minimization as primary objective.
- Full production hardening and enterprise deployment stack.

## 3) Architecture

MVP-1 uses four modules with stable interfaces to prevent evaluation drift:

1. **`arc-adapter`**
   - ARC-3 API client and session primitives.
   - Handles game discovery, start/reset, action submission, and scorecard lifecycle.
   - Normalizes API responses into internal events and typed run state.

2. **`cuga-runner`**
   - Executes game loops with pluggable scaffold profiles (`S0..S3`).
   - Exposes deterministic run configuration and control flags.
   - Emits structured execution events for both evaluation and UI.

3. **`eval-harness`**
   - Runs the fixed benchmark manifest (30 core + 20 stress).
   - Aggregates win rate and per-game metrics by scaffold stage.
   - Produces stage delta reports and baseline-lift summaries.

4. **`operator-ui`**
   - Main run control/results surface.
   - Right panel streams execution trace with explicit sections:
     - Current plan.
     - Reasoning steps.
     - Action proposal and rationale.
     - Reflection/retry notes.
   - Supports run replay from stored trajectory events.

## 4) MVP Ladder

## MVP-1: Controlled Performance Lift System

Deliver a measurable baseline and causal lift framework before broad scaling.

Required outcomes:

- End-to-end ARC-3 run capability.
- Repeatable 50-game benchmark execution.
- S0 to S3 ablation results with comparable conditions.
- UI visibility for plan/reason/action/reflection.

Success criteria:

- A complete ladder report with win rate per stage.
- Reproducible run artifacts (manifest version + config hash + scorecard IDs).

## MVP-2: Multi-Agent Impact Expansion

Increase absolute win rate using coordinated specialist agents.

Required outcomes:

- Specialized agent roles connected via a supervisor pattern.
- Portfolio routing and arbitration policy.
- Parallelizable game execution pipeline with observability.

Success criteria:

- Demonstrated win-rate lift beyond MVP-1 S3 baseline on the same fixed benchmark slice.

## 5) Evaluation Protocol

Use a deterministic loop to keep results comparable:

1. Load benchmark manifest (`core-30`, `stress-20`).
2. Select scaffold stage (`S0`, `S1`, `S2`, `S3`).
3. Open scorecard and attach run metadata.
4. For each game:
   - Start/reset session.
   - Generate plan and candidate action.
   - Execute ARC action.
   - Consume observation and update internal state.
   - Continue until solved, terminated, or step budget exhausted.
5. Close scorecard and aggregate metrics.
6. Generate stage report and stage-to-stage deltas.

Primary KPI:

- Win rate (% solved games) by stage.

Supporting metrics:

- Solved count.
- Average steps to solve.
- Failure taxonomy distribution.
- Stage lift from S0 baseline.

## 6) Scaffolding Strategy (Ablation Ladder)

### S0: Baseline

- Minimal CUGA loop with default prompting and action policy.
- No extended memory, no advanced tool priors, no specialized agent delegation.

### S1: Single-Agent Cognitive Scaffold

- Structured planning frames.
- Reflection checkpoints.
- Retry policy for bounded recovery.
- Task memory policy for in-episode reasoning continuity.

### S2: Tool-Use Scaffold

- Action abstraction layer over ARC command surface.
- Action priors informed by state features.
- Game-state feature extraction for better action proposal quality.

### S3: Multi-Agent Scaffold (MVP-1 minimal cut)

- Introduce planner/executor/critic coordination at minimal complexity.
- Preserve same adapter/harness interfaces to maintain comparability.

## 7) UI and Legibility Requirements

The right-hand panel is a first-class product requirement.

For each step, display:

- Plan version and update timestamp.
- Reasoning entry (structured text or JSON-backed text render).
- Selected action (`ACTION1..ACTION7` or complex action with `x,y`) and rationale.
- Reflection output (what changed, why next step differs).
- Outcome marker (`progress`, `stalled`, `error`, `solved`).

UI must support:

- Live mode during runs.
- Replay mode from stored event logs.
- Filtering by stage and game ID.

## 8) Error Handling and Reliability

Failure classification buckets:

- Auth/API key failure.
- Rate limit.
- Invalid action.
- Timeout.
- Scaffold logic error.
- Unknown/system error.

Policy:

- Retry transient API failures with bounded exponential backoff.
- Stop on repeated invalid-action loops and record explicit reason.
- Persist partial traces on crash/interruption for postmortem and replay.

## 9) Testing Strategy

Required test layers:

- Adapter contract tests (games, reset/start, actions, scorecards).
- Deterministic smoke benchmark tests (small subset preflight).
- Scaffold regression tests (stage invariants and interface contracts).
- UI trace rendering tests (event sequence integrity in right panel).

Release gate for performance claims:

- No claim of lift without full 50-game rerun for the target stage.

## 10) Reproducibility and Governance

Each run must store:

- Benchmark manifest version.
- Scaffold stage and configuration hash.
- Model/provider metadata.
- Prompt/profile references.
- Scorecard ID and timestamp.

Rules:

- Only change one scaffold variable per ablation step.
- Keep benchmark slice fixed during comparison cycle.
- Log every run in a machine-readable report artifact.

## 11) Risks and Mitigations

- **Benchmark overfitting on 50-game subset**
  - Mitigation: keep stress tier, rotate hidden holdout for periodic checks.
- **Attribution confusion from concurrent changes**
  - Mitigation: strict stage isolation and config hashing.
- **ARC API volatility or quota/rate pressure**
  - Mitigation: retry/backoff discipline and queue controls.
- **Reasoning trace too noisy for operators**
  - Mitigation: enforce structured event schema and concise UI rendering.

## 12) Deliverables

MVP-1 deliverables:

- Working ARC-3 integrated runner.
- Fixed benchmark manifest and harness.
- S0-S3 stage configs and comparable reports.
- Operator UI with right-panel planning/reasoning trace.
- Runbook describing how to execute and reproduce benchmark results.

MVP-2 deliverables:

- Multi-agent orchestration with routing/arbitration.
- Parallel execution strategy within platform limits.
- Per-agent attribution reporting.

## 13) Handoff Notes

This spec is intentionally written to support immediate conversion into an implementation plan with task-level decomposition and TDD-oriented execution steps.
