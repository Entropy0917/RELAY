"""Five transfer sessions: four that already happened, and today's.

planv0.2.md section 4 B3 asks for "3-4 prior sessions with real outcomes, so
Sessions isn't empty on open". Outcomes are the operative word -- an empty
session list is a hackathon tell, but a list of sessions that produced nothing
is a worse one. Each of the four past sessions therefore carries its brief,
its transcript summary, both debriefs, the findings the synthesis produced,
and the validations Dr. Mitchell recorded against them. Four of those
validations are what moved a capability level; there is no other way a level
in this corpus could have moved.

The fifth session is Clinic 14, today, at PREPARE. Its brief is seeded so the
demo opens on something rather than on a spinner, and its transcript is seeded
too -- the capture step then has real text in it whether or not anybody wants
to paste from a phone on stage. Its debriefs, findings and validations are
deliberately *absent*: producing those live is the demonstration
(RELAY.txt, success flow steps 5-10).
"""

from __future__ import annotations

from contracts.vocabulary import FindingKind, SessionStage, ValidationAction

from seed.primary.areas import (
    DATA_QUALITY,
    FORECASTING,
    GOVERNANCE,
    REPLENISHMENT,
    SUPPLIERS,
)
from seed.primary.capabilities import (
    CONSUMPTION,
    DATA_QUALITY_CAP,
    DISRUPTION,
    FORECAST,
    INV_MONITOR,
    LEAD_TIME,
    REDISTRIBUTE,
    ROOT_CAUSE,
    SEASONAL,
    STOCKOUT_RISK,
)
from seed.primary.people import AMA, EFUA, KOJO, KWAME, MITCHELL
from seed.primary.transcript import CLINIC_14_NOTES, CLINIC_14_TRANSCRIPT

S_FORECAST = "ses-q2-forecast"
S_AUDIT = "ses-clinic9-audit"
S_SUPPLIER = "ses-leadtime-review"
S_ROOTCAUSE = "ses-clinic22-review"
S_CLINIC14 = "ses-clinic14"

# days_ago for each session. Irregular: sessions happen when the work does.
SESSION_DAYS: dict[str, int] = {
    S_FORECAST: 148,
    S_AUDIT: 97,
    S_SUPPLIER: 52,
    S_ROOTCAUSE: 23,
    S_CLINIC14: 0,
}


