"""Generate session-surface fixtures for contracts/fixtures/ (scratch generator)."""

import copy
import json
from pathlib import Path

SCRATCH = Path(__file__).parent
OUT = Path("/Users/meepman/Github/RELAY/contracts/fixtures")

SHELL = json.loads((SCRATCH / "shell.json").read_text())
SHELL["active"] = "sessions"


def shell(persona="persona-expert"):
    s = copy.deepcopy(SHELL)
    s["current_persona"] = next(p for p in s["personas"] if p["id"] == persona)
    return s


def person(pid, name, initials, title, kind):
    return {"id": pid, "name": name, "initials": initials, "title": title, "kind": kind, "href": f"/people/{pid}"}


VOSS = person("p-voss", "Dr. Helena Voss", "HV", "Senior Desalination Process Engineer", "expert")
ROJAS = person("p-rojas", "Mateo Rojas", "MR", "Plant Operations Lead", "counterpart")
FUENTES = person("p-fuentes", "Camila Fuentes", "CF", "Control Room Operator", "counterpart")
IBARRA = person("p-ibarra", "Diego Ibarra", "DI", "Maintenance Planner", "counterpart")


def cap(cid, name):
    return {"id": cid, "name": name, "critical": True}


CAP_TURB = cap("cap-turbidity", "Intake Turbidity Response")
CAP_SHUT = cap("cap-shutdown", "Emergency Plant Shutdown")
CAP_FOUL = cap("cap-fouling", "Membrane Fouling Diagnosis")
CAP_ERD = cap("cap-erd", "Energy Recovery Optimization")
CAP_ALARM = cap("cap-alarm", "SCADA Alarm Triage")
CAP_RCA = cap("cap-rca", "Root Cause Analysis of Plant Trips")

AREA_INTAKE = {"id": "area-intake", "name": "Intake & Pretreatment", "href": "/blueprint?area=area-intake"}

STAGES = ["prepare", "capture", "expert-debrief", "learner-debrief", "synthesis", "validation", "next-action"]
SID = "sess-l2"


def steps(current):
    i = STAGES.index(current)
    out = []
    for n, st in enumerate(STAGES):
        if n < i:
            out.append({"stage": st, "state": "done", "href": f"/sessions/{SID}/{st}"})
        elif n == i:
            out.append({"stage": st, "state": "current", "href": f"/sessions/{SID}/{st}"})
        else:
            out.append({"stage": st, "state": "upcoming", "href": None})
    return out


def header(stage):
    return {
        "id": SID,
        "title": "Line 2 intake turbidity event",
        "held_on": "2026-09-26",
        "context": "Turbidity at Line 2 intake rose from 4 to 19 NTU over six hours after an offshore storm",
        "expert": VOSS,
        "learner": ROJAS,
        "focus": CAP_TURB,
        "stage": stage,
        "steps": steps(stage),
    }


def dump(name, obj):
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


# ───────────────────────────── sessions ─────────────────────────────

today = {
    "id": SID, "title": "Line 2 intake turbidity event", "held_on": "2026-09-26",
    "expert": VOSS, "learner": ROJAS, "focus": CAP_TURB, "stage": "prepare", "complete": False,
    "knowledge_captured": 0, "evidence_recorded": 0, "teaching_opportunities": 0, "follow_ups": 0,
    "href": f"/sessions/{SID}/prepare",
}
previous = [
    {"id": "sess-sdi", "title": "Cartridge filter SDI drift review", "held_on": "2026-09-12",
     "expert": VOSS, "learner": ROJAS, "focus": CAP_FOUL, "stage": "next-action", "complete": True,
     "knowledge_captured": 2, "evidence_recorded": 1, "teaching_opportunities": 1, "follow_ups": 2,
     "href": "/sessions/sess-sdi/next-action"},
    {"id": "sess-erd", "title": "Pressure exchanger efficiency loss", "held_on": "2026-09-03",
     "expert": VOSS, "learner": IBARRA, "focus": CAP_ERD, "stage": "next-action", "complete": True,
     "knowledge_captured": 1, "evidence_recorded": 1, "teaching_opportunities": 0, "follow_ups": 3,
     "href": "/sessions/sess-erd/next-action"},
    {"id": "sess-alarm", "title": "Night-shift alarm flood triage", "held_on": "2026-08-21",
     "expert": VOSS, "learner": FUENTES, "focus": CAP_ALARM, "stage": "next-action", "complete": True,
     "knowledge_captured": 3, "evidence_recorded": 2, "teaching_opportunities": 1, "follow_ups": 1,
     "href": "/sessions/sess-alarm/next-action"},
]
dump("sessions", {"shell": shell(), "today": today, "sessions": previous})

