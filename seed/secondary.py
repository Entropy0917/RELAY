"""A second engagement, deliberately thin.

planv0.2.md section 0.5 makes the reusability claim structural rather than
aspirational: nothing about the RELAY model may be specific to one sector, and
the engagement switcher is how that gets demonstrated in about four seconds.
The claim only lands if the second engagement is *unmistakably* a different
kind of work -- so this one is hydropower turbine reliability in Central Asia,
with different roles, a different expert, a different departure horizon and
its own readiness weights.

Thin on purpose. This exists so every page renders something coherent when the
audience switches to it, and for no other reason. Three areas, four
capabilities, one past session, a handful of requirements and knowledge items.
Padding it out would cost a day and add nothing the primary corpus does not
already show, and a second engagement that looked as rich as the first would
raise the fair question of which one the demo actually spent its time on.

The tuned weights are the other half of the point. This engagement leans
harder on capability localization and lighter on formal documentation, which
is a real judgement a programme manager might make about an engineering
handover -- and the readiness popover will show those weights rather than the
defaults, which is only possible because weights are per-engagement data.
"""

from __future__ import annotations

from sqlalchemy import Connection

from app.db.schema import (
    capabilities,
    capability_evidence,
    debriefs,
    engagements,
    findings,
    knowledge_items,
    operating_model_areas,
    people,
    person_capabilities,
    recommendations,
    sessions,
    transfer_requirements,
)
from app.db.writes import apply_validation
from contracts.vocabulary import (
    FindingKind,
    KnowledgeType,
    RequirementKind,
    Role,
    SessionStage,
    TransferState,
    ValidationAction,
)

from seed.loader import SeedScope
from seed.timeline import days_ago, days_ahead, timestamp

ENGAGEMENT_ID = "eng-naryn-hydro"

# A different horizon from the primary engagement: this expert is not leaving
# next month, so the dashboards do not both read "critical".
DAYS_TO_DEPARTURE = 116

SOKOLOVA = "ph-sokolova"
NURLAN = "ph-nurlan"
AIGERIM = "ph-aigerim"
BAKYT = "ph-bakyt"

A_CONDITION = "pha-condition-monitoring"
A_OUTAGE = "pha-outage-planning"
A_SPARES = "pha-spares"

C_VIBRATION = "phc-vibration-signature"
C_SCOPE = "phc-outage-scope"
C_GOVERNOR = "phc-governor-calibration"
C_SPARES = "phc-critical-spares"

S_GOVERNOR = "phs-governor-walkdown"


