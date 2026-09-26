"""Generate read-surface fixtures for RELAY (fictional desalination engagement)."""

import copy
import json
from pathlib import Path

SCRATCH = Path(__file__).parent
OUT = Path("/Users/meepman/Github/RELAY/contracts/fixtures")
SHELL = json.loads((SCRATCH / "shell.json").read_text())

PERSONAS = {p["id"]: p for p in SHELL["personas"]}


def shell(active, persona="persona-expert"):
    s = copy.deepcopy(SHELL)
    s["active"] = active
    s["current_persona"] = copy.deepcopy(PERSONAS[persona])
    return s


# ─────────────────────────── people / caps / areas ───────────────────────────
def pref(pid, name, initials, title, kind):
    return {"id": pid, "name": name, "initials": initials, "title": title, "kind": kind,
            "href": f"/people/{pid}"}


VOSS = pref("p-voss", "Dr. Helena Voss", "HV", "Senior Desalination Process Engineer", "expert")
ROJAS = pref("p-rojas", "Mateo Rojas", "MR", "Plant Operations Lead", "counterpart")
FUENTES = pref("p-fuentes", "Camila Fuentes", "CF", "Control Room Operator", "counterpart")
IBARRA = pref("p-ibarra", "Diego Ibarra", "DI", "Maintenance Planner", "counterpart")
NAVARRO = pref("p-navarro", "Lucía Navarro", "LN", "Program Manager", "manager")
LOCALS = [ROJAS, FUENTES, IBARRA]

CAPS = {
    "cap-fouling": "Membrane Fouling Diagnosis",
    "cap-dosing": "Antiscalant Dosing Adjustment",
    "cap-turbidity": "Intake Turbidity Response",
    "cap-alarm": "SCADA Alarm Triage",
    "cap-erd": "Energy Recovery Optimization",
    "cap-pm": "Preventive Maintenance Planning",
    "cap-compliance": "Water Quality Compliance Reporting",
    "cap-contractor": "Contractor Coordination",
    "cap-shutdown": "Emergency Plant Shutdown",
    "cap-rca": "Root Cause Analysis of Plant Trips",
}


def cap(cid):
    return {"id": cid, "name": CAPS[cid], "critical": True}


# Local capability matrix (pre-loop). Voss is 6 on everything.
LEVELS = {
    "cap-fouling":    {"p-rojas": 6, "p-fuentes": 3, "p-ibarra": 3},
    "cap-dosing":     {"p-rojas": 4, "p-fuentes": 5, "p-ibarra": 1},
    "cap-turbidity":  {"p-rojas": 3, "p-fuentes": 2, "p-ibarra": 0},
    "cap-alarm":      {"p-rojas": 5, "p-fuentes": 4, "p-ibarra": 1},
    "cap-erd":        {"p-rojas": 2, "p-fuentes": 0, "p-ibarra": 3},
    "cap-pm":         {"p-rojas": 3, "p-fuentes": 1, "p-ibarra": 6},
    "cap-compliance": {"p-rojas": 4, "p-fuentes": 6, "p-ibarra": 1},
    "cap-contractor": {"p-rojas": 2, "p-fuentes": 0, "p-ibarra": 3},
    "cap-shutdown":   {"p-rojas": 1, "p-fuentes": 1, "p-ibarra": 0},
    "cap-rca":        {"p-rojas": 4, "p-fuentes": 2, "p-ibarra": 3},
}
LOCALIZED = [c for c, lv in LEVELS.items() if max(lv.values()) >= 4]
TEACHABLE = [c for c, lv in LEVELS.items() if max(lv.values()) == 6]
DEPENDENT = [c for c in CAPS if c not in LOCALIZED]
assert len(LOCALIZED) == 6 and len(TEACHABLE) == 3 and len(DEPENDENT) == 4

AREAS = [
    # id, name, owner, formal, informal, capability, trainer, status, caps
    ("area-intake", "Intake & Pretreatment", ROJAS, 0.95, 0.70, "Developing", False, "on_track", ["cap-turbidity"]),
    ("area-ro", "Reverse Osmosis Operations", ROJAS, 1.00, 0.85, "Strong", True, "sustainable", ["cap-fouling"]),
    ("area-dosing", "Chemical Dosing", FUENTES, 0.90, 0.60, "Developing", False, "transfer_in_progress", ["cap-dosing"]),
    ("area-erd", "Energy Recovery", None, 0.70, 0.25, "Limited", False, "at_risk", ["cap-erd"]),
    ("area-maint", "Maintenance Planning", IBARRA, 0.85, 0.55, "Developing", False, "transfer_in_progress", ["cap-pm", "cap-rca"]),
    ("area-compliance", "Water Quality Compliance", FUENTES, 1.00, 0.80, "Strong", True, "sustainable", ["cap-compliance"]),
    ("area-scada", "SCADA & Alarm Management", ROJAS, 0.90, 0.65, "Developing", False, "transfer_in_progress", ["cap-alarm"]),
    ("area-contractors", "Contractor & Supplier Management", IBARRA, 0.80, 0.40, "Limited", False, "at_risk", ["cap-contractor"]),
    ("area-incident", "Incident Response", None, 0.75, 0.20, "None", False, "critical", ["cap-shutdown"]),
]
AREA = {a[0]: a for a in AREAS}


def aref(aid):
    return {"id": aid, "name": AREA[aid][1], "href": f"/operating-model/areas/{aid}"}


def area_card(a):
    aid, name, owner, formal, informal, capab, trainer, status, _ = a
    return {"id": aid, "name": name, "href": f"/operating-model/areas/{aid}", "local_owner": owner,
            "owner_confirmed": owner is not None, "formal_pct": formal, "informal_pct": informal,
            "local_capability": capab, "trainer_coverage": trainer, "status": status}


# ───────────────────────────── derived metrics ─────────────────────────────
N_AREAS = len(AREAS)
owned = sum(1 for a in AREAS if a[2] is not None)
formal_avg = sum(a[3] for a in AREAS) / N_AREAS
informal_avg = sum(a[4] for a in AREAS) / N_AREAS
trainer_areas = sum(1 for a in AREAS if a[6])
ownership = owned / N_AREAS
localization = len(LOCALIZED) / len(CAPS)
trainer_cov = trainer_areas / N_AREAS
WEIGHTS = [("Local ownership", 0.25, "local_ownership", ownership),
           ("Capability localization", 0.30, "capability_localization", localization),
           ("Formal knowledge transfer", 0.15, "formal_transfer", formal_avg),
           ("Informal knowledge transfer", 0.20, "informal_transfer", informal_avg),
           ("Trainer coverage", 0.10, "trainer_coverage", trainer_cov)]
om = sum(w * v for _, w, _, v in WEIGHTS)
assert round(om, 2) == 0.64, om


def pct(v):
    return f"{round(v * 100)}%"


def fi(label, value, display):
    return {"label": label, "value": round(value, 4), "display": display}


def m_om(delta=None):
    return {
        "key": "om_readiness", "label": "OPERATING MODEL READINESS", "value": 0.64, "display": "64%",
        "unit": "percent", "status": "transfer_in_progress",
        "formula": {
            "expression": "0.25 × local ownership + 0.30 × capability localization + 0.15 × formal transfer "
                          "+ 0.20 × informal transfer + 0.10 × trainer coverage",
            "inputs": [fi(f"{lbl} (× {w:.2f})", v, pct(v)) for lbl, w, _, v in WEIGHTS],
        },
        **({"delta": delta} if delta else {}),
    }


def m_localization():
    return {"key": "capability_localization", "label": "CAPABILITY LOCALIZATION", "value": localization,
            "display": pct(localization), "unit": "percent", "status": "transfer_in_progress",
            "formula": {"expression": "critical capabilities with ≥1 local at level ≥4 ÷ critical capabilities",
                        "inputs": [fi("Localized critical capabilities", len(LOCALIZED), str(len(LOCALIZED))),
                                   fi("Critical capabilities", len(CAPS), str(len(CAPS)))]}}


