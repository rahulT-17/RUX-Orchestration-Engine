# RUX — Production Readiness Checklist
> Current: 3.5 / 10 → Target: 9.0 / 10

---

## Phase 1 — Foundation `+1.5`

### Legacy Cleanup
- [ ] DELETE `services/expense_service.py`
- [ ] DELETE `repositories/expense_repository.py`
- [ ] DELETE `repositories/budget_repository.py`
- [ ] DELETE `repositories/project_repositories.py`
- [ ] REMOVE `get_memory` import from `main.py`
- [ ] DELETE `memory/memory_manager.py`
> Run `pytest` after every single deletion. Not at the end. After each one.

### DB Migration Discipline (Move Earlier)
- [X] Introduce Alembic and create a baseline revision from current schema
- [X] Every model change requires migration + downgrade path
- [] Add CI check: fail if ORM model changes ship without migration file
- [X] Add startup guard: app revision must match DB revision

### Security Baseline (Before Memory) 
- [X] API key auth at least on write endpoints + debug endpoints
- [X] Rate limiting baseline enabled before public exposure
- [X] Remove hardcoded secrets and rotate leaked credentials
- [X] Input guardrails: max message length + basic sanitization

### Latency Fixes
- [ ] Add per-step timing logs — find exact bottleneck first
- [ ] Shrink planner prompt to under 300 tokens
- [ ] Switch to Groq free tier or OpenAI API — target under 3s total
- [ ] Stream planner response to eliminate perceived wait time

### SLOs (Track Before Optimizing)
- [ ] Define p95 latency targets (`/chat` no-critic and critic-enabled)
- [ ] Define 5xx error budget target (rolling 7-day window)
- [ ] Add p50/p95 stage timings (planner, executor, db, critic)
- [ ] Do before/after measurement for every latency change

### Runtime Extraction
- [ ] Create `runtime/` with locked folder structure
- [ ] Extract action metadata from `executor.py` → `action_catalog.py`
- [ ] Unify confirmation path with normal execution path
- [ ] Clean `api/routes.py` — stop manual object graph wiring inline
- [ ] Move planner action definitions → shared with tool registry

---

## Phase 2 — Reliability `+2.0`

### Observability Auto-logging
- [ ] ToolResponse fields auto-map to `agent_run` columns — zero manual logging
- [ ] Every execution — success or failure — auto-writes to `agent_runs`
- [ ] Confirmation path logs outcomes identically to normal path
- [ ] Debug endpoints return enriched data including ToolResponse status

### Planner Eval Script
- [ ] 20+ test cases — actions, greetings, edge cases
- [ ] Pass/fail per case with specific failure reason printed
- [ ] Overall accuracy score — 85%+ before moving to memory
- [ ] Eval runs in CI — fails build if accuracy drops below threshold

### API Integration Gate (Before Memory)
- [ ] Add integration tests for `/chat` (greeting, action, confirm yes/no)
- [ ] Add integration tests for `/feedback` (success + 404 path)
- [ ] Add integration tests for `/debug/*` observability endpoints
- [ ] Require API integration suite green before Hybrid Memory work starts

### Rate Limiting + Backpressure
- [ ] Redis-backed rate limiting (burst + sustained quotas)
- [ ] Per-endpoint policy (`/chat`, `/feedback`, `/debug/*`) not one global limit
- [ ] Return `429` with `Retry-After` and structured error body
- [ ] Add overload/backpressure policy (`503` when queue wait exceeds threshold)

### Worker Queue (Async Workload Isolation)
- [ ] Move critic second-opinion path to background worker queue
- [ ] Add retries + dead-letter handling for failed jobs
- [ ] Track queue depth, wait time, and job success rate
- [ ] Add timeout + cancellation policy per job type

### Cache Layer (Read Path Acceleration)
- [ ] Add Redis cache for read-heavy responses (analyze/get_budget/confidence)
- [ ] Define cache keys with `user_id + normalized_intent + period/window`
- [ ] Invalidate relevant cache entries after write actions
- [ ] Track hit rate + p95 latency delta to prove cache value

### Hybrid Memory Layer
> Build in this exact order. Don't skip ahead.
- [ ] `memory/domain/models.py` — MemoryRecord, Episode, Chunk
- [ ] `short_term_store.py` — last N turns, in-memory buffer
- [ ] `episodic_store.py` — PostgreSQL structured facts about user
- [ ] `semantic_store.py` — pgvector embedded conversation chunks
- [ ] `embedding_adapter.py` — wraps embedding API call
- [ ] `retriever.py` — hybrid query across all three stores
- [ ] `context_builder.py` — assembles memory into prompt
- [ ] `manager.py` — unified memory API the runtime calls

