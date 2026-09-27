"""The seven-stage session loop — B6's service layer.

PREPARE → CAPTURE → EXPERT DEBRIEF → LEARNER DEBRIEF → SYNTHESIS → VALIDATION → NEXT ACTION

This module owns the state machine and the orchestration between the database,
the AI layer, and the validation path.  The routes call *this*; the routes do
not call `app.db` or `app.ai` directly.

Two things here are deliberately opinionated:

  1. Stage order is enforced, not advisory.  Calling `advance` out of order is
     a `StageError`, not a no-op.  A stage that hasn't finished its work
     refuses to advance: SYNTHESIS cannot start until both debriefs exist,
     VALIDATION cannot start until findings exist.

  2. Persona gating is enforced here, not in the route.  The expert debrief
     belongs to the expert; the learner debrief to the learner.  The route
     passes the current persona; this module says yes or no.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from app.ai import (
    AIError,
    analyze_session,
    generate_expert_debrief,
    generate_learner_debrief,
    prepare_session,
    recommend_next_experience,
)
from app.ai.context import SessionContext
from app.ai.schemas.debrief import DebriefQuestions
from app.ai.schemas.next_activity import NextExperience
from app.ai.schemas.session_brief import SessionBrief
from app.ai.schemas.synthesis import SessionSynthesis
from app.db.adapters import session_context
from app.db.schema import (
    capabilities,
    debriefs,
    findings,
    people,
    person_capabilities,
    recommendations,
    sessions,
    validations,
)
from app.db.scoped import Scope
from app.db.writes import apply_validation
from contracts.viewmodels import (
    DebriefQuestion,
    ErrorPartialVM,
    FindingPartialVM,
    FindingVM,
    SessionBriefVM,
    SessionRef,
    SessionStageVM,
    PersonRef,
)
from contracts.vocabulary import (
    CAPABILITY_LEVELS,
    STAGE_LABEL,
    STAGE_ORDER,
    FindingKind,
    Role,
    SessionStage,
    ValidationAction,
)


class StageError(RuntimeError):
    """The requested stage transition is not valid from the current state."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _person_ref(row) -> PersonRef:
    name = row.name
    parts = name.split()
    initials = "".join(p[0].upper() for p in parts if p) or "?"
    return PersonRef(
        id=row.id,
        name=row.name,
        title=row.title,
        role=Role(row.role),
        initials=initials,
    )


def _session_ref(row, scope: Scope) -> SessionRef:
    expert = scope.by_id(people, row.expert_id)
    learner_ids = list(row.learner_ids or ())
    learner_rows = [scope.by_id(people, lid) for lid in learner_ids]

    cap = scope.by_id(capabilities, row.capability_id) if row.capability_id else None

    return SessionRef(
        id=row.id,
        title=row.title,
        date=str(row.held_on),
        stage=SessionStage(row.stage),
        stage_label=STAGE_LABEL[SessionStage(row.stage)],
        expert=_person_ref(expert) if expert else PersonRef(
            id=row.expert_id, name="Unknown", title="", role=Role.EXPERT, initials="?"
        ),
        learners=[_person_ref(lr) for lr in learner_rows if lr is not None],
        capability_focus=cap.name if cap else "",
    )


def _stepper(current: SessionStage, session_stage: SessionStage) -> list[dict[str, str]]:
    """Build the stage stepper data for the UI.

    Each entry gets state: 'completed' | 'current' | 'upcoming'.
    `session_stage` is the session's actual stage in the DB; `current` is the
    stage the user is viewing (which may be an earlier, already-completed one).
    """
    db_idx = STAGE_ORDER.index(session_stage)
    view_idx = STAGE_ORDER.index(current)
    steps = []
    for i, stage in enumerate(STAGE_ORDER):
        if i < db_idx:
            state = "completed"
        elif i == db_idx:
            state = "current"
        else:
            state = "upcoming"
        steps.append({
            "key": stage.value,
            "label": STAGE_LABEL[stage],
            "state": state,
        })
    return steps