SESSIONS = [
    {
        "id": S_FORECAST,
        "title": "Q2 forecast build, nineteen-clinic cycle",
        "days_ago": SESSION_DAYS[S_FORECAST],
        "stage": SessionStage.NEXT_ACTION,
        "expert_id": MITCHELL,
        "learner_ids": [KWAME, KOJO],
        "area_id": FORECASTING,
        "capability_id": FORECAST,
        "brief": {
            "primary_target": "Demand Forecasting",
            "current_level": "Assisted",
            "todays_objective": (
                "Kwame builds the full nineteen-clinic Q2 forecast and defends "
                "every trend line he has drawn."
            ),
            "your_role": (
                "You are reviewing, not building. Let him finish a clinic "
                "before you say anything about it."
            ),
            "ask_before_explaining": (
                "Which of these nineteen forecasts would you bet the quarter's "
                "budget on, and which would you not?"
            ),
            "watch_for": [
                "Whether he questions a trend line or simply extends it",
                "Whether he asks Kojo for the lead-time constraint unprompted",
                "Whether he can say what would make him wrong",
            ],
            "knowledge_gap_to_explore": (
                "Reconciling forecast against the outreach campaign calendar, "
                "which is where last quarter's variance came from."
            ),
        },
        "transcript": (
            "Working session, four hours, regional supply office. Kwame built "
            "sixteen of the nineteen clinic forecasts unaided; three were "
            "reworked together after he extended a trend line through a "
            "period when Clinic 11 had been closed for renovation. Kojo "
            "supplied lead-time constraints and successfully challenged the "
            "Clinic 4 trend on the basis of a campaign that had inflated "
            "issues. Extended discussion of when a spike is signal. Full "
            "audio retained in the engagement record."
        ),
        "notes": (
            "He is past the arithmetic. What he does not yet do is ask what "
            "was happening at the clinic in the months he is extrapolating "
            "from -- the workbook does not prompt it and neither does the SOP."
        ),
    },
    {
        "id": S_AUDIT,
        "title": "Clinic 9 data quality audit",
        "days_ago": SESSION_DAYS[S_AUDIT],
        "stage": SessionStage.NEXT_ACTION,
        "expert_id": MITCHELL,
        "learner_ids": [AMA, KWAME],
        "area_id": DATA_QUALITY,
        "capability_id": DATA_QUALITY_CAP,
        "brief": {
            "primary_target": "Inventory Data Quality Assessment",
            "current_level": "Demonstrated Repeatedly",
            "todays_objective": (
                "Ama runs the audit and makes the call on whether Clinic 9's "
                "figures can be used, with you in the room but silent."
            ),
            "your_role": (
                "Observe. If she reaches the right conclusion by the wrong "
                "route, say so afterwards, not during."
            ),
            "ask_before_explaining": (
                "Before we open a single card -- what would have to be true "
                "for you to declare this site's data unusable?"
            ),
            "watch_for": [
                "Whether she sets her threshold before she sees the numbers",
                "Whether she can explain the decision to the clinic without it "
                "sounding like a sanction",
            ],
            "knowledge_gap_to_explore": (
                "Teaching the count discipline to a site that resents being "
                "audited."
            ),
        },
        "transcript": (
            "Unannounced audit, full day at Clinic 9 with the dispensary lead "
            "present. Ama set her acceptance criteria before opening the "
            "cards, found a 9% count-to-card discrepancy on two commodities, "
            "and traced it to a single week when the dispensary had been "
            "covered by a locum. She declared the data usable with a "
            "correction rather than unusable, and talked the lead through the "
            "correction herself. Kwame observed and asked twice why the "
            "threshold was 5%; neither answer satisfied him, which was the "
            "most useful thing that happened all day."
        ),
        "notes": (
            "Ama is teaching this now, not learning it. Kwame's question "
            "about the threshold is the real finding: he is applying the rule "
            "correctly without owning it."
        ),
    },
    {
        "id": S_SUPPLIER,
        "title": "Central store lead-time review",
        "days_ago": SESSION_DAYS[S_SUPPLIER],
        "stage": SessionStage.NEXT_ACTION,
        "expert_id": MITCHELL,
        "learner_ids": [KOJO],
        "area_id": SUPPLIERS,
        "capability_id": LEAD_TIME,
        "brief": {
            "primary_target": "Supplier Lead-Time Assessment",
            "current_level": "Performed Independently",
            "todays_objective": (
                "Kojo presents the lead-time case to the central store desk "
                "and asks for the planning assumption to be revised."
            ),
            "your_role": (
                "Sit in the room and say nothing unless the conversation "
                "turns adversarial."
            ),
            "ask_before_explaining": (
                "What is the smallest change you would accept from them and "
                "still call this a win?"
            ),
            "watch_for": [
                "Whether he leads with the evidence or with the complaint",
                "Whether he has a number in mind before the meeting starts",
            ],
            "knowledge_gap_to_explore": (
                "Sounding an escalation out with the regional pharmacist "
                "before filing it."
            ),
        },
        "transcript": (
            "Ninety minutes at the central medical store. Kojo opened with "
            "nine months of receipt data rather than with the two late "
            "deliveries everyone in the room was thinking about, which set "
            "the tone. The desk supervisor disputed two of the entries; both "
            "were checked on the spot and one was Kojo's error, which he "
            "conceded immediately and which cost him nothing. Agreement to "
            "move the planning assumption to eighteen days and to review "
            "again at quarter end. Dr. Mitchell did not speak."
        ),
        "notes": (
            "He negotiated better than I would have. Conceding the disputed "
            "entry was the whole meeting. What he has not done is the part "
            "before the meeting -- he went in cold rather than sounding it "
            "out with the regional pharmacist first."
        ),
    },
    {
        "id": S_ROOTCAUSE,
        "title": "Clinic 22 post-stockout review",
        "days_ago": SESSION_DAYS[S_ROOTCAUSE],
        "stage": SessionStage.NEXT_ACTION,
        "expert_id": MITCHELL,
        "learner_ids": [KWAME, AMA],
        "area_id": GOVERNANCE,
        "capability_id": ROOT_CAUSE,
        "brief": {
            "primary_target": "Root Cause Analysis of Stockouts",
            "current_level": "Demonstrated Repeatedly",
            "todays_objective": (
                "Kwame runs the review and takes Ama through her first "
                "independent root-cause write-up."
            ),
            "your_role": (
                "You are in the room as a participant, not as the chair. Let "
                "him correct Ama rather than correcting her yourself."
            ),
            "ask_before_explaining": (
                "What would have had to be different four weeks ago for this "
                "not to have happened?"
            ),
            "watch_for": [
                "Whether the corrective action changes a behaviour or only "
                "records a fact",
                "Whether Kwame teaches or simply demonstrates",
            ],
            "knowledge_gap_to_explore": (
                "Closing a corrective action honestly when the behaviour has "
                "not actually changed."
            ),
        },
        "transcript": (
            "Two hours, regional office, with the Clinic 22 dispensary lead "
            "dialled in. Kwame chaired. The room's first theory was a supply "
            "failure; the receipt log did not support it. Kwame worked back "
            "to a missed R&R cycle during a staffing gap and then further "
            "back to the fact that nobody had noticed the missed cycle for "
            "nineteen days. Ama drafted the write-up live and Kwame corrected "
            "it twice without taking the pen. Corrective action: stale-report "
            "flag at fourteen days, owner named, review date set."
        ),
        "notes": (
            "Kwame taught. That is the distinction I have been waiting for -- "
            "he could have written it in ten minutes and instead spent an "
            "hour making Ama write it. Her conclusion was right; the "
            "corrective action she drafted would not have changed anything, "
            "and he made her see why rather than telling her."
        ),
    },
    {
        "id": S_CLINIC14,
        "title": "Clinic 14 stock position review",
        "days_ago": SESSION_DAYS[S_CLINIC14],
        "stage": SessionStage.PREPARE,
        "expert_id": MITCHELL,
        "learner_ids": [KWAME],
        "area_id": REPLENISHMENT,
        "capability_id": STOCKOUT_RISK,
        "brief": {
            "primary_target": "Stockout Risk Identification",
            "current_level": "Performed with Supervision",
            "todays_objective": (
                "Kwame decides whether Clinic 14 needs intervention, and says "
                "why, before you offer any view of your own."
            ),
            "your_role": (
                "Let Kwame lead. Ask him to assess whether intervention is "
                "required and hold your own answer back until he has "
                "committed to his."
            ),
            "ask_before_explaining": (
                "The sheet says eighteen days against a fourteen-day reorder "
                "point. What would you do?"
            ),
            "watch_for": [
                "Whether he looks at the consumption trend rather than only "
                "the static days-of-cover figure",
                "Whether he notices how old the physical count is",
                "Whether he connects the rains to the demand curve unprompted",
                "Whether supplier lead time enters his reasoning at all",
            ],
            "knowledge_gap_to_explore": (
                "Emergency stock redistribution -- whether he thinks to look "
                "for genuine surplus nearby before reaching for an emergency "
                "order."
            ),
        },
        "transcript": CLINIC_14_TRANSCRIPT,
        "notes": CLINIC_14_NOTES,
    },
]


