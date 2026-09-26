"""The ten capabilities, who stands where on each, and how they got there.

RELAY.txt ("DEMO CAPABILITIES") fixes the ten. What is tuned here is the
*level matrix*, because planv0.2.md section 4 B3 makes three of the readiness
figures an acceptance criterion rather than an outcome:

    capability localization   7 of 10 critical capabilities have a local
                              person at level 4 or above          -> 70%
    locally teachable         4 capabilities have a local person at level 6
    expert dependent          3 capabilities where Mitchell is capable and
                              nobody local is

The three that are not localized are Stockout Risk Identification, Emergency
Stock Redistribution and Supply Disruption Response -- deliberately, because
the flagship session is about the first of them. Kwame sits at 3 on Stockout
Risk Identification, so approving the session's capability finding moves him
to 4, localization goes to 8/10, and operating-model readiness moves 68% ->
71% while the audience is watching (RELAY.txt, success flow steps 11 and 14).
If the seed put him at 4 already there would be nothing to show.

**Levels are inserted, never updated.** schema.py's trigger refuses a level
change that does not cite an approved validation, which is the entire point of
it. Four rows are seeded at their *previous* level and then moved by
`app.db.writes.apply_validation` from a real historical finding -- see
sessions.py -- so those four carry a genuine evidence chain rather than a
number somebody typed.

`exposure_count` is seeded above the number of evidence records on purpose.
Most exposures never get written up; a passport claiming that every single
time a person touched a task produced a paragraph would be the least credible
thing on the screen.
"""

from __future__ import annotations

from seed.primary.areas import (
    DATA_QUALITY,
    ESCALATION,
    FORECASTING,
    GOVERNANCE,
    MONITORING,
    REDISTRIBUTION,
    REPLENISHMENT,
    REPORTING,
    SUPPLIERS,
)
from seed.primary.people import AMA, EFUA, KOJO, KWAME, MITCHELL

INV_MONITOR = "cap-inventory-monitoring"
STOCKOUT_RISK = "cap-stockout-risk"
FORECAST = "cap-demand-forecasting"
REDISTRIBUTE = "cap-emergency-redistribution"
LEAD_TIME = "cap-supplier-lead-time"
DATA_QUALITY_CAP = "cap-inventory-data-quality"
CONSUMPTION = "cap-clinic-consumption"
SEASONAL = "cap-seasonal-demand"
DISRUPTION = "cap-supply-disruption"
ROOT_CAUSE = "cap-stockout-root-cause"


CAPABILITIES = [
    {
        "id": INV_MONITOR,
        "name": "Routine Inventory Monitoring",
        "description": (
            "Maintaining an accurate weekly picture of stock position and "
            "movement across nineteen clinics, and knowing which parts of "
            "that picture to trust."
        ),
        "criticality": 5,
        "area_id": MONITORING,
    },
    {
        "id": STOCKOUT_RISK,
        "name": "Stockout Risk Identification",
        "description": (
            "Determining whether a site is genuinely at risk, using the "
            "reorder threshold as one input alongside consumption "
            "trajectory, count freshness, season and supplier lead time."
        ),
        "criticality": 5,
        "area_id": REPLENISHMENT,
    },
    {
        "id": FORECAST,
        "name": "Demand Forecasting",
        "description": (
            "Building a quarterly commodity forecast from consumption history "
            "and reconciling it against what actually happened."
        ),
        "criticality": 4,
        "area_id": FORECASTING,
    },
    {
        "id": REDISTRIBUTE,
        "name": "Emergency Stock Redistribution",
        "description": (
            "Evaluating and executing a transfer between clinics: identifying "
            "genuine surplus, testing expiry and transport risk, obtaining "
            "approval and recording the movement at both ends."
        ),
        "criticality": 5,
        "area_id": REDISTRIBUTION,
    },
    {
        "id": LEAD_TIME,
        "name": "Supplier Lead-Time Assessment",
        "description": (
            "Reading supplier performance from the receipt log and converting "
            "it into a planning assumption that can be defended."
        ),
        "criticality": 4,
        "area_id": SUPPLIERS,
    },
    {
        "id": DATA_QUALITY_CAP,
        "name": "Inventory Data Quality Assessment",
        "description": (
            "Judging whether a reported figure is fit to act on, and knowing "
            "what to do when it is not."
        ),
        "criticality": 4,
        "area_id": DATA_QUALITY,
    },
    {
        "id": CONSUMPTION,
        "name": "Clinic Consumption Analysis",
        "description": (
            "Interpreting a clinic's consumption pattern -- its shape, not "
            "just its average -- and explaining what changed."
        ),
        "criticality": 4,
        "area_id": REPORTING,
    },
    {
        "id": SEASONAL,
        "name": "Seasonal Demand Planning",
        "description": (
            "Anticipating the seasonal shape of demand and adjusting stock "
            "positions before the curve rather than during it."
        ),
        "criticality": 4,
        "area_id": FORECASTING,
    },
    {
        "id": DISRUPTION,
        "name": "Supply Disruption Response",
        "description": (
            "Acting when supply fails: triage, escalation, substitution and "
            "keeping clinics informed while it is unresolved."
        ),
        "criticality": 5,
        "area_id": ESCALATION,
    },
    {
        "id": ROOT_CAUSE,
        "name": "Root Cause Analysis of Stockouts",
        "description": (
            "Establishing why a stockout happened, distinguishing cause from "
            "coincidence, and turning it into a corrective action that "
            "changes behaviour."
        ),
        "criticality": 4,
        "area_id": GOVERNANCE,
    },
]


