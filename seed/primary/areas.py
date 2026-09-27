"""The nine operating-model areas, and the 47 things that must transfer.

RELAY.txt ("DEMO OPERATING MODEL") names the nine areas and requires each one
to carry process, owner, roles, decision rights, systems, metrics, formal and
informal knowledge, required capabilities and transfer status. Schema.py
collapses those into the eight JSON dimension columns plus `transfer_
requirements`, so that is the shape used here. Every area fills all eight.

Two things about this file are load-bearing for the numbers on screen.

**`formal_pct` is a composition, not a completion.** schema.py says so in as
many words -- "informal is 100 - this" -- so it reads as *how much of this
area can be written down at all*. Emergency redistribution is 35 because most
of it is judgement; clinic reporting is 82 because most of it is a form.
Completion is counted from `transfer_requirements`, which is what the
readiness engine actually reads.

**Three areas deliberately have no local owner.** Replenishment, emergency
redistribution and stockout escalation still run through the departing
expert, which is the honest version of this engagement and is what makes
`local_ownership` come out at 6/9 rather than a flattering 9/9. RELAY.txt's
own worked example shows emergency redistribution as "Not Confirmed"; the
other two are the areas the flagship session is about.
"""

from __future__ import annotations

from contracts.vocabulary import RequirementKind, TransferState

from seed.primary.people import AMA, EFUA, KOJO, KWAME

FORECASTING = "area-forecasting"
MONITORING = "area-monitoring"
REPLENISHMENT = "area-replenishment"
REDISTRIBUTION = "area-redistribution"
SUPPLIERS = "area-suppliers"
REPORTING = "area-reporting"
DATA_QUALITY = "area-data-quality"
ESCALATION = "area-escalation"
GOVERNANCE = "area-governance"