# ---------------------------------------------------------------------------
# Debriefs
# ---------------------------------------------------------------------------
# (session, role, person, [(question, answer), ...], days_ago)
# Expert and learner are asked different things on purpose: RELAY.txt splits
# them precisely so the synthesis has two accounts to reconcile rather than
# one account twice.

DEBRIEFS: list[tuple[str, str, str, list[tuple[str, str]], int]] = [
    (S_FORECAST, "expert", MITCHELL, [
        ("You reworked three of the nineteen forecasts with Kwame. What did "
         "those three have in common?",
         "All three covered a period when something at the clinic had changed "
         "-- a closure, a campaign, a staffing gap. He extended the line "
         "through the disruption instead of asking what the disruption was. "
         "The other sixteen were periods where nothing happened, and he was "
         "fine on all of them."),
        ("What did you deliberately not say during the session?",
         "That the Clinic 11 line was wrong. I waited about four minutes and "
         "he found it. If I had said it he would have learned that I check "
         "his work, which he already knows."),
    ], 148),
    (S_FORECAST, "learner", KWAME, [
        ("Which of the nineteen forecasts are you least confident in, and why?",
         "Clinic 11 and Clinic 4. Both had something going on in the history "
         "-- 11 was closed for part of it and 4 had a campaign. I can see now "
         "that the trend line is only honest if the months behind it were "
         "ordinary months, and I do not have a way of knowing that from the "
         "workbook."),
        ("What would you do differently on the next cycle?",
         "Check the outreach calendar and the closure log before I draw "
         "anything. Should take an hour for all nineteen."),
    ], 147),
    (S_AUDIT, "expert", MITCHELL, [
        ("Ama declared the data usable with a correction rather than "
         "unusable. Was that the call you would have made?",
         "Yes, and for the reason she gave rather than the reason I would "
         "have given. She could isolate the discrepancy to one week with a "
         "locum, so the rest of the record stands. I would probably have been "
         "harder on them and I would have been wrong."),
        ("Kwame asked twice why the recount threshold is 5%. How did you read "
         "that?",
         "That he is applying the rule correctly and does not own it. He "
         "cannot tell me what 5% is protecting against, so he cannot tell me "
         "when 5% is the wrong number. That is a gap, and it is not a gap "
         "that more audits will close."),
    ], 97),
    (S_AUDIT, "learner", AMA, [
        ("You set your acceptance criteria before opening the cards. Why?",
         "Because if you look first you will find a reason for whatever you "
         "already suspect. I learned that the hard way during the "
         "reconciliation -- we went into four sites certain the cards were "
         "being copied forward and we found it in three of them, and I am "
         "still not sure the third one was real."),
        ("What was hardest about the conversation with the dispensary lead?",
         "Telling him the number was wrong without telling him he was wrong. "
         "He had covered a locum week on top of his own job. If I had led "
         "with the discrepancy he would have stopped listening."),
    ], 96),
    (S_SUPPLIER, "expert", MITCHELL, [
        ("Kojo conceded a disputed entry immediately. What did that buy him?",
         "Everything. The supervisor had come in expecting to defend the "
         "store and instead spent the rest of the meeting checking Kojo's "
         "arithmetic with him. You cannot argue with someone who corrects "
         "himself in front of you."),
        ("What is he still missing?",
         "The half hour before the meeting. He went in cold. I would have "
         "called the regional pharmacist first, so that when the store "
         "supervisor mentioned it afterwards -- and he will have -- it was "
         "already a conversation and not a complaint."),
    ], 52),
    (S_SUPPLIER, "learner", KOJO, [
        ("You opened with nine months of data rather than the two late "
         "deliveries. Was that deliberate?",
         "Yes. Two late deliveries is a grievance and nine months is a "
         "pattern. If I lead with the grievance he defends the two "
         "deliveries and we never get to the pattern."),
        ("You accepted eighteen days when your own log says nineteen and a "
         "half. Why?",
         "Because eighteen is a number he can defend upward to his own "
         "management and nineteen and a half is not. I would rather have "
         "eighteen now and review at quarter end than be right and have "
         "nothing."),
    ], 51),
    (S_ROOTCAUSE, "expert", MITCHELL, [
        ("Kwame chaired and corrected Ama twice without taking the pen. What "
         "does that tell you?",
         "That he can teach this, not just do it. There is a version of that "
         "session that finishes in ten minutes with a better write-up and "
         "nobody any more capable than they were. He did not choose that "
         "version."),
        ("Was the corrective action right?",
         "The second one. Ama's first draft recorded that the R&R had been "
         "missed, which everyone already knew. Kwame made her ask why nobody "
         "noticed for nineteen days, and that produced the stale-report flag. "
         "That one will change something."),
    ], 23),
    (S_ROOTCAUSE, "learner", KWAME, [
        ("The room's first theory was supply failure. What made you drop it?",
         "The receipt log. Everything that was ordered arrived, and it "
         "arrived roughly on time. Once that is true it is not a supply "
         "problem, it is a demand-signal problem, and the only demand signal "
         "we have is the R&R."),
        ("You spent an hour making Ama write something you could have written "
         "in ten minutes. Was that the right use of the session?",
         "Dr. Mitchell will be gone in a month. If I am the only one who can "
         "write these then we have not fixed anything, we have just moved the "
         "single point of failure closer."),
    ], 22),
]


