# Proposal 001 — knowledge item detail

**Proposed by:** M4 (backend) · **Needs:** frontend sign-off before merge
**Target:** `contracts/viewmodels.py` · **Status:** open · **Supersedes:** the six-item v1

`contracts/**` is jointly owned. Anyone may propose; nobody edits it alone.

---

## Why this got shorter

v1 of this proposal asked for six fields. It was written before I had read
`origin/fe/contracts` — the contract you drafted during your own SYNC-1, which
you later set aside when you rebased onto the frozen one at `d818207`.

I read it properly. **Five of the six things I was proposing, you had already
designed, and designed better.** Those are not proposals any more — they are
your work, and I am implementing them as you specified. They are listed at the
bottom as an adoption log, not as decisions.

What is left is the one place the two designs disagree and ours holds up
better against the seeded data.

---

## The proposal: `KnowledgeCard.detail`

**The content exists and is invisible.** `knowledge_items.body` is a populated
JSON column across the whole seed. `KnowledgeCard` exposes none of it — only
`summary` reaches the screen, so every knowledge card in the demo shows one
line out of a paragraph.

**Why not your `KnowledgeItem` shape.** Yours is the Expert Insight template,
flattened onto every item:

```python
situation, observed_signals, expert_reasoning, recommended_response, why_it_matters
```

That is the right template for *one* of the seven knowledge types. The seed
holds **22 distinct body shapes across the 7 types**, and the keys vary within
a type as well as between them:

| type | actual body keys (n distinct shapes) |
|---|---|
| `formal_document` | `scope`, `sections`, `status`, `known_limits`, `authored_by` (2) |
| `relationship` | `who`, `what_works`, `what_does_not`, `at_risk`, `current_state` (2) |
| `heuristic` | `rule`, `caveat`, `applies_to`, `signals`, `worked_example` (4) |
| `exception` | `normal_rule`, `the_exception`, `how_to_recognise`, `what_to_do` (3) |
| `case` | `what_happened`, `root_cause`, `corrective_action`, `the_turn` (4) |
| `lesson_learned` | `what_we_learned`, `what_changed`, `residual_risk` (3) |
| `expert_insight` | `practice`, `why_it_is_not_written_down`, `worked_example` (4) |

A formal document has no "observed signals". A relationship record has no
"situation". Forcing the template on all of them renders empty strings on
roughly 22 of 25 cards — the failure mode is the one thing worse than showing
too little, which is showing blanks where the product promises depth.

**Proposed** — polymorphic, but in your style rather than a raw dict, so the
backend owns the humanising and the template never sees `why_it_is_not_written_down`:

```python
class DetailSection(BaseModel):
    """One labelled block of a knowledge item's body.

    Order is the author's. The backend humanises the body key into `label`;
    templates print `label` and never inspect the key.
    """

    label: str          # "Why it is not written down"
    body: str | list[str]


class KnowledgeCard(BaseModel):
    ...
    detail: list[DetailSection] = Field(default_factory=list)   # NEW
```

Additive, defaulted. Cards that ignore it keep working; fixtures that omit it
keep validating. `extract_tacit_knowledge` already emits matching structure for
newly captured items.

**Cost to you:** one loop in the knowledge card macro. **Cost to me:** the
key-to-label humanising and the ordering.

---

## Adoption log — no decision needed

These were in v1 as my proposals. Your design is better on each; I withdraw
mine and implement yours. Listed so you know what is coming, not to be approved.

| # | v1 asked for | Adopting instead, from `fe/contracts` | Why yours wins |
|---|---|---|---|
| 1 | `NextExperienceVM` mirroring the AI schema | `NextActionVM` + `ChangeItem` + `Rationale.if_not_transferred` | `ChangeItem{surface, label, before, after, href}` is demo steps 10–15 as a data structure. `Rationale.if_not_transferred` carries the line I argued the contract was missing — you already had it, on a reusable object rather than bolted to one VM. |
| 2 | `EvidenceItem{capability, summary, observed_on, ...}` | your `EvidenceItem` | `level_before`/`level_after` make the append-only history legible, and splitting `ai_interpretation` from `validated_by` is risk #9 enforced in the type rather than in a template. |
| 3 | `CapabilityRow.changed: bool` | `PassportRow.changed` — identical — plus `rail` and `evidence_count` | Same flag. Yours also carries the Transfer Rail, which is core product vocabulary (§0.5) that my row dropped entirely. |
| 4 | `ShellVM.days_until_departure` + `departing_expert_name` | `Departure{expert, departure_date, days_remaining}` | Two loose optionals vs one cohesive object that carries the date, so the header can read "24 Nov · 28 days" rather than a bare count. |
| 5 | withdrawn in v1 | `Formula{expression, inputs: list[FormulaInput]}` on every `Metric` | I withdrew this as unnecessary. It was not. `FormulaInput{label, value, display}` and `Metric.value: float` + `display: str` keep the exact number for charts and sorting while the backend owns rounding — my `value: str` threw the number away at the contract boundary. |

Also adopting, though never in v1: the discriminated `Finding` union in place of
my `body: dict[str, object]` (mine validates nothing), and `PropagationEdge`
with `state`/`label` in place of my `children: list[str]`.

**Sequencing.** These land as additive changes to the surviving contract, one
surface at a time — not as a swap back to `fe/contracts`. Your 16 templates and
SYNC-2 wiring are built against the frozen contract, and I am not asking you to
redo that work to recover shapes we can reach incrementally.

---

## Decision

**One item.** `KnowledgeCard.detail` — approve, defer, or reject.

If approved, the `contracts/` commit carries both names.