AREAS = [
    {
        "id": FORECASTING,
        "name": "Demand Forecasting",
        "summary": (
            "Projecting consumption for each clinic and each tracer commodity "
            "over the next quarter, so that the district store orders against "
            "expected demand rather than against last month's issues."
        ),
        "local_owner_id": KWAME,
        "owner_validated": True,
        "critical": True,
        "formal_pct": 55,
        "processes": [
            "Quarterly forecast built from 12 months of issue data, refreshed "
            "monthly against actual consumption",
            "Seasonal adjustment applied to malaria commodities ahead of the "
            "rains, and to respiratory commodities in the harmattan",
            "Forecast-versus-actual reconciliation at the end of each quarter, "
            "written up as a one-page variance note",
        ],
        "roles": [
            "Regional Supply Coordinator builds and owns the forecast",
            "Health Logistics Officer supplies lead-time and supplier "
            "constraints as planning inputs",
            "Clinic Operations Officer flags catchment changes (new CHW "
            "cohorts, outreach campaigns, facility closures)",
        ],
        "governance": [
            "Forecast tabled at the monthly supply meeting; variance beyond "
            "20% must be explained, not merely noted",
            "Programme Director approves any forecast that increases the "
            "quarterly commodity budget by more than 15%",
        ],
        "tools": [
            "LMIS monthly issue extract (CSV)",
            "Forecast workbook, v4 -- one sheet per tracer commodity",
            "District malaria caseload series held by the DHMT",
        ],
        "metrics": [
            "Forecast accuracy (MAPE) by commodity, quarterly",
            "Forecast-versus-actual variance by clinic",
            "Proportion of clinics with a seasonally adjusted forecast",
        ],
        "decision_rights": [
            "Regional Supply Coordinator sets the forecast",
            "Programme Director approves budget-increasing forecasts",
            "Specialist currently reviews all seasonal adjustments before they "
            "are applied -- this is the piece not yet handed over",
        ],
        "relationships": [
            "DHMT surveillance officer, for caseload series",
            "Central Medical Store planning desk, for allocation signals",
        ],
        "capabilities_list": [
            "Demand Forecasting",
            "Seasonal Demand Planning",
            "Clinic Consumption Analysis",
        ],
    },
    {
        "id": MONITORING,
        "name": "Inventory Monitoring",
        "summary": (
            "Knowing what is actually on the shelf at nineteen clinics and two "
            "district stores, how fast it is moving, and how much of that "
            "picture can be trusted on any given day."
        ),
        "local_owner_id": KWAME,
        "owner_validated": True,
        "critical": True,
        "formal_pct": 78,
        "processes": [
            "Weekly stock-on-hand extract from LMIS, reviewed against the "
            "previous four weeks",
            "Monthly physical count at every clinic, reconciled to stock cards "
            "before the R&R is submitted",
            "Days-of-cover calculated per clinic per tracer commodity and "
            "sorted by exposure",
        ],
        "roles": [
            "Regional Supply Coordinator reviews the weekly extract",
            "Clinic dispensary leads perform and sign the physical count",
            "Clinic Operations Officer audits counts on a rotating sample",
        ],
        "governance": [
            "Any clinic below 30 days of cover on a tracer commodity appears on "
            "the weekly watchlist",
            "Count discrepancies above 5% trigger a recount before the number "
            "enters the LMIS",
        ],
        "tools": [
            "LMIS weekly stock-on-hand extract",
            "Paper stock cards at clinic level, photographed to the shared drive",
            "Watchlist workbook, refreshed each Monday",
        ],
        "metrics": [
            "Days of cover by clinic and commodity",
            "Count-to-card discrepancy rate",
            "Reporting completeness (clinics submitting on time)",
        ],
        "decision_rights": [
            "Regional Supply Coordinator decides what goes on the watchlist",
            "Clinic Operations Officer decides when a count must be repeated",
        ],
        "relationships": [
            "Nineteen clinic dispensary leads",
            "District store manager, for reconciliation disputes",
        ],
        "capabilities_list": [
            "Routine Inventory Monitoring",
            "Inventory Data Quality Assessment",
            "Stockout Risk Identification",
        ],
    },
    {
        "id": REPLENISHMENT,
        "name": "Replenishment",
        "summary": (
            "Deciding when to reorder and how much, given a static reorder "
            "threshold, a supplier whose lead time has been moving, and "
            "consumption that does not hold still through the year."
        ),
        "local_owner_id": KWAME,
        # Named, not validated. He runs the cycle; nobody has yet watched
        # him run it through a season and signed it off, and local
        # ownership scores the second claim rather than the first.
        "owner_validated": False,
        "critical": True,
        "formal_pct": 60,
        "processes": [
            "Monthly report and requisition submitted by each clinic by the 25th",
            "Reorder triggered when days of cover approaches the 14-day threshold",
            "Order quantity set to restore two months of cover plus a buffer "
            "sized to the current supplier lead time",
            "Off-cycle requisition available for clinics that fall below "
            "threshold between cycles",
        ],
        "roles": [
            "Regional Supply Coordinator raises the regional requisition",
            "Health Logistics Officer confirms lead time and freight before "
            "the order is placed",
            "Specialist currently sanity-checks every off-cycle order",
        ],
        "governance": [
            "Off-cycle orders require a written justification against the "
            "threshold rule",
            "Orders above the quarterly allocation need Programme Director "
            "sign-off",
        ],
        "tools": [
            "R&R form (paper at clinic, keyed at district)",
            "Reorder calculator in the forecast workbook",
            "Supplier lead-time log maintained by the Health Logistics Officer",
        ],
        "metrics": [
            "Orders raised before threshold breach, as a share of all orders",
            "Emergency orders per quarter",
            "Order-to-delivery days, by supplier",
        ],
        "decision_rights": [
            "Regional Supply Coordinator decides order timing within the cycle",
            "Programme Director approves over-allocation orders",
            "Nobody locally has yet made an off-cycle call without the "
            "specialist reviewing it first",
        ],
        "relationships": [
            "Central Medical Store order desk",
            "Regional transport contractor",
        ],
        "capabilities_list": [
            "Stockout Risk Identification",
            "Supplier Lead-Time Assessment",
            "Seasonal Demand Planning",
        ],
    },
    {
        "id": REDISTRIBUTION,
        "name": "Emergency Stock Redistribution",
        "summary": (
            "Moving commodity between clinics when one site is exposed and "
            "another genuinely has more than it needs. Cheaper and faster than "
            "an emergency order, and almost entirely judgement."
        ),
        "local_owner_id": None,
        "owner_validated": False,
        "critical": True,
        "formal_pct": 35,
        "processes": [
            "Candidate sending sites identified from days-of-cover and "
            "consumption trend, not from stock level alone",
            "Expiry and batch check before any transfer is proposed",
            "Inter-facility transfer note raised, signed at both ends, keyed "
            "into the LMIS within 48 hours",
        ],
        "roles": [
            "Specialist currently identifies and evaluates candidate transfers",
            "Health Logistics Officer arranges transport",
            "Clinic dispensary leads sign the transfer at both ends",
        ],
        "governance": [
            "Inter-facility transfers require district approval; which desk "
            "approves depends on commodity class and is not written down "
            "anywhere the team can find",
            "Transfers must be reflected in both clinics' stock cards before "
            "the next R&R",
        ],
        "tools": [
            "Inter-facility transfer note (paper, triplicate)",
            "Road and bridge status reports during the rains",
            "Batch and expiry register at district store",
        ],
        "metrics": [
            "Transfers completed per quarter",
            "Emergency orders avoided by redistribution",
            "Commodity written off after transfer (the failure mode)",
        ],
        "decision_rights": [
            "District health management team approves inter-facility movement",
            "Sending clinic's dispensary lead can refuse a transfer",
            "No local counterpart has yet led a redistribution decision",
        ],
        "relationships": [
            "DHMT approvals desk",
            "Transport contractor dispatcher",
            "Dispensary leads at the high-volume sites, who decide in practice "
            "whether a transfer is cooperative or contested",
        ],
        "capabilities_list": [
            "Emergency Stock Redistribution",
            "Supply Disruption Response",
        ],
    },
    {
        "id": SUPPLIERS,
        "name": "Supplier Management",
        "summary": (
            "Holding the central medical store and the transport contractors "
            "to a lead time that can be planned against, and knowing what to "
            "do when they drift."
        ),
        "local_owner_id": KOJO,
        "owner_validated": True,
        "critical": True,
        "formal_pct": 52,
        "processes": [
            "Every order's promised and actual delivery date logged on receipt",
            "Rolling three-order lead-time average maintained per supplier",
            "Quarterly performance conversation with the central store desk",
        ],
        "roles": [
            "Health Logistics Officer owns the lead-time log and the supplier "
            "relationship",
            "Regional Supply Coordinator uses the lead time as a planning input",
            "Programme Director attends the quarterly conversation when "
            "performance has slipped two quarters running",
        ],
        "governance": [
            "Planning lead-time assumption is revised only at quarter end, on "
            "evidence from the log",
            "Persistent short-shipment is escalated in writing, not by phone",
        ],
        "tools": [
            "Supplier lead-time log (workbook, started eleven months ago)",
            "Goods received notes",
            "Central store allocation notices",
        ],
        "metrics": [
            "Order-to-delivery days, rolling three orders",
            "Fill rate against quantity ordered",
            "Short-shipment incidents per quarter",
        ],
        "decision_rights": [
            "Health Logistics Officer sets the lead-time assumption used in "
            "planning",
            "Programme Director decides whether to escalate above the store desk",
        ],
        "relationships": [
            "Central Medical Store order desk supervisor",
            "Two regional transport contractors",
            "Regional pharmacist, who is consulted informally before any formal "
            "escalation and whose view usually decides whether it lands well",
        ],
        "capabilities_list": [
            "Supplier Lead-Time Assessment",
            "Supply Disruption Response",
        ],
    },
    {
        "id": REPORTING,
        "name": "Clinic Reporting",
        "summary": (
            "The monthly report and requisition cycle: nineteen clinics, paper "
            "at the point of capture, keyed at district, and the discipline "
            "that decides whether anything downstream is worth reading."
        ),
        "local_owner_id": AMA,
        "owner_validated": True,
        "critical": True,
        "formal_pct": 82,
        "processes": [
            "Clinic completes the R&R from stock cards and the physical count",
            "District keys the R&R into the LMIS within three working days",
            "Late or missing reports chased on a published escalation ladder",
        ],
        "roles": [
            "Clinic Operations Officer owns the cycle end to end",
            "Clinic dispensary leads complete the forms",
            "District data clerk keys and files",
        ],
        "governance": [
            "Reporting deadline is the 25th; the ladder starts on the 26th",
            "A clinic that misses two consecutive cycles is visited, not phoned",
        ],
        "tools": [
            "R&R form",
            "Stock cards",
            "LMIS data entry module",
            "Reporting tracker, updated daily during the cycle",
        ],
        "metrics": [
            "Reporting rate by cycle",
            "On-time reporting rate",
            "Days from clinic submission to LMIS entry",
        ],
        "decision_rights": [
            "Clinic Operations Officer decides when a clinic is visited",
            "District data clerk decides nothing; queries go back to the clinic",
        ],
        "relationships": [
            "Nineteen clinic dispensary leads",
            "District data clerk",
        ],
        "capabilities_list": [
            "Clinic Consumption Analysis",
            "Routine Inventory Monitoring",
        ],
    },
    {
        "id": DATA_QUALITY,
        "name": "Data Quality",
        "summary": (
            "Deciding whether a number can be acted on. Counts drift, cards "
            "get copied forward, and a confident figure from a site that has "
            "not counted in three weeks is worse than no figure at all."
        ),
        "local_owner_id": AMA,
        "owner_validated": True,
        "critical": True,
        "formal_pct": 74,
        "processes": [
            "Count-to-card reconciliation at every physical count",
            "Rotating audit: four clinics a quarter, unannounced",
            "Stale-count flag on any site whose last count is over 21 days old",
        ],
        "roles": [
            "Clinic Operations Officer runs the audit programme",
            "Regional Supply Coordinator acts on the stale-count flags",
            "Dispensary leads sign their own counts",
        ],
        "governance": [
            "Audit findings go to the quarterly performance review, named by "
            "clinic rather than aggregated",
            "A site flagged twice in a quarter gets a retraining visit",
        ],
        "tools": [
            "Count reconciliation sheet",
            "Audit checklist, revised after the 2025 reconciliation",
            "Stale-count report generated from the LMIS extract",
        ],
        "metrics": [
            "Count-to-card discrepancy rate",
            "Median count age at the point of decision",
            "Audit pass rate",
        ],
        "decision_rights": [
            "Clinic Operations Officer decides audit scope and schedule",
            "Clinic Operations Officer can declare a site's data unusable, "
            "which suspends automatic reordering for that site",
        ],
        "relationships": [
            "Dispensary leads",
            "DHMT quality focal person",
        ],
        "capabilities_list": [
            "Inventory Data Quality Assessment",
            "Clinic Consumption Analysis",
        ],
    },
    {
        "id": ESCALATION,
        "name": "Stockout Escalation",
        "summary": (
            "What happens once a site is out, or about to be: who is told, in "
            "what order, how fast, and what they are expected to do about it."
        ),
        "local_owner_id": None,
        "owner_validated": False,
        "critical": True,
        "formal_pct": 45,
        "processes": [
            "Clinic reports a stockout or imminent stockout the same day",
            "District confirms against the last count before escalating",
            "Escalation to DHMT if unresolved within 72 hours",
        ],
        "roles": [
            "Clinic dispensary lead raises the alert",
            "Regional Supply Coordinator triages",
            "Specialist currently decides when an escalation goes above district",
        ],
        "governance": [
            "Stockouts of tracer commodities are reported to the quarterly "
            "review individually, with root cause",
            "No written rule yet on what makes an escalation urgent rather "
            "than routine",
        ],
        "tools": [
            "Stockout alert form",
            "WhatsApp group used in practice, which is faster and leaves no "
            "record",
            "Quarterly stockout register",
        ],
        "metrics": [
            "Stockout days per clinic per commodity",
            "Time from alert to resolution",
            "Share of stockouts with a documented root cause",
        ],
        "decision_rights": [
            "Regional Supply Coordinator triages within district",
            "Programme Director escalates above district",
            "In practice the specialist has made this call every time so far",
        ],
        "relationships": [
            "DHMT duty officer",
            "Regional pharmacist",
        ],
        "capabilities_list": [
            "Supply Disruption Response",
            "Root Cause Analysis of Stockouts",
            "Stockout Risk Identification",
        ],
    },
    {
        "id": GOVERNANCE,
        "name": "Governance & Performance Review",
        "summary": (
            "The quarterly supply performance review: what gets measured, who "
            "has to answer for it, and whether a stockout produces a change or "
            "only a line in a register."
        ),
        "local_owner_id": EFUA,
        "owner_validated": True,
        "critical": True,
        "formal_pct": 70,
        "processes": [
            "Quarterly supply performance review, chaired by the Programme "
            "Director, with a fixed agenda",
            "Every tracer-commodity stockout reviewed individually for root "
            "cause and corrective action",
            "Corrective actions carry a named owner and a date, and are read "
            "back at the following review",
        ],
        "roles": [
            "Programme Director chairs and owns the agenda",
            "Regional Supply Coordinator presents forecast and stock position",
            "Health Logistics Officer presents supplier performance",
            "Clinic Operations Officer presents reporting and data quality",
        ],
        "governance": [
            "Review pack circulated three working days ahead; no pack, no item",
            "Open corrective actions older than two quarters are escalated to "
            "the Network board",
        ],
        "tools": [
            "Quarterly review pack template",
            "Corrective action register",
            "Stockout register",
        ],
        "metrics": [
            "Stockout days per quarter, by commodity",
            "Corrective actions closed on time",
            "Forecast accuracy trend",
        ],
        "decision_rights": [
            "Programme Director sets corrective actions and their owners",
            "Review can suspend a clinic's automatic allocation pending a visit",
        ],
        "relationships": [
            "Network board",
            "DHMT management",
            "Central Medical Store, invited annually",
        ],
        "capabilities_list": [
            "Root Cause Analysis of Stockouts",
            "Inventory Data Quality Assessment",
        ],
    },
]