---

## Phase 3 — Deployability `+1.5`

### Docker + Deployment
- [ ] `Dockerfile` for the FastAPI app
- [ ] `docker-compose.yml` — app + PostgreSQL + pgvector together
- [ ] `.env.example` with every required variable documented
- [ ] Live deployment on Railway or Render with public URL
- [ ] `GET /health` endpoint returns 200

### Basic Security
- [ ] API key auth on all endpoints — `X-API-Key` header
- [ ] Rate limiting — max 20 requests/minute per key
- [ ] No secrets in git — `.env` in `.gitignore`, verify clean history
- [ ] Input validation — max message length, sanitise user input

---

## Phase 4 — Polish `+1.5`

### Error Handling
- [ ] Global exception handler — no raw 500s ever reach the user
- [ ] LLM timeout — if planner takes over 15s, fail gracefully
- [ ] DB connection failure returns meaningful error, not stack trace
- [ ] All errors logged with context — user_id, action, timestamp

### Testing
- [ ] Planner unit tests — 20+ cases, mocked LLM call
- [ ] Executor unit tests — ToolResponse routing for success, error, confirm
- [ ] Integration test — full expense log flow end to end
- [ ] Memory integration test — context retrieval across 3 sessions
- [ ] `pytest` passing — zero failures before every commit

### Documentation + Demo
- [ ] README folder structure matches actual locked structure
- [X] Fix git clone URL placeholder in setup section
- [X] Remove "built as a learning project" line
- [ ] Add GitHub topics: `ai-agent` `llm` `fastapi` `orchestration` `python`
- [ ] Record 2-min demo video — narrate every architectural decision
- [X] Postman collection or curl examples for every endpoint

### CI/CD
- [ ] GitHub Actions — runs `pytest` on every push to main
- [ ] GitHub Actions — runs planner eval, fails if under 85%
- [ ] Auto-deploy to Railway on merge to main

---

## Score Map

| After phase      | Score |
|------------------|-------|
| Current state    | 3.5   |
| + Phase 1        | 5.0   |
| + Phase 2        | 7.0   |
| + Phase 3        | 8.5   |
| + Phase 4        | 9.0   |

---

## Gates — don't move forward until these pass

| Step | Gate | Status
|------|------|
| Legacy cleanup | `pytest` passes after every deletion |
| DB migrations | Alembic revision + model schema are in sync in CI | mostly DONE CI enforcement is pending 
| Security baseline | API key + rate limit + secret hygiene completed | PARTIAL ()
| Runtime extraction | Full orchestrator flow works end to end |
| Observability | Zero manual log calls in executor |
| Planner eval | 85%+ pass rate measured, not estimated |
| API integration | `/chat`, `/feedback`, `/debug/*` suite green before memory |
| Traffic control | Per-endpoint rate limiting + backpressure behavior validated |
| Worker queue | Critic/background jobs run out-of-band with retries + visibility |
| Cache layer | Read-path cache hit rate and invalidation policy validated |
| Memory layer | Context retrieved from 3 sessions ago without being in current prompt |
| SLO tracking | p95 latency + 5xx error budget tracked and within target |
| Docker | Someone clones repo, runs `docker-compose up`, RUX works |
| Demo | Someone who has never seen RUX understands it in 2 minutes |


ARCHitecture SCOPE :

