"""Preview harness + template helpers (frontend-owned, planv0.2 F6).

    /preview/                    index of every fixture
    /preview/<name>              contracts/fixtures/<name>.json through its template
    /preview/<name>?stage=<s>    session_stage fixture re-staged (walk the loop)
    /preview/_macros             component gallery
    /preview/_shell              bare app shell

This module is also where the frontend installs its Jinja globals, because
app/__init__.py is bootstrap-frozen and the frontend adds nothing there:

    vocab        contracts.vocabulary (labels, glyphs, orders)
    href(key, **params)   url_for(ROUTES[key].endpoint, **params) — templates never
                          hard-code a path (contracts/routes.py)
    TEMPLATES    viewmodel name → template path, used by preview and by routes
                 by routes through render_vm(name, vm)
"""

from __future__ import annotations

import json
from pathlib import Path

from flask import Blueprint, abort, render_template, request, url_for
from jinja2 import TemplateNotFound

from contracts import vocabulary
from contracts.routes import ROUTES
from contracts.viewmodels import VIEWMODELS

FIXTURES = Path(__file__).resolve().parent.parent / "contracts" / "fixtures"

# The frontend's half of the seam: which template renders which view model.
TEMPLATES: dict[str, str] = {
    "overview": "pages/overview.html",
    "operating_model": "pages/operating_model.html",
    "area_detail": "pages/area_detail.html",
    "blueprint": "pages/blueprint.html",
    "people": "pages/people.html",
    "passport": "pages/passport.html",
    "knowledge": "pages/knowledge.html",
    "readiness": "pages/readiness.html",
    "session_list": "pages/sessions.html",
    "session_stage": "pages/session/stage.html",
    "partial_finding": "partials/session/finding_card.html",
    "partial_capability_row": "partials/capability_row.html",
    "partial_error": "partials/error.html",
}

bp = Blueprint("preview", __name__, url_prefix="/preview")


def href(key: str, **params) -> str:
    return url_for(ROUTES[key].endpoint, **params)


@bp.record_once
def _install_globals(state) -> None:
    env = state.app.jinja_env
    env.globals.update(vocab=vocabulary, href=href, TEMPLATES=TEMPLATES)
    env.trim_blocks = True
    env.lstrip_blocks = True


def wants_json() -> bool:
    """`?format=json` or an explicit JSON Accept header keeps the raw view model (debugging, API tests)."""
    if request.args.get("format") == "json":
        return True
    return request.accept_mimetypes.best_match(["text/html", "application/json"]) == "application/json"


def render_vm(name: str, vm, status: int = 200, **extra):
    """How routes answer: the view model through its template, or as JSON on request."""
    if wants_json():
        return vm.model_dump(mode="json"), status
    return render_template(TEMPLATES[name], **context(vm), **extra), status


def load_fixture(name: str):
    path = FIXTURES / f"{name}.json"
    if name not in VIEWMODELS or not path.exists():
        abort(404)
    return VIEWMODELS[name].model_validate(json.loads(path.read_text()))


def context(vm) -> dict:
    """Template context = the view model's top-level fields (plus `vm` itself)."""
    return {field: getattr(vm, field) for field in type(vm).model_fields} | {"vm": vm}


@bp.get("/")
def index():
    names = sorted(p.stem for p in FIXTURES.glob("*.json"))
    return render_template("_preview/index.html", fixtures=names, templates=TEMPLATES,
                           stages=vocabulary.STAGE_ORDER)


@bp.get("/_shell")
def shell():
    vm = load_fixture(request.args.get("from", "overview"))
    return render_template("_preview/shell.html", shell=vm.shell, source=request.args.get("from", "overview"))


@bp.get("/_macros")
def macros():
    ctx = {n: load_fixture(n) for n in ("overview", "readiness", "blueprint", "knowledge", "operating_model", "partial_error")}
    return render_template("_preview/macros.html", shell=ctx["overview"].shell, **ctx)


@bp.get("/<name>")
def show(name: str):
    vm = load_fixture(name)
    if name == "session_stage" and (stage := request.args.get("stage")):
        vm = restage(vm, vocabulary.SessionStage(stage))
    template = TEMPLATES.get(name)
    try:
        return render_template(template, **context(vm))
    except TemplateNotFound as e:
        if e.name != template:
            raise
        return render_template("_preview/missing.html", name=name, template=template,
                               dump=json.dumps(vm.model_dump(mode="json"), indent=2, ensure_ascii=False))


def restage(vm, stage):
    """Preview-only: show the one session fixture at any stage of the loop."""
    order = vocabulary.STAGE_ORDER
    i = order.index(stage)
    stages = [{**s, "state": "done" if order.index(vocabulary.SessionStage(s["key"])) < i
               else "current" if s["key"] == stage.value else "todo"} for s in vm.stages]
    return vm.model_copy(update={"stage": stage, "stages": stages})