# ---------------------------------------------------------------------------
# Transfer requirements
# ---------------------------------------------------------------------------
# (id_suffix, area, kind, label, description, state)
#
# 27 formal (formal / technical / tool / governance) of which 23 are complete,
# and 20 informal (tacit / judgment / relationship) of which 13 are complete.
# Those four numbers are what the readiness engine divides, so changing one of
# them moves the figure on the executive dashboard; capabilities.py's module
# docstring carries the rest of the tuning, and tests/test_seed.py asserts the
# numbers those two files are tuned to produce.

_C = TransferState.COMPLETE
_P = TransferState.PARTIAL
_N = TransferState.NONE

_K = RequirementKind

REQUIREMENTS: list[tuple[str, str, RequirementKind, str, str, TransferState]] = [
    # -- Demand Forecasting: 3 formal (1 partial), 2 informal (1 partial) ----
    ("fc-sop", FORECASTING, _K.FORMAL, "Quarterly forecasting SOP",
     "Written procedure for building and refreshing the quarterly forecast, "
     "including the variance note.", _C),
    ("fc-workbook", FORECASTING, _K.TOOL, "Forecast workbook v4",
     "The workbook itself, its formulas, and who maintains it when a "
     "commodity is added.", _C),
    ("fc-seasonal-method", FORECASTING, _K.TECHNICAL, "Seasonal adjustment method",
     "How the malaria seasonal uplift is derived from caseload history and "
     "applied per clinic. Documented, but never yet applied without the "
     "specialist reviewing it.", _P),
    ("fc-when-to-override", FORECASTING, _K.JUDGMENT,
     "Knowing when to override the model",
     "Recognising when a clinic's recent consumption is signal rather than "
     "noise, and overriding the trend line deliberately.", _C),
    ("fc-caseload-source", FORECASTING, _K.RELATIONSHIP,
     "Access to DHMT caseload series",
     "The surveillance officer shares the series informally and ahead of "
     "publication. That access is personal, not institutional.", _P),

    # -- Inventory Monitoring: 4 formal (all complete), 2 informal (complete) -
    ("im-count-protocol", MONITORING, _K.FORMAL, "Physical count protocol",
     "Count procedure, sign-off, and reconciliation to stock cards.", _C),
    ("im-extract", MONITORING, _K.TOOL, "Weekly LMIS extract",
     "Pulling, cleaning and distributing the weekly stock-on-hand extract.", _C),
    ("im-cover-calc", MONITORING, _K.TECHNICAL, "Days-of-cover calculation",
     "Computing days of cover per clinic per commodity and ranking exposure.", _C),
    ("im-watchlist-rule", MONITORING, _K.GOVERNANCE, "Watchlist inclusion rule",
     "The 30-day threshold, what it is for, and who may remove a site from "
     "the list.", _C),
    ("im-which-sites-drift", MONITORING, _K.TACIT,
     "Which sites' numbers drift, and why",
     "Five of the nineteen clinics reliably report late or copy cards forward. "
     "Knowing which five changes how the extract is read.", _C),
    ("im-reading-a-quiet-site", MONITORING, _K.JUDGMENT,
     "Reading a site that has gone quiet",
     "Distinguishing low consumption from a site that has stopped reporting "
     "accurately, before it becomes a stockout.", _C),

    # -- Replenishment: 3 formal (1 partial), 3 informal (2 incomplete) ------
    ("rp-rr-cycle", REPLENISHMENT, _K.FORMAL, "R&R cycle procedure",
     "The monthly report and requisition cycle, deadlines and the escalation "
     "ladder for late submissions.", _C),
    ("rp-reorder-calc", REPLENISHMENT, _K.TECHNICAL, "Reorder quantity calculation",
     "Restoring two months of cover plus a lead-time buffer, and how the "
     "buffer is sized.", _C),
    ("rp-offcycle-rule", REPLENISHMENT, _K.GOVERNANCE, "Off-cycle order authority",
     "Who may raise an off-cycle requisition and what justification is "
     "required. Written, but every off-cycle order so far has been reviewed "
     "by the specialist first.", _P),
    ("rp-beyond-threshold", REPLENISHMENT, _K.JUDGMENT,
     "Judging when the threshold is misleading",
     "Treating the 14-day reorder point as one input among several -- "
     "consumption trajectory, count freshness, season, supplier lead time -- "
     "rather than as a rule.", _P),
    ("rp-split-the-average", REPLENISHMENT, _K.TACIT,
     "Distrusting a 30-day average",
     "Splitting a monthly average when the shape of the month matters, and "
     "knowing when it does.", _N),
    ("rp-cms-desk", REPLENISHMENT, _K.RELATIONSHIP, "Central store order desk",
     "Who to call at the central medical store, when a call works better than "
     "a form, and what that costs the next time.", _C),

    # -- Emergency Redistribution: 2 formal (1 none), 3 informal (all short) --
    ("rd-transfer-note", REDISTRIBUTION, _K.TOOL, "Inter-facility transfer note",
     "The form, the signatures required, and getting the movement into both "
     "clinics' records within 48 hours.", _C),
    ("rd-approval-path", REDISTRIBUTION, _K.GOVERNANCE, "District approval path",
     "Which desk approves an inter-facility transfer for which commodity "
     "class. Nobody in the team can currently answer this without asking.", _N),
    ("rd-true-surplus", REDISTRIBUTION, _K.JUDGMENT,
     "Distinguishing stock from surplus",
     "Establishing whether a sending clinic genuinely has more than it needs, "
     "from its consumption trend rather than its stock level.", _N),
    ("rd-expiry-risk", REDISTRIBUTION, _K.TACIT, "Expiry and batch judgement",
     "Recognising when moving short-dated stock to a lower-volume site only "
     "relocates the write-off.", _P),
    ("rd-sending-clinic", REDISTRIBUTION, _K.RELATIONSHIP,
     "Standing with the high-volume sites",
     "Whether a dispensary lead cooperates with a transfer request is a matter "
     "of standing, and the specialist has it where the team does not.", _N),

    # -- Supplier Management: 3 formal (complete), 2 informal (complete) -----
    ("sm-leadtime-log", SUPPLIERS, _K.TOOL, "Supplier lead-time log",
     "The log, how receipts are recorded against promises, and the rolling "
     "three-order average.", _C),
    ("sm-performance-review", SUPPLIERS, _K.GOVERNANCE,
     "Quarterly supplier conversation",
     "The quarterly performance conversation with the central store desk and "
     "what evidence is brought to it.", _C),
    ("sm-escalation-format", SUPPLIERS, _K.FORMAL, "Written escalation format",
     "Escalating persistent short-shipment in writing, with the evidence "
     "attached.", _C),
    ("sm-when-to-escalate", SUPPLIERS, _K.JUDGMENT, "When to escalate a supplier",
     "Telling a bad quarter from a deteriorating supplier, and escalating "
     "before the trend is undeniable rather than after.", _C),
    ("sm-regional-pharmacist", SUPPLIERS, _K.RELATIONSHIP,
     "The regional pharmacist's ear",
     "Sounding out an escalation informally before it is filed. The person who "
     "decides whether it lands well.", _C),

    # -- Clinic Reporting: 4 formal (complete), 2 informal (complete) --------
    ("cr-rr-form", REPORTING, _K.FORMAL, "R&R completion standard",
     "How the form is completed from stock cards and the count, and what "
     "makes a submission acceptable.", _C),
    ("cr-entry", REPORTING, _K.TOOL, "LMIS data entry",
     "Keying the R&R, query handling, and the three-day standard.", _C),
    ("cr-tracker", REPORTING, _K.TOOL, "Reporting tracker",
     "Daily tracking through the cycle and the published escalation ladder.", _C),
    ("cr-visit-rule", REPORTING, _K.GOVERNANCE, "Two-miss visit rule",
     "A clinic that misses two consecutive cycles is visited rather than "
     "telephoned.", _C),
    ("cr-chasing", REPORTING, _K.TACIT, "Chasing a late clinic effectively",
     "Who to call at each site, what time of day they answer, and when to "
     "stop calling and drive.", _C),
    ("cr-dispensary-leads", REPORTING, _K.RELATIONSHIP, "Dispensary lead network",
     "Nineteen working relationships that decide whether the cycle closes on "
     "time.", _C),

    # -- Data Quality: 3 formal (complete), 2 informal (complete) ------------
    ("dq-reconciliation", DATA_QUALITY, _K.FORMAL, "Count reconciliation procedure",
     "Reconciling count to card, and the 5% recount threshold.", _C),
    ("dq-audit", DATA_QUALITY, _K.GOVERNANCE, "Rotating audit programme",
     "Four unannounced clinic audits a quarter, and how findings are reported "
     "by name.", _C),
    ("dq-stale-flag", DATA_QUALITY, _K.TECHNICAL, "Stale-count flagging",
     "Generating the 21-day stale-count flag from the extract and acting on "
     "it.", _C),
    ("dq-believability", DATA_QUALITY, _K.JUDGMENT, "Judging whether a number is usable",
     "Deciding whether a figure is good enough to act on, or whether the "
     "right answer is to go and count.", _C),
    ("dq-suspend-site", DATA_QUALITY, _K.TACIT, "Calling a site's data unusable",
     "Knowing when to suspend automatic reordering for a site, and how to do "
     "it without the clinic reading it as punishment.", _C),

    # -- Stockout Escalation: 2 formal (1 partial), 2 informal (1 partial) ---
    ("se-alert", ESCALATION, _K.FORMAL, "Stockout alert procedure",
     "Same-day reporting, district confirmation against the last count, and "
     "the 72-hour DHMT escalation.", _C),
    ("se-urgency-rule", ESCALATION, _K.GOVERNANCE, "Urgent versus routine",
     "What distinguishes an urgent escalation from a routine one. Not yet "
     "written down; the specialist has made every call so far.", _P),
    ("se-who-to-wake", ESCALATION, _K.TACIT, "Who to reach, and how fast",
     "Which duty officer answers out of hours, and when the group chat beats "
     "the form even though it leaves no record.", _C),
    ("se-holding-the-line", ESCALATION, _K.JUDGMENT,
     "Escalating without spending credibility",
     "Escalating hard enough to move, seldom enough to still be believed the "
     "next time.", _P),

    # -- Governance: 3 formal (complete), 2 informal (complete) --------------
    ("gv-review-pack", GOVERNANCE, _K.FORMAL, "Quarterly review pack",
     "The template, the three-day circulation rule, and what each presenter "
     "brings.", _C),
    ("gv-action-register", GOVERNANCE, _K.TOOL, "Corrective action register",
     "Named owners, dates, read-back at the following review, and board "
     "escalation after two quarters open.", _C),
    ("gv-root-cause-standard", GOVERNANCE, _K.GOVERNANCE,
     "Individual stockout review standard",
     "Every tracer stockout reviewed individually for root cause rather than "
     "aggregated into a rate.", _C),
    ("gv-chairing", GOVERNANCE, _K.JUDGMENT, "Chairing a review that changes something",
     "Keeping the review on causes rather than on totals, and closing an item "
     "only when the behaviour has changed.", _C),
    ("gv-board", GOVERNANCE, _K.RELATIONSHIP, "Board and DHMT standing",
     "The relationships that make an escalation above district land as a "
     "request rather than a complaint.", _C),
]


# ---------------------------------------------------------------------------
# Which captures were validated
# ---------------------------------------------------------------------------
# `transfer_requirements.validated` is a second claim about a requirement, not
# a synonym for its state: `state` says the handover happened, `validated`
# says somebody checked the capture and signed it. section 4 B4 scores the two
# halves differently on purpose -- formal transfer credits a requirement that
# is merely complete, informal transfer credits one only where the capture was
# validated as well -- so the informal half of the score cannot be earned by
# writing a document and declaring victory.
#
# The default below is that a complete requirement was validated, because in
# practice the two happen in the same conversation. The exceptions are formal
# requirements that exist, are handed over, and were never reviewed by anyone
# but their author. They still score, which is exactly the asymmetry, and they
# are named here so that the gap is visible rather than implied.

UNVALIDATED_CAPTURE: frozenset[str] = frozenset({
    "se-alert",            # written by the departing expert, never reviewed
    "cr-tracker",          # built in an afternoon, documented afterwards
    "rd-transfer-note",    # inherited from the previous assignment intact
})


def is_validated(requirement_id: str, state: TransferState) -> bool:
    """Whether the capture behind a requirement was checked by a second person."""
    return state is TransferState.COMPLETE and requirement_id not in UNVALIDATED_CAPTURE
