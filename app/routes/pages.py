"""Read-surface routes — B5 (planv0.2.md section 4).

Eight GET routes producing the frozen view models.  Thin layer: open a
connection, resolve engagement+persona from the session cookie, build the
shell, delegate to app.services.pages, return the model.

NOTE: These routes return JSON (model_dump) until templates exist.  At SYNC-2
the frontend replaces `return vm.model_dump()` with `render_template(...)`.
"""

from __future__ import annotations

from datetime import date

from flask import (
    Blueprint,
    abort,
    request,
    session as flask_session,
    url_for,
)

from app.db.connection import connect
from app.db.schema import people as people_table
from app.db.scoped import Scope, list_engagements, primary_engagement
from app.services.pages import (
    build_area_detail,
    build_blueprint,
    build_capability_row,
    build_knowledge,
    build_operating_model,
    build_overview,
    build_passport,
    build_people,
    build_readiness,
)
from contracts.viewmodels import (
    AreaDetailVM,
    BlueprintVM,
    CapabilityRowPartialVM,
    EngagementRef,
    KnowledgeVM,
    NavItem,
    OperatingModelVM,
    OverviewVM,
    PassportVM,
    PeopleVM,
    PersonRef,
    ReadinessVM,
    ShellVM,
)
from contracts.routes import NAV, ROUTES
from contracts.vocabulary import Role

bp = Blueprint("pages", __name__)


# ---------------------------------------------------------------------------
# Shell builder
# ---------------------------------------------------------------------------

def _get_as_of() -> date:
    import os
    pinned = os.environ.get("RELAY_SEED_TODAY") or request.args.get("as_of")
    if pinned:
        try:
            return date.fromisoformat(pinned)
        except ValueError:
            pass
    return date.today()


def _person_ref(row) -> PersonRef:
    name = row.name
    parts = name.split()
    initials = "".join(p[0].upper() for p in parts if p) or "?"
    return PersonRef(
        id=row.id, name=row.name, title=row.title,
        role=Role(row.role), initials=initials,
    )


def _build_shell(conn, engagement_id: str, persona_id: str | None, active_key: str = "overview") -> ShellVM:
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
    people_rows = scope.rows(people_table)
    persona_refs = []
    current_persona = None
    for p in people_rows:
        ref = _person_ref(p)
        persona_refs.append(ref)
        if p.id == persona_id:
            current_persona = ref
    if current_persona is None and persona_refs:
        current_persona = persona_refs[0]

    nav_items = []
    for key, label in NAV:
        route = ROUTES.get(key)
        try:
            href = url_for(route.endpoint) if route else "#"
        except Exception:
            href = "#"
        nav_items.append(NavItem(
            key=key, label=label, href=href, active=(key == active_key),
        ))

    return ShellVM(
        nav=nav_items,
        engagements=eng_refs,
        current_engagement=current_eng,
        personas=persona_refs,
        current_persona=current_persona,
    )


def _resolve(conn):
    engagement_id = flask_session.get("engagement_id")
    persona_id = flask_session.get("persona_id")
    if not engagement_id:
        try:
            eng = primary_engagement(conn)
            engagement_id = eng.id
        except RuntimeError:
            abort(500, "no engagement — run scripts/reset.py")
    return engagement_id, persona_id


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route("/")
def overview():
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        shell = _build_shell(conn, eid, pid, "overview")
        data = build_overview(scope, as_of=_get_as_of())
        return OverviewVM(shell=shell, **data).model_dump()


@bp.route("/operating-model")
def operating_model():
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        shell = _build_shell(conn, eid, pid, "operating_model")
        data = build_operating_model(scope, as_of=_get_as_of())
        return OperatingModelVM(shell=shell, **data).model_dump()


@bp.route("/operating-model/<area_id>")
def area_detail(area_id: str):
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        shell = _build_shell(conn, eid, pid, "operating_model")
        try:
            data = build_area_detail(scope, area_id, as_of=_get_as_of())
        except ValueError as exc:
            abort(404, str(exc))
        return AreaDetailVM(shell=shell, **data).model_dump()


@bp.route("/blueprint")
def blueprint():
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        shell = _build_shell(conn, eid, pid, "blueprint")
        data = build_blueprint(scope, as_of=_get_as_of())
        return BlueprintVM(shell=shell, **data).model_dump()


@bp.route("/people", endpoint="people")
def people_page():
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        shell = _build_shell(conn, eid, pid, "people")
        data = build_people(scope)
        return PeopleVM(shell=shell, **data).model_dump()


@bp.route("/people/<person_id>")
def passport(person_id: str):
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        shell = _build_shell(conn, eid, pid, "people")
        try:
            data = build_passport(scope, person_id, as_of=_get_as_of())
        except ValueError as exc:
            abort(404, str(exc))
        return PassportVM(shell=shell, **data).model_dump()


@bp.route("/knowledge")
def knowledge():
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        shell = _build_shell(conn, eid, pid, "knowledge")
        filters = {
            "type": request.args.get("type"),
            "area": request.args.get("area"),
            "person": request.args.get("person"),
        }
        data = build_knowledge(scope, filters=filters)
        return KnowledgeVM(shell=shell, **data).model_dump()


@bp.route("/readiness")
def readiness():
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        shell = _build_shell(conn, eid, pid, "readiness")
        data = build_readiness(
            scope,
            as_of=_get_as_of(),
            capability_id=request.args.get("capability"),
        )
        return ReadinessVM(shell=shell, **data).model_dump()


@bp.route("/people/<person_id>/capability/<capability_id>")
def capability_row(person_id: str, capability_id: str):
    with connect() as conn:
        eid, pid = _resolve(conn)
        scope = Scope(conn, eid)
        try:
            data = build_capability_row(scope, person_id, capability_id)
        except ValueError as exc:
            abort(404, str(exc))
        return CapabilityRowPartialVM(**data).model_dump()