def m_teachable():
    return {"key": "locally_teachable", "label": "LOCALLY TEACHABLE", "value": len(TEACHABLE),
            "display": str(len(TEACHABLE)), "unit": "count", "status": "at_risk",
            "formula": {"expression": "critical capabilities with ≥1 local at level 6 (Can Teach Others)",
                        "inputs": [fi("Membrane Fouling Diagnosis — Mateo Rojas", 1, "1"),
                                   fi("Preventive Maintenance Planning — Diego Ibarra", 1, "1"),
                                   fi("Water Quality Compliance Reporting — Camila Fuentes", 1, "1")]}}


def m_dependent():
    return {"key": "expert_dependent", "label": "EXPERT-DEPENDENT", "value": len(DEPENDENT),
            "display": str(len(DEPENDENT)), "unit": "count", "status": "critical",
            "formula": {"expression": "critical capabilities where no local is at level ≥4",
                        "inputs": [fi("Critical capabilities", len(CAPS), str(len(CAPS))),
                                   fi("Localized critical capabilities", len(LOCALIZED), str(len(LOCALIZED)))]}}


def m_days():
    return {"key": "days_to_departure", "label": "DAYS TO EXPERT DEPARTURE", "value": 41, "display": "41 DAYS",
            "unit": "days", "status": "at_risk",
            "formula": {"expression": "departure date − today (day of year)",
                        "inputs": [fi("Departure — 6 Nov 2026", 310, "day 310"),
                                   fi("Today — 26 Sep 2026", 269, "day 269")]}}


def m_ownership():
    return {"key": "local_ownership", "label": "LOCAL OWNERSHIP", "value": round(ownership, 4),
            "display": pct(ownership), "unit": "percent", "status": "on_track",
            "formula": {"expression": "areas with a confirmed local owner ÷ operating-model areas",
                        "inputs": [fi("Areas with confirmed local owner", owned, str(owned)),
                                   fi("Operating-model areas", N_AREAS, str(N_AREAS))]}}


def m_formal():
    return {"key": "formal_transfer", "label": "FORMAL KNOWLEDGE TRANSFER", "value": round(formal_avg, 4),
            "display": pct(formal_avg), "unit": "percent", "status": "on_track",
            "formula": {"expression": "mean formal transfer across operating-model areas",
                        "inputs": [fi("Sum of area formal transfer", sum(a[3] for a in AREAS), f"{sum(a[3] for a in AREAS):.2f}"),
                                   fi("Operating-model areas", N_AREAS, str(N_AREAS))]}}


def m_informal():
    return {"key": "informal_transfer", "label": "INFORMAL KNOWLEDGE TRANSFER", "value": round(informal_avg, 4),
            "display": pct(informal_avg), "unit": "percent", "status": "at_risk",
            "formula": {"expression": "mean informal (tacit) transfer across operating-model areas",
                        "inputs": [fi("Sum of area informal transfer", sum(a[4] for a in AREAS), f"{sum(a[4] for a in AREAS):.2f}"),
                                   fi("Operating-model areas", N_AREAS, str(N_AREAS))]}}


def m_trainer():
    return {"key": "trainer_coverage", "label": "TRAINER COVERAGE", "value": round(trainer_cov, 4),
            "display": pct(trainer_cov), "unit": "percent", "status": "critical",
            "formula": {"expression": "areas where every critical capability has a local at level 6 ÷ operating-model areas",
                        "inputs": [fi("Areas with full local trainer coverage", trainer_areas, str(trainer_areas)),
                                   fi("Operating-model areas", N_AREAS, str(N_AREAS))]}}


# ─────────────────────────────── knowledge ───────────────────────────────
def sess_link(sid):
    titles = {"sess-sdi": "Cartridge filter SDI drift review", "sess-erd": "Pressure exchanger efficiency loss",
              "sess-alarm": "Night-shift alarm flood triage", "sess-l2": "Line 2 intake turbidity event"}
    return {"label": titles[sid], "href": f"/sessions/{sid}"}


def doc_link(label, code):
    return {"label": label, "href": f"/knowledge?doc={code}"}


K = []


def k(id, title, type, capid, aid, situation, signals, reasoning, response, why, source, expert, status,
      validated_by, exposed, captured, is_new=False):
    K.append({"id": id, "title": title, "type": type, "capability": cap(capid) if capid else None,
              "area": aref(aid) if aid else None, "situation": situation, "observed_signals": signals,
              "expert_reasoning": reasoning, "recommended_response": response, "why_it_matters": why,
              "source": source, "expert": expert, "validation_status": status, "validated_by": validated_by,
              "people_exposed": exposed, "captured_on": captured, "is_new": is_new})


k("k-sop-pt04", "SOP-PT-04 Enhanced Coagulation Trigger", "formal_document", "cap-turbidity", "area-intake",
  "Standing procedure for raising ferric chloride dose at the intake flash mixers when raw-water turbidity rises.",
  ["Intake turbidity > 20 NTU on either line (15-min average)", "SDI15 at cartridge outlet > 4.0"],
  "Written in 2019 for the original DAF-less pretreatment train. Assumes both intake probes read true.",
  "Step FeCl₃ from 3.5 to 6.0 mg/L as Fe; confirm floc at the media filter inlet within 20 minutes; log in shift book.",
  "Only written trigger for pretreatment escalation. Regulator audit references it by number.",
  doc_link("SOP-PT-04 rev. 3", "SOP-PT-04"), None, "validated", VOSS, [ROJAS, FUENTES, IBARRA], "2026-01-14")

k("k-sdi-before-dp", "SDI Moves Before Differential Pressure", "heuristic", "cap-fouling", "area-ro",
  "Deciding whether first-stage fouling is starting before the ΔP alarm tells you.",
  ["SDI15 at cartridge outlet creeping 0.2–0.3 per day", "First-stage ΔP still inside 1.8 bar limit",
   "Normalized permeate flow down 3–4% over a week"],
  "Colloidal load shows up in SDI 5–7 days before first-stage ΔP rises. By the time ΔP alarms, the lead elements are already caked.",
  "Trend SDI daily, not weekly. Two consecutive days above 3.5 → inspect cartridges and book a CIP slot for the affected train.",
  "Avoids an unplanned CIP on a lead-element foul. Each unplanned CIP costs ~14 h of train downtime.",
  None, VOSS, "validated", VOSS, [ROJAS, FUENTES], "2026-03-19")

k("k-dose-temp", "Antiscalant Dose Follows Feed Temperature, Not the Vendor Curve", "heuristic", "cap-dosing", "area-dosing",
  "Setting antiscalant dose through the summer when feed temperature swings 6 °C between tide cycles.",
  ["Feed temperature above 27 °C", "LSI of concentrate above +1.6", "Recovery held at 44%"],
  "The vendor projection assumes 25 °C. Calcium carbonate scaling risk climbs faster than the curve above 27 °C at this recovery.",
  "Add 0.3 mg/L to the projected dose per 2 °C above 27 °C, cap at 3.6 mg/L. Re-run the projection weekly with actual feed chemistry.",
  "Last-stage scaling on Train 4 in August 2025 took three elements out of service.",
  doc_link("Antiscalant projection, May 2026", "AS-PROJ-2605"), VOSS, "validated", VOSS, [FUENTES, ROJAS], "2026-05-07")

k("k-l2-probe", "Line 2 Turbidity Probe Reads Low After Storms", "expert_insight", "cap-turbidity", "area-intake",
  "Interpreting Line 2 intake turbidity during and after heavy swell.",
  ["Line 2 reads 3–6 NTU below Line 1 for the same swell", "Probe wiper cycle alarms within 48 h of a storm",
   "Grab sample disagrees with online reading by > 25%"],
  "The Line 2 probe sits in a low-flow pocket that fouls with biofilm after storms. It under-reads until cleaned.",
  "Take a grab sample every 2 h during storm events. Treat Line 2 online value as a floor, not a reading.",
  "Under-reading is what lets the formal 20 NTU trigger fire late.",
  sess_link("sess-l2"), VOSS, "pending", None, [ROJAS], "2026-09-26", True)

