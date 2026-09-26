"""The 12 tables (planv0.2.md section 4, B1), plus the engagement root.

Two things in here are load-bearing and easy to lose:

**Engagement scoping (planv0.2.md section 0.5).** Every content table carries
`engagement_id`. RELAY is a product, not one demo, and the thing that makes
that true is that no row exists outside an engagement. `test_db.py` asserts
it for every table rather than trusting anyone to remember.

**The invariants are triggers, not conventions.** planv0.2.md section 4 B1
calls them "enforced, not conventions", so they live in the database where no
amount of careless application code can route around them. A convention in a
docstring is not an invariant; a trigger that aborts the write is.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DDL,
    ForeignKey,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    Text,
    event,
)

metadata = MetaData()

# Owned by app/ai/cache.py (B2). Declared nowhere here on purpose -- reset.py
# must leave it alone so a reset never costs a warm demo.
PRESERVED_TABLES = {"ai_cache"}


def _eng() -> Column:
    """Every content table gets this. No exceptions -- see section 0.5."""
    return Column(
        "engagement_id",
        String,
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


# --------------------------------------------------------------------------
# The tenant root
# --------------------------------------------------------------------------

engagements = Table(
    "engagements",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("org", String, nullable=False),
    Column("sector", String, nullable=False),
    Column("location", String, nullable=False),
    Column("mission", Text, nullable=False),
    Column("started_on", Date, nullable=False),
    Column("ends_on", Date, nullable=False),
    # Readiness *weights* are per-engagement tunable; the formula shape is code.
    Column("readiness_weights", JSON, nullable=False, default=dict),
    Column("is_primary", Boolean, nullable=False, default=False),
)


# --------------------------------------------------------------------------
# People and capability
# --------------------------------------------------------------------------

people = Table(
    "people",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("name", String, nullable=False),
    Column("title", String, nullable=False),
    Column("role", String, nullable=False),  # vocabulary.Role
    Column("departure_date", Date),  # experts only
    Column("bio", Text),
)

capabilities = Table(
    "capabilities",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("name", String, nullable=False),
    Column("description", Text, nullable=False),
    Column("criticality", Integer, nullable=False),  # 1..5, feeds readiness weighting
    Column("area_id", String, ForeignKey("operating_model_areas.id")),
)

person_capabilities = Table(
    "person_capabilities",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("person_id", String, ForeignKey("people.id"), nullable=False),
    Column("capability_id", String, ForeignKey("capabilities.id"), nullable=False),
    # INVARIANT 1: only an approved validation moves this. Trigger-enforced below.
    Column("level", Integer, nullable=False, default=0),  # 0..6
    Column("exposure_count", Integer, nullable=False, default=0),
    Column("last_demonstrated", Date),
    # The trigger's proof-of-provenance: a level change must name the approved
    # validation that authorised it.
    # use_alter: person_capabilities and validations reference each other, which
    # is correct here -- a level cites its authorisation, an authorisation cites
    # what it authorised -- but the cycle has to be broken for table creation.
    Column(
        "last_validation_id",
        String,
        ForeignKey("validations.id", use_alter=True, name="fk_pc_last_validation"),
    ),
)

capability_evidence = Table(
    "capability_evidence",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("person_capability_id", String, ForeignKey("person_capabilities.id"), nullable=False),
    Column("session_id", String, ForeignKey("sessions.id")),
    Column("observed_on", Date, nullable=False),
    Column("level_at_time", Integer, nullable=False),
    Column("summary", Text, nullable=False),
    Column("source", Text, nullable=False),  # transcript span, debrief answer, etc.
    Column("created_at", String, nullable=False),
    # INVARIANT 2: append-only. Trigger-enforced below.
)


# --------------------------------------------------------------------------
# Operating model
# --------------------------------------------------------------------------

operating_model_areas = Table(
    "operating_model_areas",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("name", String, nullable=False),
    Column("summary", Text, nullable=False),
    Column("local_owner_id", String, ForeignKey("people.id")),
    # Naming an owner is not the same as demonstrating they can carry the area,
    # so readiness (section 4 B4) credits local ownership only once the owner
    # has been validated. Two columns, because they are two different claims.
    Column("owner_validated", Boolean, nullable=False, default=False),
    # Ownership and trainer coverage are scored over critical areas only.
    Column("critical", Boolean, nullable=False, default=True),
    Column("formal_pct", Integer, nullable=False),  # informal is 100 - this
    # The 8 dimensions. Displayed, never queried across -- so JSON, per the
    # collapsing rule in planv0.2.md section 4, B1.
    Column("processes", JSON, nullable=False, default=list),
    Column("roles", JSON, nullable=False, default=list),
    Column("governance", JSON, nullable=False, default=list),
    Column("tools", JSON, nullable=False, default=list),
    Column("metrics", JSON, nullable=False, default=list),
    Column("decision_rights", JSON, nullable=False, default=list),
    Column("relationships", JSON, nullable=False, default=list),
    Column("capabilities_list", JSON, nullable=False, default=list),
)

transfer_requirements = Table(
    "transfer_requirements",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("area_id", String, ForeignKey("operating_model_areas.id"), nullable=False),
    Column("kind", String, nullable=False),  # vocabulary.RequirementKind
    Column("label", String, nullable=False),
    Column("description", Text, nullable=False),
    Column("state", String, nullable=False),  # vocabulary.TransferState
    # Deliberately separate from `state`: section 4 B4 credits a formal
    # requirement that is merely complete, but credits an informal one only
    # where the capture was validated. Conflating them inflates the half of the
    # score that is hardest to earn.
    Column("validated", Boolean, nullable=False, default=False),
    Column("capability_id", String, ForeignKey("capabilities.id")),
)


# --------------------------------------------------------------------------
# The session loop
# --------------------------------------------------------------------------

sessions = Table(
    "sessions",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("title", String, nullable=False),
    Column("held_on", Date, nullable=False),
    Column("stage", String, nullable=False),  # vocabulary.SessionStage
    Column("expert_id", String, ForeignKey("people.id"), nullable=False),
    Column("learner_ids", JSON, nullable=False, default=list),
    Column("area_id", String, ForeignKey("operating_model_areas.id")),
    Column("capability_id", String, ForeignKey("capabilities.id")),
    Column("brief", JSON),  # the generated preparation brief
    Column("transcript", Text),
    Column("notes", Text),
)

debriefs = Table(
    "debriefs",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("session_id", String, ForeignKey("sessions.id"), nullable=False),
    Column("role", String, nullable=False),  # expert | learner
    Column("person_id", String, ForeignKey("people.id"), nullable=False),
    Column("questions", JSON, nullable=False, default=list),  # [{id, question, answer}]
    Column("completed_at", String),
)

findings = Table(
    "findings",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("session_id", String, ForeignKey("sessions.id"), nullable=False),
    Column("kind", String, nullable=False),  # vocabulary.FindingKind
    Column("title", String, nullable=False),
    Column("body", JSON, nullable=False),
    Column("confidence", String, nullable=False),
    Column("evidence_sources", JSON, nullable=False, default=list),
    Column("rationale", Text, nullable=False),
    Column("impact", Text, nullable=False),
    Column("risk_if_untransferred", Text, nullable=False),
    # AI output starts pending. It is a suggestion until a human says otherwise.
    Column("status", String, nullable=False, default="pending"),
)

validations = Table(
    "validations",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("finding_id", String, ForeignKey("findings.id"), nullable=False),
    Column("person_capability_id", String, ForeignKey("person_capabilities.id")),
    Column("validated_by_id", String, ForeignKey("people.id"), nullable=False),
    Column("action", String, nullable=False),  # vocabulary.ValidationAction
    Column("edited_body", JSON),
    Column("note", Text),
    Column("created_at", String, nullable=False),
)


# --------------------------------------------------------------------------
# Knowledge and recommendations
# --------------------------------------------------------------------------

knowledge_items = Table(
    "knowledge_items",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("title", String, nullable=False),
    Column("type", String, nullable=False),  # vocabulary.KnowledgeType
    Column("summary", Text, nullable=False),
    Column("body", JSON, nullable=False),
    Column("area_id", String, ForeignKey("operating_model_areas.id")),
    Column("capability_id", String, ForeignKey("capabilities.id")),
    Column("session_id", String, ForeignKey("sessions.id")),
    Column("expert_id", String, ForeignKey("people.id"), nullable=False),
    Column("validated", Boolean, nullable=False, default=False),
    Column("people_exposed", JSON, nullable=False, default=list),
    Column("captured_on", Date, nullable=False),
)

recommendations = Table(
    "recommendations",
    metadata,
    Column("id", String, primary_key=True),
    _eng(),
    Column("session_id", String, ForeignKey("sessions.id")),
    Column("person_id", String, ForeignKey("people.id"), nullable=False),
    Column("capability_id", String, ForeignKey("capabilities.id")),
    Column("objective", Text, nullable=False),
    Column("recommended_experience", Text, nullable=False),
    Column("learner_responsibilities", JSON, nullable=False, default=list),
    Column("expert_role", Text, nullable=False),
    Column("status", String, nullable=False, default="open"),
)


CONTENT_TABLES = [t for t in metadata.tables.values() if t.name != "engagements"]


# --------------------------------------------------------------------------
# Invariants, as triggers
# --------------------------------------------------------------------------

# INVARIANT 1 -- AI never certifies anyone.
# A level change must name an approved validation that has not already been
# spent on a previous change. Without this, any stray UPDATE could promote a
# person, which is precisely the failure the spec warns about.
_LEVEL_REQUIRES_VALIDATION = DDL("""
CREATE TRIGGER IF NOT EXISTS trg_level_requires_validation
BEFORE UPDATE OF level ON person_capabilities
FOR EACH ROW
WHEN NEW.level <> OLD.level
 AND (
   NEW.last_validation_id IS NULL
   OR NEW.last_validation_id IS OLD.last_validation_id
   OR NOT EXISTS (
     SELECT 1 FROM validations v
     WHERE v.id = NEW.last_validation_id
       AND v.action = 'approve'
       AND v.person_capability_id = NEW.id
   )
 )
BEGIN
  SELECT RAISE(ABORT,
    'person_capabilities.level may only change via an approved validation');
END;
""")

# INVARIANT 2 -- evidence is history, and history is not editable.
_EVIDENCE_NO_UPDATE = DDL("""
CREATE TRIGGER IF NOT EXISTS trg_evidence_no_update
BEFORE UPDATE ON capability_evidence
BEGIN
  SELECT RAISE(ABORT, 'capability_evidence is append-only');
END;
""")

_EVIDENCE_NO_DELETE = DDL("""
CREATE TRIGGER IF NOT EXISTS trg_evidence_no_delete
BEFORE DELETE ON capability_evidence
BEGIN
  SELECT RAISE(ABORT, 'capability_evidence is append-only');
END;
""")

TRIGGERS = (
    _LEVEL_REQUIRES_VALIDATION,
    _EVIDENCE_NO_UPDATE,
    _EVIDENCE_NO_DELETE,
)

for _ddl in TRIGGERS:
    event.listen(metadata, "after_create", _ddl.execute_if(dialect="sqlite"))

# INVARIANT 3 -- no stored readiness scores; everything is derived at read
# time. There is no column to enforce, so test_db.py asserts the absence.