# ---------------------------------------------------------------------------
# Findings and the validations recorded against them
# ---------------------------------------------------------------------------
# Every level movement in the corpus is here, and nowhere else. Findings are
# AI output and start `pending`; a validation is the human decision about it.
# The four that carry `new_level` run through app.db.writes.apply_validation,
# which writes the validation, appends evidence, and only then moves the
# level -- in that order, because the trigger will not permit any other.

FINDINGS = [
    {
        "id": "fnd-q2-kwame-forecast",
        "session_id": S_FORECAST,
        "kind": FindingKind.CAPABILITY_EVIDENCE,
        "title": "Kwame Mensah built sixteen of nineteen forecasts unaided",
        "body": {
            "person": "Kwame Mensah",
            "capability": "Demand Forecasting",
            "current_level": "Assisted",
            "suggested_level": "Performed Independently",
            "evidence": [
                "Built 16 of 19 clinic forecasts without intervention",
                "Identified and corrected his own Clinic 4 trend after Kojo "
                "raised the campaign period",
                "Stated the conditions under which he would consider the "
                "forecast wrong",
            ],
            "counter_evidence": [
                "Extended a trend line through a period of clinic closure "
                "without asking what the period contained",
            ],
        },
        "confidence": "high",
        "evidence_sources": ["Session transcript", "Learner debrief",
                             "Forecast workbook revision history"],
        "rationale": (
            "Independent production across the great majority of the cycle, "
            "with self-correction observed. The three reworked forecasts "
            "share a single cause that is addressed by a checklist step, not "
            "by further supervision."
        ),
        "impact": "Demand Forecasting is the input to every replenishment decision.",
        "risk_if_untransferred": (
            "The quarterly forecast is the only planning artefact the Network "
            "has. Without a local owner it stops being produced in the first "
            "quarter after departure."
        ),
        "validation": {
            "action": ValidationAction.APPROVE,
            "by": MITCHELL,
            "person_capability": (KWAME, FORECAST),
            "new_level": 4,
            "evidence_summary": (
                "Built 16 of 19 clinic forecasts unaided across a full Q2 "
                "cycle and self-corrected the Clinic 4 trend line."
            ),
            "evidence_source": "Q2 forecast build, session transcript and learner debrief",
            "note": (
                "Agreed. The closure-period error is a checklist gap, not a "
                "capability gap -- I have added the calendar check to the SOP "
                "rather than holding him at Assisted for it."
            ),
        },
    },
    {
        "id": "fnd-q2-calendar-check",
        "session_id": S_FORECAST,
        "kind": FindingKind.TACIT_KNOWLEDGE,
        "title": "A trend line is only honest if the months behind it were ordinary",
        "body": {
            "formal_knowledge": (
                "Build the quarterly forecast from twelve months of issue "
                "data, adjusted for season."
            ),
            "expert_practice": (
                "Before drawing any trend, establish what was happening at "
                "that clinic during the history being extrapolated from -- "
                "closures, campaigns, staffing gaps, outreach cohorts. A "
                "trend through a disrupted period is arithmetic, not a "
                "forecast."
            ),
            "signals": [
                "Facility closure or renovation in the history window",
                "Outreach campaign inflating issues for one or two months",
                "A staffing gap during which reporting was estimated",
            ],
            "recommended_response": (
                "Check the outreach calendar and closure log for all clinics "
                "before drawing a single trend line. One hour for nineteen "
                "sites."
            ),
        },
        "confidence": "high",
        "evidence_sources": ["Session transcript", "Expert debrief"],
        "rationale": (
            "The expert applied this consistently and it is absent from the "
            "written procedure, which is the definition of a formal/informal "
            "gap."
        ),
        "impact": "Demand Forecasting; Clinic Consumption Analysis.",
        "risk_if_untransferred": (
            "Forecast variance is currently blamed on volatility. It is "
            "partly this, and nothing in the SOP would ever reveal that."
        ),
        "validation": {
            "action": ValidationAction.APPROVE,
            "by": MITCHELL,
            "note": "Added to the forecasting SOP as a pre-step at the same time.",
        },
    },
    {
        "id": "fnd-audit-ama-quality",
        "session_id": S_AUDIT,
        "kind": FindingKind.CAPABILITY_EVIDENCE,
        "title": "Ama Boateng set acceptance criteria before seeing the data",
        "body": {
            "person": "Ama Boateng",
            "capability": "Inventory Data Quality Assessment",
            "current_level": "Demonstrated Repeatedly",
            "suggested_level": "Can Teach Others",
            "evidence": [
                "Set acceptance criteria before opening any records, and said "
                "why",
                "Isolated a 9% discrepancy to a single locum-covered week "
                "rather than condemning the record",
                "Delivered the correction to the dispensary lead without it "
                "being received as a sanction",
                "Has trained four dispensary leads on the count protocol she "
                "rewrote",
            ],
        },
        "confidence": "high",
        "evidence_sources": ["Session transcript", "Expert debrief",
                             "Training record", "Audit programme design note"],
        "rationale": (
            "Teaching is the distinguishing behaviour at this level and it is "
            "on the record four times, not once. The method is hers: she "
            "designed the audit programme and the sampling."
        ),
        "impact": "Data Quality; Clinic Reporting.",
        "risk_if_untransferred": (
            "Data quality is the input every other number depends on. It "
            "already has a local owner; this is about whether it survives her "
            "moving on, not the expert leaving."
        ),
        "validation": {
            "action": ValidationAction.APPROVE,
            "by": MITCHELL,
            "person_capability": (AMA, DATA_QUALITY_CAP),
            "new_level": 6,
            "evidence_summary": (
                "Ran the Clinic 9 audit unaided, set criteria in advance, and "
                "has trained four dispensary leads on the protocol she wrote."
            ),
            "evidence_source": "Clinic 9 data quality audit, transcript and training record",
            "note": (
                "She has been teaching this for two quarters. The record was "
                "behind the reality."
            ),
        },
    },
    {
        "id": "fnd-audit-threshold-ownership",
        "session_id": S_AUDIT,
        "kind": FindingKind.TACIT_KNOWLEDGE,
        "title": "Know what a threshold is protecting against, or you cannot move it",
        "body": {
            "formal_knowledge": (
                "Count discrepancies above 5% trigger a recount before the "
                "number enters the LMIS."
            ),
            "expert_practice": (
                "The 5% exists because below it the cost of a recount exceeds "
                "the cost of the error, at the volumes these clinics run. At "
                "a high-volume site 5% is too loose and at a very small site "
                "it fires on a single pack. Anyone who cannot say that cannot "
                "be trusted to apply the rule at a site it does not fit."
            ),
            "signals": [
                "A rule applied correctly but never questioned",
                "A site whose volume is far from the average the rule was set "
                "for",
            ],
            "recommended_response": (
                "Before applying any threshold at an unusual site, state what "
                "it is protecting against and check the protection still "
                "holds."
            ),
        },
        "confidence": "medium",
        "evidence_sources": ["Session transcript", "Expert debrief"],
        "rationale": (
            "Raised twice by the learner in one session without a "
            "satisfactory answer being available in any document."
        ),
        "impact": "Data Quality; Inventory Monitoring; Replenishment.",
        "risk_if_untransferred": (
            "Every threshold in the operating model has this problem, "
            "including the 14-day reorder point."
        ),
        "validation": {
            "action": ValidationAction.EDIT,
            "by": MITCHELL,
            "edited_body": {
                "formal_knowledge": (
                    "Count discrepancies above 5% trigger a recount before the "
                    "number enters the LMIS."
                ),
                "expert_practice": (
                    "The 5% is a cost trade-off set at the Network's median "
                    "clinic volume: below it, a recount costs more than the "
                    "error does. It is too loose at the four high-volume "
                    "sites and too tight at the three smallest, where it can "
                    "fire on a single pack. The rule is not wrong; it is "
                    "calibrated to a site that not every site is."
                ),
                "signals": [
                    "A rule applied correctly but never questioned",
                    "A site whose monthly volume is more than double or less "
                    "than half the Network median",
                ],
                "recommended_response": (
                    "Before applying any threshold at an atypical site, state "
                    "what it is protecting against and check that the "
                    "protection still holds at that volume. This applies to "
                    "the 14-day reorder point as much as to the 5%."
                ),
            },
            "note": (
                "Broadened it. This is not a data-quality point, it is a "
                "thresholds point, and it applies to replenishment more "
                "sharply than it applies here."
            ),
        },
    },
    {
        "id": "fnd-audit-kwame-gap",
        "session_id": S_AUDIT,
        "kind": FindingKind.REMAINING_GAP,
        "title": "Kwame applies the recount threshold without owning it",
        "body": {
            "person": "Kwame Mensah",
            "capability": "Inventory Data Quality Assessment",
            "understands": [
                "When the 5% rule fires and what to do about it",
                "That a stale count is less useful than a fresh one",
            ],
            "not_demonstrated": [
                "What the 5% threshold is protecting against",
                "When the threshold is the wrong number for a site",
                "Whether a figure is usable when the rule does not fire but "
                "the data is old",
            ],
            "recommendation": (
                "Do not advance the capability. This is the same shape as the "
                "reorder-threshold question and should be addressed there, "
                "where it matters more."
            ),
        },
        "confidence": "high",
        "evidence_sources": ["Session transcript", "Expert debrief"],
        "rationale": (
            "Understanding a rule is not the same as being able to judge when "
            "it does not apply. The distinction is the one RELAY exists to "
            "keep."
        ),
        "impact": "Data Quality; Replenishment.",
        "risk_if_untransferred": (
            "A coordinator who cannot tell when a threshold does not fit will "
            "apply it faithfully through the season when it fits worst."
        ),
        "validation": {
            "action": ValidationAction.APPROVE,
            "by": MITCHELL,
            "note": (
                "Correct, and it is the more important of the two findings "
                "from this session."
            ),
        },
    },
    {
        "id": "fnd-supplier-kojo-leadtime",
        "session_id": S_SUPPLIER,
        "kind": FindingKind.CAPABILITY_EVIDENCE,
        "title": "Kojo Asare carried the lead-time case alone",
        "body": {
            "person": "Kojo Asare",
            "capability": "Supplier Lead-Time Assessment",
            "current_level": "Performed Independently",
            "suggested_level": "Demonstrated Repeatedly",
            "evidence": [
                "Led the central store conversation unassisted; the expert "
                "did not speak",
                "Opened on nine months of evidence rather than on the two "
                "recent failures",
                "Conceded a disputed entry immediately and kept the room",
                "Secured a revision of the planning assumption to 18 days "
                "with a quarter-end review",
            ],
            "counter_evidence": [
                "Did not prepare the ground with the regional pharmacist "
                "beforehand",
            ],
        },
        "confidence": "high",
        "evidence_sources": ["Session transcript", "Expert debrief",
                             "Lead-time log", "Quarterly review minutes"],
        "rationale": (
            "Third independent demonstration on this capability, and the "
            "first under adversarial conditions."
        ),
        "impact": "Supplier Management; Replenishment buffer sizing.",
        "risk_if_untransferred": (
            "The planning lead time is the difference between a buffer that "
            "works and one that is eight days short."
        ),
        "validation": {
            "action": ValidationAction.APPROVE,
            "by": MITCHELL,
            "person_capability": (KOJO, LEAD_TIME),
            "new_level": 5,
            "evidence_summary": (
                "Led the central store lead-time negotiation unassisted and "
                "secured a revised planning assumption on nine months of "
                "evidence."
            ),
            "evidence_source": "Central store lead-time review, transcript and minutes",
            "note": (
                "Not yet a teacher -- the relationship groundwork is missing "
                "and he would not know to teach it. Everything else is there."
            ),
        },
    },
    {
        "id": "fnd-supplier-next",
        "session_id": S_SUPPLIER,
        "kind": FindingKind.NEXT_ACTIVITY,
        "title": "Kojo to prepare the next escalation through the regional pharmacist",
        "body": {
            "objective": "Supplier escalation groundwork",
            "recommended_experience": (
                "Before the quarter-end review, have Kojo sound the position "
                "out with the regional pharmacist and adjust his ask on what "
                "comes back. Dr. Mitchell to make the introduction and then "
                "stay out of it."
            ),
            "learner_responsibilities": [
                "Decide what he wants from the quarter-end review before "
                "speaking to anyone",
                "Put the position to the regional pharmacist informally",
                "Adjust the ask, or decide not to, and be able to say why",
            ],
            "expert_role": "Introduce, then observe.",
        },
        "confidence": "medium",
        "evidence_sources": ["Expert debrief"],
        "rationale": (
            "The only thing separating this capability from teachable is a "
            "relationship step he has never been shown."
        ),
        "impact": "Supplier Management.",
        "risk_if_untransferred": (
            "Relationship capital is the part of this operating model that "
            "leaves with the expert most completely."
        ),
        "validation": {
            "action": ValidationAction.APPROVE,
            "by": MITCHELL,
            "note": "Introduction made. Scheduled against the quarter-end review.",
        },
    },
    {
        "id": "fnd-rootcause-kwame-teach",
        "session_id": S_ROOTCAUSE,
        "kind": FindingKind.CAPABILITY_EVIDENCE,
        "title": "Kwame Mensah taught the root-cause method rather than performing it",
        "body": {
            "person": "Kwame Mensah",
            "capability": "Root Cause Analysis of Stockouts",
            "current_level": "Demonstrated Repeatedly",
            "suggested_level": "Can Teach Others",
            "evidence": [
                "Chaired the review and took the room off its first theory "
                "using the receipt log",
                "Worked past the proximate cause to the nineteen-day "
                "detection gap",
                "Corrected Ama's draft twice without taking the pen",
                "Produced a corrective action that changes a behaviour rather "
                "than recording a fact",
            ],
        },
        "confidence": "high",
        "evidence_sources": ["Session transcript", "Expert debrief",
                             "Learner debrief", "Corrective action register"],
        "rationale": (
            "Teaching under time pressure, with a correct account available "
            "to him faster if he had simply written it. He chose the slower "
            "route deliberately and said why."
        ),
        "impact": "Governance & Performance Review; Stockout Escalation.",
        "risk_if_untransferred": (
            "Root-cause discipline is what converts a stockout register into "
            "a change in behaviour. Without a local teacher it decays to a "
            "list within two quarters."
        ),
        "validation": {
            "action": ValidationAction.APPROVE,
            "by": EFUA,
            "person_capability": (KWAME, ROOT_CAUSE),
            "new_level": 6,
            "evidence_summary": (
                "Chaired the Clinic 22 review, reached the detection gap, and "
                "taught the write-up to Ama rather than producing it himself."
            ),
            "evidence_source": "Clinic 22 post-stockout review, transcript and both debriefs",
            "note": (
                "I was in the room. Validating this myself rather than "
                "leaving it to Dr. Mitchell -- after next month it will be my "
                "signature on these in any case."
            ),
        },
    },
    {
        "id": "fnd-rootcause-second-datapoint",
        "session_id": S_ROOTCAUSE,
        "kind": FindingKind.TACIT_KNOWLEDGE,
        "title": "Escalate on the second data point, not the third",
        "body": {
            "formal_knowledge": (
                "Escalation to the DHMT if a stockout is unresolved within 72 "
                "hours."
            ),
            "expert_practice": (
                "Escalate when the second consecutive signal appears, not when "
                "the pattern is undeniable. By the third the damage is done "
                "and the escalation is a report."
            ),
            "signals": [
                "Two consecutive cycles in the same direction",
                "A second late delivery from the same supplier",
            ],
            "recommended_response": (
                "Treat the second occurrence as the trigger and say "
                "explicitly that it is the second."
            ),
        },
        "confidence": "low",
        "evidence_sources": ["Session transcript"],
        "rationale": (
            "Stated once, in passing, without a worked example behind it."
        ),
        "impact": "Stockout Escalation; Supplier Management.",
        "risk_if_untransferred": "Low -- the underlying judgement is captured elsewhere.",
        "validation": {
            "action": ValidationAction.REJECT,
            "by": MITCHELL,
            "note": (
                "I did not say this and I do not believe it as stated. "
                "Sometimes the second point is the trigger and sometimes it is "
                "noise; the whole skill is telling them apart, and writing it "
                "as a counting rule would make people worse at it, not "
                "better. Rejecting rather than editing -- there is nothing "
                "here to keep."
            ),
        },
    },
    {
        "id": "fnd-rootcause-ama-next",
        "session_id": S_ROOTCAUSE,
        "kind": FindingKind.NEXT_ACTIVITY,
        "title": "Ama to lead the next root-cause review end to end",
        "body": {
            "objective": "Root Cause Analysis of Stockouts",
            "recommended_experience": (
                "Ama chairs the next post-stockout review and drafts the "
                "corrective action without a second pair of eyes until she "
                "has finished. Kwame attends as a participant."
            ),
            "learner_responsibilities": [
                "Chair the review",
                "Separate proximate cause from detection failure",
                "Draft a corrective action that names an owner and a "
                "behaviour, not a fact",
                "Defend it at the quarterly review",
            ],
            "expert_role": (
                "None. Kwame supervises; Dr. Mitchell does not attend."
            ),
        },
        "confidence": "high",
        "evidence_sources": ["Session transcript", "Expert debrief"],
        "rationale": (
            "She reached the right conclusion unaided and failed only at the "
            "corrective action, which is one specific, coachable step."
        ),
        "impact": "Governance & Performance Review.",
        "risk_if_untransferred": (
            "A single local teacher is a single point of failure by another "
            "name."
        ),
        "validation": {
            "action": ValidationAction.APPROVE,
            "by": EFUA,
            "note": "Scheduled against the next tracer-commodity stockout.",
        },
    },
]


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
# (id, session, person, capability, objective, experience, responsibilities,
#  expert_role, status)