# ───────────────────────────── prepare ─────────────────────────────

brief = {
    "heading": "TODAY WITH MATEO",
    "primary_target": CAP_TURB,
    "current_level": 3,
    "todays_objective": "Line 2 intake turbidity is climbing after last night's storm and is still under the 20 NTU trigger. "
                        "Let Mateo run the response end to end. Find out whether he acts on the trend or waits for the threshold.",
    "your_role": "Observe first. Hold your own read of the situation until Mateo has proposed a plan, then test it.",
    "let_learner_lead": "Mateo decides whether, when and how to change Line 2 pretreatment: feed flow, coagulant dose, load transfer to Line 1.",
    "expose_if_possible": CAP_FOUL,
    "ask_before_explaining": [
        "Apart from its current value, what is the turbidity trend telling you?",
        "How long does a coagulant change on Line 2 take to reach the cartridge filters?",
        "What would make you take Line 2 off line completely?",
    ],
    "watch_for": [
        "Reads the slope of the trend, not only the absolute NTU",
        "Checks cartridge filter SDI before and after changing dosing",
        "Looks at the tide and swell forecast before deciding how long the event lasts",
        "Checks the Line 2 probe against a bench grab sample",
        "Tells the control room and shift supervisor before changing production",
    ],
    "knowledge_gap_to_explore": "SOP-PT-04 triggers enhanced coagulant dosing only at 20 NTU absolute. You act earlier when the rise is steep, "
                                "and you discount the Line 2 probe after storms. Neither is written down. Name the numbers you actually use.",
    "coaching_suggestion": "When Mateo asks what you would do, answer with a question: \"Where will it be in an hour?\"",
    "rationale": {
        "why": "Intake Turbidity Response is Mateo's closest capability to Performed Independently, and today's storm is a live case. "
               "The rate-of-rise practice behind your storm responses is not captured anywhere in the blueprint.",
        "evidence": [
            "Mateo at Performed with Supervision since 2026-07-14, across 2 supervised turbidity events",
            "Blueprint: Intake & Pretreatment informal knowledge at 70%; rate-of-rise response marked as uncaptured",
            "Cartridge filter SDI session (2026-09-12) recommended a live pretreatment event as the next experience",
            "41 days until your departure",
        ],
        "om_component": "Intake & Pretreatment",
        "if_not_transferred": "Operators follow the 20 NTU trigger literally. On a fast storm event, solids reach the cartridge filters "
                              "before the dosing change does, pushing SDI toward the membrane limit and forcing an unplanned Line 2 CIP.",
    },
}
dump("session_prepare", {"shell": shell(), "session": header("prepare"), "brief": brief, "ai_error": None,
                         "start_href": f"/sessions/{SID}/capture"})
dump("session_prepare__ai_error", {
    "shell": shell(), "session": header("prepare"), "brief": None,
    "ai_error": {
        "kind": "provider_unreachable", "function": "prepare_session",
        "message": "RELAY could not reach the AI provider to build today's Session Brief. Nothing was saved. "
                   "Retry, or start the session without a brief and capture it as usual.",
        "retry_href": f"/sessions/{SID}/prepare", "retry_method": "GET",
    },
    "start_href": f"/sessions/{SID}/capture",
})

# ───────────────────────────── capture ─────────────────────────────