# ---------------------------------------------------------------------------
# Who stands where
# ---------------------------------------------------------------------------
# (person, capability, level, exposure_count_at_seed, last_demonstrated_days_ago)
#
# `level` is the CURRENT level except for the four rows listed in PROMOTIONS,
# which are seeded one step lower and moved by an approved validation.
# `last_demonstrated` is None where a person has been exposed but has not yet
# done the work themselves.

LEVELS: list[tuple[str, str, int, int, int | None]] = [
    # -- Dr. Mitchell: the reason the three at-risk capabilities are at risk --
    (MITCHELL, INV_MONITOR, 6, 41, 3),
    (MITCHELL, STOCKOUT_RISK, 6, 63, 2),
    (MITCHELL, FORECAST, 6, 22, 11),
    (MITCHELL, REDISTRIBUTE, 6, 17, 34),
    (MITCHELL, LEAD_TIME, 6, 19, 16),
    (MITCHELL, DATA_QUALITY_CAP, 5, 28, 9),
    (MITCHELL, CONSUMPTION, 5, 31, 6),
    (MITCHELL, SEASONAL, 6, 14, 26),
    (MITCHELL, DISRUPTION, 6, 25, 47),
    (MITCHELL, ROOT_CAUSE, 6, 20, 23),

    # -- Kwame Mensah: the primary counterpart -------------------------------
    (KWAME, INV_MONITOR, 6, 58, 4),
    (KWAME, STOCKOUT_RISK, 3, 17, 12),
    (KWAME, FORECAST, 3, 21, 148),  # -> 4 at the Q2 forecast review
    (KWAME, REDISTRIBUTE, 2, 4, 34),
    (KWAME, LEAD_TIME, 4, 15, 16),
    (KWAME, DATA_QUALITY_CAP, 3, 12, 31),
    (KWAME, CONSUMPTION, 4, 26, 8),
    (KWAME, SEASONAL, 3, 9, 26),
    (KWAME, DISRUPTION, 2, 6, 47),
    (KWAME, ROOT_CAUSE, 5, 18, 23),  # -> 6 at the Clinic 22 post-stockout review

    # -- Ama Boateng: strongest on the reporting and data-quality side -------
    (AMA, INV_MONITOR, 5, 34, 5),
    (AMA, STOCKOUT_RISK, 2, 6, 44),
    (AMA, FORECAST, 2, 5, 97),
    (AMA, REDISTRIBUTE, 1, 2, None),
    (AMA, LEAD_TIME, 1, 1, None),
    (AMA, DATA_QUALITY_CAP, 5, 44, 97),  # -> 6 at the Clinic 9 data audit
    (AMA, CONSUMPTION, 6, 37, 7),
    (AMA, SEASONAL, 3, 8, 26),
    (AMA, DISRUPTION, 1, 3, None),
    (AMA, ROOT_CAUSE, 3, 11, 23),

    # -- Kojo Asare: eleven months in, strongest on the supplier side --------
    (KOJO, INV_MONITOR, 4, 23, 5),
    (KOJO, STOCKOUT_RISK, 2, 7, 44),
    (KOJO, FORECAST, 3, 10, 148),
    (KOJO, REDISTRIBUTE, 3, 8, 34),
    (KOJO, LEAD_TIME, 4, 29, 52),  # -> 5 at the supplier lead-time review
    (KOJO, DATA_QUALITY_CAP, 4, 16, 19),
    (KOJO, CONSUMPTION, 3, 13, 29),
    (KOJO, SEASONAL, 4, 12, 26),
    (KOJO, DISRUPTION, 3, 9, 47),
    (KOJO, ROOT_CAUSE, 3, 7, 23),

    # -- Efua Darko: accountable for all of it, hands-on with little of it ---
    (EFUA, INV_MONITOR, 2, 6, 33),
    (EFUA, FORECAST, 3, 9, 148),
    (EFUA, DATA_QUALITY_CAP, 2, 4, 97),
    (EFUA, ROOT_CAUSE, 3, 13, 23),
]