k("k-px-mixing", "PX Mixing Rises When Low-Pressure Flow Drifts", "expert_insight", "cap-erd", "area-erd",
  "Diagnosing a slow loss of energy recovery efficiency across the pressure exchanger arrays.",
  ["Specific energy up from 3.21 to 3.38 kWh/m³ over 3 weeks", "PX volumetric mixing estimated 6.1% (design 4.5%)",
   "LP-in flow 3–5% below HP-out flow"],
  "Unbalanced flow drives brine into the HP feed. Salinity at the membrane inlet rises and the HP pump works harder.",
  "Rebalance LP flow to 102–103% of HP-out using the booster VFD; re-check mixing by conductivity after 30 min.",
  "Each 0.1 kWh/m³ is ~4,850 kWh/day at plant output. Only Voss tunes this today.",
  sess_link("sess-erd"), VOSS, "validated", VOSS, [IBARRA], "2026-09-03")

k("k-case-t3-trip", "Train 3 HP Pump Trip, 17 Sep 2026", "case", "cap-rca", "area-maint",
  "Train 3 high-pressure pump tripped on low suction pressure at 02:14 during a filter backwash.",
  ["Suction pressure dipped to 1.1 bar for 4 s", "Backwash of media filter F-06 started 02:13",
   "No VFD fault codes"],
  "Backwash draw on the filtered-water tank pulled suction below the trip setpoint. Setpoint had no time delay.",
  "Added 3 s delay on low-suction trip; staggered backwash starts against Train 3 run hours.",
  "Third low-suction trip this year. Earlier two were logged as VFD faults.",
  doc_link("RCA-2026-011", "RCA-2026-011"), VOSS, "validated", VOSS, [ROJAS, IBARRA], "2026-09-19")

k("k-case-alarm-flood", "August Alarm Flood: 214 Alarms in 38 Minutes", "case", "cap-alarm", "area-scada",
  "Night shift, 21 Aug. Loss of a PLC comms card on the dosing skid cascaded into a flood of stale alarms.",
  ["214 alarms in 38 min, 180 from one I/O rack", "Dosing pump status frozen on HMI", "Operator acknowledged 60+ alarms unread"],
  "Most alarms were consequences of one comms fault. The real risk was that dosing was running blind.",
  "Shelve the rack's alarms, switch dosing to local manual, dispatch the on-call instrument tech.",
  "Became the basis for the alarm-flood first-five-minutes card.",
  sess_link("sess-alarm"), VOSS, "validated", VOSS, [FUENTES, ROJAS], "2026-08-21")

k("k-exc-recovery", "Do Not Raise Recovery Above 42% When Feed Exceeds 29 °C", "exception", "cap-fouling", "area-ro",
  "Operators asked to push recovery to meet peak summer demand.",
  ["Feed temperature > 29 °C", "Demand forecast > 47,000 m³/d", "Concentrate LSI > +1.8"],
  "Design sheet allows 45%. At 29 °C and this feed, silica and carbonate limits are hit before the design recovery.",
  "Hold recovery at 42%; meet demand by bringing Train 4 online early instead.",
  "Overrides the design envelope. Not in any SOP.",
  None, VOSS, "validated", VOSS, [ROJAS], "2026-06-24")

k("k-exc-chlorine", "No Chlorine Shock Upstream of Membranes, Even for Biofouling", "exception", "cap-dosing", "area-dosing",
  "Suspected biofouling on first-stage elements; a contractor proposed a chlorine shock at the intake.",
  ["Biofilm on cartridge filters", "ORP at membrane inlet normally < 200 mV"],
  "Polyamide membranes are oxidized by free chlorine. SBS dechlorination capacity is sized for continuous low dose only.",
  "Use non-oxidizing biocide (DBNPA) at 10 mg/L for 45 min; keep SBS on and verify ORP < 250 mV.",
  "A single shock can cost a full train of elements.",
  doc_link("Membrane warranty terms §4.2", "WARRANTY-4.2"), VOSS, "validated", VOSS, [FUENTES], "2026-04-16")

k("k-ll-permeate", "March Near-Miss: Permeate Storage Down to 18%", "lesson_learned", "cap-shutdown", "area-incident",
  "Grid dip on 9 Mar forced a two-train shutdown. Restart took 5 h 40 min.",
  ["Permeate tank fell from 71% to 18%", "Distribution pumps not throttled until level < 30%"],
  "Nobody owned the call to throttle distribution. The shutdown procedure stops at 'trains isolated'.",
  "Throttle distribution to 60% when two or more trains trip; notify the network control desk at the same time.",
  "The shutdown procedure does not cover storage. Only Voss has run a full restart.",
  None, VOSS, "validated", VOSS, [ROJAS], "2026-03-12")

k("k-ll-cartridge", "Cartridge Change-Outs Booked by Calendar, Not ΔP", "lesson_learned", "cap-pm", "area-maint",
  "PM plan replaced 5 µm cartridges every 6 weeks regardless of condition.",
  ["Change-outs at ΔP 0.4 bar (limit 1.0)", "Cartridge spend 31% over budget by May"],
  "Calendar-based change wasted cartridges in winter and let them run too long after storms.",
  "Condition-based: change at 0.8 bar ΔP or 8 weeks, whichever first; plus inspection within 72 h after any storm.",
  "Saved ~22% of cartridge spend June–August.",
  None, IBARRA, "validated", VOSS, [IBARRA, ROJAS], "2026-06-05")

k("k-rel-grid", "Grid Operator Control Desk: Call Before Load Shed", "relationship", "cap-shutdown", "area-incident",
  "Any unplanned shutdown of two or more trains drops plant load by 9–14 MW.",
  ["Two or more HP pumps tripped", "Frequency deviation alarm from substation"],
  "The regional control desk expects a call within 10 min. Voss has the direct line and the duty engineer's trust.",
  "Call the duty engineer on the direct line, not the switchboard. Give MW dropped and expected restart time.",
  "Without the call, restart can be delayed by load-block scheduling for up to 2 h.",
  None, VOSS, "pending", None, [], "2026-08-27")

k("k-rel-px-oem", "PX OEM Service: Escalate via Regional Engineer", "relationship", "cap-erd", "area-erd",
  "Warranty claims and spare cartridges for the pressure exchangers.",
  ["Ticket open > 5 working days", "Lead time quoted > 10 weeks"],
  "The OEM ticket queue deprioritizes utilities. The regional applications engineer can release stock from the regional hub.",
  "Open the ticket, then email the regional engineer with ticket number and plant SEC trend attached.",
  "Two PX rotor spares came in 3 weeks instead of 14 this way.",
  None, VOSS, "validated", VOSS, [], "2026-02-20")

k("k-heur-divers", "Book Intake Diver Slots by Swell Forecast", "heuristic", "cap-contractor", "area-contractors",
  "Scheduling the diving contractor for intake screen inspection and cleaning.",
  ["Significant wave height forecast", "Contractor mobilization notice 5 days"],
  "Divers stand down above 1.4 m swell. Calendar bookings lose ~40% of slots in autumn.",
  "Book 3 provisional slots per job against the 7-day swell forecast; release unused slots 48 h out.",
  "Screen cleaning slipped 3 times in 2025, contributing to the October intake restriction.",
  None, VOSS, "validated", VOSS, [IBARRA], "2026-07-15")

k("k-compliance-return", "Monthly Compliance Return — Boron, TDS, Chloride", "formal_document", "cap-compliance", "area-compliance",
  "Monthly permeate quality return to the water regulator.",
  ["Boron limit 1.0 mg/L", "TDS limit 500 mg/L", "Chloride limit 250 mg/L"],
  "Regulator template; values taken from the accredited lab, online analyzers for trend only.",
  "Submit by the 5th working day. Flag any single result above 80% of limit in the cover note.",
  "Late or unflagged returns trigger an audit visit.",
  doc_link("REG-QR-01 template", "REG-QR-01"), None, "validated", FUENTES, [FUENTES, ROJAS], "2026-01-29")