TRANSCRIPT = """\
Line 2 intake turbidity event — control room, 26 Sep 2026. Present: H. Voss (V), M. Rojas (R).

[04:52] R: Line 2 intake is reading 11.8 NTU. Line 1 is sitting at 6.
[04:52] V: Still well under the 20 trigger. What are you looking at?
[04:53] R: Not the number. The trend. 4.1 at 00:40, 6.0 at 02:00, 8.3 at 03:30. The last forty minutes it went 9.9 to 11.8.
[04:53] V: So what's the slope?
[04:54] R: About 1.3 an hour until three. Since then closer to 2.8 an hour. It's accelerating.
[04:54] V: If it holds?
[04:55] R: We cross 20 before seven. The SOP says switch to enhanced dosing at 20. By the time that reaches the filters we're already carrying the solids.
[04:55] V: How long is that lag on Line 2?
[04:56] R: Dose point to flocculator, then through the media filters. Forty to fifty minutes before we see it at the cartridges.
[04:56] V: Good. Before you touch anything, what else do you want to know?
[04:57] R: Whether pretreatment is already feeling it. Media filter DP is 0.42 bar. Normal is under 0.35.
[04:57] V: Look at the cartridges. SDI.
[04:58] R: Last manual SDI15 on 2B was 2.9 at midnight. The online estimate says 3.3.
[04:58] V: Run a manual test on 2B. Don't trust the online estimate when the water is changing this fast.
[05:03] R: Manual SDI15 on 2B is 3.6.
[05:03] V: 2.9 to 3.6 in five hours. That trend matters more to me than any single reading. Past 4 at the cartridges, we're feeding it to the membranes.
[05:04] V: What is the sea doing?
[05:04] R: I haven't looked.
[05:05] V: Pull the marine forecast. Swell and tide.
[05:06] R: Swell 2.3 metres, building to 2.9 by ten. High tide 07:48.
[05:06] V: So it gets worse before it gets better. The storm has passed but the swell is still working the seabed at the intake head. Line 2's head sits in seven metres of water on sand. Line 1 is deeper, on rock. That's why they're diverging.
[05:07] R: And the flood tide brings the river plume north toward us?
[05:07] V: On a spring tide, yes. Today is springs. I've seen it peak up to two hours after high water.
[05:08] R: So the peak could be closer to ten than seven.
[05:08] V: One more thing. When was the Line 2 probe last cleaned?
[05:09] R: Wiper replaced in July. Cleaning is on the weekly round, Fridays.
[05:09] V: After a storm that window grows a film within days. It reads low. Get a grab from the intake well and run it on the bench.
[05:15] R: Bench says 15.4. Probe says 12.6.
[05:15] V: Call it three NTU low. What does that do to your estimate?
[05:16] R: We're closer than the screen says. An hour to twenty, not two.
[05:16] V: What do you want to do?
[05:17] R: Cut Line 2 feed from 1,380 to 1,100 cubic metres an hour. That takes the media filters from about 9.6 to 7.7 metres per hour. Line 1 is clean and has headroom to 1,500, so it picks up most of the difference.
[05:17] V: Coagulant?
[05:18] R: Step ferric now, 2.4 to 3.5 milligrams per litre, instead of waiting for 20 and jumping to 5. Jar test at six to confirm.
[05:18] V: The SOP doesn't say that.
[05:19] R: The SOP is a threshold. The water is telling us about the rate. If I wait for 20 I'm reacting to something that already happened an hour upstream.
[05:19] V: Permeate storage? You're taking production off Line 2.
[05:20] R: Tank is at 71%. With Line 1 up, net loss is about 160 an hour. We're fine through the morning demand peak.
[05:20] V: Who needs to know?
[05:21] R: Camila, for the control room log. And the shift supervisor, because this changes the production plan.
[05:21] V: Do it.
[05:24] R: Line 2 feed ramping. 1,240. 1,100. Holding. Line 1 at 1,490.
[05:25] R: Ferric setpoint 3.5. Logged as a pre-emptive change, trend screenshot attached.
[05:26] V: If the probe hadn't been fouled, would you have done anything differently?
[05:27] R: Same actions, maybe thirty minutes later. The slope was enough on its own.
[05:27] V: That's the right answer. The threshold tells you where you are. The rate tells you where you're going.
[05:28] R: Should I raise a work order for the probe?
[05:28] V: Yes. And move probe cleaning onto the post-storm checklist, not the weekly round. Diego will need to change the plan for it.
[05:29] R: What would make you take Line 2 off completely?
[05:30] V: Cartridge SDI above 5, or cartridge DP climbing fast right after a change-out. Then you protect the membranes and take the production hit. We're not there.
[05:31] R: And if Line 1 starts rising too?
[05:31] V: Then it's a plant-level decision, and a different sequence. We'll walk that one properly another day.
[06:10] R: Jar test. At 3.5 mg/L settled water is 1.8 NTU. At 2.4 it was 3.9.
[06:11] V: Keep 3.5.
[06:41] R: Line 2 probe just hit 19.2. Bench grab is 21.8. We're over the formal trigger.
[06:42] V: Cartridges?
[06:42] R: 2B SDI15 is 3.4, down from 3.6. Media filter DP 0.38 and flat.
[06:43] V: So by the time the SOP asked you to act, you'd already acted, and pretreatment is holding. Leave the settings. Recheck SDI at 08:00 and again after high water.
[06:43] R: Putting the 08:00 and 10:00 checks on the handover sheet now."""

