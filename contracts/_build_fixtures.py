"""Generates contracts/fixtures/*.json by constructing the view models.

Why a generator and not hand-written JSON: a fixture is only useful if it is
guaranteed to validate. Building it through the models makes an invalid
fixture impossible to commit.

DELIBERATE CHOICE (planv0.2.md section 0.5): the fixture engagement is NOT the
demo engagement. If a template only renders correctly with demo content in it,
that shows up here -- in the frontend's own harness -- on day one.

Run:  .venv/Scripts/python -m contracts._build_fixtures
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from contracts import viewmodels as vm
from contracts.routes import NAV, ROUTES
from contracts.vocabulary import (
    CAPABILITY_LEVELS,
    KNOWLEDGE_LABEL,
    REQUIREMENT_LABEL,
    STAGE_LABEL,
    STATUS_LABEL,
    TRANSFER_GLYPH,
    FindingKind,
    KnowledgeType,
    RequirementKind,
    Role,
    SessionStage,
    Status,
    TransferState,
)

OUT = Path(__file__).parent / "fixtures"

# --------------------------------------------------------------------------
# Fixture engagement -- desalination, not the demo engagement. On purpose.
# --------------------------------------------------------------------------
ENG = vm.EngagementRef(
    id="eng-desal", name="Coastal Desalination Handover", org="Al-Rima Water Authority"
)
ENG_ALT = vm.EngagementRef(
    id="eng-grid", name="Grid Reliability Transfer", org="Northern Power Company"
)


def person(pid: str, name: str, title: str, role: Role) -> vm.PersonRef:
    initials = "".join(p[0] for p in name.replace("Dr. ", "").split()[:2]).upper()
    return vm.PersonRef(id=pid, name=name, title=title, role=role, initials=initials)


EXPERT = person("p-expert", "Dr. Elena Vasquez", "Lead Process Engineer", Role.EXPERT)
LEARNER = person("p-yusuf", "Yusuf Haddad", "Plant Operations Officer", Role.COUNTERPART)
LEARNER2 = person("p-nadia", "Nadia Karim", "Water Quality Analyst", Role.COUNTERPART)
TRAINER = person("p-omar", "Omar Salim", "Shift Supervisor", Role.COUNTERPART)
MANAGER = person("p-lina", "Lina Farouk", "Programme Director", Role.MANAGER)


def shell(active: str) -> vm.ShellVM:
    return vm.ShellVM(
        nav=[
            vm.NavItem(key=k, label=lbl, href=ROUTES[k].rule, active=(k == active))
            for k, lbl in NAV
        ],
        engagements=[ENG, ENG_ALT],
        current_engagement=ENG,
        personas=[EXPERT, LEARNER, MANAGER],
        current_persona=MANAGER,
    )


def cap(cid, name, level, exposures, last=None, nxt=None) -> vm.CapabilityRow:
    return vm.CapabilityRow(
        capability_id=cid,
        capability=name,
        level=level,
        level_label=CAPABILITY_LEVELS[level],
        exposures=exposures,
        last_demonstrated=last,
        next_experience=nxt,
        trainer_ready=level >= 6,
    )


CAPS = [
    cap("c-brine", "Brine Discharge Judgment", 3, 4, "2026-09-18", "Lead next discharge window"),
    cap("c-membrane", "Membrane Fouling Diagnosis", 5, 9, "2026-09-22", "Teach-back session"),
    cap("c-chem", "Chemical Dosing Adjustment", 6, 12, "2026-09-24", None),
    cap("c-outage", "Unplanned Outage Response", 1, 1, "2026-08-30", "Shadow next drill"),
    cap("c-report", "Regulatory Submission", 4, 6, "2026-09-11", None),
]


def area(aid, name, owner, formal, informal, local, coverage, status) -> vm.AreaCard:
    return vm.AreaCard(
        id=aid, name=name, local_owner=owner, formal_pct=formal,
        informal_pct=informal, local_capability=local, trainer_coverage=coverage,
        status=status, status_label=STATUS_LABEL[status],
    )


AREAS = [
    area("a-ops", "Plant Operations", TRAINER, 70, 30, "Strong", True, Status.ON_TRACK),
    area("a-membrane", "Membrane Maintenance", LEARNER, 55, 45, "Developing", True, Status.IN_PROGRESS),
    area("a-quality", "Water Quality Assurance", LEARNER2, 80, 20, "Strong", False, Status.SUSTAINABLE),
    area("a-supply", "Chemical Supply Chain", None, 40, 60, "Limited", False, Status.AT_RISK),
    area("a-reg", "Regulatory Reporting", LEARNER2, 85, 15, "Developing", False, Status.IN_PROGRESS),
    area("a-emergency", "Emergency Response", None, 30, 70, "Limited", False, Status.CRITICAL),
]

RISKS = [
    vm.RiskItem(
        severity=Status.CRITICAL,
        title="Emergency Response has no local owner",
        problem="Outage response judgment sits entirely with the departing expert; "
                "the highest local level is 1 (Observed).",
        local_trainer=None,
        recommended_action="Schedule two supervised drills before departure.",
    ),
    vm.RiskItem(
        severity=Status.AT_RISK,
        title="Supplier relationships are undocumented",
        problem="Chemical procurement runs on personal relationships with two "
                "regional suppliers. Nothing is written down.",
        local_trainer=None,
        recommended_action="Run a relationship-transfer session with joint supplier calls.",
    ),
    vm.RiskItem(
        severity=Status.IN_PROGRESS,
        title="Brine discharge judgment not yet independent",
        problem="Learner explains the reasoning but has not led a discharge decision.",
        local_trainer="Omar Salim",
        recommended_action="Assign lead role on the next discharge window.",
    ),
]

KNOW = [
    vm.KnowledgeCard(
        id="k-1", title="Why a static cover threshold fails in rising demand",
        type=KnowledgeType.HEURISTIC, type_label=KNOWLEDGE_LABEL[KnowledgeType.HEURISTIC],
        area="Chemical Supply Chain", capability="Brine Discharge Judgment",
        expert=EXPERT.name, source_session="s-1", validated=True,
        people_exposed=[LEARNER.name, TRAINER.name],
        summary="Static cover thresholds assume a flat consumption rate. When "
                "consumption is climbing, nominal cover overstates real cover.",
    ),
    vm.KnowledgeCard(
        id="k-2", title="Membrane differential-pressure signature before fouling",
        type=KnowledgeType.EXPERT_INSIGHT, type_label=KNOWLEDGE_LABEL[KnowledgeType.EXPERT_INSIGHT],
        area="Membrane Maintenance", capability="Membrane Fouling Diagnosis",
        expert=EXPERT.name, source_session="s-2", validated=True,
        people_exposed=[LEARNER.name],
        summary="Pressure differential rises before flux drops. The gap between the "
                "two indicates the fouling mechanism.",
    ),
    vm.KnowledgeCard(
        id="k-3", title="Standard Operating Procedure: Discharge Authorisation",
        type=KnowledgeType.FORMAL_DOCUMENT, type_label=KNOWLEDGE_LABEL[KnowledgeType.FORMAL_DOCUMENT],
        area="Plant Operations", capability=None, expert=EXPERT.name,
        source_session=None, validated=True, people_exposed=[],
        summary="The written authorisation chain for discharge outside permitted windows.",
    ),
    vm.KnowledgeCard(
        id="k-4", title="The 2025 intake blockage and what was missed",
        type=KnowledgeType.LESSON_LEARNED, type_label=KNOWLEDGE_LABEL[KnowledgeType.LESSON_LEARNED],
        area="Emergency Response", capability="Unplanned Outage Response",
        expert=EXPERT.name, source_session="s-3", validated=False,
        people_exposed=[TRAINER.name],
        summary="Early turbidity readings were treated as sensor drift for eleven hours.",
    ),
]

METRICS = [
    vm.MetricTile(
        label="Transfer Readiness", value="64%", caption="6 areas assessed", delta="+7",
        formula="mean(area_readiness) weighted by area criticality",
        inputs={"areas_assessed": "6", "critical_areas": "1", "weighted_sum": "3.84"},
    ),
    vm.MetricTile(
        label="Days Until Departure", value="31 days", caption="Handover window",
        formula="departure_date - today", inputs={"departure_date": "2026-10-27"},
    ),
    vm.MetricTile(
        label="Capabilities Localized", value="2 of 5",
        caption="Level 4 or above", delta="+1",
        formula="count(level >= LEVEL_INDEPENDENT) / count(capabilities)",
        inputs={"threshold": "4", "at_or_above": "2", "total": "5"},
    ),
    vm.MetricTile(
        label="Locally Teachable", value="1 of 5", caption="Level 6",
        formula="count(level == LEVEL_TEACHER)", inputs={"at_level_6": "1"},
    ),
]


def reqs(prefix: str) -> list[vm.RequirementRow]:
    states = [
        TransferState.COMPLETE, TransferState.PARTIAL, TransferState.NONE,
        TransferState.PARTIAL, TransferState.COMPLETE, TransferState.NONE,
        TransferState.PARTIAL,
    ]
    return [
        vm.RequirementRow(
            id=f"{prefix}-{k.value}", kind=k, label=REQUIREMENT_LABEL[k],
            description=f"{REQUIREMENT_LABEL[k]} required to run this area without the expert.",
            state=s, glyph=TRANSFER_GLYPH[s],
        )
        for k, s in zip(RequirementKind, states)
    ]


SESSION = vm.SessionRef(
    id="s-1", title="Brine Discharge Window -- North Basin", date="2026-09-25",
    stage=SessionStage.SYNTHESIS, stage_label=STAGE_LABEL[SessionStage.SYNTHESIS],
    expert=EXPERT, learners=[LEARNER, TRAINER],
    capability_focus="Brine Discharge Judgment",
)

BRIEF = vm.SessionBriefVM(
    primary_target="Yusuf Haddad",
    current_level="Level 3 -- Performed with Supervision",
    todays_objective="Move toward independent judgment on discharge timing.",
    your_role="Let him reach the decision first. Intervene only on safety.",
    ask_before_explaining="What would you do if the tide window closed early?",
    watch_for=[
        "Whether he checks the salinity trend, not just the instantaneous reading",
        "Whether he considers permit exposure unprompted",
    ],
    knowledge_gap_to_explore="How you decide between delaying discharge and "
                            "reducing production rate.",
)

FINDINGS = [
    vm.FindingVM(
        id="f-1", kind=FindingKind.CAPABILITY_EVIDENCE,
        title="Evidence for Brine Discharge Judgment",
        body={
            "person": LEARNER.name, "capability": "Brine Discharge Judgment",
            "evidence": "Identified that nominal cover overstated real cover because "
                        "consumption was climbing, and named four converging signals.",
            "current_level": 3, "suggested_level": 4,
        },
        confidence="high",
        evidence_sources=["Transcript 04:12-06:40", "Learner debrief Q2"],
        rationale="The reasoning was volunteered before the expert explained it, "
                  "which distinguishes independent judgment from recall.",
        impact="Plant Operations -- Decision Rights",
        risk_if_untransferred="Discharge timing decisions would escalate to the "
                              "regional office, adding days to each cycle.",
    ),
    vm.FindingVM(
        id="f-2", kind=FindingKind.TACIT_KNOWLEDGE,
        title="Check neighbouring capacity before emergency procurement",
        body={
            "situation": "Cover appears adequate but the trend is adverse.",
            "observed_signals": [
                "Consumption rose sharply over two weeks",
                "Last physical count several days stale",
                "Supplier lead times lengthening",
            ],
            "expert_reasoning": "Any one signal alone is noise. Together they mean "
                                "the static threshold is measuring the wrong thing.",
            "recommended_response": "Check genuine surplus at nearby sites before "
                                    "initiating emergency procurement.",
        },
        confidence="medium",
        evidence_sources=["Expert debrief Q1"],
        rationale="The expert stated a rule she applies but which appears in no "
                  "written procedure.",
        impact="Chemical Supply Chain -- Processes",
        risk_if_untransferred="Emergency procurement would be triggered "
                              "unnecessarily, at roughly three times unit cost.",
    ),
    vm.FindingVM(
        id="f-3", kind=FindingKind.REMAINING_GAP,
        title="Escalation path not yet demonstrated",
        body={
            "capability": "Brine Discharge Judgment",
            "understands": "Can explain when escalation is warranted.",
            "not_yet_demonstrated": [
                "Has never initiated an emergency procurement request",
                "Has not negotiated a lead-time exception with a supplier",
            ],
        },
        confidence="high",
        evidence_sources=["Learner debrief Q3"],
        rationale="The learner said so directly.",
        impact="Chemical Supply Chain -- Decision Rights",
        risk_if_untransferred="The first real escalation after departure would be "
                              "attempted without precedent.",
    ),
    vm.FindingVM(
        id="f-4", kind=FindingKind.NEXT_ACTIVITY,
        title="Next: lead a supervised escalation",
        body={
            "objective": "Move Brine Discharge Judgment from level 4 to level 5.",
            "recommended_experience": "Learner leads the next discharge window "
                                      "end to end, including any escalation.",
            "learner_responsibilities": [
                "Make the go/no-go call and state the reasoning first",
                "Draft the escalation request unaided",
            ],
            "expert_role": "Observe. Intervene only on permit or safety exposure.",
        },
        confidence="medium",
        evidence_sources=["Finding f-1", "Finding f-3"],
        rationale="Targets the specific gap the session surfaced.",
        impact="Plant Operations -- Capabilities",
        risk_if_untransferred="The capability plateaus at supervised performance.",
    ),
]


def build() -> dict[str, BaseModel]:
    return {
        "overview": vm.OverviewVM(
            shell=shell("overview"), metrics=METRICS, departing_expert=EXPERT,
            days_until_departure=31, risks=RISKS,
            priority_actions=[
                "Assign an owner for Emergency Response",
                "Run a relationship-transfer session for chemical supply",
                "Give Yusuf Haddad the lead on the next discharge window",
            ],
            recent_knowledge=KNOW, trainer_progress=CAPS,
        ),
        "operating_model": vm.OperatingModelVM(
            shell=shell("operating_model"),
            mission="Deliver potable water to the coastal district at permitted "
                    "quality and cost, operated entirely by the local authority.",
            areas=AREAS,
        ),
        "area_detail": vm.AreaDetailVM(
            shell=shell("operating_model"), area=AREAS[1],
            dimensions={
                "processes": ["Weekly integrity check", "Clean-in-place cycle"],
                "roles": ["Shift Supervisor", "Maintenance Technician"],
                "governance": ["Maintenance log signed off weekly"],
                "tools": ["SCADA historian", "Differential pressure sensors"],
                "metrics": ["Specific flux", "Normalized differential pressure"],
                "decision_rights": ["Supervisor authorises unscheduled cleaning"],
                "relationships": ["Membrane vendor technical support"],
                "capabilities": ["Membrane Fouling Diagnosis", "Chemical Dosing Adjustment"],
            },
            requirements=reqs("a-membrane"), capabilities=CAPS[:3],
        ),
        "blueprint": vm.BlueprintVM(
            shell=shell("blueprint"),
            areas=[
                vm.BlueprintAreaVM(
                    area=a,
                    groups={k: [r for r in reqs(a.id) if r.kind == k] for k in RequirementKind},
                    local_capability=CAPS[:3], transfer_risk=a.status,
                )
                for a in AREAS[:3]
            ],
        ),
        "people": vm.PeopleVM(
            shell=shell("people"), experts=[EXPERT],
            counterparts=[LEARNER, LEARNER2, TRAINER], trainers=[TRAINER],
        ),
        "passport": vm.PassportVM(
            shell=shell("people"), person=LEARNER, capabilities=CAPS,
            evidence_count=18, knowledge_exposed=KNOW[:2],
        ),
        "knowledge": vm.KnowledgeVM(
            shell=shell("knowledge"), items=KNOW,
            counts_by_type={k: sum(1 for i in KNOW if i.type == k) for k in KnowledgeType},
            active_filters={},
        ),
        "readiness": vm.ReadinessVM(
            shell=shell("readiness"), metrics=METRICS, areas=AREAS, risks=RISKS,
            before_departure=[
                "Two supervised outage drills",
                "Joint supplier calls with both regional vendors",
                "One teach-back on membrane fouling led by Yusuf Haddad",
            ],
            propagation=[
                vm.PropagationNode(person=EXPERT, taught_by=None, children=[LEARNER.id, TRAINER.id]),
                vm.PropagationNode(person=LEARNER, taught_by=EXPERT.id, children=[LEARNER2.id]),
                vm.PropagationNode(person=TRAINER, taught_by=EXPERT.id, children=[]),
                vm.PropagationNode(person=LEARNER2, taught_by=LEARNER.id, children=[]),
            ],
            propagation_capability="Membrane Fouling Diagnosis",
        ),
        "session_list": vm.SessionListVM(
            shell=shell("session_list"), upcoming=[SESSION],
            past=[
                SESSION.model_copy(update={
                    "id": "s-2", "title": "Membrane Integrity Walkthrough",
                    "date": "2026-09-22", "stage": SessionStage.NEXT_ACTION,
                    "stage_label": STAGE_LABEL[SessionStage.NEXT_ACTION],
                }),
            ],
        ),
        "session_stage": vm.SessionStageVM(
            shell=shell("session_list"), session=SESSION, stage=SessionStage.SYNTHESIS,
            stages=[
                {"key": s.value, "label": STAGE_LABEL[s],
                 "state": "done" if i < 4 else "current" if i == 4 else "todo"}
                for i, s in enumerate(SessionStage)
            ],
            brief=BRIEF,
            transcript="Expert and learner reviewed the discharge window for the "
                       "north basin. The permitted salinity ceiling is 55 g/L...",
            notes="The learner raised the tide-window conflict unprompted.",
            expert_questions=[
                vm.DebriefQuestion(
                    id="eq-1",
                    question="What made you treat this window differently from the standard rule?",
                    answer="Four things together -- salinity trend, tide window, a "
                           "stale sample, and the permit renewal date.",
                ),
            ],
            learner_questions=[
                vm.DebriefQuestion(
                    id="lq-1",
                    question="Why was nominal cover concerning when it exceeded the threshold?",
                    answer="Because the threshold assumes last month's rate.",
                ),
                vm.DebriefQuestion(
                    id="lq-2",
                    question="What if redistribution were not possible?", answer=None,
                ),
            ],
            findings=FINDINGS, next_brief=BRIEF, can_act=True, blocked_reason=None,
        ),
        "partial_finding": vm.FindingPartialVM(
            finding=FINDINGS[0].model_copy(update={
                "validated_by": EXPERT.name, "validation_action": "approve",
            })
        ),
        "partial_capability_row": vm.CapabilityRowPartialVM(row=CAPS[0], person=LEARNER),
        "partial_error": vm.ErrorPartialVM(
            title="AI provider unreachable",
            detail="RELAY could not reach the configured model provider at "
                   "http://localhost:11434. Synthesis was not run and nothing was "
                   "saved. RELAY does not substitute placeholder analysis.",
            retry_href="/sessions/s-1/synthesize", kind="provider_unreachable",
        ),
    }


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    built = build()
    for name, model in built.items():
        (OUT / f"{name}.json").write_text(
            json.dumps(model.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(f"{len(built)} fixtures written to {OUT}")
