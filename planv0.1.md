# RELAY — Build Plan v0.1

**Target:** polished, working hackathon prototype. Single-day build, RAD-concurrent spiral.
**Source of truth for product intent:** `RELAY.txt` (unchanged; this plan does not supersede it).
**Date:** 2026-09-26

---

## 0. Decisions locked

| Decision | Choice | Rationale |
|---|---|---|
| Framework | Next.js 15 (App Router), TypeScript strict | Per spec |
| Mutations | **Server Actions** (no REST layer) | Removes an entire API tier; ~2h saved |
| Database | **better-sqlite3 + Drizzle ORM**, single `relay.db` | Replaces Supabase: synchronous, zero network, real SQL, sub-second reset |
| Styling | Tailwind v4 + shadcn/ui | Per spec |
| Visual language | **Linear/Vercel dark** — near-black canvas, elevated panels, hairline borders, one accent | Status indicators are RELAY's primary visual language; they read strongest on dark |
| Charts | Recharts where it earns it; **inline SVG** for propagation tree | Spec: "a clean diagram is sufficient" |
| AI | **Vercel AI SDK `generateObject` + Zod** | Provider swap = one env var; schema validation free |
| AI model | `gemma4:31b-cloud` via Ollama. **No silent fallback — unreachable cloud is a hard error.** | Silent degradation hides bugs; failures must be loud during build |
| Auth | **None.** Three-persona switcher instead | Spec deprioritizes SSO; personas are demo value, auth is not |
| Deployment | localhost only | No wifi dependency on stage |

### Scope posture
Nothing the judge can **see or click** is cut. Depth is rationed *behind* non-flagship surfaces. The flagship Transfer Session loop is fully stateful; peripheral surfaces are richly seeded views with real (but narrower) interaction.

---

## 1. The one thing that must work

The spec's 15-step demo has a closed loop. Steps 10–15 are the entire product thesis:

```
Validate finding  →  Kwame's passport changes
                  →  Knowledge Library grows
                  →  Blueprint status flips
                  →  Readiness recomputes
                  →  Next Session Brief regenerates
```

This must be **real mutation propagating through real state**, not five hardcoded screens. Everything else in this plan exists to frame it.

---

## 2. AI architecture (the seam)

```
lib/ai/
  provider.ts      getModel() keyed on RELAY_AI_PROVIDER = mock | ollama | xai | anthropic | openai
  cache.ts         SQLite-backed: (fnName + sha256(input)) -> validated JSON
  run.ts           resolver
  schemas/*.ts     one Zod schema per AI function
  fixtures/*.ts    one deterministic seeded response per AI function
  functions/*.ts   one module per spec'd AI function
```

### Failure policy — fail loud

```
1. cache hit                    → return instantly, byte-identical
2. live provider                → generateObject(schema); on success, write cache
3. provider unreachable / bad   → THROW. Surfaced, logged, not swallowed.
```

**There is no automatic fallback.** If the cloud model is unreachable, or returns schema-invalid output, the call errors. `mock` is a mode you *select* (`RELAY_AI_PROVIDER=mock`), never something that engages behind your back.

Consequences that matter:
- Every AI bug is visible the moment it happens, not discovered at hour 10 behind a fixture that quietly papered over it.
- The demo's network safety comes from the **cache**, not from a fallback. Run the flagship path once in rehearsal → every subsequent run is instant, byte-identical, and never touches the network.
- Error states must therefore be *designed*, not incidental: a real inline error component, not a stack trace or a white screen. This is a WP-1 deliverable.

**Provider swap matrix** (`RELAY_AI_PROVIDER`):

| Value | Package | Model env var |
|---|---|---|
| `mock` | — | — (explicit demo mode) |
| `ollama` | `@ai-sdk/openai-compatible` @ `localhost:11434/v1` | `RELAY_AI_MODEL=gemma4:31b-cloud` |
| `xai` | `@ai-sdk/xai` | `grok-4` |
| `anthropic` | `@ai-sdk/anthropic` | `claude-opus-5` |
| `openai` | `@ai-sdk/openai` | `gpt-5` |

Swapping providers later = install one package, change one env var. Zero call-site changes.

### AI functions (spec §AI FUNCTIONS)
Each is `(input) => Promise<z.infer<Schema>>`, cached, schema-validated:

`prepareSession` · `generateExpertDebrief` · `generateLearnerDebrief` · `analyzeSession` · `extractTacitKnowledge` · `assessCapabilityEvidence` · `recommendNextExperience` · `identifyTrainerCandidates` · `analyzeReadiness` · `generateDeparturePlan` · `buildOperatingModel` · `identifyTransferRequirements` · `identifyFormalInformalGaps` · `generateTransferPlan`

**Priority:** `analyzeSession` is the hardest schema (4 nested finding types) and the demo centerpiece. It is validated first, in WP-0.

---

## 3. Data model (12 tables)

Collapsed from the spec's 23. Rule applied: **anything displayed but never queried across becomes a typed JSON column.**

| Table | Notes |
|---|---|
| `people` | role: `expert` \| `counterpart` \| `manager`; `departureDate` on experts |
| `capabilities` | the 10 seeded capabilities; `criticality` |
| `person_capabilities` | current level 0–6, `lastDemonstrated`, `exposureCount` |
| `capability_evidence` | **append-only.** Never overwrite history (spec §STEP 6) |
| `operating_model_areas` | JSON cols: `processes`, `roles`, `decisionRights`, `tools`, `metrics`, `relationships` |
| `transfer_requirements` | typed `formal`/`informal`/`technical`/`judgment`/`relationship`/`tool`/`governance`; status `complete`/`partial`/`none` |
| `sessions` | stage enum drives the loop UI |
| `debriefs` | discriminated by `role: expert \| learner` |
| `findings` | AI output, `status: pending \| approved \| edited \| rejected` |
| `knowledge_items` | 7 spec'd types; FK to area/capability/session/expert |
| `recommendations` | feeds the next Session Brief |
| `validations` | who validated what, when — the audit trail |

**Invariants (enforced, not conventions):**
1. AI never writes `person_capabilities.level`. Only an approved `validation` does.
2. `capability_evidence` is insert-only.
3. Every readiness number is derived at read time. No stored scores.

---

## 4. Readiness engine (deterministic, explainable)

`lib/readiness/` — pure functions over the store, no AI. Each returns `{ value, inputs, formula }` so the UI can render a **"how this is calculated"** popover. Spec is explicit: no unexplained score.

```
capabilityLocalization  = critical caps with >=1 local counterpart at level >=4  / critical caps
locallyTeachable        = count(caps with >=1 counterpart at level 6)
expertDependent         = critical caps where expert capable AND no local >=4
localOwnership          = areas with validated local owner / critical areas
formalTransfer          = formal requirements marked complete / total formal
informalTransfer        = informal requirements with validated capture / total informal
trainerCoverage         = areas with >=1 local trainer / critical areas

operatingModelReadiness = 0.25*localOwnership + 0.30*capabilityLocalization
                        + 0.15*formalTransfer + 0.20*informalTransfer
                        + 0.10*trainerCoverage
```

Weights live in one exported const, surfaced verbatim in the UI popover.

**Seed must be tuned so this yields ≈68% pre-demo and visibly increments post-validation.** That tuning is a WP-3 acceptance criterion, not an accident.

---

## 5. Work packages

Each WP below is independently dispatchable. **File ownership is exclusive** — no two WPs write the same path, so parallel agents cannot collide. Shared contracts are frozen in WP-0/WP-2 before dependents start.

### WP-0 · Risk spike ⛔ BLOCKING — ~90 min
**Owns:** `app/_spike/`, `.env.local`, `package.json`, `drizzle.config.ts`
**Depends on:** nothing. **Everything depends on this.**

Not scaffolding. Three proofs on one deliberately ugly page:
1. Server Action writes to SQLite; subsequent read reflects it.
2. `generateObject` against `gemma4:31b-cloud` returns schema-valid output for the **`analyzeSession` schema** (4 nested findings) — 5 consecutive runs, latency recorded.
3. A readiness function computes from seeded rows.

**Gate:** proof 2 must pass ≥4/5 with tolerable p95 latency. If the cloud model can't hold the nested schema, the *schema* gets flattened (fewer nested levels, more top-level fields) — the model does not get swapped and the failure does not get hidden. Record the outcome in §9.
**Outputs:** frozen `db/schema.ts`, frozen `lib/ai/run.ts` signature, benchmark numbers in §9.