# ---------------------------------------------------------------------------
# Session list
# ---------------------------------------------------------------------------

def list_sessions(scope: Scope) -> dict:
    """Build the SessionListVM data."""
    rows = scope.rows(sessions)
    upcoming = []
    past = []
    for row in rows:
        ref = _session_ref(row, scope)
        stage = SessionStage(row.stage)
        if stage == SessionStage.NEXT_ACTION:
            past.append(ref)
        else:
            upcoming.append(ref)
    return {"upcoming": upcoming, "past": past}


# ---------------------------------------------------------------------------
# Stage rendering
# ---------------------------------------------------------------------------

def _build_brief_vm(brief_data: dict | None) -> SessionBriefVM | None:
    if not brief_data:
        return None
    return SessionBriefVM(**brief_data)


# findings.status is past tense; FindingVM.validation_action is a ValidationAction.
_STATUS_ACTION = {"approved": "approve", "edited": "edit", "rejected": "reject"}


def _build_finding_vm(row, scope: Scope | None = None) -> FindingVM:
    """`scope` lets a re-rendered page show who validated each finding."""
    validated_by = None
    if scope is not None and row.status != "pending":
        rows = scope.rows(validations, validations.c.finding_id == row.id)
        if rows:
            latest = max(rows, key=lambda v: v.created_at)
            person = scope.by_id(people, latest.validated_by_id)
            validated_by = person.name if person else latest.validated_by_id
    action = None if row.status == "pending" else _STATUS_ACTION.get(row.status, row.status)
    return FindingVM(
        id=row.id,
        kind=FindingKind(row.kind),
        title=row.title,
        body=row.body or {},
        confidence=row.confidence,
        evidence_sources=list(row.evidence_sources or []),
        rationale=row.rationale,
        impact=row.impact,
        risk_if_untransferred=row.risk_if_untransferred,
        validated_by=validated_by,
        validation_action=action,
    )


def _debrief_questions(scope: Scope, session_id: str, role: str) -> list[DebriefQuestion]:
    """Load debrief questions for the given role from the DB."""
    rows = scope.rows(debriefs, debriefs.c.session_id == session_id)
    questions = []
    for row in rows:
        if row.role != role:
            continue
        for item in (row.questions or []):
            questions.append(DebriefQuestion(
                id=item.get("id", ""),
                question=item.get("question", ""),
                answer=item.get("answer"),
            ))
    return questions


def get_stage_vm(
    scope: Scope,
    session_id: str,
    stage: SessionStage,
    shell,
    persona_id: str | None = None,
    *,
    as_of: date | None = None,
) -> SessionStageVM:
    """Build a SessionStageVM for a given session and stage."""
    session = scope.by_id(sessions, session_id)
    if session is None:
        raise StageError(f"no session '{session_id}'")

    db_stage = SessionStage(session.stage)
    ref = _session_ref(session, scope)

    # You can view completed stages but not future ones
    if STAGE_ORDER.index(stage) > STAGE_ORDER.index(db_stage):
        raise StageError(
            f"session is at '{db_stage.value}'; cannot view '{stage.value}' yet"
        )

    brief_vm = _build_brief_vm(session.brief)

    # Load findings
    finding_rows = scope.rows(
        findings, findings.c.session_id == session_id
    )
    finding_vms = [_build_finding_vm(r, scope) for r in finding_rows]

    # Load debrief questions
    expert_qs = _debrief_questions(scope, session_id, "expert")
    learner_qs = _debrief_questions(scope, session_id, "learner")

    # Persona gating: determine whether the current user can act at this stage
    can_act = True
    blocked_reason = None
    if persona_id and stage in (SessionStage.EXPERT_DEBRIEF, SessionStage.LEARNER_DEBRIEF):
        expert_row = scope.by_id(people, session.expert_id)
        learner_ids = list(session.learner_ids or ())
        if stage == SessionStage.EXPERT_DEBRIEF:
            if persona_id != session.expert_id:
                can_act = False
                expert_name = expert_row.name if expert_row else "the expert"
                blocked_reason = f"This debrief belongs to {expert_name}."
        elif stage == SessionStage.LEARNER_DEBRIEF:
            if persona_id not in learner_ids:
                can_act = False
                blocked_reason = "This debrief belongs to the learner."

    # For VALIDATION, only the expert (or manager) validates
    if persona_id and stage == SessionStage.VALIDATION:
        learner_ids = list(session.learner_ids or ())
        if persona_id in learner_ids:
            can_act = False
            blocked_reason = "Learners cannot validate their own capability findings."

    return SessionStageVM(
        shell=shell,
        session=ref,
        stage=stage,
        stages=_stepper(stage, db_stage),
        brief=brief_vm,
        transcript=session.transcript,
        notes=session.notes,
        expert_questions=expert_qs,
        learner_questions=learner_qs,
        findings=finding_vms,
        can_act=can_act,
        blocked_reason=blocked_reason,
    )


