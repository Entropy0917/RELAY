"""Shell routes — persona and engagement switching.

These live outside both the page routes and the session routes because they
are product-level state changes, not page renders.  They set a Flask session
cookie and redirect back to wherever the user was.
"""

from __future__ import annotations

from flask import (
    Blueprint,
    redirect,
    request,
    session as flask_session,
    url_for,
)

from app.db.connection import connect
from app.db.schema import engagements, people
from app.db.scoped import Scope

bp = Blueprint("shell", __name__)


@bp.route("/persona/<person_id>", methods=["POST"])
def set_persona(person_id: str):
    """Switch the current persona.  Redirects back to Referer."""
    flask_session["persona_id"] = person_id
    return redirect(request.referrer or url_for("pages.overview"))


@bp.route("/engagement/<engagement_id>", methods=["POST"])
def set_engagement(engagement_id: str):
    """Switch engagement — proves reusability is real.  Redirects to overview."""
    flask_session["engagement_id"] = engagement_id
    # Clear persona so it re-defaults for the new engagement
    flask_session.pop("persona_id", None)
    return redirect(url_for("pages.overview"))