dump("session_capture", {
    "shell": shell(), "session": header("capture"), "transcript": "", "notes": "",
    "sample_transcript_label": "Load Line 2 intake turbidity transcript",
    "sample_transcript": TRANSCRIPT,
    "submit_href": f"/sessions/{SID}/capture",
})

# ───────────────────────────── debriefs ─────────────────────────────

expert_qs = [
    {"id": "q-e1",
     "prompt": "At 04:52 Line 2 read 11.8 NTU, eight below the SOP trigger, and you agreed with Mateo acting anyway. "
               "What rate of rise makes you act regardless of the absolute value, and over what window do you judge it?",
     "rationale": "Mateo overrode SOP-PT-04 on slope alone (05:19) and you endorsed it. The SOP has no rate criterion. "
                  "This is the undocumented rule to pin down with numbers.",
     "answer": None, "tags": []},
    {"id": "q-e2",
     "prompt": "You asked for a manual SDI on 2B and the tide and swell forecast before Mateo proposed a plan. He had not looked at the sea. "
               "What would a less experienced operator most likely get wrong in this event?",
     "rationale": "Two checks came from you, not Mateo (04:58, 05:05). They separate a correct response from a lucky one.",
     "answer": None, "tags": []},
    {"id": "q-e3",
     "prompt": "You said the Line 2 probe \"reads low\" after a storm. The bench grab was 2.8 NTU above the probe at 05:15. "
               "How soon after a storm does that offset appear, how large does it get, and does Line 1 ever show it?",
     "rationale": "The probe offset changed Mateo's time-to-trigger from two hours to one. It is equipment-specific knowledge "
                  "held only by you and not in the maintenance plan.",
     "answer": None, "tags": []},
]
dump("session_expert_debrief", {
    "shell": shell(), "session": header("expert-debrief"), "role": "expert", "respondent": VOSS,
    "allowed": True, "switch_to_persona_id": "persona-expert", "questions": expert_qs, "ai_error": None,
    "submit_href": f"/sessions/{SID}/debrief/expert",
})

learner_qs = [
    {"id": "q-l1",
     "prompt": "Line 2 was at 11.8 NTU, well under the 20 NTU trigger. Why did you treat that as urgent?",
     "rationale": "Tests whether the early action came from reasoning Mateo can reproduce, or from Dr. Voss's prompting.",
     "answer": "Because the rise was speeding up. 1.3 an hour, then 2.8. At that rate we'd hit 20 before seven, and a dose change "
               "takes forty-plus minutes to reach the cartridges. Waiting for 20 means acting an hour late. The grab sample made it "
               "worse, the probe was three low. I'd have cut feed on the slope alone.",
     "tags": ["understanding"]},
    {"id": "q-l2",
     "prompt": "Suppose Line 1 had started rising at the same time and SDI on 2B passed 5. Walk through what you would do, in order.",
     "rationale": "Dr. Voss deferred this at 05:31 as a plant-level decision. Probes whether Mateo can carry the response past "
                  "single-line load shifting into Emergency Plant Shutdown.",
     "answer": "SDI over 5 means protect the membranes, so take Line 2 off first. If Line 1 is also climbing there's nowhere to move "
               "the load, so both lines come down. I know the triggers. I'm less sure of the order after that: which train first, "
               "when to call the grid operator about the load drop, how long storage lasts. I've watched Dr. Voss do it once, in March. "
               "I'd want her on the radio.",
     "tags": ["understanding", "experience_gap", "confidence_gap"]},
]
learner_payload = {
    "session": header("learner-debrief"), "role": "learner", "respondent": ROJAS,
    "switch_to_persona_id": "persona-learner", "questions": learner_qs, "ai_error": None,
    "submit_href": f"/sessions/{SID}/debrief/learner",
}
dump("session_learner_debrief", {"shell": shell("persona-learner"), **learner_payload, "allowed": True})
dump("session_learner_debrief__gated", {"shell": shell("persona-expert"), **learner_payload, "allowed": False})