# ---------------------------------------------------------------------------
# Stage advancing
# ---------------------------------------------------------------------------

def _next_stage(current: SessionStage) -> SessionStage:
    idx = STAGE_ORDER.index(current)
    if idx >= len(STAGE_ORDER) - 1:
        raise StageError("already at the final stage")
    return STAGE_ORDER[idx + 1]


def advance_stage(
    scope: Scope,
    session_id: str,
    from_stage: SessionStage,
    *,
    form_data: dict[str, Any] | None = None,
    persona_id: str | None = None,
    as_of: date | None = None,
) -> SessionStage:
    """Advance a session from `from_stage` to the next stage.

    Returns the new stage.  Raises StageError if the advance is invalid.
    """
    session = scope.by_id(sessions, session_id)
    if session is None:
        raise StageError(f"no session '{session_id}'")

    db_stage = SessionStage(session.stage)
    if db_stage != from_stage:
        raise StageError(
            f"session is at '{db_stage.value}', cannot advance from '{from_stage.value}'"
        )

    # Stage-specific work before advancing
    if from_stage == SessionStage.PREPARE:
        _on_leave_prepare(scope, session, as_of=as_of or date.today())
    elif from_stage == SessionStage.CAPTURE:
        _on_leave_capture(scope, session, form_data)
    elif from_stage == SessionStage.EXPERT_DEBRIEF:
        _on_leave_expert_debrief(scope, session, form_data, persona_id)
    elif from_stage == SessionStage.LEARNER_DEBRIEF:
        _on_leave_learner_debrief(scope, session, form_data, persona_id)
    elif from_stage == SessionStage.SYNTHESIS:
        _guard_synthesis_complete(scope, session_id)
    elif from_stage == SessionStage.VALIDATION:
        # Validation itself happens per-finding via validate_finding. What is
        # left on the way out is the recommendation, generated only now so it
        # sees the levels the validated findings just moved.
        _on_leave_validation(scope, session, as_of=as_of or date.today())
    elif from_stage == SessionStage.NEXT_ACTION:
        raise StageError("cannot advance past the final stage")

    next_s = _next_stage(from_stage)
    scope.update(sessions, session_id, stage=next_s.value)
    return next_s


def _on_leave_prepare(scope: Scope, session, *, as_of: date) -> None:
    """Generate the session brief (AI) when leaving PREPARE."""
    if session.brief:
        return  # already generated, cached
    ctx = session_context(scope, session.id, as_of=as_of)
    brief: SessionBrief = prepare_session(ctx)
    scope.update(sessions, session.id, brief=brief.model_dump())


