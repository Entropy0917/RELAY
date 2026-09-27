"""Regenerate app/ai/fixtures/*.json -- the RELAY_AI_PROVIDER=mock replies.

Run: .venv/Scripts/python -m app.ai._build_fixtures

Built from the Pydantic models rather than hand-written JSON, so a fixture
cannot drift out of its schema: if a model changes, this file stops running
until someone fixes the content. Same trick as contracts/_build_fixtures.py.

TWO RULES FOR THE CONTENT BELOW.

1. Section 0.5. Every fixture uses one neutral fictional engagement -- a grid
   maintenance handover -- and none of it may read as the demo engagement.
   tests/test_no_baked_data.py greps this directory.
2. These are never served automatically. MockClient is reachable only under
   RELAY_AI_PROVIDER=mock, set by a human. A provider failure raises; it does
   not land here.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from app.ai.schemas import (
    CapabilityAssessment,
    CapabilityEvidence,
    CapabilityFinding,
    DebriefQuestion,
    DebriefQuestions,
    DepartureAction,
    DeparturePlan,
    DepartureRisk,
    FormalInformalAnalysis,
    FormalInformalGap,
    KnowledgeItem,
    NextActivity,
    NextExperience,
    OperatingModelArea,
    OperatingModelDraft,
    ReadinessAnalysis,
    ReadinessRisk,
    RemainingGap,
    SessionBrief,
    SessionSynthesis,
    TacitKnowledge,
    TacitKnowledgeSet,
    TrainerCandidate,
    TrainerCandidates,
    TransferPlan,
    TransferPlanStep,
    TransferRequirement,
    TransferRequirementSet,
)
from contracts.vocabulary import (
    KnowledgeType,
    Rail,
    RequirementKind,
    Status,
    TransferState,
)

OUT = Path(__file__).parent / "fixtures"

EXPERT = "A. Lindqvist"
LEARNER = "M. Dahl"
SECOND_LEARNER = "P. Okafor"
AREA = "Substation Maintenance Planning"
CAPABILITY = "Load Trend Interpretation"
SECOND_CAPABILITY = "Emergency Load Transfer"


def fixtures() -> dict[str, BaseModel]:
    return {
        "prepare_session": SessionBrief(
            primary_target=CAPABILITY,
            current_level="Performed with Supervision",
            todays_objective=(
                f"{LEARNER} leads the maintenance-window decision end to end and "
                f"states the reasoning before {EXPERT} gives an opinion."
            ),
            your_role=(
                "Observe and question. Hand over the decision, and only correct "
                "if the choice would cause an unplanned outage."
            ),
            ask_before_explaining=(
                "Ask what they would schedule and why, before you say what you "
                "would do."
            ),
            watch_for=[
                "Whether they check the load trend rather than the static threshold.",
                "Whether they ask about the age of the last reading.",
                "Whether they name the fallback if the window slips.",
            ],
            knowledge_gap_to_explore=(
                f"{SECOND_CAPABILITY} -- they have observed it twice but never led it."
            ),
        ),
        "expert_debrief": DebriefQuestions(
            questions=[
                DebriefQuestion(
                    question=(
                        "You moved the window a week earlier than the schedule "
                        "rule allows. What made this case different?"
                    ),
                    grounded_in=(
                        "The expert overrode the standing maintenance interval "
                        "during the session."
                    ),
                    looking_for=(
                        "The conditions that make the written interval unreliable "
                        "-- the judgment nobody has written down."
                    ),
                ),
                DebriefQuestion(
                    question="Was there anything you noticed that the learner did not?",
                    grounded_in=(
                        "The learner did not mention the age of the last reading."
                    ),
                    looking_for="Signals an experienced reader treats as decisive.",
                ),
            ]
        ),
        "learner_debrief": DebriefQuestions(
            questions=[
                DebriefQuestion(
                    question=(
                        "The interval rule said the window was fine. Why was it "
                        "still a concern?"
                    ),
                    grounded_in="The learner accepted the override without explaining it.",
                    looking_for=(
                        "Whether they reconstruct the reasoning or only recall the "
                        "conclusion."
                    ),
                ),
                DebriefQuestion(
                    question=(
                        "What would you do if the neighbouring feeder could not "
                        "take the load?"
                    ),
                    grounded_in="The option the expert chose was available this time.",
                    looking_for="Whether their understanding extends past the case seen.",
                ),
            ]
        ),
        "analyze_session": SessionSynthesis(
            capability_evidence=CapabilityEvidence(
                kind="capability_evidence",
                person=LEARNER,
                capability=CAPABILITY,
                evidence=(
                    "Identified unprompted that the rising load trend made the "
                    "standing maintenance interval unreliable, and said so before "
                    "the expert gave an opinion."
                ),
                current_level=3,
                suggested_level=4,
                confidence="medium",
                evidence_sources=["Session transcript", "Learner debrief"],
            ),
            tacit_knowledge=TacitKnowledge(
                kind="tacit_knowledge",
                title="When the standing interval stops being a safe guide",
                operating_model_area=AREA,
                capability=CAPABILITY,
                situation=(
                    "Scheduled maintenance on an asset whose load has been climbing "
                    "for several weeks."
                ),
                observed_signals=[
                    "Load trending up over consecutive readings, not one spike.",
                    "The last physical reading is several days old.",
                    "Seasonal demand is beginning.",
                ],
                expert_reasoning=(
                    "The interval assumes last period's load. Any one signal the "
                    "expert would ignore; together they mean the margin is "
                    "smaller than the schedule implies."
                ),
                recommended_response=(
                    "Confirm the reading is current, then bring the window forward "
                    "before the trend closes the margin."
                ),
                why_it_matters=(
                    "Without this, a scheduler follows the interval and the asset "
                    "goes into the busiest period without a maintenance slot."
                ),
            ),
            remaining_gap=RemainingGap(
                kind="remaining_gap",
                capability=SECOND_CAPABILITY,
                understands=(
                    "That load can be moved to a neighbouring feeder before the "
                    "window opens."
                ),
                not_yet_demonstrated=[
                    "Has not led a transfer request themselves.",
                    "Has not negotiated a window with the regional operator.",
                ],
            ),
            next_activity=NextActivity(
                kind="next_activity",
                objective=(
                    f"{LEARNER} leads an emergency load transfer with {EXPERT} "
                    "observing only."
                ),
                recommended_experience=(
                    "The transfer already scheduled for the next maintenance "
                    "window on the adjacent feeder."
                ),
                learner_responsibilities=[
                    "Assess whether the neighbouring feeder has genuine headroom.",
                    "Raise and justify the transfer request.",
                    "Brief the operator on the fallback if the window slips.",
                ],
                expert_role=(
                    "Observe. Ask why after each decision. Intervene only on a "
                    "safety risk."
                ),
            ),
        ),
        "recommend_next_experience": NextExperience(
            capability=SECOND_CAPABILITY,
            current_level=1,
            target_level=2,
            rail=Rail.ASSIST,
            objective=(
                f"{LEARNER} assists a live load transfer and drafts the request "
                "themselves."
            ),
            recommended_experience=(
                "The transfer planned for the adjacent feeder during the next "
                "maintenance window."
            ),
            learner_responsibilities=[
                "Draft the transfer request and justify the headroom assessment.",
                "Identify the fallback if the window slips.",
            ],
            expert_role="Review the draft, then let it go out as written unless it is unsafe.",
            rationale=(
                "They can now read the load trend that triggers a transfer, but "
                "have only observed the transfer itself."
            ),
            risk_if_deferred=(
                "Load transfers stay expert-dependent, which is the decision most "
                "likely to be needed in the first month after departure."
            ),
            urgency="high",
        ),
        "build_operating_model": OperatingModelDraft(
            mission=(
                "Keep regional distribution assets serviceable through the "
                "high-demand season without unplanned outages."
            ),
            areas=[
                OperatingModelArea(
                    name=AREA,
                    purpose="Decide what gets maintained, when, and at what cost to service.",
                    processes=[
                        "Weekly review of asset condition readings.",
                        "Maintenance window scheduling against the load forecast.",
                        "Deferral approval when a window cannot be taken.",
                    ],
                    roles=[
                        "Maintenance planner owns the schedule.",
                        "Regional operator approves windows that affect supply.",
                    ],
                    governance=["Deferrals beyond one interval need operator sign-off."],
                    tools=["Asset register", "Load forecast sheet"],
                    metrics=["Windows taken on schedule", "Unplanned outages per quarter"],
                    decision_rights=[
                        "The planner may move a window by up to two weeks unilaterally."
                    ],
                    relationships=["Regional operator", "Contract maintenance crews"],
                    capabilities=[CAPABILITY, SECOND_CAPABILITY, "Window Negotiation"],
                    expert_dependency=(
                        "Only the departing expert currently judges when the "
                        "standing interval should be overridden."
                    ),
                )
            ],
            open_questions=[
                "Whether deferral approval is a written rule or local custom.",
            ],
        ),
        "identify_transfer_requirements": TransferRequirementSet(
            area=AREA,
            requirements=[
                TransferRequirement(
                    kind=RequirementKind.FORMAL,
                    label="Maintenance interval standard",
                    description="Can state the standing interval and where it is published.",
                    state=TransferState.COMPLETE,
                    evidence="Cited the interval correctly without prompting.",
                    risk_if_untransferred="Windows scheduled against the wrong standard.",
                ),
                TransferRequirement(
                    kind=RequirementKind.JUDGMENT,
                    label="Overriding the standing interval",
                    description=(
                        "Can decide, unsupervised, when trend conditions make the "
                        "interval unsafe."
                    ),
                    state=TransferState.PARTIAL,
                    evidence="Reasoned it out once, with the expert present.",
                    risk_if_untransferred=(
                        "Maintenance follows the calendar into the high-demand season."
                    ),
                ),
                TransferRequirement(
                    kind=RequirementKind.RELATIONSHIP,
                    label="Regional operator escalation",
                    description="Known to the operator well enough to negotiate a window by phone.",
                    state=TransferState.NONE,
                    evidence="Every contact in the material went through the expert.",
                    risk_if_untransferred="Windows that need negotiation simply do not happen.",
                ),
            ],
        ),
        "identify_formal_informal_gaps": FormalInformalAnalysis(
            area=AREA,
            formal_coverage_pct=70,
            informal_coverage_pct=25,
            gaps=[
                FormalInformalGap(
                    topic="Maintenance interval",
                    formal_rule="Service at the published interval for the asset class.",
                    actual_practice=(
                        "Experienced planners bring the window forward when load "
                        "has been trending up and the last reading is stale."
                    ),
                    why_they_differ=(
                        "The interval assumes stable load. The override is the "
                        "judgment that keeps it safe when load is not stable."
                    ),
                    documented=False,
                    severity=Status.AT_RISK,
                ),
                FormalInformalGap(
                    topic="Deferral approval",
                    formal_rule="(undocumented)",
                    actual_practice=(
                        "The planner calls the regional operator before raising a "
                        "formal deferral."
                    ),
                    why_they_differ="The informal call is what makes the formal step succeed.",
                    documented=False,
                    severity=Status.IN_PROGRESS,
                ),
            ],
        ),
        "generate_transfer_plan": TransferPlan(
            area=AREA,
            steps=[
                TransferPlanStep(
                    sequence=1,
                    capability=CAPABILITY,
                    rail=Rail.LEAD,
                    learner=LEARNER,
                    experience="Lead the next two weekly condition reviews.",
                    expert_role="Observe; question after each decision.",
                    success_signal="Flags a trend-driven override before the expert does.",
                    target_window="Weeks 1-2 of the remaining period.",
                ),
                TransferPlanStep(
                    sequence=2,
                    capability=SECOND_CAPABILITY,
                    rail=Rail.ASSIST,
                    learner=LEARNER,
                    experience="Draft and raise the next load transfer request.",
                    expert_role="Review the draft; let it go out unless unsafe.",
                    success_signal="Request approved without substantive rework.",
                    target_window="Week 3.",
                    depends_on=[1],
                ),
                TransferPlanStep(
                    sequence=3,
                    capability="Window Negotiation",
                    rail=Rail.OBSERVE,
                    learner=SECOND_LEARNER,
                    experience="Sit in on the operator call for the next contested window.",
                    expert_role="Lead the call; debrief afterwards.",
                    success_signal="Can describe what made the operator agree.",
                    target_window="Week 3.",
                ),
            ],
            not_achievable_before_departure=[
                "Independent window negotiation -- it needs a relationship that "
                "takes longer than the time remaining."
            ],
        ),
        "extract_tacit_knowledge": TacitKnowledgeSet(
            items=[
                KnowledgeItem(
                    title="Three signals that make the standing interval unsafe",
                    type=KnowledgeType.HEURISTIC,
                    capability=CAPABILITY,
                    operating_model_area=AREA,
                    situation="Scheduling maintenance on an asset with rising load.",
                    content=(
                        "Rising trend across consecutive readings, a reading more "
                        "than a few days old, and the season starting. Any one is "
                        "ignorable; together they mean the margin is smaller than "
                        "the schedule implies."
                    ),
                    why_it_matters=(
                        "It is the judgment that keeps a calendar rule from sending "
                        "an asset into peak demand unserviced."
                    ),
                    source="Expert debrief",
                    people_exposed=[LEARNER],
                ),
                KnowledgeItem(
                    title="Check neighbouring headroom before escalating",
                    type=KnowledgeType.EXPERT_INSIGHT,
                    capability=SECOND_CAPABILITY,
                    operating_model_area=AREA,
                    situation="A window cannot be taken without moving load.",
                    content=(
                        "Confirm the neighbouring feeder has genuine headroom, not "
                        "nominal headroom, before raising an escalation."
                    ),
                    why_it_matters="An escalation raised on nominal figures loses credibility.",
                    source="Session transcript",
                    people_exposed=[LEARNER, SECOND_LEARNER],
                ),
            ]
        ),
        "assess_capability_evidence": CapabilityAssessment(
            findings=[
                CapabilityFinding(
                    person=LEARNER,
                    capability=CAPABILITY,
                    current_level=3,
                    suggested_level=4,
                    evidence=(
                        "Stated the trend-driven override unprompted and justified "
                        "it against the written interval."
                    ),
                    evidence_sources=["Session transcript", "Learner debrief"],
                    confidence="medium",
                    counter_evidence=(
                        "Only one instance, and the expert was present throughout."
                    ),
                ),
                CapabilityFinding(
                    person=SECOND_LEARNER,
                    capability=CAPABILITY,
                    current_level=1,
                    suggested_level=1,
                    evidence="Present for the discussion; contributed no reasoning of their own.",
                    evidence_sources=["Session transcript"],
                    confidence="high",
                    counter_evidence="",
                ),
            ]
        ),
        "identify_trainer_candidates": TrainerCandidates(
            candidates=[
                TrainerCandidate(
                    person=LEARNER,
                    capability=CAPABILITY,
                    current_level=4,
                    readiness_to_teach=(
                        "Can already walk someone through reading the trend. Has "
                        "not yet explained the override judgment to a third person."
                    ),
                    evidence=[
                        "Two independent demonstrations in the last month.",
                        "Explained the reasoning unprompted in debrief.",
                    ],
                    next_step=f"Have them brief {SECOND_LEARNER} on the next review, unaided.",
                )
            ],
            capabilities_with_no_candidate=[SECOND_CAPABILITY, "Window Negotiation"],
        ),
        "analyze_readiness": ReadinessAnalysis(
            summary=(
                "Routine scheduling would survive the departure. The judgment "
                "calls and every external relationship would not."
            ),
            expert_dependent=[
                "Overriding the standing interval under trend conditions.",
                "Negotiating a contested window with the regional operator.",
            ],
            sustainable=[
                "Weekly condition review -- led twice without the expert present.",
            ],
            risks=[
                ReadinessRisk(
                    severity=Status.CRITICAL,
                    title="No local relationship with the regional operator",
                    problem=(
                        "Every window negotiation in the record went through the "
                        "departing expert."
                    ),
                    evidence="No other name appears on any operator contact.",
                    recommended_action=(
                        "Introduce a named local contact on the next two calls and "
                        "hand over the third."
                    ),
                    local_owner="",
                ),
                ReadinessRisk(
                    severity=Status.AT_RISK,
                    title="Override judgment rests on one demonstration",
                    problem="One unprompted instance is thin evidence for independence.",
                    evidence="Single occurrence, expert present.",
                    recommended_action="Have them lead the next two reviews unobserved.",
                    local_owner=LEARNER,
                ),
            ],
            before_departure=[
                "Hand over one operator negotiation end to end.",
                "Two unobserved condition reviews led locally.",
                "Write down the override heuristic and have it reviewed.",
            ],
        ),
        "generate_departure_plan": DeparturePlan(
            days_remaining=28,
            summary=(
                "Four weeks. Spend them on the two things that do not transfer by "
                "documentation: the override judgment and the operator relationship."
            ),
            actions=[
                DepartureAction(
                    week=1,
                    action="Learner leads both condition reviews; expert observes only.",
                    owner=LEARNER,
                    capability=CAPABILITY,
                    why_now="Independence needs more than one demonstration to be credible.",
                ),
                DepartureAction(
                    week=2,
                    action="Introduce the local contact on the operator call.",
                    owner=EXPERT,
                    capability="Window Negotiation",
                    why_now="A relationship needs two contacts before it holds on its own.",
                ),
                DepartureAction(
                    week=3,
                    action="Learner raises the load transfer request unaided.",
                    owner=LEARNER,
                    capability=SECOND_CAPABILITY,
                    why_now="Last window before departure where a transfer is actually due.",
                ),
                DepartureAction(
                    week=4,
                    action="Document the override heuristic and review it with the team.",
                    owner=EXPERT,
                    capability=CAPABILITY,
                    why_now="The only artefact that outlives the handover.",
                ),
            ],
            risks=[
                DepartureRisk(
                    title="Operator relationship does not transfer",
                    severity=Status.CRITICAL,
                    what_stops_working="Contested windows stop being negotiable locally.",
                    who_absorbs_it="",
                    mitigation="Two joint calls, then one handed over entirely.",
                    days_needed=10,
                ),
                DepartureRisk(
                    title="Override judgment stays thinly evidenced",
                    severity=Status.AT_RISK,
                    what_stops_working=(
                        "Scheduling reverts to the calendar rule under pressure."
                    ),
                    who_absorbs_it=LEARNER,
                    mitigation="Two unobserved reviews plus a written heuristic.",
                    days_needed=6,
                ),
            ],
            still_expert_dependent_at_departure=[
                "Independent window negotiation with the regional operator.",
            ],
        ),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, model in fixtures().items():
        path = OUT / f"{name}.json"
        path.write_text(
            json.dumps(model.model_dump(mode="json"), indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {path.relative_to(Path(__file__).parent.parent.parent)}")


if __name__ == "__main__":
    main()