RECOMMENDATIONS = [
    {
        "id": "rec-kojo-pharmacist",
        "session_id": S_SUPPLIER,
        "person_id": KOJO,
        "capability_id": LEAD_TIME,
        "objective": "Prepare the quarter-end supplier escalation through the regional pharmacist.",
        "recommended_experience": (
            "Sound the position out informally before the quarter-end review "
            "and adjust the ask on what comes back."
        ),
        "learner_responsibilities": [
            "Decide the ask before speaking to anyone",
            "Put it to the regional pharmacist informally",
            "Adjust it, or decide not to, and be able to say why",
        ],
        "expert_role": "Make the introduction, then stay out of it.",
        "status": "open",
    },
    {
        "id": "rec-ama-chair",
        "session_id": S_ROOTCAUSE,
        "person_id": AMA,
        "capability_id": ROOT_CAUSE,
        "objective": "Chair a post-stockout review end to end.",
        "recommended_experience": (
            "Take the next tracer-commodity stockout review without a second "
            "pair of eyes on the corrective action until it is drafted."
        ),
        "learner_responsibilities": [
            "Chair the review",
            "Separate proximate cause from detection failure",
            "Draft a corrective action that names an owner and a behaviour",
            "Defend it at the quarterly review",
        ],
        "expert_role": "None. Kwame supervises.",
        "status": "open",
    },
    {
        "id": "rec-kwame-seasonal",
        "session_id": S_FORECAST,
        "person_id": KWAME,
        "capability_id": SEASONAL,
        "objective": "Derive a seasonal uplift without the method in front of him.",
        "recommended_experience": (
            "Take six clinics' malaria caseload history and produce the "
            "uplift, then compare against Kojo's, who has already done this "
            "for the other six."
        ),
        "learner_responsibilities": [
            "Pull the caseload series from the DHMT contact directly",
            "Derive the uplift per site",
            "Explain any divergence from Kojo's figures",
        ],
        "expert_role": "Review the output, not the working.",
        "status": "open",
    },
    {
        "id": "rec-kwame-calendar",
        "session_id": S_FORECAST,
        "person_id": KWAME,
        "capability_id": FORECAST,
        "objective": "Close the closure-and-campaign gap in the forecast cycle.",
        "recommended_experience": (
            "Run the calendar check across all nineteen clinics before the "
            "next cycle and report what it changed."
        ),
        "learner_responsibilities": [
            "Obtain the outreach calendar and closure log",
            "Re-examine every trend line drawn through a disrupted period",
        ],
        "expert_role": "Nothing. This is a checklist step now.",
        "status": "completed",
    },
    {
        "id": "rec-ama-consumption-teach",
        "session_id": S_AUDIT,
        "person_id": AMA,
        "capability_id": CONSUMPTION,
        "objective": "Extend the consumption-shape method to the remaining dispensary leads.",
        "recommended_experience": (
            "Teach two more sites per cycle until all nineteen flag their own "
            "anomalies before the district does."
        ),
        "learner_responsibilities": [
            "Run the teaching session at each site",
            "Record who has been trained and on what",
        ],
        "expert_role": "None.",
        "status": "open",
    },
    {
        "id": "rec-kwame-redistribution",
        "session_id": S_ROOTCAUSE,
        "person_id": KWAME,
        "capability_id": REDISTRIBUTE,
        "objective": "Lead a redistribution evaluation end to end.",
        "recommended_experience": (
            "The next time a site is exposed, Kwame evaluates whether stock "
            "can safely be moved from a neighbouring clinic before any "
            "emergency order is raised."
        ),
        "learner_responsibilities": [
            "Identify candidate sending sites from consumption trend, not "
            "stock level",
            "Establish whether the surplus is genuine",
            "Check expiry and batch",
            "Check transport and road status",
            "Establish which desk approves the transfer",
            "Make a recommendation and own it",
        ],
        "expert_role": "Observe. Intervene only if the transfer would create risk.",
        "status": "open",
    },
]