# ───────────────────────────── findings ─────────────────────────────

FORMAL_RULE = "Switch to enhanced coagulant dosing when intake turbidity exceeds 20 NTU. (SOP-PT-04 §3.2)"


def fhref(fid):
    return f"/sessions/{SID}/findings/{fid}"


f_cap = {
    "kind": "capability_evidence",
    "id": "f-cap", "title": "Mateo Rojas acted on the rate of rise before the formal trigger",
    "status": "pending", "confidence": "high",
    "evidence_sources": ["Session transcript 04:53–05:25", "Learner debrief Q1", "Expert observation (Dr. Voss)"],
    "rationale": {
        "why": "Mateo read the trend, not the threshold, and proposed the correct response without prompting. "
               "His debrief answer reproduces the reasoning, including the dosing lag.",
        "evidence": [
            "04:54: computed the slope change, 1.3 to 2.8 NTU/h, unprompted",
            "05:17: proposed Line 2 feed cut to 1,100 m³/h and load shift to Line 1 before 20 NTU",
            "06:42: outcome held; 2B SDI15 fell from 3.6 to 3.4 after the formal trigger was crossed",
        ],
        "om_component": "Intake & Pretreatment",
        "if_not_transferred": "Storm response keeps waiting on Dr. Voss's judgment call; after 6 Nov no one on shift is cleared to act before 20 NTU.",
    },
    "actions": ["approve", "edit", "not-yet"],
    "action_href": fhref("f-cap"),
    "person": ROJAS, "capability": CAP_TURB,
    "evidence": [
        "Identified the accelerating rise (1.3 → 2.8 NTU/h) at 11.8 NTU, 8 NTU below the SOP trigger",
        "Estimated time-to-trigger and the 40–50 min dose-to-cartridge lag on Line 2",
        "Reduced Line 2 feed 1,380 → 1,100 m³/h and shifted load to Line 1 before the trigger",
        "Stepped ferric 2.4 → 3.5 mg/L and confirmed it by jar test (settled 1.8 NTU)",
        "Checked permeate storage and notified the control room and shift supervisor",
    ],
    "current_level": 3, "suggested_level": 4,
}

KI = {
    "id": "ki-rate-of-rise",
    "title": "Watch the Rate of Rise, Not the Threshold",
    "type": "heuristic",
    "capability": CAP_TURB,
    "area": AREA_INTAKE,
    "situation": "Intake turbidity is below the 20 NTU enhanced-dosing trigger but rising fast, typically in the 12–36 hours after an offshore storm.",
    "observed_signals": [
        "Rise accelerating past ~2 NTU/h sustained over an hour",
        "Manual SDI15 on the cartridge filters trending up (e.g. 2.9 → 3.6 in five hours)",
        "Swell forecast building, spring tide, high water still ahead",
        "Line 2 probe reading below a bench grab sample",
    ],
    "expert_reasoning": "The threshold tells you where the water is; the rate tells you where it will be when a dosing change "
                        "arrives 40–50 minutes later at the cartridges. After storms the Line 2 probe reads low, so the real margin is smaller than the screen shows.",
    "recommended_response": "Confirm with a bench grab and a manual SDI15. Check tide and swell. Reduce the affected line's feed flow, "
                            "shift load to the cleaner line, step coagulant up early and confirm by jar test. Tell the control room and shift supervisor.",
    "why_it_matters": "Waiting for 20 NTU on a fast event lets solids reach the cartridge filters before pretreatment responds, "
                      "pushing SDI toward the membrane limit of 5 and risking an unplanned CIP.",
    "source": {"label": "Line 2 intake turbidity event · 26 Sep 2026", "href": f"/sessions/{SID}/synthesis"},
    "expert": VOSS,
    "validation_status": "pending",
    "validated_by": None,
    "people_exposed": [ROJAS],
    "captured_on": "2026-09-26",
    "is_new": True,
}