def _on_leave_validation(scope: Scope, session, *, as_of: date) -> None:
    """Generate the next-experience recommendation (AI) when leaving VALIDATION.

    NEXT_ACTION was the one stage that produced nothing: the function existed,
    was tested, and was never called. It runs here rather than at synthesis so
    that it reads the capability levels the validated findings have already
    moved -- recommending what someone should do next is only honest once the
    record says where they now stand.

    Stored whole. The view model that carries it to the screen is still under
    discussion (PROPOSAL-001, item 1), and persisting the full object means
    that decision costs a passthrough rather than another AI call.
    """
    if session.next_experience:
        return  # already generated, cached
    ctx = session_context(scope, session.id, as_of=as_of)
    recommendation: NextExperience = recommend_next_experience(ctx)
    scope.update(
        sessions, session.id, next_experience=recommendation.model_dump()
    )


def _on_leave_capture(scope: Scope, session, form_data: dict | None) -> None:
    """Save transcript/notes submitted during CAPTURE."""
    updates: dict[str, Any] = {}
    if form_data:
        if "transcript" in form_data:
            updates["transcript"] = form_data["transcript"]
        if "notes" in form_data:
            updates["notes"] = form_data["notes"]
    if updates:
        scope.update(sessions, session.id, **updates)


def _on_leave_expert_debrief(
    scope: Scope, session, form_data: dict | None, persona_id: str | None
) -> None:
    """Save expert debrief answers, or generate the questions if first visit."""
    # Check persona
    if persona_id and persona_id != session.expert_id:
        raise StageError("only the expert can complete the expert debrief")

    _save_debrief_answers(scope, session.id, "expert", session.expert_id, form_data)


def _on_leave_learner_debrief(
    scope: Scope, session, form_data: dict | None, persona_id: str | None
) -> None:
    """Save learner debrief answers."""
    learner_ids = list(session.learner_ids or ())
    if persona_id and persona_id not in learner_ids:
        raise StageError("only the learner can complete the learner debrief")

    # Use the first learner as the debrief owner
    person_id = persona_id or (learner_ids[0] if learner_ids else session.expert_id)
    _save_debrief_answers(scope, session.id, "learner", person_id, form_data)


def _save_debrief_answers(
    scope: Scope, session_id: str, role: str, person_id: str,
    form_data: dict | None,
) -> None:
    """Update or create a debrief with the submitted answers."""
    existing = [
        row for row in scope.rows(debriefs, debriefs.c.session_id == session_id)
        if row.role == role
    ]

    # Merge answers from form_data into the existing questions
    if existing:
        debrief_row = existing[0]
        questions = list(debrief_row.questions or [])
        if form_data:
            answer_map = {k: v for k, v in form_data.items() if k.startswith("answer_")}
            for q in questions:
                key = f"answer_{q.get('id', '')}"
                if key in answer_map:
                    q["answer"] = answer_map[key]
        scope.update(debriefs, debrief_row.id, questions=questions, completed_at=_now())
    else:
        # No debrief yet: create one with the answers if provided
        questions = []
        if form_data and "questions" in form_data:
            questions = form_data["questions"]
        scope.insert(
            debriefs,
            id=_new_id("db"),
            session_id=session_id,
            role=role,
            person_id=person_id,
            questions=questions,
            completed_at=_now(),
        )


def _guard_synthesis_complete(scope: Scope, session_id: str) -> None:
    """SYNTHESIS → VALIDATION requires that findings exist."""
    finding_rows = scope.rows(findings, findings.c.session_id == session_id)
    if not finding_rows:
        raise StageError("synthesis has not produced findings yet; run synthesize first")


# ---------------------------------------------------------------------------
# AI: generate debrief questions
# ---------------------------------------------------------------------------