# ---------------------------------------------------------------------------
# Session evidence that moved nothing
# ---------------------------------------------------------------------------
# Most of what happens in a session is not a promotion. These rows are the
# observations the synthesis recorded against people who were in the room and
# whose standing did not change -- which is the ordinary case, and a passport
# that only ever shows step changes would misrepresent how transfer actually
# goes.
#
# (session, person, capability, days_ago, summary, source)

SESSION_EVIDENCE: list[tuple[str, str, str, int, str, str]] = [
    (S_FORECAST, KOJO, FORECAST, 148,
     "Challenged the Clinic 4 trend on the basis of an outreach campaign that "
     "had inflated issues, and was right. Did not build a forecast himself.",
     "Session transcript, Q2 forecast build"),
    (S_FORECAST, KWAME, SEASONAL, 148,
     "Applied the seasonal uplift to eleven clinics correctly using the "
     "documented method, with the method open in front of him throughout.",
     "Forecast workbook revision history"),
    (S_AUDIT, KWAME, DATA_QUALITY_CAP, 97,
     "Observed the full audit and asked twice what the 5% recount threshold "
     "protects against. Neither answer available to him was sufficient.",
     "Session transcript, Clinic 9 data quality audit"),
    (S_SUPPLIER, KOJO, DISRUPTION, 52,
     "Presented the lead-time drift as a supply-risk case rather than as a "
     "service complaint, and set a quarter-end review point.",
     "Central store meeting minutes"),
    (S_ROOTCAUSE, AMA, ROOT_CAUSE, 23,
     "Drafted her first independent root-cause write-up. Conclusion correct; "
     "the corrective action she proposed would not have changed a behaviour.",
     "Corrective action register, first draft retained"),
    (S_ROOTCAUSE, KWAME, CONSUMPTION, 23,
     "Reconstructed the site's consumption from card data when the monthly "
     "report was missing, and established the nineteen-day detection gap.",
     "Session transcript, Clinic 22 post-stockout review"),
    (S_ROOTCAUSE, AMA, INV_MONITOR, 23,
     "Proposed the stale-report flag threshold at fourteen days and justified "
     "it against the reporting cycle rather than by preference.",
     "Corrective action register"),
]