---

### WP-1 · Design system + app shell — ~2h
**Owns:** `app/globals.css`, `app/layout.tsx`, `components/ui/**`, `components/shell/**`
**Depends on:** WP-0 (project init only)
**Parallel with:** WP-2, WP-4

- Dark token set: canvas, panel, elevated, hairline, text primary/secondary/tertiary, single accent.
- **Status system** — one component, five states, used everywhere: `SUSTAINABLE` · `ON TRACK` · `TRANSFER IN PROGRESS` · `AT RISK` · `CRITICAL`.
- Transfer-requirement glyphs: `✓` complete · `△` partial · `○` none.
- Capability level chip (0–6) with consistent color ramp.
- **Designed error + retry state** for AI calls — required by the fail-loud policy (§2). Must look deliberate, not like a crash.
- App shell: sidebar nav in spec order (Overview · Operating Model · Transfer Blueprint · People · Sessions · Knowledge · Readiness), engagement switcher, **persona switcher** (Dr. Mitchell / Kwame Mensah / Program Manager).
- Typography: one family, tight scale, tabular numerics for all metrics.

**Acceptance:** every status in the product renders through one component. No ad-hoc colors. No emoji. No gradients.

---

### WP-2 · Schema, DB, reset — ~1h
**Owns:** `db/schema.ts`, `db/client.ts`, `db/migrate.ts`, `scripts/reset.ts`
**Depends on:** WP-0. **Blocks:** WP-3, WP-5, WP-6, WP-7

- 12 tables per §3, with the three invariants enforced at the data-access layer.
- `npm run db:reset` → drop, migrate, seed, <1s. **P0 — you will run this five times on demo day.**
- Reset must **preserve the AI response cache** (separate table, not dropped) so a reset doesn't cost you a warm demo.
- Typed query helpers; no raw SQL in components.

**Acceptance:** reset is idempotent, sub-second, and leaves the cache intact.

---

### WP-3 · Seed corpus (content-heavy) — ~2.5h
**Owns:** `db/seed/**`
**Depends on:** WP-2 types. **Parallel with:** WP-1, WP-4

Highest "does this look real?" leverage in the build. Generic seed data is the #1 tell of a hackathon prototype.

- Ghana community-health engagement; Dr. Sarah Mitchell (28 days out), Kwame Mensah, Ama Boateng, Kojo Asare.
- 9 operating-model areas, each fully populated (process, owner, roles, decision rights, tools, metrics, formal/informal knowledge, capabilities, status).
- 10 capabilities × per-person levels + **evidence history** (dated, uneven, plausible).
- ~18 validated knowledge items across all 7 types.
- 3–4 prior sessions with real outcomes, so Sessions isn't empty on open.
- **A genuinely well-written Clinic 14 transcript** — this is read aloud or scanned on stage. It must sound like two supply-chain professionals talking, not like LLM filler.

**Acceptance:** readiness computes to ≈68% / ≈70% localization / 4 teachable / 3 expert-dependent pre-demo. No lorem. No round-number-everything. Dates consistent with a 9-month assignment 28 days from its end. **Fictional org explicitly not implied to be Peace Corps** (spec §DEMO SCENARIO).

---

### WP-4 · AI layer — ~2h
**Owns:** `lib/ai/**`
**Depends on:** WP-0 frozen `run.ts` signature. **Parallel with:** WP-1, WP-3

- Provider factory + swap matrix (§2).
- SQLite response cache (survives `db:reset`).
- Fail-loud resolver: cache → live → throw. Typed error classes (`ProviderUnreachable`, `SchemaViolation`, `Timeout`) so the UI can render a sensible message per case.
- 14 Zod schemas + 14 function modules + 14 fixtures (used **only** under `RELAY_AI_PROVIDER=mock`).
- Prompts carry operating-model + blueprint + prior-evidence context (spec §AI SYNTHESIS).

**Acceptance:** with the cloud reachable, all 14 return valid typed data. With it unreachable, every call throws a typed error that the UI renders deliberately — no silent fixtures, no white screens.

---

### WP-5 · Read-only surfaces — ~2.5h
**Owns:** `app/(app)/overview`, `/operating-model`, `/blueprint`, `/people`, `/knowledge`
**Depends on:** WP-1, WP-2, WP-3