for it in K:
    if it["validation_status"] == "pending":
        it["validated_by"] = None


def ksum(it):
    return {"id": it["id"], "title": it["title"], "type": it["type"], "area": it["area"],
            "captured_on": it["captured_on"], "source": it["source"],
            "validation_status": it["validation_status"], "href": f"/knowledge#{it['id']}"}


K_SORTED = sorted(K, key=lambda i: i["captured_on"], reverse=True)
TYPES = ["formal_document", "expert_insight", "case", "heuristic", "exception", "lesson_learned", "relationship"]
TYPE_LABEL = {t: t.replace("_", " ").title() for t in TYPES}
KNOWLEDGE_AT_RISK = [i for i in K if not any(p["kind"] == "counterpart" for p in i["people_exposed"])
                     or i["validation_status"] == "pending"]


def m_k_risk():
    no_local = sum(1 for i in K if not any(p["kind"] == "counterpart" for p in i["people_exposed"]))
    pending_only = len(KNOWLEDGE_AT_RISK) - no_local
    return {"key": "knowledge_at_risk", "label": "KNOWLEDGE AT RISK", "value": len(KNOWLEDGE_AT_RISK),
            "display": str(len(KNOWLEDGE_AT_RISK)), "unit": "count", "status": "at_risk",
            "formula": {"expression": "library items with no local exposed + items still pending expert validation",
                        "inputs": [fi("Items with no local exposed", no_local, str(no_local)),
                                   fi("Other items pending validation", pending_only, str(pending_only))]}}


def m_dependency_pct():
    v = len(DEPENDENT) / len(CAPS)
    return {"key": "expert_dependency", "label": "EXPERT DEPENDENCY", "value": v, "display": pct(v),
            "unit": "percent", "status": "critical",
            "formula": {"expression": "critical capabilities where no local is at level ≥4 ÷ critical capabilities",
                        "inputs": [fi("Expert-dependent capabilities", len(DEPENDENT), str(len(DEPENDENT))),
                                   fi("Critical capabilities", len(CAPS), str(len(CAPS)))]}}


