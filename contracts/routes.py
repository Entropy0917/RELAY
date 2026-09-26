"""Frozen URL table (planv0.2 §1).

Backend implements every route here, returning the named view model rendered
through the named template. Frontend builds each template against
`contracts/fixtures/<viewmodel>.json` via `/preview/<viewmodel>`.

kind:
  page     full HTML document (extends base.html)
  partial  HTMX fragment (no base.html); swapped into the page
  action   POST that mutates state, then responds with an HX-Redirect header
           (or a partial, when `template` is set)

Persona and engagement are carried in the Flask session cookie. Every data
route is engagement-scoped by that cookie (§0.5), never by URL.
"""

from typing import Literal, NamedTuple


class Route(NamedTuple):
    name: str  # Flask endpoint name
    method: Literal["GET", "POST"]
    path: str
    kind: Literal["page", "partial", "action"]
    viewmodel: str | None  # key in contracts.viewmodels.VIEWMODELS
    template: str | None
    notes: str = ""


ROUTES: list[Route] = [
    # ── shell ──
    Route("index", "GET", "/", "action", None, None, "302 → /overview"),
    Route("switch_persona", "POST", "/persona", "action", None, None,
          "form: persona_id. Sets cookie, HX-Redirect to the referring page."),
    Route("switch_engagement", "POST", "/engagement", "action", None, None,
          "form: engagement_id. Sets cookie, resets persona to that engagement's expert, HX-Redirect /overview."),

    # ── read surfaces ──
    Route("overview", "GET", "/overview", "page", "overview", "pages/overview.html"),
    Route("operating_model", "GET", "/operating-model", "page", "operating_model", "pages/operating_model.html"),
    Route("area_drawer", "GET", "/operating-model/areas/<area_id>", "partial", "area_drawer",
          "partials/read/area_drawer.html", "hx-target the drawer region"),
    Route("blueprint", "GET", "/blueprint", "page", "blueprint", "pages/blueprint.html",
          "optional ?area=<id> scrolls/highlights one component"),
    Route("people", "GET", "/people", "page", "people", "pages/people.html"),
    Route("passport", "GET", "/people/<person_id>", "page", "passport", "pages/passport.html"),
    Route("knowledge", "GET", "/knowledge", "page", "knowledge", "pages/knowledge.html",
          "accepts the same query params as knowledge_results"),
    Route("knowledge_results", "GET", "/knowledge/results", "partial", "knowledge_results",
          "partials/read/knowledge_results.html",
          "query: area, capability, expert, person, type, status — all optional"),
    Route("readiness", "GET", "/readiness", "page", "readiness", "pages/readiness.html"),
    Route("propagation", "GET", "/readiness/propagation", "partial", "propagation",
          "partials/read/propagation.html", "query: capability=<id>"),

    # ── sessions ──
    Route("sessions", "GET", "/sessions", "page", "sessions", "pages/sessions.html"),
    Route("session", "GET", "/sessions/<session_id>", "action", None, None,
          "302 → the session's current stage"),
    Route("session_prepare", "GET", "/sessions/<session_id>/prepare", "page", "session_prepare",
          "pages/session/prepare.html"),
    Route("session_capture", "GET", "/sessions/<session_id>/capture", "page", "session_capture",
          "pages/session/capture.html"),
    Route("session_capture_submit", "POST", "/sessions/<session_id>/capture", "action", None, None,
          "form: transcript, notes. Generates expert debrief questions. HX-Redirect → expert-debrief."),
    Route("session_expert_debrief", "GET", "/sessions/<session_id>/expert-debrief", "page",
          "session_expert_debrief", "pages/session/debrief.html"),
    Route("session_learner_debrief", "GET", "/sessions/<session_id>/learner-debrief", "page",
          "session_learner_debrief", "pages/session/debrief.html"),
    Route("session_debrief_submit", "POST", "/sessions/<session_id>/debrief/<role>", "action", None, None,
          "role: expert|learner. form: answer_<question id>. Persona-gated. "
          "expert → HX-Redirect learner-debrief; learner → runs synthesis, HX-Redirect synthesis."),
    Route("session_synthesis", "GET", "/sessions/<session_id>/synthesis", "page", "session_synthesis",
          "pages/session/synthesis.html"),
    Route("session_synthesize", "POST", "/sessions/<session_id>/synthesize", "action", None, None,
          "Retry target for a failed synthesis. HX-Redirect synthesis."),
    Route("session_validation", "GET", "/sessions/<session_id>/validation", "page", "session_validation",
          "pages/session/synthesis.html", "same template as synthesis with actions live"),
    Route("finding_edit_form", "GET", "/sessions/<session_id>/findings/<finding_id>/edit", "partial",
          "finding_card", "partials/session/finding_card.html", "editing=true"),
    Route("finding_action", "POST", "/sessions/<session_id>/findings/<finding_id>/<action>", "partial",
          "finding_card", "partials/session/finding_card.html",
          "action: approve|edit|reject|not-yet. Expert persona only. edit form: reviewer_note + edited fields. "
          "Approve on capability_evidence writes validation + evidence, then level (invariant #1)."),
    Route("session_complete_validation", "POST", "/sessions/<session_id>/validate", "action", None, None,
          "422 while any finding is pending. HX-Redirect next-action."),
    Route("session_next_action", "GET", "/sessions/<session_id>/next-action", "page", "session_next_action",
          "pages/session/next_action.html"),
    Route("session_schedule_next", "POST", "/sessions/<session_id>/schedule-next", "action", None, None,
          "Creates the next session from next_brief. HX-Redirect its prepare stage."),
]

ROUTES_BY_NAME = {r.name: r for r in ROUTES}
