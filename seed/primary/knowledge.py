"""The knowledge library: twenty entries, eighteen of them validated.

planv0.2.md section 4 B3 asks for "~18 validated knowledge items spanning all
7 knowledge types". The spread is the point rather than the count. A library
that is twenty formal documents is a filing cabinet and proves nothing; the
argument RELAY makes is that most of what an expert knows was never written
down, so the informal categories -- insight, heuristic, exception, lesson,
relationship -- have to carry real weight here, and they have to read as
though a practitioner said them out loud.

Two items are deliberately left unvalidated. Everything validated carries a
person who signed it off in the session record; a library where nothing is
ever still in the queue would quietly undercut the claim that validation is a
real step rather than a default.

`captured_on` is days-before-anchor (seed/timeline.py). The dates are uneven
because capture is uneven: three items came out of one afternoon early in the
assignment and then nothing for six weeks.
"""

from __future__ import annotations

from contracts.vocabulary import KnowledgeType

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
from seed.primary.sessions import S_AUDIT, S_FORECAST, S_ROOTCAUSE, S_SUPPLIER

_T = KnowledgeType

# (id, title, type, summary, body, area, capability, session, validated,
#  exposed, days_ago)
KNOWLEDGE = [
    {
        "id": "kn-replenishment-sop",
        "title": "Replenishment cycle: standard operating procedure",
        "type": _T.FORMAL_DOCUMENT,
        "summary": (
            "The written monthly cycle -- count, report, requisition, "
            "receipt, reconcile -- with the reorder point and the buffer "
            "rule as they currently stand."
        ),
        "body": {
            "scope": "All nineteen clinics and both district stores.",
            "sections": [
                "Physical count on the last working day of the month",
                "Report and requisition submitted by the 25th",
                "Reorder point: 14 days of cover on the 30-day average",
                "Buffer: 30 days, reviewed annually",
                "Receipt reconciliation within 48 hours of delivery",
            ],
            "known_limits": [
                "The reorder point assumes steady consumption. Nothing in the "
                "procedure tells the reader what to do when it is not.",
                "The 14-day point was set against a 14-day planning lead "
                "time. The lead time has moved; the point has not.",
            ],
            "status": "Version 3, issued this assignment. Supersedes the 2024 cycle note.",
        },
        "area_id": REPLENISHMENT,
        "capability_id": None,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, AMA, KOJO, EFUA],
        "days_ago": 243,
    },
    {
        "id": "kn-count-protocol",
        "title": "Physical count protocol and recount threshold",
        "type": _T.FORMAL_DOCUMENT,
        "summary": (
            "The count discipline Ama Boateng rewrote after the 2025 "
            "reconciliation, including the 5% recount threshold and the "
            "two-person rule."
        ),
        "body": {
            "scope": "Clinic dispensaries and both district stores.",
            "sections": [
                "Two-person count on tracer commodities; single count otherwise",
                "Card and shelf reconciled before the figure is entered",
                "Discrepancy above 5% triggers a recount before entry",
                "Recount result entered with a reason code, never overwritten",
            ],
            "authored_by": "Ama Boateng, with review by the expert.",
            "known_limits": [
                "The 5% is set at the Network's median clinic volume and is "
                "too loose at the four highest-volume sites.",
            ],
        },
        "area_id": DATA_QUALITY,
        "capability_id": DATA_QUALITY_CAP,
        "session_id": None,
        "validated": True,
        "exposed": [AMA, KWAME, KOJO],
        "days_ago": 243,
    },
    {
        "id": "kn-escalation-pathway",
        "title": "Stockout escalation pathway and approval matrix",
        "type": _T.FORMAL_DOCUMENT,
        "summary": (
            "Who is told what, and who can authorise what, when a tracer "
            "commodity goes below one week of cover."
        ),
        "body": {
            "scope": "Tracer commodities only.",
            "sections": [
                "Clinic notifies the regional supply coordinator same day",
                "Coordinator escalates to the DHMT if unresolved at 72 hours",
                "Emergency requisition requires Programme Director sign-off",
                "Inter-facility transfer: approval route to be confirmed",
            ],
            "known_limits": [
                "The inter-facility transfer route has never been written "
                "down. Nobody has needed it badly enough to find out, which "
                "is not the same as it being settled.",
            ],
            "status": "Draft. Two of four routes confirmed with the DHMT.",
        },
        "area_id": ESCALATION,
        "capability_id": None,
        "session_id": None,
        "validated": False,
        "exposed": [KWAME, EFUA],
        "days_ago": 61,
    },
    {
        "id": "kn-average-hides-acceleration",
        "title": "A thirty-day average hides the fortnight that matters",
        "type": _T.EXPERT_INSIGHT,
        "summary": (
            "Split any average consumption figure in half before trusting it. "
            "A quiet first fortnight will mask an acceleration in the second "
            "and hold the days-of-cover figure above the reorder point while "
            "the site is already at it."
        ),
        "body": {
            "practice": (
                "Never act on a 30-day ADC without splitting it 1-15 and "
                "16-30. If the second half is more than a quarter above the "
                "first, recompute cover on the second half and use that "
                "number, not the average."
            ),
            "why_it_is_not_written_down": (
                "The LMIS reports one ADC figure and the procedure names "
                "that figure. Splitting it is not forbidden; it simply never "
                "occurs to anyone the report has not prompted."
            ),
            "worked_example": (
                "A site reading eighteen days of cover on the month average "
                "reads fourteen point four on the second fortnight. The "
                "reorder point is fourteen. The difference between those two "
                "readings is the difference between acting this week and "
                "acting after the stockout."
            ),
            "learned_from": "Repeated across three seasons in two countries.",
        },
        "area_id": MONITORING,
        "capability_id": STOCKOUT_RISK,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, AMA],
        "days_ago": 209,
    },
    {
        "id": "kn-stale-not-wrong",
        "title": "A stale count is not a wrong count, and the distinction matters",
        "type": _T.EXPERT_INSIGHT,
        "summary": (
            "An old physical count is accurate as of its date and has drifted "
            "in one direction since. Treating it as wrong invites a guess; "
            "treating it as stale tells you exactly what to go and find out."
        ),
        "body": {
            "practice": (
                "Read the count date before the count. Multiply the days "
                "elapsed by the current daily consumption and hold that "
                "figure in mind as the size of what you do not know. If it is "
                "material, get a fresh count before doing anything else -- it "
                "is twenty minutes and everything downstream depends on it."
            ),
            "why_it_is_not_written_down": (
                "The extract prints stock on hand without prominence given to "
                "the count date, so the figure arrives looking current."
            ),
            "worked_example": (
                "A count six days old at twenty-eight units a day is a "
                "hundred and seventy units of unrecorded movement -- forty "
                "per cent of the balance on the sheet."
            ),
        },
        "area_id": MONITORING,
        "capability_id": INV_MONITOR,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, AMA, KOJO],
        "days_ago": 209,
    },
    {
        "id": "kn-threshold-calibration",
        "title": "Every threshold is calibrated to a site that not every site is",
        "type": _T.EXPERT_INSIGHT,
        "summary": (
            "A person who cannot say what a threshold protects against cannot "
            "tell when it is the wrong number. This applies to the recount "
            "threshold and to the reorder point equally."
        ),
        "body": {
            "practice": (
                "Before applying any threshold at an atypical site, state "
                "what it is protecting against and check the protection still "
                "holds at that volume and that lead time."
            ),
            "why_it_is_not_written_down": (
                "Thresholds are published as numbers. The trade-off behind "
                "each one lived in whoever set it."
            ),
            "applies_to": [
                "5% recount threshold -- set at median clinic volume",
                "14-day reorder point -- set against a 14-day lead time that "
                "no longer holds",
                "30-day buffer -- set before the road works",
            ],
            "origin": "Raised twice by a counterpart in one session, unanswerable from any document.",
        },
        "area_id": REPLENISHMENT,
        "capability_id": STOCKOUT_RISK,
        "session_id": S_AUDIT,
        "validated": True,
        "exposed": [KWAME, AMA, KOJO, EFUA],
        "days_ago": 97,
    },
    {
        "id": "kn-ordinary-months",
        "title": "A trend line is only honest if the months behind it were ordinary",
        "type": _T.EXPERT_INSIGHT,
        "summary": (
            "Establish what was happening at a site during the history being "
            "extrapolated from -- closures, campaigns, staffing gaps -- "
            "before drawing any trend."
        ),
        "body": {
            "practice": (
                "Open the outreach calendar and the closure log alongside the "
                "issue data. Any month containing a disruption is excluded or "
                "adjusted, and the adjustment is written down so the next "
                "person can see it was deliberate."
            ),
            "why_it_is_not_written_down": (
                "The forecasting workbook takes twelve months of issues and "
                "draws the line. It has no field for 'the clinic was shut'."
            ),
            "worked_example": (
                "Three of nineteen clinic forecasts in one quarter were built "
                "through a disrupted period. All three were the quarter's "
                "largest variances."
            ),
        },
        "area_id": FORECASTING,
        "capability_id": FORECAST,
        "session_id": S_FORECAST,
        "validated": True,
        "exposed": [KWAME, KOJO],
        "days_ago": 148,
    },
    {
        "id": "kn-case-clinic22",
        "title": "Clinic 22: a stockout nobody noticed for nineteen days",
        "type": _T.CASE,
        "summary": (
            "The proximate cause was a missed reporting cycle during a "
            "staffing gap. The real failure was that nothing in the system "
            "noticed the cycle had been missed."
        ),
        "body": {
            "what_happened": (
                "A dispensary lead went on compassionate leave; the locum was "
                "not briefed on the reporting cycle. The site's monthly "
                "report was not submitted. Replenishment was calculated from "
                "the previous month's figure and under-supplied. The site ran "
                "out of two tracer commodities."
            ),
            "first_theory": "Supply failure at the central store.",
            "why_it_was_wrong": (
                "The receipt log showed everything ordered had arrived, "
                "roughly on time. Once that is true it is a demand-signal "
                "problem, not a supply problem."
            ),
            "root_cause": (
                "No detection mechanism for a missing report. Nineteen days "
                "elapsed before anyone noticed the site had gone quiet."
            ),
            "corrective_action": (
                "Stale-report flag at fourteen days, owner named, review date "
                "set. Not 'brief locums on reporting', which records a fact "
                "and changes nothing."
            ),
            "cost": "Eleven days of stockout on two tracer commodities.",
        },
        "area_id": GOVERNANCE,
        "capability_id": ROOT_CAUSE,
        "session_id": S_ROOTCAUSE,
        "validated": True,
        "exposed": [KWAME, AMA, EFUA],
        "days_ago": 23,
    },
    {
        "id": "kn-case-leadtime",
        "title": "Central store lead-time negotiation: nine months of evidence",
        "type": _T.CASE,
        "summary": (
            "How the planning lead time was moved from fourteen to eighteen "
            "days, and why opening on the pattern rather than the grievance "
            "was the whole meeting."
        ),
        "body": {
            "what_happened": (
                "Two consecutive late deliveries prompted a review. Rather "
                "than raising the two failures, the logistics officer "
                "presented nine months of receipt data showing a consistent "
                "drift."
            ),
            "the_turn": (
                "The store supervisor disputed two entries. Both were checked "
                "on the spot; one was the officer's own error and he conceded "
                "it immediately. The supervisor spent the rest of the meeting "
                "checking the arithmetic with him rather than defending the "
                "store."
            ),
            "outcome": (
                "Planning assumption moved to eighteen days with a "
                "quarter-end review. The buffer was resized accordingly."
            ),
            "what_was_missed": (
                "No groundwork with the regional pharmacist beforehand. The "
                "meeting succeeded anyway; it did not have to."
            ),
        },
        "area_id": SUPPLIERS,
        "capability_id": LEAD_TIME,
        "session_id": S_SUPPLIER,
        "validated": True,
        "exposed": [KOJO, KWAME],
        "days_ago": 52,
    },
    {
        "id": "kn-case-clinic9-audit",
        "title": "Clinic 9: usable with a correction, not unusable",
        "type": _T.CASE,
        "summary": (
            "A 9% count discrepancy traced to a single locum-covered week, "
            "and the judgement call about whether the rest of the record "
            "could still be believed."
        ),
        "body": {
            "what_happened": (
                "An unannounced audit found a 9% card-to-shelf discrepancy on "
                "two commodities, well above the recount threshold."
            ),
            "the_judgement": (
                "The discrepancy was isolated to one week covered by a locum. "
                "Everything either side reconciled. The record was therefore "
                "declared usable with a correction rather than condemned "
                "wholesale."
            ),
            "how_it_was_delivered": (
                "The correction was explained to the dispensary lead as a "
                "gap in cover rather than as a failure of his. Leading with "
                "the discrepancy would have ended the conversation."
            ),
            "transferable_point": (
                "Set the acceptance criteria before opening the records. If "
                "you look first you will find a reason for whatever you "
                "already suspect."
            ),
        },
        "area_id": DATA_QUALITY,
        "capability_id": DATA_QUALITY_CAP,
        "session_id": S_AUDIT,
        "validated": True,
        "exposed": [AMA, KWAME],
        "days_ago": 97,
    },
    {
        "id": "kn-heuristic-second-signal",
        "title": "Two consecutive cycles in the same direction is a pattern",
        "type": _T.HEURISTIC,
        "summary": (
            "One unusual reading is noise; two in the same direction is "
            "information worth acting on, and three is a report written after "
            "the fact."
        ),
        "body": {
            "rule": (
                "When a second consecutive cycle moves the same way -- "
                "consumption up, lead time out, reporting late -- treat it as "
                "a signal and say explicitly that it is the second."
            ),
            "caveat": (
                "This is a prompt to look, not a trigger to act. The judgement "
                "about whether the second point is signal or coincidence "
                "cannot be reduced to a counting rule, and a version of this "
                "written as a rule was rejected at validation for exactly "
                "that reason."
            ),
            "applies_to": [
                "Supplier lead time",
                "Clinic consumption trend",
                "Late or missing monthly reports",
            ],
        },
        "area_id": ESCALATION,
        "capability_id": DISRUPTION,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, KOJO],
        "days_ago": 131,
    },
    {
        "id": "kn-heuristic-surplus-tests",
        "title": "Four tests that separate 'has stock' from 'has surplus'",
        "type": _T.HEURISTIC,
        "summary": (
            "Before moving a single pack out of a site, check consumption "
            "trend, expiry, transport and approval route -- in that order."
        ),
        "body": {
            "rule": (
                "1. Consumption trend, not stock level. A site with four "
                "months of cover and a rising ADC has no surplus. "
                "2. Expiry and batch. Moving short-dated stock to a "
                "lower-volume site is choosing where it gets written off. "
                "3. Road and transport. If the catchment is flooding, the "
                "reason the receiving site needs it is the reason the truck "
                "cannot reach it. "
                "4. Approval route, established before the day you need it."
            ),
            "why_it_matters": (
                "An emergency requisition costs a freight premium, "
                "credibility with the supplier for the next genuine urgency, "
                "and about two weeks of somebody's attention. A "
                "redistribution costs a driver and a form."
            ),
            "cold_chain_note": (
                "Cold chain is a fifth test wherever it applies. It does not "
                "apply to the oral tracer commodities, which is luck rather "
                "than design."
            ),
        },
        "area_id": REDISTRIBUTION,
        "capability_id": REDISTRIBUTE,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME],
        "days_ago": 174,
    },
    {
        "id": "kn-heuristic-quiet-site",
        "title": "A site that has gone quiet is a site in trouble",
        "type": _T.HEURISTIC,
        "summary": (
            "Absence of a signal reads as 'no news' and is almost always the "
            "opposite. Check the sites that have not reported before checking "
            "the ones that have."
        ),
        "body": {
            "rule": (
                "Start the monthly review with the exception list -- who has "
                "not submitted, whose count date is oldest, whose figures are "
                "identical to last month. Only then read the reports that "
                "arrived."
            ),
            "why_it_is_not_obvious": (
                "Every report on the desk demands attention. The site that "
                "sent nothing demands none, which is precisely the problem."
            ),
            "signals": [
                "No monthly report submitted",
                "A stock figure identical to the previous month",
                "A physical count date more than six weeks old",
            ],
        },
        "area_id": REPORTING,
        "capability_id": CONSUMPTION,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, AMA, KOJO],
        "days_ago": 174,
    },
    {
        "id": "kn-exception-seasonal-start",
        "title": "The first week of the rains is not the peak, it is the start of the curve",
        "type": _T.EXCEPTION,
        "summary": (
            "During seasonal onset the current consumption rate is a floor, "
            "not a ceiling, and days-of-cover arithmetic based on it "
            "overstates the position at every site in a low-lying catchment."
        ),
        "body": {
            "normal_rule": (
                "Days of cover equals stock on hand divided by average daily "
                "consumption."
            ),
            "the_exception": (
                "From the onset of the rains until the seasonal peak, the "
                "denominator is rising week on week. The cover figure is "
                "therefore an overstatement that grows worse the longer you "
                "rely on it."
            ),
            "how_to_recognise": [
                "Rains have begun in the catchment within the last fortnight",
                "Low-lying or flood-prone site",
                "Prior-year consumption for the same commodity rose steeply "
                "from the same point in the season",
            ],
            "what_to_do": (
                "Recompute cover against the prior-year seasonal peak rate "
                "rather than the current rate, and bring the reorder decision "
                "forward accordingly."
            ),
            "magnitude": (
                "At the flood-prone sites, prior-year consumption of the oral "
                "tracer more than doubled between the first week of the rains "
                "and the peak."
            ),
        },
        "area_id": FORECASTING,
        "capability_id": SEASONAL,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, KOJO],
        "days_ago": 118,
    },
    {
        "id": "kn-exception-campaign-months",
        "title": "Outreach campaign months must be excluded from the trend, not smoothed",
        "type": _T.EXCEPTION,
        "summary": (
            "A campaign inflates issues without changing underlying demand. "
            "Averaging it in raises the baseline permanently; excluding it "
            "keeps the trend honest."
        ),
        "body": {
            "normal_rule": "Build the forecast from twelve months of issue data.",
            "the_exception": (
                "Months containing an outreach campaign, a mass screening or "
                "a school programme are excluded from the trend entirely and "
                "the campaign volume is added back as a separate line."
            ),
            "why_smoothing_fails": (
                "Smoothing spreads the campaign across the year, which raises "
                "every month's baseline by a little and is wrong in both "
                "directions -- too high in ordinary months, too low in the "
                "campaign month."
            ),
            "how_to_recognise": [
                "A single month two or more times the neighbouring months",
                "A date that appears in the outreach calendar",
            ],
        },
        "area_id": FORECASTING,
        "capability_id": FORECAST,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, KOJO],
        "days_ago": 148,
    },
    {
        "id": "kn-lesson-corrective-actions",
        "title": "A corrective action that records a fact changes nothing",
        "type": _T.LESSON_LEARNED,
        "summary": (
            "Most corrective actions in the register restate what went wrong. "
            "A useful one names a behaviour, an owner and a date."
        ),
        "body": {
            "what_we_learned": (
                "Reviewing eleven closed corrective actions from the previous "
                "two years, eight were statements of fact -- 'the report was "
                "not submitted', 'stock was not counted'. None of the eight "
                "would have prevented a recurrence and three of them had "
                "recurred."
            ),
            "what_changed": (
                "Corrective actions are now rejected at the quarterly review "
                "unless they name a behaviour that will be different, a "
                "person accountable for it, and a date it will be checked."
            ),
            "cost_of_learning_it": "Two repeat stockouts at the same site.",
        },
        "area_id": GOVERNANCE,
        "capability_id": ROOT_CAUSE,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, AMA, EFUA],
        "days_ago": 84,
    },
    {
        "id": "kn-lesson-audit-tone",
        "title": "An audit that is received as a sanction stops producing data",
        "type": _T.LESSON_LEARNED,
        "summary": (
            "The first round of unannounced audits improved accuracy for one "
            "cycle and then made it worse, because sites began preparing for "
            "the audit rather than keeping the cards."
        ),
        "body": {
            "what_we_learned": (
                "Accuracy improved sharply in the first cycle after audits "
                "began and then degraded below the pre-audit baseline by the "
                "third. Sites had learned to reconcile cards in advance of a "
                "visit rather than continuously."
            ),
            "what_changed": (
                "Audit findings are delivered to the dispensary lead as a "
                "correction to be made together, never as a score. Repeat "
                "discrepancies are treated as a supervision question rather "
                "than a compliance one."
            ),
            "residual_risk": (
                "This depends heavily on who delivers the finding. It is a "
                "relationship, not a procedure."
            ),
        },
        "area_id": DATA_QUALITY,
        "capability_id": DATA_QUALITY_CAP,
        "session_id": None,
        "validated": True,
        "exposed": [AMA, KWAME],
        "days_ago": 231,
    },
    {
        "id": "kn-lesson-buffer-review",
        "title": "An annually reviewed buffer against a moving lead time is a fiction",
        "type": _T.LESSON_LEARNED,
        "summary": (
            "The 30-day buffer was set against a 14-day lead time and "
            "reviewed once a year. The lead time moved four days inside two "
            "quarters and nothing noticed."
        ),
        "body": {
            "what_we_learned": (
                "Buffer adequacy is a function of lead-time variability, not "
                "of a calendar. Reviewing it annually guarantees that it is "
                "correct on one day a year."
            ),
            "what_changed": (
                "Buffer is now reviewed whenever the rolling lead-time "
                "average moves by more than two days, which in practice means "
                "quarterly."
            ),
            "open_question": (
                "Nobody has yet decided who owns triggering that review after "
                "the assignment ends."
            ),
        },
        "area_id": SUPPLIERS,
        "capability_id": LEAD_TIME,
        "session_id": None,
        "validated": False,
        "exposed": [KOJO, EFUA],
        "days_ago": 38,
    },
    {
        "id": "kn-relationship-cms-desk",
        "title": "The central store desk: how urgency is spent",
        "type": _T.RELATIONSHIP,
        "summary": (
            "The supply desk supervisor responds to evidence and to "
            "consistency, and remembers every time he was told something was "
            "urgent and it was not."
        ),
        "body": {
            "who": "Supply desk supervisor, central medical store.",
            "what_works": [
                "Arriving with months of data rather than the most recent "
                "failure",
                "Conceding an error of your own immediately and in front of "
                "him",
                "Asking for a number he can defend upward to his own "
                "management, not the number you are entitled to",
            ],
            "what_does_not": [
                "Escalating over his head without telling him first",
                "Calling something urgent more than about twice a quarter",
            ],
            "current_state": (
                "Relationship is good and rests on the logistics officer "
                "rather than on the Network. A successor would be starting "
                "from the beginning."
            ),
            "at_risk": True,
        },
        "area_id": SUPPLIERS,
        "capability_id": LEAD_TIME,
        "session_id": None,
        "validated": True,
        "exposed": [KOJO],
        "days_ago": 155,
    },
    {
        "id": "kn-relationship-dhmt",
        "title": "The district health team: escalating without spending goodwill",
        "type": _T.RELATIONSHIP,
        "summary": (
            "The district team will move quickly on a request that arrives "
            "already thought through, and slowly on one that arrives as a "
            "complaint about somebody else."
        ),
        "body": {
            "who": (
                "District health management team -- the pharmacist and the "
                "planning officer in practice, whatever the org chart says."
            ),
            "what_works": [
                "Sounding a position out informally before it is filed",
                "Bringing the district the decision rather than the problem",
                "Giving them something to say to the region",
            ],
            "what_does_not": [
                "A written escalation the pharmacist has not seen first",
                "Asking for an exception without saying what the rule cost",
            ],
            "current_state": (
                "Held almost entirely by the departing expert. The "
                "introduction to the regional pharmacist has been made but "
                "the working relationship has not transferred."
            ),
            "at_risk": True,
        },
        "area_id": ESCALATION,
        "capability_id": DISRUPTION,
        "session_id": None,
        "validated": True,
        "exposed": [KWAME, KOJO, EFUA],
        "days_ago": 96,
    },
]

# Every item is attributable to the departing expert: the library exists to
# record what leaves with her.
EXPERT_ID = MITCHELL
