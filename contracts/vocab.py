"""RELAY product vocabulary.

These enums ARE the product (planv0.2 §0.5, left column): they are identical for
every engagement. Anything that would differ between engagements belongs in the
database, never here.
"""

from enum import IntEnum, StrEnum


class Status(StrEnum):
    """The five transfer statuses. Rendered everywhere through one macro."""

    SUSTAINABLE = "sustainable"
    ON_TRACK = "on_track"
    TRANSFER_IN_PROGRESS = "transfer_in_progress"
    AT_RISK = "at_risk"
    CRITICAL = "critical"

    @property
    def label(self) -> str:
        return self.name.replace("_", " ")


class Severity(StrEnum):
    """Knowledge-at-risk severity (risk cards, flags)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"

    @property
    def label(self) -> str:
        return self.name


class LocalCapability(StrEnum):
    """Aggregate local capability on an operating-model area."""

    STRONG = "strong"
    DEVELOPING = "developing"
    LIMITED = "limited"
    NONE = "none"

    @property
    def label(self) -> str:
        return self.name.title()


class TransferState(StrEnum):
    """Per-requirement transfer state. Glyphs: ✓ complete · △ partial · ○ none."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    NONE = "none"

    @property
    def glyph(self) -> str:
        return {"complete": "✓", "partial": "△", "none": "○"}[self.value]


class CapabilityLevel(IntEnum):
    NOT_EXPOSED = 0
    OBSERVED = 1
    ASSISTED = 2
    PERFORMED_WITH_SUPERVISION = 3
    PERFORMED_INDEPENDENTLY = 4
    DEMONSTRATED_REPEATEDLY = 5
    CAN_TEACH_OTHERS = 6

    @property
    def label(self) -> str:
        return self.name.replace("_", " ").title().replace("With", "with")


class TransferRail(IntEnum):
    """The seven Transfer Rails, shown as a visible progression."""

    KNOW = 1
    OBSERVE = 2
    EXPLAIN = 3
    ASSIST = 4
    LEAD = 5
    VALIDATE = 6
    TEACH = 7

    @property
    def label(self) -> str:
        return self.name


class KnowledgeType(StrEnum):
    """Knowledge Library categories."""

    FORMAL_DOCUMENT = "formal_document"
    EXPERT_INSIGHT = "expert_insight"
    CASE = "case"
    HEURISTIC = "heuristic"
    EXCEPTION = "exception"
    LESSON_LEARNED = "lesson_learned"
    RELATIONSHIP = "relationship"

    @property
    def label(self) -> str:
        return self.name.replace("_", " ")


class OMDimension(StrEnum):
    """The eight operating-model dimensions."""

    PROCESSES = "processes"
    PEOPLE_ROLES = "people_roles"
    GOVERNANCE = "governance"
    TOOLS_SYSTEMS = "tools_systems"
    DATA_METRICS = "data_metrics"
    DECISION_RIGHTS = "decision_rights"
    EXTERNAL_RELATIONSHIPS = "external_relationships"
    CAPABILITIES = "capabilities"

    @property
    def label(self) -> str:
        return {
            "people_roles": "PEOPLE & ROLES",
            "tools_systems": "TOOLS & SYSTEMS",
            "data_metrics": "DATA & METRICS",
        }.get(self.value, self.name.replace("_", " "))


class RequirementCategory(StrEnum):
    """Transfer Blueprint requirement categories."""

    FORMAL_KNOWLEDGE = "formal_knowledge"
    INFORMAL_KNOWLEDGE = "informal_knowledge"
    TECHNICAL_CAPABILITY = "technical_capability"
    DECISION_JUDGMENT = "decision_judgment"
    RELATIONSHIPS = "relationships"
    TOOLS_SYSTEMS = "tools_systems"
    GOVERNANCE = "governance"

    @property
    def label(self) -> str:
        return {
            "decision_judgment": "DECISION & JUDGMENT",
            "tools_systems": "TOOLS & SYSTEMS",
        }.get(self.value, self.name.replace("_", " "))


class EvidenceType(StrEnum):
    EXPERT_OBSERVATION = "expert_observation"
    LEARNER_EXPLANATION = "learner_explanation"
    WORK_PRODUCT = "work_product"
    REAL_WORLD_OUTCOME = "real_world_outcome"
    SCENARIO_PERFORMANCE = "scenario_performance"
    PEER_TEACHING = "peer_teaching"
    REPEATED_PERFORMANCE = "repeated_performance"

    @property
    def label(self) -> str:
        return self.name.replace("_", " ")


class ValidationStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"

    @property
    def label(self) -> str:
        return {"pending": "PENDING EXPERT VALIDATION"}.get(self.value, self.name)


class SessionStage(StrEnum):
    """Transfer Session loop, in order. URL segment = value."""

    PREPARE = "prepare"
    CAPTURE = "capture"
    EXPERT_DEBRIEF = "expert-debrief"
    LEARNER_DEBRIEF = "learner-debrief"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    NEXT_ACTION = "next-action"

    @property
    def label(self) -> str:
        return {"synthesis": "AI SYNTHESIS", "validation": "VALIDATE"}.get(
            self.value, self.name.replace("_", " ")
        )


class StepState(StrEnum):
    DONE = "done"
    CURRENT = "current"
    UPCOMING = "upcoming"


class FindingKind(StrEnum):
    CAPABILITY_EVIDENCE = "capability_evidence"
    TACIT_KNOWLEDGE = "tacit_knowledge"
    REMAINING_GAP = "remaining_gap"
    NEXT_ACTIVITY = "next_activity"

    @property
    def label(self) -> str:
        return {
            "capability_evidence": "CAPABILITY EVIDENCE DETECTED",
            "tacit_knowledge": "NEW TACIT KNOWLEDGE DETECTED",
            "remaining_gap": "REMAINING KNOWLEDGE GAP",
            "next_activity": "NEXT RECOMMENDED EXPERIENCE",
        }[self.value]


class FindingStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    EDITED = "edited"
    REJECTED = "rejected"
    NOT_YET = "not_yet"


class FindingAction(StrEnum):
    """URL segment for POST /sessions/<id>/findings/<fid>/<action>."""

    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"
    NOT_YET = "not-yet"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LearnerResultTag(StrEnum):
    UNDERSTANDING = "understanding"
    MISUNDERSTANDING = "misunderstanding"
    CONFIDENCE_GAP = "confidence_gap"
    EXPERIENCE_GAP = "experience_gap"


class DebriefRole(StrEnum):
    EXPERT = "expert"
    LEARNER = "learner"


class PersonKind(StrEnum):
    EXPERT = "expert"
    COUNTERPART = "counterpart"
    TRAINER = "trainer"
    MANAGER = "manager"


class PersonaRole(StrEnum):
    """Persona switcher roles. The persona's display name comes from the DB."""

    EXPERT = "expert"
    LEARNER = "learner"
    PROGRAM_MANAGER = "program_manager"


class AIErrorKind(StrEnum):
    PROVIDER_UNREACHABLE = "provider_unreachable"
    SCHEMA_VIOLATION = "schema_violation"
    TIMEOUT = "timeout"