f_tacit = {
    "kind": "tacit_knowledge",
    "id": "f-tacit", "title": "Watch the Rate of Rise, Not the Threshold",
    "status": "pending", "confidence": "high",
    "evidence_sources": ["Session transcript 05:03–05:27", "Expert debrief", "SOP-PT-04 Intake Turbidity Response"],
    "rationale": {
        "why": "Dr. Voss's storm response departs from SOP-PT-04 in four specific, repeatable ways. None appear in the SOP, the blueprint or the maintenance plan.",
        "evidence": [
            "05:27: \"The threshold tells you where you are. The rate tells you where you're going.\"",
            "05:09: Line 2 probe reads low after storms; bench grab 2.8 NTU above probe",
            "05:06: tide and swell used to predict when the event peaks",
        ],
        "om_component": "Intake & Pretreatment · informal knowledge",
        "if_not_transferred": "The SOP stays the only written rule. Operators wait for 20 NTU on a probe that under-reads by ~3 NTU after storms.",
    },
    "actions": ["approve", "edit", "reject"],
    "action_href": fhref("f-tacit"),
    "formal_rule": FORMAL_RULE,
    "expert_practice": [
        "Acts before 20 NTU when the rise is steep and accelerating, judged over the last hour",
        "Takes a manual SDI15 on the cartridge filters rather than trusting the online estimate",
        "Checks tide and swell forecast; on spring tides expects the peak up to two hours after high water",
        "Discounts the Line 2 probe after storms: biofouling on the window makes it read low",
    ],
    "proposed_record": KI,
}

f_gap = {
    "kind": "remaining_gap",
    "id": "f-gap", "title": "Emergency Plant Shutdown: triggers understood, sequence not demonstrated",
    "status": "pending", "confidence": "medium",
    "evidence_sources": ["Learner debrief Q2", "Session transcript 05:29–05:31", "Passport: Emergency Plant Shutdown at Observed since 2026-03-18"],
    "rationale": {
        "why": "Mateo named the membrane-protection triggers correctly but said he is unsure of the sequence once both lines must come down. "
               "Understanding is not demonstrated capability.",
        "evidence": [
            "Learner debrief Q2: \"I know the triggers. I'm less sure of the order after that.\"",
            "Only exposure: observed one shutdown, March 2026",
            "Incident Response area has no local owner and no local trainer",
        ],
        "om_component": "Incident Response",
        "if_not_transferred": "A two-line shutdown after 6 Nov is run from memory of one observed event, with no local person able to sequence it.",
    },
    "actions": ["approve", "edit", "reject"],
    "action_href": fhref("f-gap"),
    "capability": CAP_SHUT, "person": ROJAS,
    "understanding": [
        "Cartridge SDI above 5 means protect the membranes and take the line off",
        "If both intakes are rising there is nowhere to shift load, so the plant comes down",
        "The grid operator must be told about the load drop",
    ],
    "not_demonstrated": [
        "Isolating RO trains in the correct order",
        "Notifying the grid operator ahead of the high-pressure pump load drop",
        "Managing permeate storage and supply to the network during the outage",
        "Restart sequencing, including flush and SDI confirmation before feed",
        "Regulator notification within the permit window",
        "Shift handover during a shutdown",
    ],
    "instruction": "Do not advance Emergency Plant Shutdown. Mateo remains at Observed.",
}