def write(name, data):
    (OUT / f"{name}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


OUT.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────── overview ───────────────────────────────
RISK_CARDS = [
    {"severity": "critical", "title": "Emergency Plant Shutdown",
     "problem": "Only Voss has run a full two-train shutdown and restart. Procedure stops at 'trains isolated'; storage, grid call and restart order are undocumented.",
     "local_label": "LOCAL CAPABILITY", "local_value": "Mateo Rojas — Observed",
     "recommended_action": "Run a tabletop shutdown with Rojas leading, then a supervised drill on Train 4 before 23 Oct.",
     "area": aref("area-incident"),
     "rationale": {"why": "Highest consequence capability with no local above level 1 and 41 days left.",
                   "evidence": ["March near-miss: permeate storage fell to 18%", "No local owner for Incident Response",
                                "Grid desk relationship held only by Voss"],
                   "om_component": "Incident Response",
                   "if_not_transferred": "Next grid dip after 6 Nov is handled without anyone who has restarted the plant."}},
    {"severity": "critical", "title": "Energy Recovery Optimization",
     "problem": "PX flow balancing is done by feel from the SEC trend. Specific energy drifted from 3.21 to 3.38 kWh/m³ in three weeks before Voss caught it.",
     "local_label": "LOCAL CAPABILITY", "local_value": "Diego Ibarra — Performed with Supervision",
     "recommended_action": "Confirm Ibarra as Energy Recovery owner; two more supervised rebalances on Trains 1 and 3.",
     "area": aref("area-erd"),
     "rationale": {"why": "Single holder, no owner, informal transfer at 25%.",
                   "evidence": ["sess-erd: Ibarra assisted PX rebalance on Train 2", "PX OEM escalation route held only by Voss"],
                   "om_component": "Energy Recovery",
                   "if_not_transferred": "~4,850 kWh/day lost for every 0.1 kWh/m³ drift left uncorrected."}},
    {"severity": "high", "title": "Intake Turbidity Response",
     "problem": "Formal trigger is 20 NTU. Voss acts on rate of rise, SDI trend and swell forecast, and discounts the Line 2 probe after storms.",
     "local_label": "LOCAL TRAINER", "local_value": "None",
     "recommended_action": "Validate today's Line 2 session evidence; capture the rate-of-rise heuristic.",
     "area": aref("area-intake")},
    {"severity": "medium", "title": "Contractor Coordination",
     "problem": "Diving, membrane autopsy and HP pump overhaul contractors are called through Voss's contacts.",
     "local_label": "LOCAL CAPABILITY", "local_value": "Diego Ibarra — Performed with Supervision",
     "recommended_action": "Ibarra leads the October diver booking; Voss hands over the three contractor contacts in writing.",
     "area": aref("area-contractors")},
]

PRIORITY = [
    {"rank": 1, "text": "Validate findings from the Line 2 intake turbidity session", "href": "/sessions/sess-l2/validation",
     "capability": cap("cap-turbidity"), "person": ROJAS, "ai_suggested": True},
    {"rank": 2, "text": "Schedule tabletop shutdown scenario — Rojas leads, Voss observes", "href": "/sessions",
     "capability": cap("cap-shutdown"), "person": ROJAS, "ai_suggested": True},
    {"rank": 3, "text": "Confirm a local owner for Energy Recovery", "href": "/operating-model/areas/area-erd",
     "capability": cap("cap-erd"), "person": IBARRA, "ai_suggested": True},
    {"rank": 4, "text": "Introduce Rojas to the grid operator duty engineer", "href": "/knowledge#k-rel-grid",
     "capability": cap("cap-shutdown"), "person": ROJAS, "ai_suggested": True},
    {"rank": 5, "text": "Hand over PX OEM regional engineer contact to Ibarra", "href": "/knowledge#k-rel-px-oem",
     "capability": cap("cap-erd"), "person": IBARRA, "ai_suggested": False},
]

TTT = [
    {"capability": cap("cap-turbidity"), "current_expert": VOSS, "candidate_trainer": ROJAS, "current_level": 3,
     "target_level": 6, "recommended_activity": "Rojas leads the next storm-event response and briefs night shift on the rate-of-rise check.",
     "rationale": {"why": "Rojas owns Intake & Pretreatment and already reads SDI trends at level 6.",
                   "evidence": ["Line 2 session: reduced feed flow on rate of rise before 20 NTU", "k-sdi-before-dp"],
                   "om_component": "Intake & Pretreatment", "if_not_transferred": "Intake stays with no local trainer."}},
    {"capability": cap("cap-erd"), "current_expert": VOSS, "candidate_trainer": IBARRA, "current_level": 3,
     "target_level": 6, "recommended_activity": "Ibarra rebalances Train 1 PX array unassisted, then walks Rojas through the method.",
     "rationale": {"why": "Ibarra is the only local above level 2 on energy recovery.",
                   "evidence": ["sess-erd, 3 Sep", "k-px-mixing"], "om_component": "Energy Recovery"}},
    {"capability": cap("cap-alarm"), "current_expert": VOSS, "candidate_trainer": ROJAS, "current_level": 5,
     "target_level": 6, "recommended_activity": "Rojas runs the alarm-flood first-five-minutes drill for the B and C shifts.",
     "rationale": None},
]

overview = {"shell": shell("overview"),
            "headline": [m_om(), m_localization(), m_teachable(), m_dependent(), m_days()],
            "knowledge_at_risk": RISK_CARDS, "priority_actions": PRIORITY,
            "recent_knowledge": [ksum(i) for i in K_SORTED[:5]], "train_the_trainer": TTT}
write("overview", overview)
ov_pm = copy.deepcopy(overview)
ov_pm["shell"] = shell("overview", "persona-pm")
write("overview__pm", ov_pm)

# ─────────────────────────── operating model ───────────────────────────
write("operating_model", {
    "shell": shell("operating_model"),
    "title": "DESALINATION PLANT OPERATING MODEL",
    "mission": "Produce 48,500 m³/d of compliant potable water from seawater at ≤ 3.30 kWh/m³, run and maintained by the Authority's own staff after 6 Nov 2026.",
    "summary": [m_om(), m_ownership(), m_formal(), m_informal(), m_trainer()],
    "areas": [area_card(a) for a in AREAS],
})

# ─────────────────────────────── area drawer ───────────────────────────────
erd = AREA["area-erd"]
erd_ready = 0.25 * 0 + 0.30 * 0 + 0.15 * erd[3] + 0.20 * erd[4] + 0.10 * 0
write("area_drawer", {
    "area": area_card(erd),
    "description": "Four PX pressure-exchanger arrays (one per RO train) recovering brine pressure into the HP feed. Target specific energy ≤ 3.30 kWh/m³; currently 3.34 after the September rebalance.",
    "dimensions": [
        {"dimension": "processes", "items": [
            {"label": "PX flow balancing", "detail": "LP-in held at 102–103% of HP-out via booster VFD; weekly check.", "owner": None, "depends_on_expert": True},
            {"label": "Mixing check by conductivity", "detail": "Membrane-inlet vs. filtered-seawater conductivity after each rebalance.", "owner": IBARRA},
            {"label": "PX rotor inspection", "detail": "Every 16,000 run hours or on noise complaint.", "owner": IBARRA},
        ]},
        {"dimension": "people_roles", "items": [
            {"label": "Area owner", "detail": "Unassigned. Ibarra proposed; not confirmed by plant manager.", "depends_on_expert": True},
            {"label": "Shift operators", "detail": "Read SEC on HMI; do not adjust booster setpoints.", "owner": ROJAS},
        ]},
        {"dimension": "governance", "items": [
            {"label": "Booster setpoint changes", "detail": "Logged in MOC register; today approved verbally by Voss.", "depends_on_expert": True},
            {"label": "Monthly energy review", "detail": "Plant manager sign-off on SEC vs. budget.", "owner": NAVARRO},
        ]},
        {"dimension": "tools_systems", "items": [
            {"label": "SCADA SEC trend screen", "detail": "kWh/m³ per train, 1-min resolution.", "owner": ROJAS},
            {"label": "PX performance spreadsheet", "detail": "Voss's personal workbook; estimates mixing from four conductivity readings.", "owner": VOSS, "depends_on_expert": True},
        ]},
        {"dimension": "data_metrics", "items": [
            {"label": "Specific energy consumption", "detail": "3.34 kWh/m³ (target ≤ 3.30).", "owner": ROJAS},
            {"label": "Volumetric mixing", "detail": "Estimated 5.2% after rebalance (design 4.5%).", "depends_on_expert": True},
            {"label": "HP pump efficiency", "detail": "Monthly from motor kW and flow.", "owner": IBARRA},
        ]},
        {"dimension": "decision_rights", "items": [
            {"label": "When to rebalance vs. inspect rotors", "detail": "Voss decides from mixing trend and noise.", "owner": VOSS, "depends_on_expert": True},
            {"label": "Taking a PX array offline", "detail": "Shift lead may isolate on high vibration.", "owner": ROJAS},
        ]},
        {"dimension": "external_relationships", "items": [
            {"label": "PX OEM regional applications engineer", "detail": "Releases hub stock; bypasses the ticket queue.", "owner": VOSS, "depends_on_expert": True},
            {"label": "Motor rewind contractor", "detail": "Framework contract via procurement.", "owner": IBARRA},
        ]},
        {"dimension": "capabilities", "items": [
            {"label": "Energy Recovery Optimization", "detail": "Ibarra L3, Rojas L2, Fuentes L0. No local at L4.", "depends_on_expert": True},
            {"label": "Preventive Maintenance Planning", "detail": "Ibarra L6 — covers PX rotor PM scheduling.", "owner": IBARRA},
        ]},
    ],
    "transfer_readiness": {
        "key": "area_transfer_readiness", "label": "AREA TRANSFER READINESS", "value": round(erd_ready, 4),
        "display": "16%", "unit": "percent", "status": "at_risk",
        "formula": {"expression": "0.25 × owner confirmed + 0.30 × capabilities localized + 0.15 × formal + 0.20 × informal + 0.10 × trainer coverage",
                    "inputs": [fi("Owner confirmed (× 0.25)", 0, "No"), fi("Capabilities localized (× 0.30)", 0, "0 / 1"),
                               fi("Formal transfer (× 0.15)", erd[3], pct(erd[3])), fi("Informal transfer (× 0.20)", erd[4], pct(erd[4])),
                               fi("Trainer coverage (× 0.10)", 0, "No")]}},
    "blueprint_href": "/blueprint?area=area-erd",
})

# ─────────────────────────────── blueprint ───────────────────────────────
def pl(pid_levels):
    return [{"person": p, "level": l} for p, l in pid_levels]


def lv(capid):
    return pl([(p, LEVELS[capid][p["id"]]) for p in LOCALS if LEVELS[capid][p["id"]] > 0])


def grp(category, *items):
    return {"category": category, "items": [{"id": f"{category[:4]}-{i}", "label": lbl, "state": st}
                                            for i, (lbl, st) in enumerate(items, 1)]}


def comp(cid, aid, name, target, trainer, risk, groups, gaps=(), action=None, levels_from=None):
    a = AREA[aid]
    return {"id": cid, "area": aref(aid), "name": name, "status": a[7], "local_owner_target": target,
            "local_capability": [x for c in (levels_from or a[8]) for x in lv(c)],
            "local_trainer": trainer, "transfer_risk": risk,
            "groups": [{"category": g["category"], "items": [{**it, "id": f"{cid}-{it['id']}"} for it in g["items"]]} for g in groups],
            "gap_callouts": list(gaps), "recommended_action": action}


C, P, N = "complete", "partial", "none"
COMPONENTS = [
    comp("bp-intake", "area-intake", "Intake & Pretreatment", ROJAS, None,
         "Formal trigger documented; the judgment that makes it work early is not.",
         [grp("formal_knowledge", ("SOP-PT-04 enhanced coagulation trigger", C), ("Media filter backwash sequence", C), ("Cartridge filter change criteria", C)),
          grp("informal_knowledge", ("Rate-of-rise vs. absolute turbidity", P), ("Line 2 probe under-read after storms", P), ("Swell forecast as leading signal", N)),
          grp("technical_capability", ("FeCl₃ dose step and floc check", C), ("Grab-sample turbidity and SDI15", C), ("Feed-flow reduction per line", P)),
          grp("decision_judgment", ("When to act before 20 NTU", P), ("When to take a line off intake", N)),
          grp("relationships", ("Port authority swell bulletin", P)),
          grp("tools_systems", ("SCADA intake trend screen", C), ("Portable turbidimeter calibration", C)),
          grp("governance", ("Shift log entry for coagulant changes", C))],
         gaps=[{"title": "Intake turbidity escalation",
                "formal_rule": "Switch to enhanced coagulant dosing when intake turbidity exceeds 20 NTU.",
                "expert_practice": ["Acts when the rate of rise is steep (>2 NTU/h), well before 20 NTU.",
                                    "Checks SDI15 trend on the cartridge filters before changing dose.",
                                    "Checks tide and swell forecast for the next 12 h.",
                                    "Treats Line 2 as under-reading after storms — biofouling on the probe."],
                "capture_href": "/sessions/sess-l2/capture"}],
         action="Validate Rojas's rate-of-rise response from the Line 2 session and capture it as a heuristic."),
    comp("bp-ro", "area-ro", "Reverse Osmosis Operations", ROJAS, ROJAS,
         "Low. Rojas teaches fouling diagnosis; recovery exception still held informally.",
         [grp("formal_knowledge", ("Normalization per ASTM D4516", C), ("CIP procedure, acid and alkaline", C)),
          grp("informal_knowledge", ("SDI moves before ΔP", C), ("Recovery cap above 29 °C feed", P)),
          grp("technical_capability", ("Fouling vs. scaling diagnosis", C), ("Probe testing a pressure vessel", C)),
          grp("decision_judgment", ("When to book an unplanned CIP", C)),
          grp("tools_systems", ("Normalization workbook", C)),
          grp("governance", ("CIP authorization", C))]),
    comp("bp-dosing", "area-dosing", "Chemical Dosing", FUENTES, None,
         "Temperature-based dose correction held by Voss and Fuentes only; not in SOP.",
         [grp("formal_knowledge", ("Antiscalant vendor projection", C), ("SBS dechlorination SOP", C)),
          grp("informal_knowledge", ("Dose follows feed temperature", P), ("No chlorine shock upstream of membranes", C)),
          grp("technical_capability", ("Dose pump calibration drawdown", C), ("LSI calculation from feed chemistry", P)),
          grp("decision_judgment", ("Dose override outside vendor curve", P)),
          grp("relationships", ("Antiscalant supplier technical rep", N)),
          grp("governance", ("Chemical change MOC", C))],
         action="Fuentes re-runs the weekly projection unassisted for 3 weeks."),
    comp("bp-erd", "area-erd", "Energy Recovery", IBARRA, None,
         "Single holder. Mixing estimate lives in Voss's spreadsheet; no owner confirmed.",
         [grp("formal_knowledge", ("PX OEM operating manual", C), ("HP pump curves", C), ("Booster VFD setpoint table", P)),
          grp("informal_knowledge", ("Mixing rises when LP flow drifts", P), ("Rotor noise signature before failure", N)),
          grp("technical_capability", ("PX flow rebalance", P), ("Mixing estimate by conductivity", N)),
          grp("decision_judgment", ("Rebalance vs. rotor inspection", N)),
          grp("relationships", ("PX OEM regional applications engineer", N)),
          grp("tools_systems", ("PX performance workbook", N), ("SEC trend screen", C)),
          grp("governance", ("Area owner confirmed", N), ("Booster setpoint MOC", P))],
         action="Confirm Ibarra as owner; move the PX workbook onto the plant share and walk him through it."),
    comp("bp-maint", "area-maint", "Maintenance Planning", IBARRA, IBARRA,
         "PM planning is local. RCA of plant trips still leans on Voss for data interpretation.",
         [grp("formal_knowledge", ("CMMS PM schedule", C), ("OEM service intervals", C)),
          grp("informal_knowledge", ("Condition-based cartridge change", C), ("Backwash/suction trip interaction", P)),
          grp("technical_capability", ("PM schedule build", C), ("Trip RCA from historian data", P)),
          grp("decision_judgment", ("Deferring PM under demand pressure", P)),
          grp("tools_systems", ("CMMS", C), ("Historian trend export", P)),
          grp("governance", ("Maintenance backlog review", C))],
         levels_from=["cap-pm", "cap-rca"]),
    comp("bp-compliance", "area-compliance", "Water Quality Compliance", FUENTES, FUENTES,
         "Low. Fuentes owns and teaches the monthly return.",
         [grp("formal_knowledge", ("Regulator return template", C), ("Sampling plan", C)),
          grp("informal_knowledge", ("Flag results above 80% of limit", C)),
          grp("technical_capability", ("Lab result reconciliation", C)),
          grp("relationships", ("Regulator compliance officer", C)),
          grp("governance", ("Return sign-off", C))]),
    comp("bp-scada", "area-scada", "SCADA & Alarm Management", ROJAS, None,
         "Alarm-flood response practiced; rationalization of standing alarms not started.",
         [grp("formal_knowledge", ("Alarm philosophy document", C), ("HMI operator manual", C)),
          grp("informal_knowledge", ("First five minutes of an alarm flood", P), ("Which alarms are chronic nuisance", P)),
          grp("technical_capability", ("Alarm shelving", C), ("Switching dosing to local manual", C)),
          grp("decision_judgment", ("When to call the on-call instrument tech", P)),
          grp("tools_systems", ("Alarm historian report", P)),
          grp("governance", ("Alarm shelving authorization", C))]),
    comp("bp-contractors", "area-contractors", "Contractor & Supplier Management", IBARRA, None,
         "Contracts exist; the contacts that make them move are Voss's.",
         [grp("formal_knowledge", ("Framework contracts register", C), ("Permit-to-work procedure", C)),
          grp("informal_knowledge", ("Book diver slots by swell forecast", P)),
          grp("technical_capability", ("Scope-of-work drafting", P)),
          grp("relationships", ("Diving contractor supervisor", N), ("Membrane autopsy lab", N), ("HP pump overhaul shop", P)),
          grp("governance", ("Contractor performance review", N))],
         action="Voss introduces Ibarra to the three contractor leads before 16 Oct."),
    comp("bp-incident", "area-incident", "Incident Response", None, None,
         "Critical. No owner, no local above Observed on shutdown, restart sequence undocumented.",
         [grp("formal_knowledge", ("Emergency shutdown procedure (to trains isolated)", P), ("Regulator incident notification", C)),
          grp("informal_knowledge", ("Throttle distribution to protect permeate storage", P), ("Restart sequencing by train", N)),
          grp("technical_capability", ("Isolating trains in order", N), ("Managing permeate storage", N), ("Restart sequencing", N)),
          grp("decision_judgment", ("When to shut down vs. ride through", N)),
          grp("relationships", ("Grid operator duty engineer", N), ("Network control desk", P)),
          grp("governance", ("Incident commander on each shift", N), ("Shift handover during incident", N))],
         action="Tabletop shutdown scenario with Rojas leading, then supervised drill on Train 4."),
]

write("blueprint", {
    "shell": shell("blueprint"),
    "summary": [m_formal(), m_informal(), m_ownership()],
    "components": COMPONENTS,
})

# ─────────────────────────────── people ───────────────────────────────
def count(pid, lvl):
    if pid == "p-voss":
        return len(CAPS)
    return sum(1 for c in CAPS if (LEVELS[c][pid] >= 4 if lvl == 4 else LEVELS[c][pid] == 6))


def owned_areas(pid):
    return [aref(a[0]) for a in AREAS if a[2] and a[2]["id"] == pid]


DEP = SHELL["departure"]
CARDS = {
    "p-voss": {"person": VOSS, "role_summary": "Seconded process engineer. Designed the pretreatment upgrade and has run every restart since commissioning.",
               "tenure": "22 years' experience · Assignment: month 10 of 12", "departure": DEP,
               "independent_count": count("p-voss", 4), "teachable_count": count("p-voss", 6), "owned_areas": []},
    "p-rojas": {"person": ROJAS, "role_summary": "Leads the four operating shifts. Owns intake, RO and SCADA areas. Candidate trainer for intake turbidity.",
                "tenure": "9 years at the plant", "independent_count": count("p-rojas", 4),
                "teachable_count": count("p-rojas", 6), "owned_areas": owned_areas("p-rojas")},
    "p-fuentes": {"person": FUENTES, "role_summary": "Control room, B shift. Owns dosing and compliance; submits the monthly regulator return.",
                  "tenure": "4 years at the plant", "independent_count": count("p-fuentes", 4),
                  "teachable_count": count("p-fuentes", 6), "owned_areas": owned_areas("p-fuentes")},
    "p-ibarra": {"person": IBARRA, "role_summary": "Plans PM across 4 trains and 2 intake lines. Proposed owner for Energy Recovery.",
                 "tenure": "6 years at the plant", "independent_count": count("p-ibarra", 4),
                 "teachable_count": count("p-ibarra", 6), "owned_areas": owned_areas("p-ibarra")},
}
TRAINER_CARDS = [
    {**CARDS["p-rojas"], "role_summary": "Trains shift operators on membrane fouling diagnosis. Next: intake turbidity response.",
     "tenure": "Trainer since Sep 2026"},
    {**CARDS["p-ibarra"], "role_summary": "Trains planners on preventive maintenance scheduling and condition-based change-outs.",
     "tenure": "Trainer since Jul 2026"},
    {**CARDS["p-fuentes"], "role_summary": "Trains control room staff on the monthly compliance return.",
     "tenure": "Trainer since Apr 2026"},
]
write("people", {"shell": shell("people"), "experts": [CARDS["p-voss"]],
                 "counterparts": [CARDS["p-rojas"], CARDS["p-fuentes"], CARDS["p-ibarra"]],
                 "trainers": TRAINER_CARDS})

# ─────────────────────────────── passport ───────────────────────────────
def rail_for(level, explains=False):
    return {0: 1, 1: 3 if explains else 2, 2: 4, 3: 5, 4: 5, 5: 6, 6: 7}[level]


EV = [
    ("ev-r13", "cap-rca", "work_product", "Wrote RCA-2026-011 for the Train 3 HP pump low-suction trip. Traced it to backwash draw on the filtered-water tank, not the VFD.",
     {"label": "RCA-2026-011", "href": "/knowledge#k-case-t3-trip"}, "2026-09-19",
     "Correct causal chain from historian data; proposed a 3 s trip delay and staggered backwash.", VOSS, "validated", 3, 4,
     "Next: lead the RCA on the next trip without review of the draft."),
    ("ev-r12", "cap-fouling", "peer_teaching", "Walked Fuentes through SDI15 drift from 2.9 to 3.8 on cartridge bank B and the decision to book a Train 2 CIP.",
     sess_link("sess-sdi"), "2026-09-12",
     "Taught the SDI-before-ΔP heuristic unprompted; Fuentes reproduced the reasoning.", VOSS, "validated", 5, 6,
     "Rojas is trainer-ready on fouling diagnosis."),
    ("ev-r11", "cap-erd", "expert_observation", "Assisted Ibarra's PX rebalance on Train 2; read LP/HP flow ratio and called the 103% setpoint.",
     sess_link("sess-erd"), "2026-09-03", "Understands flow balance; did not estimate mixing.", VOSS, "validated", 1, 2, None),
    ("ev-r10", "cap-alarm", "repeated_performance", "Third night-shift alarm flood handled without escalation: 96 alarms, root cause isolated in 7 min.",
     None, "2026-08-29", None, VOSS, "validated", 4, 5, "Candidate to run the alarm-flood drill for B and C shifts."),
    ("ev-r09", "cap-alarm", "scenario_performance", "As shift lead during the 21 Aug flood, directed Fuentes to shelve rack 4 alarms and put dosing in local manual.",
     sess_link("sess-alarm"), "2026-08-21", "Prioritized the dosing blind spot over alarm count.", VOSS, "validated", None, None, None),
    ("ev-r08", "cap-dosing", "real_world_outcome", "Trimmed Line 1 antiscalant from 3.2 to 2.7 mg/L after feed cooled to 24.6 °C; concentrate LSI held at +1.4 for 3 weeks.",
     None, "2026-08-14", "Dose correction consistent with the temperature heuristic.", VOSS, "validated", 3, 4, None),
    ("ev-r07", "cap-rca", "learner_explanation", "Attributed the 2 Aug Train 1 trip to a VFD fault.",
     None, "2026-08-05", "Historian showed a suction dip before the VFD alarm. Explanation not supported.", VOSS, "rejected", None, None,
     "Review historian export before assigning cause."),
    ("ev-r06", "cap-turbidity", "expert_observation", "Stepped FeCl₃ from 3.5 to 6.0 mg/L at 21 NTU on Line 1 and confirmed floc at the media filter inlet in 16 min.",
     None, "2026-07-30", "Follows SOP-PT-04 correctly; acted on the threshold, not the trend.", VOSS, "validated", 2, 3, None),
    ("ev-r05", "cap-compliance", "work_product", "Prepared the July regulator return; boron 0.82 mg/L flagged in the cover note (82% of limit).",
     {"label": "REG-QR-01 template", "href": "/knowledge#k-compliance-return"}, "2026-07-22", None, FUENTES, "validated", 3, 4, None),
    ("ev-r04", "cap-fouling", "repeated_performance", "Four normalizations in a row matched Voss's within 1.5% on Trains 1–4.",
     None, "2026-07-09", None, VOSS, "validated", 4, 5, None),
    ("ev-r03", "cap-shutdown", "learner_explanation", "Explained the three automatic shutdown triggers and why HP pumps stop before the intake.",
     None, "2026-06-18", "Can explain triggers; has not performed any step of a shutdown.", VOSS, "validated", 0, 1,
     "Tabletop scenario before any live drill."),
    ("ev-r02", "cap-pm", "work_product", "Co-built the Q3 cartridge change plan with Ibarra on the condition-based rule.",
     None, "2026-06-02", None, IBARRA, "validated", 2, 3, None),
    ("ev-r01", "cap-contractor", "expert_observation", "Joined Voss on the May diver mobilization call; drafted the permit-to-work.",
     None, "2026-05-11", None, VOSS, "validated", 1, 2, None),
]
evidence = []
for (eid, cid, et, desc, src, on, ai, vb, vs, lb, la, rec) in EV:
    evidence.append({"id": eid, "capability": cap(cid), "evidence_type": et, "description": desc, "source": src,
                     "recorded_on": on, "ai_interpretation": ai, "validated_by": vb, "validation_status": vs,
                     "level_before": lb, "level_after": la, "resulting_recommendation": rec})
assert [e["recorded_on"] for e in evidence] == sorted([e["recorded_on"] for e in evidence], reverse=True)
# check level transitions end at current level
for c in CAPS:
    trans = [e for e in evidence if e["capability"]["id"] == c and e["level_after"] is not None]
    if trans:
        assert trans[0]["level_after"] == LEVELS[c]["p-rojas"], c

NEXT = {"cap-fouling": "Teach the SDI-before-ΔP check to C-shift operators",
        "cap-dosing": "Run the weekly antiscalant projection unassisted",
        "cap-turbidity": "Lead the next storm-event response; Voss observes",
        "cap-alarm": "Run the alarm-flood drill for B and C shifts",
        "cap-erd": "Estimate PX mixing from conductivity on Train 1",
        "cap-pm": "Build the Q4 HP pump PM window with Ibarra reviewing",
        "cap-compliance": "Submit the September return without review",
        "cap-contractor": "Lead the October diver booking",
        "cap-shutdown": "Tabletop shutdown scenario, Rojas leading",
        "cap-rca": "Lead the next trip RCA; Voss reviews the final only"}
EV_COUNT = {"cap-fouling": 11, "cap-dosing": 6, "cap-turbidity": 5, "cap-alarm": 8, "cap-erd": 2, "cap-pm": 4,
            "cap-compliance": 5, "cap-contractor": 2, "cap-shutdown": 1, "cap-rca": 4}
EXPOSURES = {"cap-fouling": 23, "cap-dosing": 14, "cap-turbidity": 9, "cap-alarm": 17, "cap-erd": 3, "cap-pm": 6,
             "cap-compliance": 10, "cap-contractor": 3, "cap-shutdown": 2, "cap-rca": 7}
rows = []
for c in CAPS:
    lvl = LEVELS[c]["p-rojas"]
    mine = [e for e in evidence if e["capability"]["id"] == c and e["validation_status"] == "validated"]
    rows.append({"capability": cap(c), "level": lvl, "rail": rail_for(lvl, explains=(c == "cap-shutdown")),
                 "evidence_count": EV_COUNT[c], "exposures": EXPOSURES[c],
                 "last_demonstrated": mine[0]["recorded_on"] if mine else None,
                 "next_experience": NEXT[c], "trainer_ready": lvl == 6, "changed": False})
    assert EV_COUNT[c] >= len([e for e in evidence if e["capability"]["id"] == c])
write("passport", {"shell": shell("people"), "person": CARDS["p-rojas"], "rows": rows, "evidence": evidence})

# ─────────────────────────────── knowledge ───────────────────────────────
def opts(pairs):
    return [{"value": v, "label": l, "count": n} for v, l, n in pairs]


def cnt(pred):
    return sum(1 for i in K if pred(i))


filters = {
    "areas": opts([(a[0], a[1], cnt(lambda i, a=a: i["area"] and i["area"]["id"] == a[0])) for a in AREAS]),
    "capabilities": opts([(c, n, cnt(lambda i, c=c: i["capability"] and i["capability"]["id"] == c)) for c, n in CAPS.items()]),
    "experts": opts([(p["id"], p["name"], cnt(lambda i, p=p: i["expert"] and i["expert"]["id"] == p["id"])) for p in [VOSS, IBARRA]]),
    "people": opts([(p["id"], p["name"], cnt(lambda i, p=p: any(x["id"] == p["id"] for x in i["people_exposed"]))) for p in LOCALS]),
    "types": opts([(t, TYPE_LABEL[t], cnt(lambda i, t=t: i["type"] == t)) for t in TYPES]),
    "validation_statuses": opts([(s, l, cnt(lambda i, s=s: i["validation_status"] == s))
                                 for s, l in [("validated", "Validated"), ("pending", "Pending expert validation"), ("rejected", "Rejected")]]),
}
GROWTH_DATES = ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30", "2026-05-31", "2026-06-30",
                "2026-07-31", "2026-08-31", "2026-09-26"]