def generate_debrief(
    scope: Scope,
    session_id: str,
    role: str,
    *,
    as_of: date | None = None,
) -> list[DebriefQuestion]:
    """Generate AI debrief questions and persist them.  Returns the questions."""
    ctx = session_context(scope, session_id, as_of=as_of or date.today())

    if role == "expert":
        result: DebriefQuestions = generate_expert_debrief(ctx)
    else:
        result = generate_learner_debrief(ctx)

    questions = []
    for q in result.questions:
        questions.append({
            "id": _new_id("dq"),
            "question": q.question,
            "answer": None,
        })

    # Look for existing debrief row, or create
    session = scope.by_id(sessions, session_id)
    person_id = session.expert_id if role == "expert" else (
        (session.learner_ids or [session.expert_id])[0]
    )

    existing = [
        row for row in scope.rows(debriefs, debriefs.c.session_id == session_id)
        if row.role == role
    ]
    if existing:
        scope.update(debriefs, existing[0].id, questions=questions)
    else:
        scope.insert(
            debriefs,
            id=_new_id("db"),
            session_id=session_id,
            role=role,
            person_id=person_id,
            questions=questions,
        )

    return [
        DebriefQuestion(id=q["id"], question=q["question"], answer=None)
        for q in questions
    ]


# ---------------------------------------------------------------------------
# AI: synthesize
# ---------------------------------------------------------------------------

def synthesize(
    scope: Scope,
    session_id: str,
    *,
    as_of: date | None = None,
) -> list[FindingVM]:
    """Run AI synthesis, persist findings, and return the view models.

    This is the centrepiece: the AI produces four findings, each of which a
    human validates.  Nothing here writes a level or evidence — that waits for
    `validate_finding`.
    """
    session = scope.by_id(sessions, session_id)
    if session is None:
        raise StageError(f"no session '{session_id}'")

    db_stage = SessionStage(session.stage)
    if db_stage != SessionStage.SYNTHESIS:
        raise StageError(
            f"session is at '{db_stage.value}'; synthesis requires stage 'synthesis'"
        )

    # Don't re-synthesize if findings already exist
    existing = scope.rows(findings, findings.c.session_id == session_id)
    if existing:
        return [_build_finding_vm(r, scope) for r in existing]

    ctx = session_context(scope, session_id, as_of=as_of or date.today())
    synthesis: SessionSynthesis = analyze_session(ctx)

    # Persist the four findings
    result: list[FindingVM] = []
    for finding_obj in [
        synthesis.capability_evidence,
        synthesis.tacit_knowledge,
        synthesis.remaining_gap,
        synthesis.next_activity,
    ]:
        fid = _new_id("fnd")
        kind = FindingKind(finding_obj.kind)
        body = finding_obj.model_dump(exclude={"kind"})

        title = _finding_title(finding_obj)
        confidence = getattr(finding_obj, "confidence", "medium")
        evidence_sources = getattr(finding_obj, "evidence_sources", [])
        rationale = _finding_rationale(finding_obj)
        impact = _finding_impact(finding_obj, session)
        risk = _finding_risk(finding_obj)

        scope.insert(
            findings,
            id=fid,
            session_id=session_id,
            kind=kind.value,
            title=title,
            body=body,
            confidence=confidence,
            evidence_sources=evidence_sources,
            rationale=rationale,
            impact=impact,
            risk_if_untransferred=risk,
            status="pending",
        )
        result.append(FindingVM(
            id=fid,
            kind=kind,
            title=title,
            body=body,
            confidence=confidence,
            evidence_sources=evidence_sources,
            rationale=rationale,
            impact=impact,
            risk_if_untransferred=risk,
        ))

    # Move to validation now that findings exist
    scope.update(sessions, session_id, stage=SessionStage.VALIDATION.value)
    return result


def _finding_title(obj) -> str:
    if hasattr(obj, "title"):
        return obj.title
    if hasattr(obj, "capability"):
        return f"Capability: {obj.capability}"
    if hasattr(obj, "objective"):
        return obj.objective
    return "Finding"


def _finding_rationale(obj) -> str:
    if hasattr(obj, "evidence") and isinstance(obj.evidence, str):
        return obj.evidence
    if hasattr(obj, "expert_reasoning"):
        return obj.expert_reasoning
    if hasattr(obj, "understands"):
        return obj.understands
    if hasattr(obj, "recommended_experience"):
        return obj.recommended_experience
    return ""