f_next = {
    "kind": "next_activity",
    "id": "f-next", "title": "Mateo leads a shutdown tabletop, then a supervised drill",
    "status": "pending", "confidence": "medium",
    "evidence_sources": ["Remaining gap finding", "Transfer blueprint: Incident Response", "Expert availability to 6 Nov"],
    "rationale": {
        "why": "Emergency Plant Shutdown is the last critical capability with no local holder above Observed. A tabletop is low-risk "
               "and exposes the sequence; a supervised drill on Line 2 then produces performance evidence before Dr. Voss leaves.",
        "evidence": [
            "Incident Response: informal 20%, no local owner, status critical",
            "Mateo at Observed on Emergency Plant Shutdown",
            "Two drill windows remain before 6 Nov (low-demand weekends 10 Oct and 24 Oct)",
        ],
        "om_component": "Incident Response",
        "if_not_transferred": "The plant's worst-case procedure leaves with Dr. Voss.",
    },
    "actions": ["approve", "edit", "reject"],
    "action_href": fhref("f-next"),
    "objective": CAP_SHUT,
    "recommended_experience": "Mateo runs a tabletop of a two-line shutdown triggered by both intakes rising after a storm, then leads a "
                              "supervised Line 2 shutdown drill. Dr. Voss observes and intervenes only if membranes or supply are at risk.",
    "responsibilities": [
        "Decide the shutdown trigger and call it",
        "Isolate RO trains in order and confirm each is safe",
        "Notify the grid operator before the load drop",
        "Set permeate storage drawdown and network supply limits",
        "Draft the regulator notification",
        "Plan restart: flush, SDI check, feed ramp",
        "Brief the incoming shift",
    ],
    "target_date": "2026-10-10",
    "backup_experience": "If the drill window slips, run the tabletop twice with Camila Fuentes acting as control room, and hold the drill for 24 Oct.",
}

findings_pending = [f_cap, f_tacit, f_gap, f_next]
INPUTS = [
    "Session transcript", "Expert debrief", "Learner debrief",
    "Operating model: Intake & Pretreatment", "Transfer blueprint", "SOP-PT-04 Intake Turbidity Response",
    "Previous capability evidence: Mateo Rojas",
]

dump("session_synthesis", {
    "shell": shell(), "session": header("synthesis"), "findings": findings_pending, "inputs_used": INPUTS,
    "ai_error": None, "can_validate": True, "complete_href": f"/sessions/{SID}/validate",
})
dump("session_synthesis__ai_error", {
    "shell": shell(), "session": header("synthesis"), "findings": [], "inputs_used": INPUTS,
    "ai_error": {
        "kind": "schema_violation", "function": "analyze_session",
        "message": "The AI response did not match the findings schema (next_activity finding missing 'objective'). "
                   "Nothing was saved. Your transcript and both debriefs are kept; retry to run synthesis again.",
        "retry_href": f"/sessions/{SID}/synthesize", "retry_method": "POST",
    },
    "can_validate": True, "complete_href": f"/sessions/{SID}/validate",
})

# validation: mixed
cap_ok = {**copy.deepcopy(f_cap), "status": "approved", "actions": [],
          "validated_by": VOSS, "validated_at": "2026-09-26T10:14:00"}
ki_edited = {**copy.deepcopy(KI),
             "expert_reasoning": "The threshold tells you where the water is; the rate tells you where it will be when a dosing change "
                                 "arrives 40–50 minutes later at the cartridges. Act when the rise exceeds 2 NTU/h sustained over 60 minutes, "
                                 "whatever the absolute value. For 3–5 days after a storm, add 3 NTU to the Line 2 probe or use a bench grab.",
             "validation_status": "validated", "validated_by": VOSS}
tacit_edited = {**copy.deepcopy(f_tacit), "status": "edited", "actions": [],
                "validated_by": VOSS, "validated_at": "2026-09-26T10:19:00",
                "reviewer_note": "Added the numbers: 2 NTU/h over 60 min, and the Line 2 probe offset (~3 NTU low for 3–5 days after a storm). "
                                 "Line 1 doesn't show it; different mount, better flushed.",
                "proposed_record": ki_edited}
gap_ok = {**copy.deepcopy(f_gap), "status": "approved", "actions": [],
          "validated_by": VOSS, "validated_at": "2026-09-26T10:22:00"}