growth = [{"on": d, "total": cnt(lambda i, d=d: i["captured_on"] <= d)} for d in GROWTH_DATES]
write("knowledge", {
    "shell": shell("knowledge"),
    "type_counts": opts([(t, TYPE_LABEL[t], cnt(lambda i, t=t: i["type"] == t)) for t in TYPES]),
    "filters": filters,
    "results_href": "/knowledge/results",
    "results": {"items": K_SORTED, "total": len(K_SORTED), "active": {}},
    "growth": growth,
})
heur = [i for i in K_SORTED if i["type"] == "heuristic"]
write("knowledge_results", {"items": heur, "total": len(heur), "active": {"type": "heuristic"}})

# ─────────────────────────────── propagation ───────────────────────────────
SHIFT = {"id": "grp-shift-ops", "name": "Shift operators", "initials": "SO", "title": "Shift Operator, A–D shifts",
         "kind": "counterpart", "href": "/people"}
local_holders = lambda c: sum(1 for v in LEVELS[c].values() if v >= 1)
propagation = {
    "capability": cap("cap-fouling"),
    "capability_options": opts([(c, n, local_holders(c)) for c, n in CAPS.items()]),
    "nodes": [
        {"id": "n-voss", "person": VOSS, "level": 6, "depth": 0},
        {"id": "n-rojas", "person": ROJAS, "level": LEVELS["cap-fouling"]["p-rojas"], "depth": 1},
        {"id": "n-ibarra", "person": IBARRA, "level": LEVELS["cap-fouling"]["p-ibarra"], "depth": 1},
        {"id": "n-fuentes", "person": FUENTES, "level": LEVELS["cap-fouling"]["p-fuentes"], "depth": 2},
        {"id": "n-shift", "person": SHIFT, "level": None, "depth": 2, "group_label": "Shift operators (6)"},
    ],
    "edges": [
        {"source": "n-voss", "target": "n-rojas", "label": "taught 19 Mar"},
        {"source": "n-voss", "target": "n-ibarra", "label": "co-diagnosed 5 Jun"},
        {"source": "n-rojas", "target": "n-fuentes", "label": "taught 12 Sep"},
        {"source": "n-rojas", "target": "n-shift", "label": "briefed 16 Sep"},
    ],
    "href": "/readiness/propagation",
}
write("propagation", propagation)

