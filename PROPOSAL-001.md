# Proposal 001 — additive view-model fields

**Proposed by:** M4 (backend) · **Needs:** frontend sign-off before merge
**Target:** `contracts/viewmodels.py` · **Status:** open

`contracts/**` is jointly owned. Anyone may propose; nobody edits it alone.
This is one batched proposal rather than six separate ones so the shell
change — which touches every page and every fixture — lands exactly once.

Every field below is **additive with a default**. Nothing is renamed, nothing
is removed, no existing field changes type. Templates that ignore these
fields keep working; fixtures that omit them keep validating.

---

## Summary

| # | Change | VM | Status | Blast radius |
|---|--------|-----|--------|--------------|
| 1 | `next_experience` | `SessionStageVM` | **backend already done** — passthrough only | one stage template |
| 2 | `evidence` | `PassportVM` | rows already read | one page |
| 3 | `changed` | `CapabilityRow` | known at validation | wherever rows render |
| 4 | `days_until_departure` | `ShellVM` | helper already exists | **every page, every fixture** |
| 5 | `formula` / `inputs` | `RiskItem` | ~~**withdrawn** — solved without a contract change~~ | — |
| 6 | `detail` | `KnowledgeCard` | **now priced** — content already in the DB | one page |

**Five decisions left: 1, 2, 3, 4, 6.** Item 5 is withdrawn. Item 1's backend
is built and committed, so approving it is a one-line passthrough.

---

## 1. `SessionStageVM.next_experience` — the one that matters

**Backend is done** (`3fc1f0b`). `recommend_next_experience` now runs on
leaving VALIDATION — after validation rather than at synthesis, so it reads
the levels the validated findings just moved — and the whole recommendation is
persisted to `sessions.next_experience`. Approving this item costs a
passthrough, not an AI call or a rewrite.

**What was wrong.** The last stage of the loop generated nothing:
`recommend_next_experience` was imported at `app/services/session.py:33` and
never called, and `SessionStageVM(...)` never passed `next_brief`. Demo step 15
showed an empty panel.

**Already visible without any contract change:** `CapabilityRow.next_experience`
has been in the frozen contract all along and was `None` on all 40 instances.
It now shows the recommended work on the learner's row. So the recommendation
already reaches the screen — this item is about the NEXT_ACTION panel, where
`rail`, `urgency` and `risk_if_deferred` have nowhere to go.

**Why not just fill `next_brief`.** The contract offers
`next_brief: SessionBriefVM`. The built AI function returns `NextExperience`,
which is a different shape:

| `SessionBriefVM` wants | `NextExperience` gives |
|---|---|
| `primary_target` | `capability` |
| `todays_objective` | `objective` |
| `your_role` | `expert_role` |
| `watch_for` | `learner_responsibilities` |
| `ask_before_explaining` | **nothing** |
| — | `rail`, `urgency`, `risk_if_deferred`, `rationale` — dropped |

Mapping one onto the other means **inventing `ask_before_explaining` out of
nothing** and discarding `risk_if_deferred` and `urgency`. For a product about
someone leaving, "what stays expert-dependent if this doesn't happen before
the expert goes" is the line that sells it. Fabricating a coaching question
also breaks the fail-loud rule in spirit: the screen would show a sentence no
model produced.

**Proposed.** A new VM mirroring the existing AI schema, plus one field:

```python
class NextExperienceVM(BaseModel):
    """NEXT_ACTION output. Mirrors app.ai.schemas.next_activity.NextExperience."""

    capability: str
    current_level: int = Field(ge=0, le=6)
    target_level: int = Field(ge=0, le=6)
    rail: Rail
    objective: str
    recommended_experience: str
    learner_responsibilities: list[str]
    expert_role: str
    rationale: str
    risk_if_deferred: str
    urgency: Literal["low", "medium", "high"]


class SessionStageVM(BaseModel):
    ...
    next_brief: SessionBriefVM | None = None      # unchanged
    next_experience: NextExperienceVM | None = None   # NEW
```

