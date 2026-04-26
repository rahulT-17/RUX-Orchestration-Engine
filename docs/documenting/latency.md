# Latency Baseline Report

Last Updated: 2026-04-26

## Scope

This report tracks latency baselines across three runtime modes:

1. No critic path (analyze flow).
2. Critic inline path (blocking).
3. Critic background path (non-blocking, persisted async result).

Instrumentation currently includes:

1. Request-level timing (`X-Process-Time-ms` + request timing logs).
2. Stage-level orchestration timing (`confirmation_ms`, `planning_ms`, `execution_ms`, `finalize_ms`).
3. Execution sub-stage timing (`tool_call_ms`, `run_log_ms`, `outcome_log_ms`, `decision_engine_ms`, `critic_ms`, `confidence_ms`, `response_build_ms`, `finalize_ms`).
4. Persisted timing and critic metadata in run result JSON.

## Baseline A: No Critic (Analyze Path, n=20)

| Metric | ms | s |
|---|---:|---:|
| Average | 9492.76 | 9.49 |
| p50 (nearest-rank) | 9174.19 | 9.17 |
| Median (middle-average) | 9189.98 | 9.19 |
| p95 (nearest-rank) | 11435.17 | 11.44 |
| Min | 8946.03 | 8.95 |
| Max | 11878.70 | 11.88 |

## Baseline B: Critic Inline (Blocking, Log Path, n=20)

| Metric | ms | s |
|---|---:|---:|
| Average | 61491.49 | 61.49 |
| p50 | 60020.66 | 60.02 |
| p95 | 68637.89 | 68.64 |
| Min | 53839.26 | 53.84 |
| Max | 76349.49 | 76.35 |

## Baseline C: Critic Background (Non-Blocking, Log Path, n=20)

Date captured: 2026-04-26

| Metric | ms | s |
|---|---:|---:|
| Average | 24037.48 | 24.04 |
| p50 | 24821.55 | 24.82 |
| p95 | 27554.08 | 27.55 |
| Min | 14673.78 | 14.67 |
| Max | 28071.32 | 28.07 |

Background critic status distribution from the same benchmark window:

| Status | Count |
|---|---:|
| completed | 0 |
| timeout | 15 |
| failed | 0 |
| pending_or_missing | 5 |

## Stage Snapshot Examples

| Scenario | confirmation_ms | planning_ms | execution_ms | total_ms | Dominant stage |
|---|---:|---:|---:|---:|---|
| No-critic sample | 86.68 | 11614.63 | 100.85 | 11952.83 | planning |
| Critic-inline sample | 59.28 | 14498.05 | 47465.16 | 62101.93 | execution |
| Critic-background sample | 1.59 | 23682.06 | 654.11 | 24356.20 | planning |

## Key Findings

1. No-critic path is planning-bound.
2. Critic-inline path is execution-bound due to waiting on critic LLM.
3. Critic-background path shifts back to planning-bound (decision/critic wait removed from response path).
4. Non-blocking critic reduced latency vs inline critic:
	- Average: 61.49s -> 24.04s (about 60.9% faster)
	- p50: 60.02s -> 24.82s (about 58.6% faster)
	- p95: 68.64s -> 27.55s (about 59.9% faster)
5. p95 still exceeds SLO target and requires planner/model optimization.

## Where To Observe Latency

1. Total request latency: middleware log + `X-Process-Time-ms` header.
2. High-level stage latency: `core.orchestrator` `stage_timings` log.
3. Execution sub-stage latency: `core.executor` `execution_substages` log.
4. Persisted stage metrics: `/debug/runs` payload under `result.metadata`.

## Current SLO Gap vs Target

| Path | Current p95 | Target p95 | Gap |
|---|---:|---:|---:|
| No critic | 11.44s | 3.00s | +8.44s |
| Critic inline (blocking) | 68.64s | 4.50s | +64.14s |
| Critic background (non-blocking) | 27.55s | 4.50s | +23.05s |

## Next Actions

1. Keep no-critic baseline fixed as control dataset.
2. Reduce planner latency first (prompt shrink + stronger deterministic intent routing).
3. Run provider benchmark (Groq/OpenAI) and compare p50/p95 using identical workloads.
4. Track background critic reliability separately (completed/timeout/failed) to avoid silent quality loss.
5. Add a rolling 7-day 5xx and timeout report to satisfy SLO governance.

## Optional Non-Blocking Critic Mode

Set `CRITIC_NON_BLOCKING=true` in `.env` to queue critic work in background and remove critic wait time from user-facing response latency.

Use benchmark command:

`./scripts/run_20_background_critic.ps1 -Runs 20 -UserId rahul -Message "log 100 food"`

