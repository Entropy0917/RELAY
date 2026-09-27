"""Session loop routes — B6 (planv0.2.md section 4).

Thin layer between HTTP and the session service. Every route:
  - opens a connection + Scope
  - builds the shell (engagement/persona from session cookie)
  - delegates to app.services.session
  - returns the rendered view model or a redirect

AI errors are caught here and turned into 502 + ErrorPartialVM, exactly as the
fail-loud policy requires.  No fallback, no mock, no degradation.
"""

from __future__ import annotations

from datetime import date

from flask import (
    Blueprint,
    abort,
    redirect,
    request,
    session as flask_session,
    url_for,
)

from app.ai.errors import AIError
from app.db.connection import connect
from app.preview import render_vm, wants_json
from app.db.schema import engagements, people, sessions
from app.db.scoped import Scope, list_engagements, primary_engagement
from app.services.session import (
    StageError,
    advance_stage,
    generate_debrief,
    get_stage_vm,
    list_sessions,
    synthesize,
    validate_finding,
)
from contracts.viewmodels import (
    EngagementRef,
    ErrorPartialVM,
    NavItem,
    PersonRef,
    ShellVM,
    SessionListVM,
    SessionStageVM,
    FindingPartialVM,
)
from contracts.routes import NAV, ROUTES
from contracts.vocabulary import (
    Role,
    SessionStage,
    STAGE_LABEL,
    ValidationAction,
)

bp = Blueprint("sessions", __name__)


# ---------------------------------------------------------------------------
# Shell builder — shared by every route here
# ---------------------------------------------------------------------------

def _get_as_of() -> date:
    """Allow pinning the date for demo rehearsal via env or query param."""
    import os
    pinned = os.environ.get("RELAY_SEED_TODAY") or request.args.get("as_of")
    if pinned:
        try:
            return date.fromisoformat(pinned)
        except ValueError:
            pass
    return date.today()


def _build_shell(conn, engagement_id: str, persona_id: str | None) -> ShellVM:
    """Build the ShellVM that wraps every page."""
    all_engs = list_engagements(conn)
    current_eng = None
    eng_refs = []
    for row in all_engs:
        ref = EngagementRef(id=row.id, name=row.name, org=row.org)
        eng_refs.append(ref)
        if row.id == engagement_id:
            current_eng = ref

    if current_eng is None and eng_refs:
        current_eng = eng_refs[0]

    scope = Scope(conn, engagement_id)

    # Personas: all people in this engagement
    people_rows = scope.rows(people)
    persona_refs = []
    current_persona = None
    for p in people_rows:
        ref = _person_ref(p)
        persona_refs.append(ref)
        if p.id == persona_id:
            current_persona = ref

    if current_persona is None and persona_refs:
        current_persona = persona_refs[0]

    # Nav
    nav_items = []
    for key, label in NAV:
        route = ROUTES.get(key)
        if route:
            try:
                href = url_for(route.endpoint)
            except Exception:
                href = "#"
        else:
            href = "#"
        nav_items.append(NavItem(
            key=key,
            label=label,
            href=href,
            active=(key == "session_list"),
        ))

    return ShellVM(
        nav=nav_items,
        engagements=eng_refs,
        current_engagement=current_eng,
        personas=persona_refs,
        current_persona=current_persona,
    )


def _person_ref(row) -> PersonRef:
    name = row.name
    parts = name.split()
    initials = "".join(p[0].upper() for p in parts if p) or "?"
    return PersonRef(
        id=row.id, name=row.name, title=row.title,
        role=Role(row.role), initials=initials,
    )


def _resolve_engagement_and_persona(conn):
    """Read the session cookie for engagement + persona, falling back to defaults."""
    engagement_id = flask_session.get("engagement_id")
    persona_id = flask_session.get("persona_id")

    if not engagement_id:
        try:
            eng = primary_engagement(conn)
            engagement_id = eng.id
        except RuntimeError:
            abort(500, "no engagement in the database — run scripts/reset.py")
    return engagement_id, persona_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route("/sessions")
def index():
    """Session list page."""
    with connect() as conn:
        engagement_id, persona_id = _resolve_engagement_and_persona(conn)
        scope = Scope(conn, engagement_id)
        shell = _build_shell(conn, engagement_id, persona_id)
        data = list_sessions(scope)
        return render_vm("session_list", SessionListVM(shell=shell, **data))