def _finding_impact(obj, session) -> str:
    if hasattr(obj, "operating_model_area"):
        return obj.operating_model_area
    return session.title


def _finding_risk(obj) -> str:
    if hasattr(obj, "why_it_matters"):
        return obj.why_it_matters
    if hasattr(obj, "not_yet_demonstrated"):
        items = obj.not_yet_demonstrated
        if isinstance(items, list):
            return "; ".join(items)
    if hasattr(obj, "expert_role"):
        return obj.expert_role
    return ""


# ---------------------------------------------------------------------------
# Finding validation
# ---------------------------------------------------------------------------

def validate_finding(
    scope: Scope,
    session_id: str,
    finding_id: str,
    action: ValidationAction,
    persona_id: str,
    *,
    as_of: date | None = None,
    edited_body: dict | None = None,
    note: str | None = None,
) -> FindingVM:
    """Validate a single finding: approve, edit, or reject.

    For capability_evidence findings with action=approve and a suggested_level
    that differs from current, this triggers the full validation path:
      validation → evidence → level (trigger-enforced)
    """
    finding = scope.by_id(findings, finding_id)
    if finding is None:
        raise StageError(f"no finding '{finding_id}'")
    if finding.session_id != session_id:
        raise StageError("finding does not belong to this session")

    session = scope.by_id(sessions, session_id)

    # Determine if this is a capability-level-changing approval
    pc_id = None
    new_level = None
    evidence_summary = None

    body = edited_body if edited_body is not None else finding.body

    if (
        action == ValidationAction.APPROVE
        and FindingKind(finding.kind) == FindingKind.CAPABILITY_EVIDENCE
    ):
        # Extract the level data from the finding body
        suggested = body.get("suggested_level")
        current = body.get("current_level")
        person_name = body.get("person", "")
        capability_name = body.get("capability", "")

        if suggested is not None and current is not None and suggested != current:
            # Find the person_capability row for this finding
            pc_id = _resolve_person_capability(
                scope, session, person_name, capability_name
            )
            new_level = suggested
            evidence_summary = body.get("evidence", finding.title)

    validation_id = apply_validation(
        scope,
        finding_id=finding_id,
        validated_by_id=persona_id,
        action=action.value,
        person_capability_id=pc_id,
        new_level=new_level,
        evidence_summary=evidence_summary,
        evidence_source=f"session:{session_id}",
        observed_on=as_of or date.today(),
        edited_body=edited_body,
        note=note,
    )

    # Re-read the finding after the update
    updated = scope.by_id(findings, finding_id)
    vm = _build_finding_vm(updated)
    # Attach validation info
    validator = scope.by_id(people, persona_id)
    vm.validated_by = validator.name if validator else persona_id
    vm.validation_action = action.value
    return vm


def _resolve_person_capability(
    scope: Scope, session, person_name: str, capability_name: str
) -> str | None:
    """Find the person_capability ID from fuzzy name matches.

    The AI output has names as strings; the DB has IDs.  We match by looking
    at the session's learners and the session's capability.
    """
    learner_ids = list(session.learner_ids or ())

    # Find the capability by the session's capability_id first, then by name
    cap_id = session.capability_id
    if not cap_id:
        # fallback: search by name
        for cap_row in scope.rows(capabilities):
            if cap_row.name.lower() == capability_name.lower():
                cap_id = cap_row.id
                break

    if not cap_id:
        return None

    # Find the person
    person_id = None
    for lid in learner_ids:
        p = scope.by_id(people, lid)
        if p and p.name.lower() == person_name.lower():
            person_id = lid
            break

    if not person_id and learner_ids:
        # If only one learner, use them (the session is about their capability)
        if len(learner_ids) == 1:
            person_id = learner_ids[0]

    if not person_id:
        return None

    # Find the person_capability row
    for row in scope.rows(
        person_capabilities,
        person_capabilities.c.person_id == person_id,
        person_capabilities.c.capability_id == cap_id,
    ):
        return row.id

    return None
