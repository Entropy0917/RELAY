"""Preview harness (F6): render any template against its contract fixture.

    /preview/                      index of every fixture
    /preview/<name>                fixture <name>.json through its route's template
    /preview/<name>?variant=<v>    fixture <name>__<v>.json

Lets the whole frontend track run before a single backend route exists. If the
template hasn't been written yet, the validated fixture is shown as JSON instead.
"""

import json

from flask import Blueprint, abort, render_template, request
from jinja2 import TemplateNotFound

from contracts import fixture_names, fixture_path, load_fixture
from contracts.routes import ROUTES
from contracts.viewmodels import VIEWMODELS

bp = Blueprint("preview", __name__, url_prefix="/preview")

TEMPLATES = {r.viewmodel: r.template for r in ROUTES if r.viewmodel}


@bp.get("/")
def index():
    return render_template(
        "_preview/index.html",
        fixtures=fixture_names(),
        templates=TEMPLATES,
    )


@bp.get("/_shell")
def shell():
    """The bare app shell, using any page fixture's `shell` (default: overview)."""
    source = request.args.get("from", "overview")
    vm = load_fixture(source, request.args.get("variant") or None)
    return render_template("_preview/shell.html", shell=vm.shell, source=source)


@bp.get("/_macros")
def macros():
    """Component gallery: every ui.html macro against real fixtures."""
    overview = load_fixture("overview")
    return render_template(
        "_preview/macros.html",
        shell=overview.shell,
        overview=overview,
        readiness=load_fixture("readiness"),
        blueprint=load_fixture("blueprint"),
        synthesis_error=load_fixture("session_synthesis", "ai_error"),
        prepare_error=load_fixture("session_prepare", "ai_error"),
    )


@bp.get("/<name>")
def show(name: str):
    if name not in VIEWMODELS:
        abort(404)
    variant = request.args.get("variant") or None
    if not fixture_path(name, variant).exists():
        abort(404)
    vm = load_fixture(name, variant)
    template = TEMPLATES[name]
    context = {field: getattr(vm, field) for field in type(vm).model_fields}
    try:
        return render_template(template, vm=vm, **context)
    except TemplateNotFound as e:
        if e.name != template:
            raise
        return render_template(
            "_preview/missing.html",
            name=name,
            variant=variant,
            template=template,
            dump=json.dumps(vm.model_dump(mode="json"), indent=2, ensure_ascii=False),
        )
