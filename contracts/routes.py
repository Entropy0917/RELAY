"""FROZEN CONTRACT -- the URL table.

Frontend templates NEVER hardcode a path and never guess an endpoint name.
They call `url_for(ROUTES[...].endpoint, **params)`. Backend registers exactly
these endpoints. Either side changing a URL without the other is caught by
tests/test_contracts.py, not at demo time.

`partial` marks endpoints that return an HTMX fragment rather than a page --
those render a *_PartialVM and no shell.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Route:
    endpoint: str  # Flask endpoint name, e.g. "pages.overview"
    rule: str  # URL rule with <converters>
    methods: tuple[str, ...] = ("GET",)
    viewmodel: str | None = None  # key into viewmodels.VIEWMODELS
    partial: bool = False
    params: tuple[str, ...] = field(default_factory=tuple)
    note: str = ""


ROUTES: dict[str, Route] = {
    # -- read surfaces (backend B5 / frontend F3) ---------------------------
    "overview": Route(
        "pages.overview", "/", viewmodel="overview",
        note="Program Overview. Landing page; demo step 1.",
    ),
    "operating_model": Route(
        "pages.operating_model", "/operating-model", viewmodel="operating_model",
    ),
    "area_detail": Route(
        "pages.area_detail", "/operating-model/<area_id>",
        viewmodel="area_detail", params=("area_id",),
        note="Full page; also fetched by HTMX into a drawer.",
    ),
    "blueprint": Route(
        "pages.blueprint", "/blueprint", viewmodel="blueprint",
    ),
    "people": Route("pages.people", "/people", viewmodel="people"),
    "passport": Route(
        "pages.passport", "/people/<person_id>",
        viewmodel="passport", params=("person_id",),
    ),
    "knowledge": Route(
        "pages.knowledge", "/knowledge", viewmodel="knowledge",
        note="Filters arrive as query args: ?type=&area=&person=",
    ),
    "readiness": Route("pages.readiness", "/readiness", viewmodel="readiness"),

    # -- session loop (backend B6 / frontend F4) ----------------------------
    "session_list": Route(
        "sessions.index", "/sessions", viewmodel="session_list",
    ),
    "session_stage": Route(
        "sessions.stage", "/sessions/<session_id>/<stage>",
        viewmodel="session_stage", params=("session_id", "stage"),
        note="stage is a SessionStage value. Canonical deep link for the demo.",
    ),
    "session_advance": Route(
        "sessions.advance", "/sessions/<session_id>/<stage>/advance",
        methods=("POST",), params=("session_id", "stage"),
        note="Records stage input, moves to the next stage. Returns a redirect.",
    ),

    # -- HTMX partials ------------------------------------------------------
    "synthesize": Route(
        "sessions.synthesize", "/sessions/<session_id>/synthesize",
        methods=("POST",), viewmodel="session_stage", partial=True,
        params=("session_id",),
        note="Runs the AI. Slow path -- frontend must show a pending state. "
             "On provider failure returns partial_error, status 502.",
    ),
    "validate_finding": Route(
        "sessions.validate_finding",
        "/sessions/<session_id>/findings/<finding_id>/<action>",
        methods=("POST",), viewmodel="partial_finding", partial=True,
        params=("session_id", "finding_id", "action"),
        note="action is a ValidationAction. Swaps the finding card in place.",
    ),
    "capability_row": Route(
        "pages.capability_row", "/people/<person_id>/capability/<capability_id>",
        viewmodel="partial_capability_row", partial=True,
        params=("person_id", "capability_id"),
        note="Re-renders one passport row after validation updates a level.",
    ),

    # -- state switches -----------------------------------------------------
    "set_persona": Route(
        "shell.set_persona", "/persona/<person_id>",
        methods=("POST",), params=("person_id",),
        note="Sets the session cookie, redirects back to Referer.",
    ),
    "set_engagement": Route(
        "shell.set_engagement", "/engagement/<engagement_id>",
        methods=("POST",), params=("engagement_id",),
        note="Proves reusability live. Redirects to overview.",
    ),

    # -- frontend-owned harness (frontend F6) -------------------------------
    "preview": Route(
        "preview.show", "/preview/<name>", params=("name",),
        note="Renders a template against contracts/fixtures/<name>.json. "
             "Frontend-owned; never linked from the app shell.",
    ),
}

# Primary navigation, in order. ShellVM.nav is built from this.
NAV: list[tuple[str, str]] = [
    ("overview", "Overview"),
    ("operating_model", "Operating Model"),
    ("blueprint", "Transfer Blueprint"),
    ("session_list", "Sessions"),
    ("knowledge", "Knowledge"),
    ("people", "People"),
    ("readiness", "Readiness"),
]