findings_mixed = [cap_ok, tacit_edited, gap_ok, copy.deepcopy(f_next)]

dump("session_validation", {
    "shell": shell(), "session": header("validation"), "findings": findings_mixed, "inputs_used": INPUTS,
    "ai_error": None, "can_validate": True, "complete_href": f"/sessions/{SID}/validate",
})

dump("finding_card", {"session_id": SID, "finding": cap_ok, "editing": False, "can_validate": True})
dump("finding_card__editing", {"session_id": SID, "finding": copy.deepcopy(f_tacit), "editing": True, "can_validate": True})

# ───────────────────────────── next action ─────────────────────────────

changes = [
    {"surface": "passport", "label": "Mateo Rojas · Intake Turbidity Response",
     "before": "3 · Performed with Supervision", "after": "4 · Performed Independently", "href": "/people/p-rojas"},
    {"surface": "knowledge", "label": "Knowledge Library · heuristics",
     "before": "11 records", "after": "12 records · + Watch the Rate of Rise, Not the Threshold",
     "href": "/knowledge?capability=cap-turbidity"},
    {"surface": "blueprint", "label": "Intake & Pretreatment · informal knowledge",
     "before": "70% · rate-of-rise response uncaptured", "after": "78% · captured and validated",
     "href": "/blueprint?area=area-intake"},
    {"surface": "readiness", "label": "Operating model readiness",
     "before": "64% · localization 6 / 10", "after": "67% · localization 7 / 10", "href": "/readiness"},
    {"surface": "brief", "label": "Next session objective",
     "before": "Intake Turbidity Response", "after": "Emergency Plant Shutdown · tabletop, then supervised drill",
     "href": f"/sessions/{SID}/next-action#next-brief"},
]
next_brief = {
    "heading": "TODAY WITH MATEO",
    "primary_target": CAP_SHUT,
    "current_level": 1,
    "todays_objective": "Move Emergency Plant Shutdown from Observed toward Assisted. Mateo runs a two-line shutdown as a tabletop, "
                        "start to restart, with you in the room.",
    "your_role": "Do not open with the sequence. Set the scenario, then stay quiet. Intervene only on a step that would damage membranes or cut supply.",
    "let_learner_lead": "Mateo calls the shutdown, sequences train isolation, and makes every external notification himself.",
    "expose_if_possible": CAP_RCA,
    "ask_before_explaining": [
        "Both intakes are rising and 2B SDI is 5.3. What do you do first, and why that first?",
        "When do you call the grid operator, and what do you tell them?",
        "How long does permeate storage last at current network demand?",
    ],
    "watch_for": [
        "Isolates RO trains in the right order and confirms each",
        "Notifies the grid operator before the high-pressure pump load drop",
        "Sets a storage drawdown limit and tells the network team",
        "Drafts the regulator notification inside the permit window",
        "Restart plan includes flush and SDI confirmation before feed",
        "Hands over cleanly to the incoming shift",
    ],
    "knowledge_gap_to_explore": "Ask: \"What would make you restart one line early instead of holding the whole plant down?\" "
                                "Your restart criteria after a storm shutdown are not in SOP-EM-01.",
    "coaching_suggestion": "Let Mateo reach the grid call on his own, even if he is late to it. Debrief the timing afterwards rather than prompting.",
    "rationale": {
        "why": "Validated gap from the Line 2 turbidity session: Mateo understands the shutdown triggers but has not demonstrated the sequence. "
               "It is the only critical capability with no local holder above Observed.",
        "evidence": [
            "Remaining gap finding approved by Dr. Voss, 26 Sep 2026",
            "Learner debrief: \"I'm less sure of the order after that.\"",
            "Incident Response: no local owner, informal knowledge 20%, status critical",
            "41 days until Dr. Voss departs",
        ],
        "om_component": "Incident Response",
        "if_not_transferred": "After 6 Nov a storm shutdown depends on one observed event and a written SOP that omits restart criteria.",
    },
}
dump("session_next_action", {
    "shell": shell(), "session": header("next-action"), "changes": changes, "next_brief": next_brief,
    "ai_error": None, "schedule_href": f"/sessions/{SID}/schedule-next",
})
print("ok")
