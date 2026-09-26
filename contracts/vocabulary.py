"""RELAY product vocabulary -- lives in code, not the database.

Per planv0.2.md section 0.5, this is the boundary: the RELAY *model* is the
product and belongs here. Anything an engagement fills in belongs in tables.

Test: "would this differ for a Saudi manufacturing engagement?"  No -> here.
"""

from __future__ import annotations

from enum import StrEnum


class Status(StrEnum):
    """The five transfer states. Rendered by exactly one macro."""

    SUSTAINABLE = "sustainable"
    ON_TRACK = "on_track"
    IN_PROGRESS = "in_progress"
    AT_RISK = "at_risk"
    CRITICAL = "critical"


STATUS_LABEL: dict[Status, str] = {
    Status.SUSTAINABLE: "Sustainable",
    Status.ON_TRACK: "On Track",
    Status.IN_PROGRESS: "Transfer in Progress",
    Status.AT_RISK: "At Risk",
    Status.CRITICAL: "Critical",
}


class Rail(StrEnum):
    """The seven Transfer Rails -- the experiential pathway."""

    KNOW = "know"
    OBSERVE = "observe"
    EXPLAIN = "explain"
    ASSIST = "assist"
    LEAD = "lead"
    VALIDATE = "validate"
    TEACH = "teach"


RAIL_LABEL: dict[Rail, str] = {
    Rail.KNOW: "Know",
    Rail.OBSERVE: "Observe",
    Rail.EXPLAIN: "Explain",
    Rail.ASSIST: "Assist",
    Rail.LEAD: "Lead",
    Rail.VALIDATE: "Validate",
    Rail.TEACH: "Teach",
}

RAIL_ORDER: list[Rail] = list(RAIL_LABEL)


# Capability levels 0-6. The index IS the level.
CAPABILITY_LEVELS: list[str] = [
    "Not Exposed",
    "Observed",
    "Assisted",
    "Performed with Supervision",
    "Performed Independently",
    "Demonstrated Repeatedly",
    "Can Teach Others",
]

LEVEL_INDEPENDENT = 4  # threshold for "capability localization"
LEVEL_TEACHER = 6  # threshold for "locally teachable"


class TransferState(StrEnum):
    """Per-requirement transfer state. Rendered as a glyph."""

    COMPLETE = "complete"  # checkmark
    PARTIAL = "partial"  # triangle
    NONE = "none"  # circle


TRANSFER_GLYPH: dict[TransferState, str] = {
    TransferState.COMPLETE: "✓",
    TransferState.PARTIAL: "△",
    TransferState.NONE: "○",
}


class RequirementKind(StrEnum):
    """The transfer-requirement categories shown per operating-model area."""

    FORMAL = "formal"
    TECHNICAL = "technical"
    JUDGMENT = "judgment"
    TACIT = "tacit"
    RELATIONSHIP = "relationship"
    TOOL = "tool"
    GOVERNANCE = "governance"


REQUIREMENT_LABEL: dict[RequirementKind, str] = {
    RequirementKind.FORMAL: "Formal Knowledge",
    RequirementKind.TECHNICAL: "Technical Capability",
    RequirementKind.JUDGMENT: "Decision & Judgment",
    RequirementKind.TACIT: "Tacit Knowledge",
    RequirementKind.RELATIONSHIP: "Relationships",
    RequirementKind.TOOL: "Tools & Systems",
    RequirementKind.GOVERNANCE: "Governance",
}


class KnowledgeType(StrEnum):
    """The seven knowledge-library categories."""

    FORMAL_DOCUMENT = "formal_document"
    EXPERT_INSIGHT = "expert_insight"
    CASE = "case"
    HEURISTIC = "heuristic"
    EXCEPTION = "exception"
    LESSON_LEARNED = "lesson_learned"
    RELATIONSHIP = "relationship"


KNOWLEDGE_LABEL: dict[KnowledgeType, str] = {
    KnowledgeType.FORMAL_DOCUMENT: "Formal Documents",
    KnowledgeType.EXPERT_INSIGHT: "Expert Insights",
    KnowledgeType.CASE: "Cases",
    KnowledgeType.HEURISTIC: "Heuristics",
    KnowledgeType.EXCEPTION: "Exceptions",
    KnowledgeType.LESSON_LEARNED: "Lessons Learned",
    KnowledgeType.RELATIONSHIP: "Relationships",
}


class SessionStage(StrEnum):
    """The transfer-session loop. Drives the stepper UI."""

    PREPARE = "prepare"
    CAPTURE = "capture"
    EXPERT_DEBRIEF = "expert_debrief"
    LEARNER_DEBRIEF = "learner_debrief"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    NEXT_ACTION = "next_action"


STAGE_LABEL: dict[SessionStage, str] = {
    SessionStage.PREPARE: "Prepare",
    SessionStage.CAPTURE: "Capture",
    SessionStage.EXPERT_DEBRIEF: "Expert Debrief",
    SessionStage.LEARNER_DEBRIEF: "Learner Debrief",
    SessionStage.SYNTHESIS: "AI Synthesis",
    SessionStage.VALIDATION: "Validation",
    SessionStage.NEXT_ACTION: "Next Action",
}

STAGE_ORDER: list[SessionStage] = list(STAGE_LABEL)


class Role(StrEnum):
    EXPERT = "expert"
    COUNTERPART = "counterpart"
    MANAGER = "manager"


class FindingKind(StrEnum):
    CAPABILITY_EVIDENCE = "capability_evidence"
    TACIT_KNOWLEDGE = "tacit_knowledge"
    REMAINING_GAP = "remaining_gap"
    NEXT_ACTIVITY = "next_activity"


class ValidationAction(StrEnum):
    APPROVE = "approve"
    EDIT = "edit"
    REJECT = "reject"


# The eight operating-model dimensions (spec section 1).
OM_DIMENSIONS: list[tuple[str, str]] = [
    ("processes", "Processes"),
    ("roles", "People & Roles"),
    ("governance", "Governance"),
    ("tools", "Tools & Systems"),
    ("metrics", "Data & Metrics"),
    ("decision_rights", "Decision Rights"),
    ("relationships", "External Relationships"),
    ("capabilities", "Capabilities"),
]