`next_brief` stays exactly as it is. If a real next session ever gets
scheduled, `prepare_session` fills it honestly. Until then it stays `None`
instead of holding a half-invented brief.

**Backend:** call `recommend_next_experience` on leaving VALIDATION, persist
to `sessions`, pass through. Cached like every other AI call.

---

## 2. `PassportVM.evidence`

**Problem.** `evidence_count: int` is a number with nothing behind it — the
one place in the app where a figure has no explanation. The rows exist and are
already read in `app.db.adapters._capability_states`.

```python
class EvidenceItem(BaseModel):
    capability: str
    summary: str
    observed_on: str | None = None
    source_session: str | None = None
    validated_by: str | None = None


class PassportVM(BaseModel):
    ...
    evidence_count: int                              # unchanged
    evidence: list[EvidenceItem] = Field(default_factory=list)   # NEW
```

Worth doing because the passport is the artifact the product claims a person
can carry to their next job. A count alone doesn't survive that claim.

---

## 3. `CapabilityRow.changed`

**Problem.** After a finding is validated, a level moves. Nothing in the VM
says which row moved, so the frontend can't highlight it — and the moment
readiness visibly responds is the SYNC-3 gate.

```python
class CapabilityRow(BaseModel):
    ...
    changed: bool = False   # NEW — set only on the row this action moved
```

Scoped deliberately: `changed` means *this request's action moved it*, not
"recently changed". No timestamps, no diffing against stored history.

---

## 4. `ShellVM.days_until_departure` — highest blast radius

**Problem.** The countdown is the product's whole tension and it currently
appears only on Overview. The shell wraps every page.

```python
class ShellVM(BaseModel):
    ...
    days_until_departure: int | None = None   # NEW
    departing_expert_name: str | None = None  # NEW
```

Negative is meaningful — the expert has already left. `None` means no
departure date on record, not zero. `adapters._days_until` already computes
this against `as_of`, never `date.today()`, so a demo rehearsed today and
presented tomorrow shows the same number.

**Flagging honestly:** this is the one change that touches every fixture and
every template. If the frontend is mid-flight on shell markup, this is the
item to defer — the other four are independent of it.

---

## 5. `RiskItem.formula` / `inputs`

**Withdrawn.** Shipped without a contract change (`8e2cbb0`): risk
explanations fold the deciding numbers into `problem`, and `local_trainer` —
also hardcoded `None` — is now driven by the engine's `teachers` input.

Kept here only as a note. If risks ever want the same "how is this calculated"
popover as metrics, the fields would be:

```python
class RiskItem(BaseModel):
    ...
    formula: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict)
```

`RiskFinding` already carries both. **Not proposed — no decision needed.**

---

## 6. `KnowledgeCard.detail` — priced, and bigger than it looked

**The content already exists and is invisible.** `knowledge_items.body` is a
populated JSON column across the whole seed, holding `scope`, `sections`,
`known_limits`, `status`, `authored_by`. `KnowledgeCard` exposes none of it —
only `summary` reaches the screen. Every knowledge card in the demo is showing
one line out of a paragraph.

`extract_tacit_knowledge` produces matching structure for new items:
`situation`, `content`, `why_it_matters`, `source`.

```python
class KnowledgeCard(BaseModel):
    ...
    detail: dict[str, Any] = Field(default_factory=dict)   # NEW
```

A free-form dict because `body` genuinely varies per item — a written
procedure has `sections`, a judgement call has `known_limits`. A fixed schema
would force empty keys on most cards. The frontend renders whatever keys are
present.

`capability` on this card was also hardcoded `None` while 23 of 25 rows had a
`capability_id`; fixed in `7f04ad0`, no contract change needed.

---

## Decision

Five items: **1, 2, 3, 4, 6** (5 withdrawn). Per item, one of: **approve**,
**defer**, **reject**.

Suggested order if time is short — **1** (already built, passthrough only),
then **6** (most hidden content per line of work), then **2**, then **4**.
Item 3 is polish. **Item 4 is the one to defer if shell markup is in flight** —
it is the only change that touches every page and every fixture.

On approval I implement the backend side and the `contracts/` commit carries
both names.