def pc_id(person_id: str, capability_id: str) -> str:
    """Deterministic person_capability id, so evidence can name one by hand."""
    return f"pc-{person_id.removeprefix('p-')}-{capability_id.removeprefix('cap-')}"


# The four rows seeded one level low, to be moved by an approved validation
# in sessions.py. Keyed by (person, capability) -> level to seed at.
PROMOTIONS: dict[tuple[str, str], int] = {
    (KWAME, FORECAST): 3,
    (AMA, DATA_QUALITY_CAP): 5,
    (KOJO, LEAD_TIME): 4,
    (KWAME, ROOT_CAUSE): 5,
}


# ---------------------------------------------------------------------------
# Standing evidence
# ---------------------------------------------------------------------------
# Observations that did not come out of a transfer session: supervision
# visits, audits, the ordinary record of somebody doing the job. Session-
# derived evidence lives in sessions.py, where the finding that produced it
# is.
#
# (person, capability, days_ago, summary, source)
#
# Dates are irregular on purpose, and the intervals are uneven: a real history
# clusters around field visits and quarter ends, it does not tick.

EVIDENCE: list[tuple[str, str, int, str, str]] = [
    # -- Kwame ---------------------------------------------------------------
    (KWAME, INV_MONITOR, 214,
     "Rebuilt the weekly watchlist after the extract format changed at the "
     "central store; did it unprompted and without losing a week of history.",
     "Supervision note, regional supply office"),
    (KWAME, INV_MONITOR, 96,
     "Spotted that three clinics had identical stock-on-hand figures for two "
     "consecutive weeks and treated it as a reporting fault rather than a "
     "quiet month. He was right.",
     "Weekly extract review, annotated"),
    (KWAME, INV_MONITOR, 4,
     "Ran the full weekly review and briefed the district store without "
     "reference to the specialist.",
     "Weekly extract review"),
    (KWAME, STOCKOUT_RISK, 121,
     "Identified the Clinic 7 exposure correctly but only after it crossed "
     "the 14-day threshold. Applied the rule rather than anticipating it.",
     "Field visit debrief"),
    (KWAME, STOCKOUT_RISK, 66,
     "Raised an off-cycle requisition for Clinic 3 on the specialist's "
     "prompting. Reasoning was sound once stated; he did not initiate it.",
     "Replenishment review, supervised"),
    (KWAME, STOCKOUT_RISK, 12,
     "Asked, without prompting, whether the reorder threshold should be "
     "different for the sites that flood. Question was better than the "
     "answer he had for it.",
     "Monthly supply meeting, minuted"),
    (KWAME, LEAD_TIME, 88,
     "Used Kojo's lead-time log as a planning input for the first time "
     "instead of the standing 14-day assumption.",
     "Requisition workings, Q3 cycle"),
    (KWAME, LEAD_TIME, 16,
     "Sized a buffer against the current rolling lead time and explained the "
     "arithmetic to the Programme Director unaided.",
     "Quarterly review, observed"),
    (KWAME, CONSUMPTION, 133,
     "Reconciled Clinic 11's consumption against the outreach campaign "
     "calendar and explained a spike that had been recorded as a data error.",
     "Variance note, Q2"),
    (KWAME, CONSUMPTION, 8,
     "Produced the consumption shape for four sites by hand when the extract "
     "failed, and got the same answers as the workbook.",
     "Ad hoc analysis, shared drive"),
    (KWAME, DATA_QUALITY_CAP, 31,
     "Acted on a stale-count flag correctly but did not question whether the "
     "flag threshold itself was right for a high-volume site.",
     "Data quality audit, observed"),
    (KWAME, SEASONAL, 26,
     "Sat in on the seasonal adjustment for the malaria commodities. Followed "
     "the method; has not yet derived an uplift himself.",
     "Forecast working session"),
    (KWAME, REDISTRIBUTE, 34,
     "Observed the Clinic 6 transfer end to end. Asked good questions about "
     "the approval path; did not make any of the calls.",
     "Transfer observation note"),
    (KWAME, DISRUPTION, 47,
     "Present for the central store allocation shortfall. Handled clinic "
     "communication; the triage decisions were the specialist's.",
     "Incident log, allocation shortfall"),
    (KWAME, FORECAST, 197,
     "First full forecast cycle worked through with the specialist. Arithmetic "
     "correct, judgement calls deferred.",
     "Forecast working session"),
    (KWAME, FORECAST, 163,
     "Built the Q2 forecast for eight of nineteen clinics independently; the "
     "remaining eleven were reviewed line by line.",
     "Forecast workbook v4, revision history"),
    (KWAME, ROOT_CAUSE, 176,
     "Traced the Clinic 15 ACT stockout to a reporting gap rather than to "
     "supply, against the room's initial assumption.",
     "Quarterly review minutes"),
    (KWAME, ROOT_CAUSE, 109,
     "Wrote the corrective action for the Clinic 15 finding and followed it to "
     "closure two quarters later.",
     "Corrective action register"),
    (KWAME, ROOT_CAUSE, 54,
     "Coached Ama through her first root-cause write-up rather than doing it "
     "for her.",
     "Peer observation, Clinic Operations Officer"),

    # -- Ama -----------------------------------------------------------------
    (AMA, INV_MONITOR, 188,
     "Rewrote the physical count protocol after the reconciliation and "
     "trained four dispensary leads on it herself.",
     "Count protocol, revision note"),
    (AMA, INV_MONITOR, 5,
     "Ran the monthly count reconciliation across all nineteen sites and "
     "cleared every discrepancy before the R&R deadline.",
     "Reconciliation sheet, current cycle"),
    (AMA, DATA_QUALITY_CAP, 231,
     "Identified that two clinics were copying stock cards forward and "
     "escalated it with the evidence attached rather than as a suspicion.",
     "Audit finding, Q1"),
    (AMA, DATA_QUALITY_CAP, 152,
     "Designed the unannounced rotating audit and set the sampling herself.",
     "Audit programme design note"),
    (AMA, DATA_QUALITY_CAP, 118,
     "Suspended automatic reordering for a site whose data she judged "
     "unusable, and handled the clinic conversation without it being read as "
     "a sanction.",
     "Data quality decision log"),
    (AMA, CONSUMPTION, 205,
     "Explained the harmattan respiratory pattern to the district store using "
     "three years of issue data.",
     "District store briefing"),
    (AMA, CONSUMPTION, 141,
     "Separated a genuine consumption rise at Clinic 2 from a stock card "
     "arithmetic error that had inflated it.",
     "Variance note, Q2"),
    (AMA, CONSUMPTION, 73,
     "Taught the consumption-shape method to two dispensary leads; both now "
     "flag their own anomalies before the district does.",
     "Training record"),
    (AMA, CONSUMPTION, 7,
     "Current cycle's consumption review completed and circulated unaided.",
     "Monthly consumption review"),
    (AMA, STOCKOUT_RISK, 44,
     "Escalated a Clinic 18 exposure correctly, on the threshold rule alone.",
     "Escalation log"),
    (AMA, SEASONAL, 26,
     "Attended the seasonal adjustment session and supplied the outreach "
     "calendar that changed two clinics' uplift.",
     "Forecast working session"),
    (AMA, ROOT_CAUSE, 23,
     "Wrote her first independent root-cause note for the Clinic 22 "
     "shortage; conclusion was right, the corrective action was thin.",
     "Quarterly review pack"),

    # -- Kojo ----------------------------------------------------------------
    (KOJO, LEAD_TIME, 236,
     "Started the supplier lead-time log in his first month, before anyone "
     "asked for one.",
     "Lead-time log, first entry"),
    (KOJO, LEAD_TIME, 194,
     "Converted eleven weeks of receipt data into a defensible planning "
     "assumption and got it adopted at the quarterly review.",
     "Quarterly review minutes"),
    (KOJO, LEAD_TIME, 84,
     "Detected the lead-time drift at the central store two orders before it "
     "would have shown in the quarterly average.",
     "Lead-time log, annotated"),
    (KOJO, INV_MONITOR, 166,
     "Took over the weekly extract during the specialist's leave and kept the "
     "watchlist current for three weeks.",
     "Cover arrangement, supervision note"),
    (KOJO, INV_MONITOR, 5,
     "Weekly review completed jointly with Kwame; independent on the "
     "arithmetic, still checks his exposure ranking with someone.",
     "Weekly extract review"),
    (KOJO, DATA_QUALITY_CAP, 129,
     "Cross-checked goods received notes against LMIS entries and found a "
     "systematic keying error worth six weeks of phantom stock.",
     "Reconciliation finding"),
    (KOJO, DATA_QUALITY_CAP, 19,
     "Applied the stale-count rule to the receipt side as well as the issue "
     "side, which nobody had thought to do.",
     "Data quality audit"),
    (KOJO, REDISTRIBUTE, 102,
     "Arranged transport and paperwork for the Clinic 6 transfer competently. "
     "The decision to transfer was not his.",
     "Transfer note, Clinic 6"),
    (KOJO, REDISTRIBUTE, 34,
     "Asked the right question about expiry on the second transfer, without "
     "being able to say what he would have done with the answer.",
     "Transfer observation note"),
    (KOJO, SEASONAL, 138,
     "Built the seasonal buffer sizing into the reorder calculator so the "
     "uplift survives contact with the order quantity.",
     "Forecast workbook v4, revision history"),
    (KOJO, SEASONAL, 26,
     "Derived the malaria uplift for six clinics independently; the "
     "specialist reviewed and changed none of them.",
     "Forecast working session"),
    (KOJO, DISRUPTION, 111,
     "Managed the transport contractor failure over a weekend and kept eight "
     "clinics supplied. Did not escalate, and probably should have.",
     "Incident log, transport failure"),
    (KOJO, DISRUPTION, 47,
     "Handled supplier-side triage during the allocation shortfall with the "
     "specialist directing.",
     "Incident log, allocation shortfall"),
    (KOJO, FORECAST, 148,
     "Supplied lead-time constraints into the Q2 forecast and challenged one "
     "clinic's trend line successfully.",
     "Forecast working session"),
    (KOJO, CONSUMPTION, 29,
     "Read a consumption shape correctly for the first time without being "
     "walked through it.",
     "Monthly consumption review"),
    (KOJO, STOCKOUT_RISK, 44,
     "Flagged a Clinic 18 exposure from the watchlist. Threshold rule "
     "applied correctly; no contextual reasoning offered.",
     "Escalation log"),
    (KOJO, ROOT_CAUSE, 23,
     "Contributed the supplier timeline to the Clinic 22 root-cause review.",
     "Quarterly review pack"),
]