@bp.route("/sessions/<session_id>/<stage>")
def stage(session_id: str, stage: str):
    """Session stage page — the seven-step loop."""
    try:
        stage_enum = SessionStage(stage)
    except ValueError:
        abort(400, f"unknown stage: {stage}")

    with connect() as conn:
        engagement_id, persona_id = _resolve_engagement_and_persona(conn)
        scope = Scope(conn, engagement_id)
        shell = _build_shell(conn, engagement_id, persona_id)
        as_of = _get_as_of()

        try:
            vm = get_stage_vm(
                scope, session_id, stage_enum, shell,
                persona_id=persona_id, as_of=as_of,
            )
        except StageError as exc:
            abort(400, str(exc))

        return render_vm("session_stage", vm)


@bp.route("/sessions/<session_id>/<stage>/advance", methods=["POST"])
def advance(session_id: str, stage: str):
    """Record stage input and move to the next stage."""
    try:
        stage_enum = SessionStage(stage)
    except ValueError:
        abort(400, f"unknown stage: {stage}")

    form_data = request.get_json(silent=True) or dict(request.form)
    as_of = _get_as_of()

    with connect() as conn:
        engagement_id, persona_id = _resolve_engagement_and_persona(conn)
        scope = Scope(conn, engagement_id)

        try:
            new_stage = advance_stage(
                scope, session_id, stage_enum,
                form_data=form_data,
                persona_id=persona_id,
                as_of=as_of,
            )
        except StageError as exc:
            abort(400, str(exc))
        except AIError as exc:
            if wants_json():
                retry_href = url_for(
                    "sessions.advance", session_id=session_id, stage=stage
                )
                return exc.as_error_partial(retry_href=retry_href).model_dump(), 502
            # A plain form POST: re-render this stage with the designed error and
            # the user's input kept, so resubmitting the form is the retry.
            shell = _build_shell(conn, engagement_id, persona_id)
            vm = get_stage_vm(
                scope, session_id, stage_enum, shell,
                persona_id=persona_id, as_of=as_of,
            )
            kept = {k: form_data[k] for k in ("transcript", "notes") if form_data.get(k)}
            return render_vm(
                "session_stage", vm.model_copy(update=kept), 502,
                error=exc.as_error_partial(retry_href=None),
            )

    # Redirect to the new stage
    return redirect(
        url_for("sessions.stage", session_id=session_id, stage=new_stage.value)
    )


@bp.route("/sessions/<session_id>/synthesize", methods=["POST"], endpoint="synthesize")
def synthesize_route(session_id: str):
    """Run AI synthesis.  Returns a partial with findings."""
    as_of = _get_as_of()

    with connect() as conn:
        engagement_id, persona_id = _resolve_engagement_and_persona(conn)
        scope = Scope(conn, engagement_id)

        try:
            finding_vms = synthesize(scope, session_id, as_of=as_of)
        except StageError as exc:
            abort(400, str(exc))
        except AIError as exc:
            retry_href = url_for(
                "sessions.synthesize", session_id=session_id
            )
            return render_vm("partial_error", exc.as_error_partial(retry_href=retry_href), 502)

        # Rebuild the stage VM to return the full validation view
        shell = _build_shell(conn, engagement_id, persona_id)
        try:
            vm = get_stage_vm(
                scope, session_id, SessionStage.VALIDATION, shell,
                persona_id=persona_id, as_of=as_of,
            )
        except StageError:
            # If something went wrong, return just the findings
            if wants_json():
                return {"findings": [f.model_dump() for f in finding_vms]}
            raise

        return render_vm("session_stage", vm)


@bp.route(
    "/sessions/<session_id>/findings/<finding_id>/<action>",
    methods=["POST"],
    endpoint="validate_finding",
)
def validate_finding_route(session_id: str, finding_id: str, action: str):
    """Validate a single finding — approve, edit, or reject."""
    try:
        action_enum = ValidationAction(action)
    except ValueError:
        abort(400, f"unknown validation action: {action}")

    as_of = _get_as_of()
    body = request.get_json(silent=True) or {}
    edited_body = body.get("edited_body")
    note = body.get("note")

    with connect() as conn:
        engagement_id, persona_id = _resolve_engagement_and_persona(conn)
        scope = Scope(conn, engagement_id)

        if not persona_id:
            abort(400, "no persona set — switch persona first")

        try:
            vm = validate_finding(
                scope, session_id, finding_id, action_enum, persona_id,
                as_of=as_of,
                edited_body=edited_body,
                note=note,
            )
        except StageError as exc:
            abort(400, str(exc))
        except Exception as exc:
            abort(400, str(exc))

        return render_vm("partial_finding", FindingPartialVM(finding=vm))