# ─────────────────────────────── readiness ───────────────────────────────
DEP_ACTIONS = [
    {"rank": 1, "text": "Tabletop shutdown scenario, then supervised drill on Train 4", "href": "/sessions",
     "capability": cap("cap-shutdown"), "person": ROJAS, "ai_suggested": True},
    {"rank": 2, "text": "Name and confirm owners for Energy Recovery and Incident Response", "href": "/operating-model",
     "capability": None, "person": NAVARRO, "ai_suggested": True},
    {"rank": 3, "text": "Introduce Rojas to the grid operator duty engineer on the direct line", "href": "/knowledge#k-rel-grid",
     "capability": cap("cap-shutdown"), "person": ROJAS, "ai_suggested": True},
    {"rank": 4, "text": "Move Voss's PX performance workbook to the plant share and walk Ibarra through it", "href": "/blueprint?area=area-erd",
     "capability": cap("cap-erd"), "person": IBARRA, "ai_suggested": True},
    {"rank": 5, "text": "Rojas leads a storm-event turbidity response with Voss observing only", "href": "/blueprint?area=area-intake",
     "capability": cap("cap-turbidity"), "person": ROJAS, "ai_suggested": False},
]
validated_k = cnt(lambda i: i["validation_status"] == "validated")
write("readiness", {
    "shell": shell("readiness"),
    "headline": m_om(),
    "metrics": [m_localization(), m_ownership(), m_trainer(), m_formal(), m_informal(), m_dependency_pct(), m_days(), m_k_risk()],
    "weights": [{"component": lbl, "weight": w, "metric_key": key} for lbl, w, key, _ in WEIGHTS],
    "areas": [{"area": aref(a[0]), "formal_pct": a[3], "informal_pct": a[4], "local_owner": a[2], "status": a[7]} for a in AREAS],
    "departure": {
        "departure": DEP,
        "stats": [
            {"label": "OPERATING MODEL AREAS", "display": f"{owned} / {N_AREAS}", "caption": "locally owned", "metric": m_ownership()},
            {"label": "CRITICAL CAPABILITIES", "display": f"{len(LOCALIZED)} / {len(CAPS)}", "caption": "localized at level ≥4", "metric": m_localization()},
            {"label": "LOCAL TRAINERS", "display": f"{len(TEACHABLE)} / {len(CAPS)}", "caption": "capabilities teachable locally"},
            {"label": "EXPERT-DEPENDENT", "display": str(len(DEPENDENT)), "caption": "capabilities with no local at level ≥4", "metric": m_dependent()},
            {"label": "KNOWLEDGE LIBRARY", "display": f"{validated_k} / {len(K)}", "caption": "records validated"},
        ],
        "before_departure": DEP_ACTIONS,
    },
    "flags": [
        {"kind": "no_local_coverage", "label": "No local coverage", "detail": "Emergency Plant Shutdown: highest local level is Observed (Rojas, Fuentes).",
         "area": aref("area-incident"), "capability": cap("cap-shutdown"), "severity": "critical"},
        {"kind": "no_local_owner", "label": "No local owner", "detail": "Incident Response has no owner. Shutdown procedure stops at 'trains isolated'.",
         "area": aref("area-incident"), "capability": None, "severity": "critical"},
        {"kind": "no_local_owner", "label": "No local owner", "detail": "Energy Recovery: Ibarra proposed in August, not confirmed.",
         "area": aref("area-erd"), "capability": None, "severity": "high"},
        {"kind": "single_holder", "label": "Single holder", "detail": "PX mixing estimate and rebalance decision held only by Voss; method lives in a personal workbook.",
         "area": aref("area-erd"), "capability": cap("cap-erd"), "severity": "critical"},
        {"kind": "undocumented_tacit", "label": "Undocumented tacit knowledge", "detail": "Rate-of-rise trigger and Line 2 probe under-read are practiced but not in SOP-PT-04.",
         "area": aref("area-intake"), "capability": cap("cap-turbidity"), "severity": "high"},
        {"kind": "observed_only", "label": "Observed only", "detail": "Rojas has watched one restart (9 Mar) and performed no step of it.",
         "area": aref("area-incident"), "capability": cap("cap-shutdown"), "severity": "high"},
        {"kind": "expert_relationship", "label": "Expert-held relationship", "detail": "Grid operator duty engineer and PX OEM regional engineer deal only with Voss.",
         "area": aref("area-contractors"), "capability": cap("cap-contractor"), "severity": "medium"},
        {"kind": "no_local_trainer", "label": "No local trainer", "detail": "Intake Turbidity Response: Rojas at level 3; no local can teach it to night shift.",
         "area": aref("area-intake"), "capability": cap("cap-turbidity"), "severity": "medium"},
    ],
    "propagation": propagation,
})
print("ok", len(K), "knowledge items; om =", round(om, 4), "erd =", erd_ready)
