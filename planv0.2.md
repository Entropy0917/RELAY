# RELAY — Build Plan v0.2 (two-person, Flask + Jinja + HTMX)

**Supersedes:** `planv0.1.md` (Next.js stack — retained for the data model, readiness math, and risk register, all of which carry over unchanged).
**Team:** 2 engineers working concurrently, each dispatching their own subagents.
**Target:** polished working prototype, single-day build, RAD-concurrent spiral.
**Product intent source of truth:** `RELAY.txt`.
**Date:** 2026-09-26

---

## 0. Stack

| Layer | Choice | Replaces (v0.1) |
|---|---|---|
| Language | Python 3.13 (`uv` for env + deps) | Node/TypeScript |
| Framework | **Flask** | Next.js |
| Templating | **Jinja2** | React |
| Interactivity | **HTMX** (~14kb, no build step) | React client state |
| CSS | **Hand-rolled design tokens + Jinja macro component library** | Tailwind + shadcn/ui |
| Charts | **Inline SVG Jinja macros** | Recharts |
| DB | **SQLite + SQLAlchemy Core** (or raw `sqlite3`) | Drizzle |
| Schemas | **Pydantic v2** | Zod |
| AI client | **`openai` SDK with configurable `base_url`** | Vercel AI SDK |
| AI model | `gemma4:31b-cloud` via Ollama. **No silent fallback — unreachable = hard error** | unchanged |
| Auth | None. Three-persona switcher via Flask session cookie | unchanged |
| Deploy | localhost only | unchanged |

### Why hand-rolled CSS specifically for this stack
HTMX swaps **server-rendered fragments** into the DOM. With utility classes those fragments become verbose and the frontend/backend diff gets noisy; with semantic classes they stay small and readable. No watcher process to die mid-demo. And Jinja macros give the same reuse guarantee a component library does — one definition, one place to change.

### v0.1 is archived, not a reference

Everything still in force has been **inlined below** — the 12-table data model
into §4 B1, the readiness formula and weights into §4 B4, the fail-loud AI
policy into §4 B2, the risk register into §8.

**This document is self-contained. Do not read or cite `planv0.1.md`** — it
describes a Next.js/Drizzle/Zod stack we are not building, and citing it is how
someone ends up implementing against the wrong one. It stays in the repo as
history only.

---

## 0.5 Reusability constraint ⛔ NON-NEGOTIABLE

**No engagement content appears anywhere except the database.** Not in routes, not in services, not in templates, not in macros, not in prompts, not in fixtures.

If the string `Kwame`, `Mitchell`, `Ama`, `Kojo`, `Ghana`, `Clinic 14`, `antimalarial`, or any other seed proper noun appears outside `seed/`, it is a defect.

### The line: product vocabulary vs engagement content

Taken literally, "everything in the database" produces config-driven mush. The principled boundary:

| Lives in **code** (it *is* the product) | Lives in the **database** (it's tenant data) |
|---|---|
| The 7 Transfer Rails (Know → Observe → … → Teach) | Engagement, organization, sector, dates |
| The 7 capability levels 0–6 and their labels | People, roles, names |
| The 7 knowledge types | Capabilities and the taxonomy used |
| The 5 status states | Operating-model area names and contents |
| The 8 operating-model dimensions | Transfer requirements, sessions, knowledge items |
| The readiness formula shape | Readiness **weights** (per-engagement tunable) |

RELAY's *model* is the product and belongs in code. Everything an engagement fills in belongs in tables. If you find yourself unsure, ask: *would this differ for a Saudi manufacturing engagement?* If yes → database.

### Enforcement (not aspiration)

1. **`engagement_id` FK on every content table.** Every query is engagement-scoped. No unscoped `SELECT` reaches a template.
2. **`tests/test_no_baked_data.py`** — greps `app/`, `templates/`, `contracts/` for a banlist of seed proper nouns and fails the build on a hit. Written at SYNC-1, runs in CI-of-one. This is what makes the rule real.
3. **SYNC-1 fixtures use a *different* fictional engagement** — a manufacturing or utilities scenario, not Ghana. If the templates look right against both, they are genuinely data-driven. This proves reusability by construction rather than claiming it.
4. **Seed two engagements** (B3): Ghana in full depth, plus a thin second one. The engagement switcher in the shell then does something real.
5. **AI prompts take context as parameters** — never a hardcoded domain example. Few-shot examples, if used, come from the DB or are sector-neutral.

### Demo dividend

A judge asking *"is this just a Ghana demo?"* gets answered by clicking the engagement switcher. That is a materially stronger answer than a slide claiming the product generalizes.

---

## 1. The concurrency mechanism (read this before anything else)

Two people cannot work in parallel on a server-rendered app unless the seam between them is a **frozen data contract**. Everything below depends on this.

```
contracts/                      ← JOINT OWNERSHIP. Frozen at hour 1.
  viewmodels.py                 Pydantic model per page/partial = the template's context
  routes.py                     URL table: name, method, full-page|partial, viewmodel
  fixtures/*.json               one realistic fixture per viewmodel
```

**How it removes all blocking:**

- **Frontend** builds every template against `fixtures/*.json`, rendered through a **preview harness** (`/preview/<name>` — a Flask blueprint the frontend owns). They run the real app, see real layouts, with zero backend code existing.
- **Backend** builds services and routes that produce those exact same Pydantic models.
- At integration, the route swaps `load_fixture()` for `build_viewmodel()`. **The template never changes.**

Two rules that keep this honest:
1. A fixture that doesn't validate against its Pydantic model is a build error. Add a test at hour 1.
2. **Contract changes require both people.** Anyone can *propose*; nobody edits `contracts/` alone. This is the single most likely way a two-person day goes sideways.

### File ownership

| Owner | Paths |
|---|---|
| **Backend** (you) | `app/routes/**` · `app/services/**` · `app/db/**` · `app/ai/**` · `app/readiness/**` · `seed/**` · `scripts/**` |
| **Frontend** (teammate) | `templates/**` · `static/css/**` · `static/js/**` · `app/preview.py` |
| **Joint, frozen** | `contracts/**` |
| Bootstrap only | `app/__init__.py` · `pyproject.toml` (written once in SYNC-1, then effectively frozen) |

No path appears twice. Neither of you nor your subagents can collide.

---

## 2. Sync points

RAD-spiral needs scheduled convergence, not continuous merging. Four stops:

| Sync | ~Hour | What happens | Exit condition |
|---|---|---|---|
| **SYNC-1** | 0 → 1 | Together: freeze `contracts/`, scaffold Flask app, write fixtures | Fixtures validate; both can run the app |
| **SYNC-2** | ~5 | Wire read surfaces: backend routes render frontend templates with real data | Overview/OpModel/Blueprint/People/Knowledge live on real DB |
| **SYNC-3** | ~9 | Wire the flagship loop: session state machine + its templates | Approve a finding → Kwame's passport changes |
| **SYNC-4** | ~11 | Joint QA: five-persona walkthrough, demo run ×2 | Clean 15-step run, twice |

Between syncs you do not touch each other's files. At syncs you integrate and re-freeze.

---

## 3. SYNC-1 — Joint foundation ⛔ BLOCKING · ~60 min · both people

Nothing parallelizes until this is done. Do it together, at one screen.

1. `uv init`, deps: `flask jinja2 pydantic openai python-dotenv pytest`
2. `app/__init__.py` — app factory, registers `routes` and `preview` blueprints
3. **Freeze `contracts/viewmodels.py`** — one Pydantic model per page + per HTMX partial
4. **Freeze `contracts/routes.py`** — the URL table both sides code against
5. Write `contracts/fixtures/*.json` — **using a second fictional engagement, not Ghana** (§0.5). Realistic enough to design against; the full Ghana seed is B3
6. `tests/test_contracts.py` — every fixture validates against its model
7. `tests/test_no_baked_data.py` — banlist grep over `app/`, `templates/`, `contracts/` (§0.5)
7. **Risk spike (backend, 20 min):** `gemma4:31b-cloud` returns schema-valid output for the `SessionSynthesis` Pydantic model — the hardest one, 4 nested findings. 5 runs, record latency in §7.

**Gate:** both people can `flask run` and see something; both tests green. Spike passed, or the synthesis schema gets flattened (fewer nested levels, more top-level fields). Model does not get swapped; failure does not get hidden.

---

## 4. BACKEND TRACK — you

| # | Package | Owns | Depends on | Good subagent target? |
|---|---|---|---|---|
| **B1** | DB schema + reset | `app/db/**`, `scripts/reset.py` | SYNC-1 | Medium — you'll want to own the invariants |
| **B2** | AI layer | `app/ai/**` | SYNC-1 | Medium — spike first yourself, then delegate the 14 functions |
| **B3** | Seed corpus | `seed/**` | B1 | ✅ **Strongest delegation target** — heavy content writing |
| **B4** | Readiness engine | `app/readiness/**` | B1 | ✅ Pure functions + tests, self-contained |
| **B5** | Read-surface routes | `app/routes/read.py`, `app/services/**` | B1, B3 | ✅ Mechanical once contracts exist |
| **B6** | Session loop ⭐ | `app/routes/session.py`, `app/services/session.py` | B1, B2, B3 | ❌ **Keep this yourself** — it's the product |

### B1 · DB schema + reset — ~1h

**The data model — 12 tables**, plus `engagements` as the tenant root and
`ai_cache` owned by B2. Collapsed from the spec's 23 by one rule: *anything
displayed but never queried across becomes a typed JSON column.*

| Table | Notes |
|---|---|
| `engagements` | tenant root; org, sector, location, dates, per-engagement `readiness_weights` |
| `people` | role: `expert` \| `counterpart` \| `manager`; `departure_date` on experts |
| `capabilities` | the seeded capabilities; `criticality` feeds readiness weighting |
| `person_capabilities` | current level 0–6, `last_demonstrated`, `exposure_count` |
| `capability_evidence` | **append-only.** Never overwrite history (spec §STEP 6) |
| `operating_model_areas` | JSON cols for all 8 dimensions |
| `transfer_requirements` | 7 `RequirementKind`s; state `complete`/`partial`/`none` |
| `sessions` | stage enum drives the loop UI |
| `debriefs` | discriminated by `role: expert \| learner` |
| `findings` | AI output; `status: pending \| approved \| edited \| rejected` |
| `knowledge_items` | the 7 knowledge types; FK to area/capability/session/expert |
| `recommendations` | feeds the next Session Brief |
| `validations` | who validated what, when — the audit trail |

Four invariants — **enforced in the database, not by convention**:
1. AI never writes `person_capabilities.level` — only an approved validation does.
2. `capability_evidence` is insert-only.
3. No stored readiness scores; all derived at read time.
4. **`engagement_id` FK on every content table; no unscoped query reaches a template** (§0.5).

`python scripts/reset.py` → drop, migrate, seed, <1s. **Must preserve the `ai_cache` table** — a reset shouldn't cost you a warm demo.

### B2 · AI layer — ~2h
```
app/ai/
  provider.py    get_client() keyed on RELAY_AI_PROVIDER = mock|ollama|xai|anthropic|openai
  cache.py       sqlite ai_cache: (fn_name, sha256(input)) -> validated JSON
  run.py         cache → live → RAISE. Typed errors: ProviderUnreachable, SchemaViolation, Timeout
  schemas/       14 Pydantic models
  functions/     14 modules
  fixtures/      used ONLY under RELAY_AI_PROVIDER=mock
```
Provider swap = one env var, zero call-site changes. `openai` SDK with `base_url` covers Ollama / xAI / OpenAI; Anthropic gets its own thin adapter behind the same `get_client()`.

Structured output: Ollama's OpenAI-compatible endpoint takes `response_format={"type":"json_schema", ...}`; the native `ollama` package takes `format=<json schema>`. **WP-0 spike decides which path holds.**

**Acceptance:** cloud reachable → all 14 return valid typed data. Unreachable → typed error the UI renders deliberately. Never a silent fixture.

### B3 · Seed corpus — ~2.5h · delegate this
Highest "does this look real?" leverage in the build. Generic seed data is the #1 tell of a hackathon prototype.

**Seeds two engagements** (§0.5). All of it lives in `seed/` — nothing leaks into `app/` or `templates/`.

- Ghana community-health engagement; Dr. Sarah Mitchell (28 days out), Kwame Mensah, Ama Boateng, Kojo Asare
- 9 operating-model areas, each fully populated across all 8 dimensions
- 10 capabilities × per-person levels + dated, uneven, plausible evidence history
- ~18 validated knowledge items spanning all 7 types
- 3–4 prior sessions with outcomes, so Sessions isn't empty on open
- **A second, thin engagement** (different sector/geography) so the engagement switcher does something real
- **A genuinely well-written Clinic 14 transcript** — scanned or read aloud on stage. Must sound like two supply-chain professionals, not LLM filler.

**Acceptance:** readiness computes to ≈68% / ≈70% localization / 4 teachable / 3 expert-dependent. No lorem, no round-number-everything, dates consistent with a 9-month assignment 28 days from its end. **Fictional org explicitly not implied to be Peace Corps** (spec §DEMO SCENARIO).

### B4 · Readiness engine — ~1.5h · delegate this

Pure functions, no AI, no I/O. Each returns `{value, inputs, formula}` so the UI
can render a **"how this is calculated"** popover — the spec is explicit that no
score may be unexplained.

```
capability_localization  = critical caps with >=1 local counterpart at level >=4 / critical caps
locally_teachable        = count(caps with >=1 counterpart at level 6)
expert_dependent         = critical caps where the expert is capable AND no local >=4
local_ownership          = areas with a validated local owner / critical areas
formal_transfer          = formal requirements complete / total formal
informal_transfer        = informal requirements with validated capture / total informal
trainer_coverage         = areas with >=1 local trainer / critical areas

operating_model_readiness = 0.25*local_ownership + 0.30*capability_localization
                          + 0.15*formal_transfer + 0.20*informal_transfer
                          + 0.10*trainer_coverage
```

Thresholds: level ≥ `LEVEL_INDEPENDENT` (4) is localized; level == `LEVEL_TEACHER`
(6) is teachable. Both live in `contracts/vocabulary.py`.

Weights sit in one exported const and are surfaced verbatim in the popover. They
are **per-engagement tunable** (§0.5 puts weights in the database, the formula
shape in code), so they are a parameter with a documented default — never a
literal inside a function.

**Seed must be tuned so this yields ≈68% pre-demo and visibly increments after
validation.** That is a B3 acceptance criterion, not an accident.

### B5 · Read-surface routes — ~2h · delegate this
Services + routes producing the frozen view models for Overview, Operating Model, Transfer Blueprint, People, Knowledge. Mechanical once B1/B3 land.

### B6 · Session loop ⭐ — ~3h · keep this
`PREPARE → CAPTURE → EXPERT DEBRIEF → LEARNER DEBRIEF → SYNTHESIS → VALIDATION → NEXT ACTION`

State machine + HTMX partial endpoints. Persona gating via session cookie: expert debrief is Mitchell's, learner debrief is Kwame's. Validation writes `validations` + `capability_evidence`, and **only then** updates the level.

**Acceptance:** approve the capability finding → Kwame's passport reads *Performed with Supervision → Performed Independently*, evidence attached, history intact.

---

## 5. FRONTEND TRACK — teammate

| # | Package | Owns | Depends on | Good subagent target? |
|---|---|---|---|---|
| **F1** | Design system + shell | `static/css/**`, `templates/base.html`, `templates/_shell/**` | SYNC-1 | ❌ Keep — sets the visual voice |
| **F2** | Macro component library | `templates/macros/**` | F1 | Medium — delegate individual macros |
| **F3** | Read-surface templates | `templates/pages/{overview,operating_model,blueprint,people,knowledge}.html` | F2, fixtures | ✅ Strong target — 5 independent pages |
| **F4** | Session loop templates ⭐ | `templates/pages/session/**`, `templates/partials/**` | F2 | ❌ Keep — it's the demo |
| **F5** | Charts + propagation SVG | `templates/macros/charts.html` | F2 | ✅ Self-contained |
| **F6** | Preview harness | `app/preview.py` | SYNC-1 | Build first, 20 min |

### F6 · Preview harness — ~20 min · build this FIRST
A Flask blueprint: `/preview/<viewmodel_name>` loads the matching fixture, validates it, renders the real template. This is what lets the entire frontend track run before a single backend route exists. Twenty minutes that unblocks ten hours.

### F1 · Design system + shell — ~2h
- **Token layer** (`:root` custom properties): canvas, panel, elevated, hairline, text-primary/secondary/tertiary, one accent, five status colors
- **Status system** — one macro, five states, used everywhere: `SUSTAINABLE` · `ON TRACK` · `TRANSFER IN PROGRESS` · `AT RISK` · `CRITICAL`
- Transfer-requirement glyphs: `✓` complete · `△` partial · `○` none
- Capability chip 0–6 with a consistent color ramp
- **Designed error + retry state** for AI failures — required by the fail-loud policy. Must look deliberate, never like a crash.
- Shell: sidebar nav in spec order (Overview · Operating Model · Transfer Blueprint · People · Sessions · Knowledge · Readiness), engagement switcher, **persona switcher** (Mitchell / Kwame / Program Manager)
- Typography: one family, tight scale, **tabular numerics on every metric**

**Acceptance:** every status in the product renders through one macro. No ad-hoc colors. No emoji. No gradients.

### F2 · Macro component library — ~2h
The ~12 types RELAY actually needs: `status_badge` · `capability_chip` · `transfer_glyph` · `metric_tile` · `data_table` · `panel` · `drawer` · `stage_stepper` · `finding_card` · `evidence_item` · `formula_popover` · `error_state`.

**Acceptance:** no raw `<div class="...">` duplication across pages. If it appears twice, it's a macro.

### F3 · Read-surface templates — ~2.5h · delegate per page
Overview (executive metrics, knowledge-at-risk, priority actions, recent captures, train-the-trainer) · Operating Model (9 area cards + detail drawer, all 8 dimensions) · Transfer Blueprint (7 requirement categories with `✓△○`, local owner, risk) · People (profiles + **Capability Passport**) · Knowledge (7 categories, 6 filters).

### F4 · Session loop templates ⭐ — ~3h · keep
Seven stages, HTMX partials for approve/edit/reject, stage stepper, the two persona-gated debriefs, findings with **evidence sources + confidence + "why RELAY recommended this."**

### F5 · Charts + propagation — ~1.5h · delegate
SVG macros: horizontal readiness bars, the formal/informal dual-bar table, and the knowledge propagation tree (capability-filterable). Spec blesses simple: *"a clean diagram is sufficient."*

---

## 6. Parallel timeline

```
HOUR  0    1    2    3    4    5    6    7    8    9    10   11
      │ SYNC-1 │
BE    │████│ B1 │  B2   │  B3   │   B5   │    B6 ⭐     │ QA │
FE    │████│ F6 │  F1   │  F2   │   F3   │    F4 ⭐     │ QA │
                              ▲                      ▲      ▲
                           SYNC-2                 SYNC-3  SYNC-4

B4 (readiness) + F5 (charts) run as delegated subagent work in parallel throughout.
```

**Critical path:** SYNC-1 → B1 → B3 → B6 → SYNC-3 → SYNC-4 ≈ **11h**, with the frontend track fully absorbed in parallel.

Single-person serial estimate for the same scope ≈ 20h. **The two-track split is what makes the day work — it isn't an optimization.**

---

## 7. Benchmark results

Measured on `SessionSynthesis` — 4 heterogeneous nested findings, the hardest
structured output in the product. If this holds, every other schema is easier.
5 runs each. Scripts: `scripts/spike_structured_output.py` (paths A/B),
`scripts/spike_diagnose.py` (cause isolation), `scripts/spike_decide.py` (decision).

| Model | Path | Valid | p50 | max |
|---|---|---|---|---|
| `gemma4:31b-cloud` | `response_format` json_schema (OpenAI-compat) | **0/5** | 3.7s | — |
| `gemma4:31b-cloud` | `format=<schema>` (Ollama native) | **0/5** | 3.7s | — |
| `gemma4:31b-cloud` | unconstrained + schema in the prompt | **5/5** | **3.9s** | 16.1s |
| `gpt-oss:20b` (local) | `format=<schema>` constrained | **5/5** | 46.1s | 57.7s |
| `qwen3.5` (local) | `format=<schema>` constrained | **5/5** | 186.9s | 207.6s |

**What the failures actually were.** Not malformed JSON — markdown prose. The
cloud model never attempted JSON, which is the signature of the constraint
never reaching the sampler.

**Root cause (confirmed on a two-field schema, so complexity is excluded):**
Ollama's cloud routing drops constrained decoding. Both `format=<schema>` and
`format="json"` are no-ops on cloud-routed models; the same calls bind
correctly on local models. This is a property of the routing, not of gemma.

**Decision — primary path: `gemma4:31b-cloud`, unconstrained, schema in the prompt.**
12× faster than the nearest constrained alternative and 5/5 valid on the
hardest schema we have. The reasoning quality is also visibly better, which
matters because the synthesis output *is* the demo.

**What we give up, and what covers it.** Prompt-obedience is not a guarantee
the way grammar-constrained sampling is. Three things make that acceptable:

1. Every response is validated against the Pydantic model on our side. An
   unvalidated model response never reaches the database or a template.
2. One bounded retry on schema violation, same provider, appending the
   validation error to the prompt. This is a retry of the *same* path — not a
   provider substitution, so it does not violate the fail-loud policy.
3. Second failure → `ErrorPartialVM`, HTTP 502, nothing saved. Designed error
   state, not a stack trace, and never placeholder analysis.

**Offline path: `gpt-oss:20b`, constrained, selected by `RELAY_MODEL`.** If the
venue has no network, this is one env var and it is genuinely constrained — a
worse demo but a working one. 46s is too slow for live synthesis on stage, so
it runs behind the `ai_cache` (§4 B2) if we need it.

> ⚠️ **Not automatic.** Nothing falls back on its own. If the cloud provider is
> unreachable, RELAY errors. Switching to the local path is a deliberate act by
> a human with an env var.

**Also settled:** the OpenAI-compatible endpoint (`/v1/chat/completions`) works
against Ollama, so `openai` SDK + `base_url` remains the single code path for
ollama / xAI / OpenAI. The `response_format` *field* is what the cloud route
ignores — the endpoint itself is fine. We put the schema in the prompt and
validate ourselves, which is provider-portable anyway.

---

## 8. Risk register

| # | Risk | Mitigation | Owner |
|---|---|---|---|
| 1 | **Contract churn** — view models change mid-build, invalidating the other person's work | Freeze at SYNC-1; changes require both; fixture-validation test catches drift immediately | Joint |
| 2 | `gemma4:31b-cloud` unreachable on demo day → hard error by design | Pre-warm the cache in rehearsal; demo path then never calls the network | BE |
| 3 | Nested-schema conformance fails on a 32B model | Spike at SYNC-1; flatten the schema if needed | BE |
| 4 | The loop changes nothing visible | Entire product thesis; dedicated gate at SYNC-3 | BE + FE |
| 5 | Seed data reads as fake | Real writing time budgeted; tuned-number acceptance criterion | BE |
| 6 | **Hand-built CSS doesn't reach "premium"** | F1 before F2 before F3 — tokens first, never ad-hoc styling; enforce the no-raw-div rule | FE |
| 7 | HTMX partials return unstyled HTML | Partials render the same macros as full pages; never hand-write fragment HTML | FE |
| 8 | Demo drift between runs | AI response cache + `reset.py` | BE |
| 9 | AI appears to auto-certify people | Invariant #1; `AI SUGGESTION` vs `VALIDATED BY` always visually distinct | BE + FE |
| 10 | Subagents collide | Exclusive path ownership (§1); no two packages write the same file | Joint |
| 11 | **Seed data leaks into code**, killing reusability | `test_no_baked_data.py` banlist grep fails the build; fixtures use a non-Ghana engagement (§0.5) | Joint |
| 12 | Unscoped queries silently mix engagements | `engagement_id` FK everywhere; a scoped query helper is the only data-access path | BE |

---

## 9. Demo-day runbook

1. Rehearse the full 15-step path once — warms the AI response cache.
2. `python scripts/reset.py` immediately before presenting (cache survives).
3. Confirm `RELAY_AI_PROVIDER=ollama` and the Ollama cloud endpoint is reachable.
4. Persona = **Dr. Mitchell**, route `/overview`.
5. Run the spec's 15-step Demo Success Flow.
6. On desync: `reset.py` and resume — sub-second, cache intact.

**Closing line the product must earn:** *"When the expert leaves, does the expertise stay?"*

---

## 10. Open items

- [ ] SYNC-1 spike → §7
- [ ] Which Ollama structured-output path holds (`response_format` vs native `format=`)
- [ ] Whether the AI Companion panel and OM Builder wizard make the demo path or ship as time permits
- [ ] Confirm the persona switcher's third role (Program Manager) has a distinct enough view to justify existing