rux/
├── app/                            # HTTP/bootstrap layer only
│   ├── main.py
│   ├── config.py
│   ├── dependencies/
│   │   ├── db.py
│   │   ├── runtime.py
│   │   └── services.py
│   └── routes/
│       ├── chat.py
│       ├── feedback.py
│       └── debug.py
│
├── runtime/                        # Agent execution engine
│   ├── orchestrator.py
│   ├── planner.py
│   ├── executor.py
│   ├── confirmation.py
│   ├── state.py
│   ├── tool.py
│   ├── tool_registry.py
│   ├── tool_response.py
│   └── action_catalog.py
│
├── domains/                        # Business / reasoning capabilities
│   ├── expense/
│   │   ├── application/
│   │   │   ├── service.py
│   │   │   └── tools.py
│   │   ├── domain/
│   │   │   ├── models.py
│   │   │   ├── rules.py
│   │   │   └── schemas.py
│   │   └── infrastructure/
│   │       └── repository.py
│   │
│   ├── project/
│   │   ├── application/
│   │   │   ├── service.py
│   │   │   └── tools.py
│   │   ├── domain/
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   └── infrastructure/
│   │       └── repository.py
│   │
│   └── knowledge/
│       ├── application/
│       │   ├── service.py
│       │   └── tools.py
│       ├── domain/
│       │   ├── models.py          # Fact, Preference, Note, Concept, Source
│       │   ├── rules.py
│       │   └── schemas.py
│       └── infrastructure/
│           └── repository.py
│
├── memory/                         # Cognitive substrate / retrieval system
│   ├── application/
│   │   ├── manager.py             # unified memory API for runtime/domains
│   │   ├── context_builder.py
│   │   └── retrieval.py
│   ├── domain/
│   │   ├── models.py              # memory record, episode, chunk, summary
│   │   ├── policies.py
│   │   └── schemas.py
│   └── infrastructure/
│       ├── short_term_store.py
│       ├── episodic_store.py
│       ├── semantic_store.py
│       ├── embedding_adapter.py
│       └── repository.py
│
├── observability/                  # Telemetry and evaluation
│   ├── application/
│   │   └── service.py
│   ├── domain/
│   │   ├── models.py
│   │   └── schemas.py
│   └── infrastructure/
│       ├── repository.py
│       └── logger.py
│
├── services/                       # Shared infra adapters only
│   ├── llm_service.py
│   ├── embedding_service.py
│   ├── critic_service.py
│   ├── confidence_service.py
│   └── classifier_service.py
│
├── shared/                         # Cross-cutting shared code
│   ├── contracts/
│   │   ├── response.py
│   │   └── common.py
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models.py              # only truly shared tables
│   └── utils/
│       ├── time.py
│       ├── helpers.py
│       └── constants.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── migrations/
├── docker/
├── requirements.txt
└── README.md


PAHsE 1 : deecision 3 security baseline
Define the security contract first
Location: config.py:6, .env, .env.example, database.py:11
How: add and standardize security-related settings (API key, max message size, rate limit values) in one place.
Why: this prevents scattered hardcoded values and makes behavior predictable across all endpoints.
What you learn: configuration-first design keeps security changes easy to reason about and test.

Add API key verification dependency
Location: use FastAPI dependency pattern already used in routes.py:56 and debug_routes.py:17
How: create one shared verifier function in core and reuse it through dependency injection.
Why: this creates a trust gate before any endpoint logic runs.
What you learn: dependencies are clean security hooks in FastAPI.

Apply auth to write and debug surfaces
Location: write endpoints at routes.py:56 and routes.py:98, debug router at debug_routes.py:15
How: protect chat and feedback endpoints directly, and protect the whole debug router at router level.
Why: these are your highest-risk surfaces today (state-changing and observability data).
What you learn: route-level vs endpoint-level protection tradeoff.

Add input guardrails on request models
Location: routes.py:44, routes.py:90, schemas.py:9, schemas.py:6, schemas.py:13
How: add max length bounds and strict validation for user-facing text fields.
Why: this blocks oversized payload abuse and reduces LLM/context and DB pressure.
What you learn: validation is both correctness and security.

Add conservative sanitization where text enters system flow
Location: request handling in routes.py:56 and service boundaries in domain services
How: normalize text with safe cleanup (trim, remove control noise) without changing intent.
Why: cleaner logs, fewer malformed inputs, fewer edge-case surprises.
What you learn: sanitize for consistency, validate for safety.

Add baseline rate limiting (per endpoint policy)
Location: wiring point in main.py:47 and endpoint map in routes.py:56, routes.py:98, debug_routes.py:17
How: add an async-friendly limiter with different budgets for chat, feedback, and debug endpoints.
Why: protects LLM and DB from bursts and accidental abuse.
What you learn: security is also resource governance.

Standardize 429 responses and retry behavior
Location: API response path in routers and limiter integration
How: return consistent 429 payload plus Retry-After metadata.
Why: clients need actionable responses, not generic errors.
What you learn: reliability UX is part of security posture.

Rotate secrets and lock hygiene
Location: .env, .env.example, .gitignore, and your git history process
How: rotate exposed credentials, keep only examples tracked, verify secret files are ignored.
Why: leaked secrets remain risk even after code fixes.
What you learn: security baseline is incomplete without credential hygiene.

Verify with focused tests before marking checklist done
Location: existing tests in conftest.py, smoke tests, and new security tests
How: validate auth failures, valid access, validation failures, rate-limit behavior, then run full test suite.
Why: this ensures no silent regressions while adding security controls.
What you learn: evidence-based completion beats assumption-based completion.

Update checklist gate only after evidence
Location: rux-checklist.md
How: mark Security Baseline done only when auth + guardrails + rate limiting + secret hygiene are all verified.
Why: keeps your roadmap honest and production-grade.
What you learn: execution discipline is architecture quality.