- **Overview** — executive metrics row, knowledge-at-risk (CRITICAL/HIGH/MEDIUM), priority actions, recent captures, train-the-trainer progress.
- **Operating Model** — 9 area cards with transfer readiness; detail drawer showing all 8 dimensions.
- **Transfer Blueprint** — per area: formal / informal / technical / judgment / relationships / tools / governance, `✓△○` glyphs, local owner, transfer risk.
- **People** — profiles; **Capability Passport** (capability, level, evidence, exposures, last demonstrated, next recommended experience, trainer readiness).
- **Knowledge** — 7 categories, filter by area/capability/expert/person/type/validation status.

**Acceptance:** every surface reads real DB state. Nothing hardcoded. All reflect post-validation changes automatically.

---

### WP-6 · Flagship session loop ⭐ — ~3.5h
**Owns:** `app/(app)/sessions/**`, `app/actions/session.ts`
**Depends on:** WP-1, WP-2, WP-3, WP-4. **Highest priority after WP-0.**

Full stage machine: `PREPARE → CAPTURE → EXPERT DEBRIEF → LEARNER DEBRIEF → SYNTHESIS → VALIDATION → NEXT ACTION`

- **Prepare** — 30-second Session Brief (primary target, current level, today's objective, your role, ask-before-explaining, watch-for checklist, knowledge gap to explore). Generated from prior state, not hardcoded.
- **Capture** — paste transcript / session notes. Pre-loaded Clinic 14 transcript one click away.
- **Expert debrief** — ≤3 AI questions derived from the transcript. Persona-gated to Mitchell.
- **Learner debrief** — separate, understanding-probing. **Persona-gated to Kwame** — switching persona here is the demo's strongest single moment.
- **Synthesis** — the 4 spec'd findings: capability evidence · formal/informal gap · remaining gap · next activity. Each with evidence sources + confidence + **why RELAY recommended this**.
- **Validation** — `APPROVE` / `EDIT` / `NOT YET` per finding, independently. Writes `validations` + `capability_evidence`; only then updates level.
- **Next action** — becomes the next Session Brief.

**Acceptance:** approve the capability finding → Kwame's passport shows *Performed with Supervision → Performed Independently* with the evidence record attached and history intact.

---

### WP-7 · Readiness engine + dashboards — ~2h
**Owns:** `lib/readiness/**`, `app/(app)/readiness`
**Depends on:** WP-2, WP-3. **Parallel with:** WP-6

- Pure calculation module per §4, each metric returning its own inputs + formula.
- Readiness surface: OM readiness, capability localization, local ownership, trainer coverage, formal/informal transfer, expert dependency, departure readiness, knowledge at risk.
- **Departure Readiness** view: Mitchell header, 7/9 areas, 7/10 capabilities, 2 trainers, 18 insights, 3 risks, prioritized before-departure actions.
- **"How this is calculated"** popover on every score.
- **Knowledge propagation tree** — inline SVG, capability-filterable.

**Acceptance:** every number traces to a query. Numbers move after WP-6 validation.

---

### WP-8 · AI Companion + OM Builder — ~1.5h
**Owns:** `components/companion/**`, `app/(app)/operating-model/builder`
**Depends on:** WP-4, WP-5

- Companion: right-side panel, **page-aware**, suggested prompts per surface (spec §AI COMPANION). Not centered, not a chatbot-first UI.
- OM Builder: 8-step wizard, real Zod-validated extraction, **pre-filled with the spec's example answers** so it never faces a blank prompt on stage. Approve/Edit/Add/Remove on extracted components. Closes with the OM Review → "3 potential dependencies identified" → `[CREATE TRANSFER REQUIREMENTS]`.

**Acceptance:** Companion answers each spec'd per-page question sensibly. Wizard completes without a dead end.

---

### WP-9 · QA sweep + polish — ~1.5h
**Owns:** cross-cutting; no new files
**Depends on:** all

Spec's own final-QA instruction, executed literally. Walk the product as: Dr. Mitchell → Kwame → program manager → executive sponsor → hackathon judge. Log anything broken / confusing / redundant / unconvincing / visually weak / obviously mocked. Fix, then re-run the 15-step demo **twice**.

Checklist: loading states · designed error states · empty states · no layout shift · tabular numerics aligned · no horizontal scroll · no console errors · no TypeScript errors · **`db:reset` mid-demo recovers cleanly and keeps the cache warm**.

---

## 6. Dependency graph & dispatch sets

```
WP-0 (blocking, solo)
  │
  ├── WP-1 ───┐
  ├── WP-2 ───┼── WP-3 ──┐
  └── WP-4 ───┘          │
                         ├── WP-5 ──┐
                         ├── WP-6 ──┼── WP-8 ── WP-9
                         └── WP-7 ──┘
```

**Dispatch set A** (after WP-0): WP-1 ∥ WP-2 ∥ WP-4 — *3 concurrent, no shared files*
**Dispatch set B** (after WP-2): WP-3
**Dispatch set C** (after WP-3): WP-5 ∥ WP-6 ∥ WP-7 — *3 concurrent, no shared files*
**Dispatch set D:** WP-8 → WP-9

**Critical path:** WP-0 → WP-2 → WP-3 → WP-6 → WP-9 ≈ **10h**. Everything else absorbs into parallel slack.

Serial single-thread estimate ≈ 18.5h. Concurrency is what makes the one-day target reachable — it is not optional.

---

## 7. Spiral gates

No spiral closes without passing its gate. A failed gate re-scopes the *next* spiral, not the schedule.

| Spiral | WPs | Gate |
|---|---|---|
| S0 | WP-0 | All three spikes green; benchmark recorded in §9 |
| S1 | WP-1, WP-2, WP-4 | Every nav route loads; all 14 AI fns return valid typed data; errors render deliberately |
| S2 | WP-3, WP-5 | Product looks fully populated and credible; readiness reads ≈68% |
| S3 | WP-6 | Approve a finding → passport changes → evidence recorded |
| S4 | WP-7 | Readiness numbers move; every score explains itself |
| S5 | WP-8, WP-9 | Full 15-step demo, twice, clean |

---

## 8. Risk register

| # | Risk | Mitigation | Killed by |
|---|---|---|---|
| 1 | `gemma4:31b-cloud` unreachable on demo day → hard error by design | Pre-warm the cache in rehearsal; the demo path then never calls the network. Explicit `mock` mode as a manual last resort | WP-4, runbook |
| 2 | Nested-schema conformance fails on the 32B model | Benchmark `analyzeSession` first; flatten the schema if needed | WP-0 |
| 3 | The loop changes nothing visible | Entire thesis; dedicated gate S3 | WP-6 |
| 4 | Seed data reads as fake | Real writing time budgeted; tuned-number acceptance criterion | WP-3 |
| 5 | Readiness looks hand-wavy | Deterministic + formula popover | WP-7 |
| 6 | Demo drift between runs | Response cache + `db:reset` | WP-2, WP-4 |
| 7 | AI appears to auto-certify people | Invariant #1 enforced; `AI SUGGESTION` vs `VALIDATED BY` always distinct | WP-6 |
| 8 | Parallel agents collide | Exclusive file ownership per WP; contracts frozen in WP-0/WP-2 | §5 |
| 9 | Cloud cold-start makes the first live call slow | Measure in WP-0; warm the cache before presenting | WP-0 |

---

## 9. Benchmark results

*To be filled by WP-0.*

| Model | Schema | Runs | Valid | p50 latency | p95 latency | Cold start | Decision |
|---|---|---|---|---|---|---|---|
| `gemma4:31b-cloud` | `analyzeSession` | 5 | — | — | — | — | — |

---

## 10. Demo-day runbook

1. Rehearse the full 15-step path once end to end — this warms the AI response cache.
2. `npm run db:reset` immediately before presenting (cache survives).
3. Confirm `RELAY_AI_PROVIDER=ollama` and the Ollama cloud endpoint is reachable.
4. Persona starts as **Dr. Mitchell**, route `/overview`.
5. Run the spec's 15-step Demo Success Flow.
6. If anything desyncs: `db:reset` and resume — sub-second, cache intact.

**Closing line the product must earn:** *"When the expert leaves, does the expertise stay?"*

---

## 11. Open items

- [ ] WP-0 benchmark → §9
- [ ] `gemma4:31b-cloud` cold-start latency measured and judged tolerable
- [ ] Decide whether the OM Builder wizard is reachable in the demo path or shown only if time permits