def load(conn: Connection) -> int:
    """Insert the secondary engagement. Returns the number of rows written."""
    scope = SeedScope(conn, ENGAGEMENT_ID)

    scope.insert(
        engagements,
        id=ENGAGEMENT_ID,
        name="Hydropower Reliability Handover",
        org="Ala-Too Energy Company",
        sector="Energy & Utilities",
        location="Naryn Province, Kyrgyz Republic",
        mission=(
            "A two-year reliability assignment at a 42 MW run-of-river "
            "station. Unplanned outages have halved since it began. The "
            "question the assignment is actually being measured on is whether "
            "the station's own engineers can keep them down once the "
            "reliability engineer's contract ends."
        ),
        started_on=days_ago(614),
        ends_on=days_ahead(DAYS_TO_DEPARTURE),
        readiness_weights={
            "local_ownership": 0.20,
            "capability_localization": 0.35,
            "formal_transfer": 0.15,
            "informal_transfer": 0.20,
            "trainer_coverage": 0.10,
        },
        is_primary=False,
    )

    for person in (
        {
            "id": SOKOLOVA,
            "name": "Ing. Marta Sokolova",
            "title": "Turbine Reliability Engineer",
            "role": Role.EXPERT,
            "departure_date": days_ahead(DAYS_TO_DEPARTURE),
            "bio": (
                "Twenty-two years on Francis and Kaplan units, most of it in "
                "stations where the nearest spare is a two-day drive. Reads a "
                "vibration spectrum the way most people read a sentence."
            ),
        },
        {
            "id": NURLAN,
            "name": "Nurlan Abdiev",
            "title": "Mechanical Maintenance Lead",
            "role": Role.COUNTERPART,
            "departure_date": None,
            "bio": (
                "Nine years at the station, the last four leading mechanical "
                "maintenance. Knows every noise the units make and is "
                "learning to say why."
            ),
        },
        {
            "id": AIGERIM,
            "name": "Aigerim Toktogulova",
            "title": "Reliability Engineer",
            "role": Role.COUNTERPART,
            "departure_date": None,
            "bio": (
                "Joined from the national grid operator two years ago. Built "
                "the station's outage planning discipline from nothing and "
                "now owns it."
            ),
        },
        {
            "id": BAKYT,
            "name": "Bakyt Osmonov",
            "title": "Station Manager",
            "role": Role.MANAGER,
            "departure_date": None,
            "bio": (
                "Accountable for station availability and for the "
                "maintenance budget. Chairs the outage planning review."
            ),
        },
    ):
        scope.insert(people, **person)

    for area in (
        {
            "id": A_CONDITION,
            "name": "Turbine Condition Monitoring",
            "summary": (
                "Continuous vibration, bearing temperature and cavitation "
                "monitoring across both units, and the interpretation that "
                "turns a trace into a decision."
            ),
            "local_owner_id": NURLAN,
            "owner_validated": True,
            "critical": True,
            "formal_pct": 40,
            "processes": [
                "Weekly vibration spectrum capture on both units",
                "Bearing temperature trend review at each shift handover",
                "Quarterly alignment check against the baseline signature",
            ],
            "roles": [
                "Mechanical Maintenance Lead owns the monitoring routine",
                "Reliability Engineer reviews trends against the outage plan",
            ],
            "governance": [
                "Any spectrum change beyond the alarm band is reported to the "
                "Station Manager same shift",
            ],
            "tools": [
                "Portable spectrum analyser and the station's baseline library",
                "SCADA historian, 2-second resolution",
            ],
            "metrics": [
                "Unplanned outage hours per unit per quarter",
                "Time from anomaly detection to intervention",
            ],
            "decision_rights": [
                "Mechanical Maintenance Lead may derate a unit without "
                "approval; taking it offline needs the Station Manager",
            ],
            "relationships": [
                "OEM regional service desk -- consulted on signature "
                "interpretation, slowly",
            ],
            "capabilities_list": [
                "Vibration Signature Interpretation",
                "Governor Calibration",
            ],
        },
        {
            "id": A_OUTAGE,
            "name": "Outage Planning",
            "summary": (
                "Deciding what work goes into each planned outage window, in "
                "what order, and what is deferred to the next one."
            ),
            "local_owner_id": AIGERIM,
            "owner_validated": True,
            "critical": True,
            "formal_pct": 72,
            "processes": [
                "Annual outage calendar agreed against the hydrological year",
                "Scope frozen four weeks before each window",
                "Post-outage review within ten days",
            ],
            "roles": [
                "Reliability Engineer builds and owns the outage scope",
                "Station Manager approves the scope and the budget",
            ],
            "governance": [
                "Scope changes inside the freeze window require written "
                "justification and Station Manager approval",
            ],
            "tools": [
                "Outage scope workbook",
                "Maintenance history extract from the CMMS",
            ],
            "metrics": [
                "Planned outage hours versus actual",
                "Work deferred from one window to the next",
            ],
            "decision_rights": [
                "Reliability Engineer sets the scope; the Station Manager can "
                "remove items but not add them after the freeze",
            ],
            "relationships": [
                "Grid dispatcher -- outage windows are negotiated, not declared",
            ],
            "capabilities_list": ["Outage Scope Definition"],
        },
        {
            "id": A_SPARES,
            "name": "Critical Spares & Procurement",
            "summary": (
                "Holding the right spares for a station three hundred "
                "kilometres from the nearest depot, against a procurement "
                "cycle measured in months."
            ),
            "local_owner_id": None,
            "owner_validated": False,
            "critical": True,
            "formal_pct": 58,
            "processes": [
                "Annual critical spares review against failure history",
                "Long-lead item ordering ahead of the outage calendar",
            ],
            "roles": [
                "Reliability Engineer proposes; no single owner for the "
                "holding decision",
            ],
            "governance": [
                "Spares budget approved annually by the Station Manager",
            ],
            "tools": ["CMMS spares register", "OEM lead-time schedule"],
            "metrics": [
                "Stockout events on critical spares",
                "Value of slow-moving holdings",
            ],
            "decision_rights": [
                "Currently sits with the departing engineer in practice, "
                "whatever the procedure says",
            ],
            "relationships": [
                "OEM parts desk",
                "Two regional machining shops used for emergency fabrication",
            ],
            "capabilities_list": ["Critical Spares Forecasting"],
        },
    ):
        scope.insert(operating_model_areas, **area)

    for req_id, area_id, kind, label, description, state in (
        ("ph-cond-routine", A_CONDITION, RequirementKind.FORMAL,
         "Condition monitoring routine",
         "The written weekly capture and review routine.",
         TransferState.COMPLETE),
        ("ph-cond-baseline", A_CONDITION, RequirementKind.TOOL,
         "Baseline signature library",
         "The reference spectra both units are read against, and how a new "
         "baseline is established after major work.",
         TransferState.PARTIAL),
        ("ph-cond-read", A_CONDITION, RequirementKind.JUDGMENT,
         "Reading a spectrum change",
         "Telling a developing fault from an instrumentation artefact or a "
         "load change.",
         TransferState.PARTIAL),
        ("ph-cond-oem", A_CONDITION, RequirementKind.RELATIONSHIP,
         "OEM service desk",
         "Who to ask, how to frame it, and how long an answer takes.",
         TransferState.NONE),
        ("ph-out-scope", A_OUTAGE, RequirementKind.FORMAL,
         "Outage scoping procedure",
         "How scope is built, frozen and changed.",
         TransferState.COMPLETE),
        ("ph-out-workbook", A_OUTAGE, RequirementKind.TOOL,
         "Outage scope workbook",
         "The workbook and its maintenance-history inputs.",
         TransferState.COMPLETE),
        ("ph-out-defer", A_OUTAGE, RequirementKind.JUDGMENT,
         "What can safely wait a year",
         "Deferring work without accumulating a failure.",
         TransferState.COMPLETE),
        ("ph-out-dispatch", A_OUTAGE, RequirementKind.RELATIONSHIP,
         "Grid dispatcher negotiation",
         "Securing a window that suits the station rather than the schedule.",
         TransferState.PARTIAL),
        ("ph-spare-list", A_SPARES, RequirementKind.FORMAL,
         "Critical spares list and review",
         "The list, the review cycle and the failure history behind it.",
         TransferState.COMPLETE),
        ("ph-spare-leadtime", A_SPARES, RequirementKind.TECHNICAL,
         "Long-lead item planning",
         "Matching order dates to the outage calendar and the OEM schedule.",
         TransferState.PARTIAL),
        ("ph-spare-fabricate", A_SPARES, RequirementKind.TACIT,
         "When to fabricate locally",
         "Which parts can be machined regionally and which absolutely cannot.",
         TransferState.NONE),
        ("ph-spare-gov", A_SPARES, RequirementKind.GOVERNANCE,
         "Spares budget approval route",
         "How an unplanned critical purchase is authorised.",
         TransferState.COMPLETE),
    ):
        scope.insert(
            transfer_requirements,
            id=f"req-{req_id}",
            area_id=area_id,
            kind=kind,
            label=label,
            description=description,
            state=state,
            validated=state is TransferState.COMPLETE,
        )

    for capability in (
        {
            "id": C_VIBRATION,
            "name": "Vibration Signature Interpretation",
            "description": (
                "Reading a spectrum against the unit's baseline and saying "
                "what is developing, how fast, and whether it can wait for "
                "the planned window."
            ),
            "criticality": 5,
            "area_id": A_CONDITION,
        },
        {
            "id": C_SCOPE,
            "name": "Outage Scope Definition",
            "description": (
                "Building an outage scope that fits the window, the budget "
                "and the condition evidence."
            ),
            "criticality": 4,
            "area_id": A_OUTAGE,
        },
        {
            "id": C_GOVERNOR,
            "name": "Governor Calibration",
            "description": (
                "Calibrating and verifying the speed governor after "
                "mechanical work, including the response test."
            ),
            "criticality": 4,
            "area_id": A_CONDITION,
        },
        {
            "id": C_SPARES,
            "name": "Critical Spares Forecasting",
            "description": (
                "Deciding what must be on the shelf at a station three "
                "hundred kilometres from a depot."
            ),
            "criticality": 4,
            "area_id": A_SPARES,
        },
    ):
        scope.insert(capabilities, **capability)

    # Seeded levels. Nurlan on governor calibration is one step low and is
    # moved by the validation below, so this engagement also has a level with
    # an evidence chain behind it rather than four numbers and a story.
    for person_id, capability_id, level, exposures, demonstrated in (
        (SOKOLOVA, C_VIBRATION, 6, 74, 6),
        (SOKOLOVA, C_SCOPE, 5, 31, 41),
        (SOKOLOVA, C_GOVERNOR, 6, 48, 12),
        (SOKOLOVA, C_SPARES, 6, 22, 88),
        (NURLAN, C_VIBRATION, 3, 29, 6),
        (NURLAN, C_GOVERNOR, 3, 19, 12),  # -> 4 below
        (NURLAN, C_SPARES, 2, 5, 88),
        (AIGERIM, C_VIBRATION, 4, 21, 13),
        (AIGERIM, C_SCOPE, 6, 34, 41),
        (AIGERIM, C_SPARES, 3, 11, 88),
        (BAKYT, C_SCOPE, 3, 8, 41),
    ):
        scope.insert(
            person_capabilities,
            id=f"phpc-{person_id.removeprefix('ph-')}-{capability_id.removeprefix('phc-')}",
            person_id=person_id,
            capability_id=capability_id,
            level=level,
            exposure_count=exposures,
            last_demonstrated=None if demonstrated is None else days_ago(demonstrated),
        )

    scope.insert(
        sessions,
        id=S_GOVERNOR,
        title="Unit 2 governor walkdown after the spring outage",
        held_on=days_ago(12),
        stage=SessionStage.NEXT_ACTION,
        expert_id=SOKOLOVA,
        learner_ids=[NURLAN],
        area_id=A_CONDITION,
        capability_id=C_GOVERNOR,
        brief={
            "primary_target": "Governor Calibration",
            "current_level": "Performed with Supervision",
            "todays_objective": (
                "Nurlan calibrates Unit 2's governor and runs the response "
                "test without being prompted through the sequence."
            ),
            "your_role": "Stand back from the panel. Answer, do not instruct.",
            "ask_before_explaining": (
                "What will you check first if the response test overshoots?"
            ),
            "watch_for": [
                "Whether he verifies the feedback linkage before adjusting gain",
                "Whether he records the pre-adjustment values",
            ],
            "knowledge_gap_to_explore": (
                "Distinguishing a genuine governor fault from a hydraulic "
                "supply pressure problem upstream of it."
            ),
        },
        transcript=(
            "Walkdown and calibration, Unit 2, following the spring outage. "
            "Nurlan ran the full sequence from the procedure and recorded "
            "pre-adjustment values without being reminded. The response test "
            "overshot on the first pass; he checked the feedback linkage "
            "before touching gain, which is the order that matters. Second "
            "pass within tolerance. Ing. Sokolova intervened once, to point "
            "out that the hydraulic supply pressure reading had been drifting "
            "for three weeks and would have produced the same symptom."
        ),
        notes=(
            "He has the sequence and he has the discipline. What he does not "
            "have yet is the instinct to look upstream of the thing that is "
            "misbehaving -- the governor was fine, the oil supply was not."
        ),
    )

    scope.insert(
        debriefs,
        id="phdbf-governor-expert",
        session_id=S_GOVERNOR,
        role="expert",
        person_id=SOKOLOVA,
        questions=[
            {
                "id": "q1",
                "question": "He checked the linkage before touching gain. Taught or worked out?",
                "answer": (
                    "Taught, and it stuck, which is the part I care about. "
                    "Anyone can turn a gain adjustment until the trace looks "
                    "right and leave a linkage fault in place for the next "
                    "person to find."
                ),
            },
            {
                "id": "q2",
                "question": "What is he still missing?",
                "answer": (
                    "He solves the component in front of him. The supply "
                    "pressure had been drifting for three weeks in the "
                    "historian and nobody had looked, because the governor "
                    "was the thing that was complaining."
                ),
            },
        ],
        completed_at=timestamp(12),
    )

    scope.insert(
        debriefs,
        id="phdbf-governor-learner",
        session_id=S_GOVERNOR,
        role="learner",
        person_id=NURLAN,
        questions=[
            {
                "id": "q1",
                "question": "The test overshot. Walk me through what you did.",
                "answer": (
                    "Linkage first. If the feedback is lying to the governor "
                    "then the gain is the wrong thing to change, and you "
                    "cannot tell afterwards which one you fixed."
                ),
            },
            {
                "id": "q2",
                "question": "What would you do differently?",
                "answer": (
                    "Pull the hydraulic supply trend before I start, not "
                    "after. It was sitting in the historian the whole time."
                ),
            },
        ],
        completed_at=timestamp(11),
    )

    scope.insert(
        findings,
        id="phfnd-nurlan-governor",
        session_id=S_GOVERNOR,
        kind=FindingKind.CAPABILITY_EVIDENCE,
        title="Nurlan Abdiev calibrated Unit 2's governor unassisted",
        body={
            "person": "Nurlan Abdiev",
            "capability": "Governor Calibration",
            "current_level": "Performed with Supervision",
            "suggested_level": "Performed Independently",
            "evidence": [
                "Ran the full calibration sequence without prompting",
                "Recorded pre-adjustment values unprompted",
                "Checked the feedback linkage before adjusting gain when the "
                "response test overshot",
            ],
            "counter_evidence": [
                "Did not consult the hydraulic supply trend, which had been "
                "drifting for three weeks",
            ],
        },
        confidence="high",
        evidence_sources=["Session transcript", "Both debriefs", "Calibration record"],
        rationale=(
            "Independent execution with correct diagnostic ordering under a "
            "failed first pass. The upstream gap is a separate capability."
        ),
        impact="Turbine Condition Monitoring; unit availability after any mechanical work.",
        risk_if_untransferred=(
            "Governor calibration follows every outage. Without it the "
            "station waits for an OEM visit."
        ),
        status="pending",
    )

    apply_validation(
        scope,
        finding_id="phfnd-nurlan-governor",
        validated_by_id=SOKOLOVA,
        action=ValidationAction.APPROVE,
        person_capability_id=f"phpc-{NURLAN.removeprefix('ph-')}-"
        f"{C_GOVERNOR.removeprefix('phc-')}",
        new_level=4,
        evidence_summary=(
            "Calibrated Unit 2's governor unassisted and diagnosed the "
            "overshoot in the correct order."
        ),
        evidence_source="Unit 2 governor walkdown, transcript and calibration record",
        observed_on=days_ago(12),
        note=(
            "The upstream point is real but it is a condition-monitoring gap, "
            "not a calibration one. Logged against vibration instead."
        ),
    )

    for evidence_id, person_id, capability_id, offset, level_at_time, summary, source in (
        ("phev-nurlan-vib-1", NURLAN, C_VIBRATION, 201, 2,
         "Identified a bearing temperature trend ahead of the alarm band and "
         "raised it at handover.",
         "Shift handover log"),
        ("phev-nurlan-vib-2", NURLAN, C_VIBRATION, 63, 3,
         "Captured and filed a full spectrum set on both units without "
         "supervision; interpretation still reviewed.",
         "Condition monitoring record"),
        ("phev-aigerim-scope-1", AIGERIM, C_SCOPE, 219, 5,
         "Built the autumn outage scope end to end and defended two deferrals "
         "at the planning review.",
         "Outage planning review minutes"),
        ("phev-aigerim-scope-2", AIGERIM, C_SCOPE, 41, 6,
         "Ran the outage scoping walkthrough for two new maintenance "
         "planners, using her own worked examples.",
         "Training record"),
        ("phev-aigerim-vib-1", AIGERIM, C_VIBRATION, 13, 4,
         "Correlated a spectrum change on Unit 1 to a load pattern rather "
         "than a developing fault, and was right.",
         "Condition monitoring record"),
    ):
        scope.insert(
            capability_evidence,
            id=evidence_id,
            person_capability_id=(
                f"phpc-{person_id.removeprefix('ph-')}-"
                f"{capability_id.removeprefix('phc-')}"
            ),
            session_id=None,
            observed_on=days_ago(offset),
            level_at_time=level_at_time,
            summary=summary,
            source=source,
            created_at=timestamp(offset),
        )

    for item in (
        {
            "id": "phkn-baseline-after-work",
            "title": "Re-baseline after major work, or every reading afterwards is a lie",
            "type": KnowledgeType.EXPERT_INSIGHT,
            "summary": (
                "A spectrum is only meaningful against a baseline taken with "
                "the machine in its current mechanical state."
            ),
            "body": {
                "practice": (
                    "Establish a new baseline signature after any work that "
                    "touches alignment, bearings or the runner, before the "
                    "unit goes back into commercial operation. Not the week "
                    "after."
                ),
                "why_it_is_not_written_down": (
                    "The procedure names a baseline library. It does not say "
                    "the library expires."
                ),
            },
            "area_id": A_CONDITION,
            "capability_id": C_VIBRATION,
            "validated": True,
            "exposed": [NURLAN, AIGERIM],
            "days_ago": 188,
        },
        {
            "id": "phkn-look-upstream",
            "title": "The component that complains is rarely the component that failed",
            "type": KnowledgeType.HEURISTIC,
            "summary": (
                "Before working on the thing that is misbehaving, check what "
                "feeds it."
            ),
            "body": {
                "rule": (
                    "Pull three weeks of trend on every supply to the "
                    "component -- hydraulic pressure, oil temperature, "
                    "cooling water -- before touching the component itself."
                ),
                "worked_example": (
                    "A governor overshoot that was a hydraulic supply "
                    "pressure drift visible in the historian for three weeks."
                ),
            },
            "area_id": A_CONDITION,
            "capability_id": C_GOVERNOR,
            "validated": True,
            "exposed": [NURLAN],
            "days_ago": 12,
        },
        {
            "id": "phkn-fabricate-locally",
            "title": "Which parts the regional shops can machine, and which they cannot",
            "type": KnowledgeType.EXCEPTION,
            "summary": (
                "Emergency local fabrication is viable for a narrow set of "
                "parts and catastrophic for the rest."
            ),
            "body": {
                "normal_rule": "Critical spares are OEM-sourced.",
                "the_exception": (
                    "Wear rings, some coupling hardware and non-pressure "
                    "brackets can be machined regionally to drawing. Runner "
                    "components, governor hydraulics and anything on a "
                    "balance certificate cannot, at any price, under any "
                    "schedule pressure."
                ),
                "why_it_matters": (
                    "The pressure to fabricate comes when a unit is down and "
                    "the OEM quotes fourteen weeks, which is exactly when the "
                    "judgement is worst."
                ),
            },
            "area_id": A_SPARES,
            "capability_id": C_SPARES,
            "validated": False,
            "exposed": [NURLAN],
            "days_ago": 88,
        },
        {
            "id": "phkn-dispatcher",
            "title": "The grid dispatcher: outage windows are negotiated",
            "type": KnowledgeType.RELATIONSHIP,
            "summary": (
                "A window asked for six months out is granted; the same "
                "window asked for six weeks out costs something."
            ),
            "body": {
                "who": "Regional grid dispatch desk.",
                "what_works": [
                    "Bringing the whole year's plan once rather than each "
                    "window separately",
                    "Offering a second-choice window unprompted",
                ],
                "current_state": (
                    "Held jointly by the reliability engineer and the expert. "
                    "Partially transferred."
                ),
                "at_risk": True,
            },
            "area_id": A_OUTAGE,
            "capability_id": C_SCOPE,
            "validated": True,
            "exposed": [AIGERIM, BAKYT],
            "days_ago": 147,
        },
        {
            "id": "phkn-spring-outage",
            "title": "Spring outage: two deferrals that were right and one that was not",
            "type": KnowledgeType.CASE,
            "summary": (
                "Reviewing the deferral decisions from the spring window "
                "against what happened afterwards."
            ),
            "body": {
                "what_happened": (
                    "Three items were deferred out of the spring window on "
                    "budget grounds. Two ran without incident to the autumn "
                    "window. The third, a coupling inspection, produced an "
                    "unplanned four-day outage in August."
                ),
                "what_distinguished_them": (
                    "The two safe deferrals had condition evidence behind "
                    "them. The coupling was deferred on the basis that "
                    "nothing had gone wrong yet, which is not evidence."
                ),
                "what_changed": (
                    "Deferral now requires a condition-monitoring reading, "
                    "not an absence of complaints."
                ),
            },
            "area_id": A_OUTAGE,
            "capability_id": C_SCOPE,
            "validated": True,
            "exposed": [AIGERIM, NURLAN, BAKYT],
            "days_ago": 41,
        },
    ):
        scope.insert(
            knowledge_items,
            id=item["id"],
            title=item["title"],
            type=item["type"],
            summary=item["summary"],
            body=item["body"],
            area_id=item["area_id"],
            capability_id=item["capability_id"],
            session_id=None,
            expert_id=SOKOLOVA,
            validated=item["validated"],
            people_exposed=item["exposed"],
            captured_on=days_ago(item["days_ago"]),
        )

    scope.insert(
        recommendations,
        id="phrec-nurlan-upstream",
        session_id=S_GOVERNOR,
        person_id=NURLAN,
        capability_id=C_VIBRATION,
        objective="Check upstream supplies before diagnosing a component.",
        recommended_experience=(
            "On the next three anomalies of any kind, pull three weeks of "
            "trend on every supply to the component before touching it, and "
            "report what the trends showed even when they showed nothing."
        ),
        learner_responsibilities=[
            "Identify the supplies feeding the component",
            "Pull the historian trend for each",
            "State a conclusion before opening anything",
        ],
        expert_role="Review the conclusion, not the method.",
        status="open",
    )

    scope.insert(
        recommendations,
        id="phrec-aigerim-spares",
        session_id=None,
        person_id=AIGERIM,
        capability_id=C_SPARES,
        objective="Take ownership of the critical spares holding decision.",
        recommended_experience=(
            "Run the annual critical spares review with the expert present "
            "but not contributing, and defend the holding list to the Station "
            "Manager."
        ),
        learner_responsibilities=[
            "Rebuild the list from failure history and lead times",
            "Justify every long-lead item",
            "Say which items she is choosing not to hold, and why",
        ],
        expert_role="Attend. Do not speak.",
        status="open",
    )

    return scope.written
