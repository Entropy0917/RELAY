# Fixture canon — second fictional engagement (NOT the demo seed)

Purpose: SYNC-1 fixtures for RELAY (planv0.2 §0.5 item 3). They must use a DIFFERENT
engagement than the demo seed so templates are proven data-driven. Never use any name on
the BANLIST in tests/test_no_baked_data.py, nor the demo seed's domain terms.

## Engagement
- id `eng-cwa`, name "Desalination Operations Localization", organization "Coastal Water Authority" (fictional),
  sector "Water utilities", region "Northern coastal region (fictional)".
- Second engagement listed in the switcher: id `eng-nmr`, name "Rolling Mill Maintenance Transfer",
  organization "Norvale Metals" (fictional), sector "Manufacturing", region "Midlands".
- Scenario: a seconded expert is transferring operation of a reverse-osmosis desalination plant to local staff.
  Month 10 of a 12-month assignment. Today = 2026-09-26. Expert departs 2026-11-06 → days_remaining 41.

## People (ids, initials, titles, kind) — href = /people/<id>
- `p-voss` Dr. Helena Voss, "HV", "Senior Desalination Process Engineer", expert (22 years' experience)
- `p-rojas` Mateo Rojas, "MR", "Plant Operations Lead", counterpart — MAIN LEARNER, candidate trainer
- `p-fuentes` Camila Fuentes, "CF", "Control Room Operator", counterpart
- `p-ibarra` Diego Ibarra, "DI", "Maintenance Planner", counterpart
- `p-navarro` Lucía Navarro, "LN", "Program Manager", manager
Personas: `persona-expert` (role expert, p-voss), `persona-learner` (learner, p-rojas),
`persona-pm` (program_manager, p-navarro). current_persona = persona-expert unless the fixture needs otherwise.

## Capabilities (id, name, all critical=true)
cap-fouling Membrane Fouling Diagnosis · cap-dosing Antiscalant Dosing Adjustment · cap-turbidity Intake Turbidity Response ·
cap-alarm SCADA Alarm Triage · cap-erd Energy Recovery Optimization · cap-pm Preventive Maintenance Planning ·
cap-compliance Water Quality Compliance Reporting · cap-contractor Contractor Coordination ·
cap-shutdown Emergency Plant Shutdown · cap-rca Root Cause Analysis of Plant Trips

## Operating-model areas (id, name, owner, formal, informal, capability, trainer, status)
- area-intake Intake & Pretreatment · Rojas · 0.95 · 0.70 · Developing · false · on_track
- area-ro Reverse Osmosis Operations · Rojas · 1.00 · 0.85 · Strong · true · sustainable
- area-dosing Chemical Dosing · Fuentes · 0.90 · 0.60 · Developing · false · transfer_in_progress
- area-erd Energy Recovery · (none, owner_confirmed false) · 0.70 · 0.25 · Limited · false · at_risk
- area-maint Maintenance Planning · Ibarra · 0.85 · 0.55 · Developing · false · transfer_in_progress
- area-compliance Water Quality Compliance · Fuentes · 1.00 · 0.80 · Strong · true · sustainable
- area-scada SCADA & Alarm Management · Rojas · 0.90 · 0.65 · Developing · false · transfer_in_progress
- area-contractors Contractor & Supplier Management · Ibarra · 0.80 · 0.40 · Limited · false · at_risk
- area-incident Incident Response · (none) · 0.75 · 0.20 · None · false · critical
AreaRef.href = /operating-model/areas/<id>. Blueprint href /blueprint?area=<id>.

## Headline numbers (pre-loop)
OM readiness 0.64 "64%" · capability localization 0.60 "60%" (6/10) · locally teachable 3 · expert-dependent 4 ·
41 DAYS. Weights: ownership 0.25, localization 0.30, formal 0.15, informal 0.20, trainer 0.10.
Make formula inputs arithmetically consistent with displays.

## Flagship session
- id `sess-l2`, title "Line 2 intake turbidity event", held_on 2026-09-26,
  context "Turbidity at Line 2 intake rose from 4 to 19 NTU over six hours after an offshore storm".
- Expert Voss, learner Rojas, focus cap-turbidity (Rojas currently level 3 Performed with Supervision).
- Formal rule: "Switch to enhanced coagulant dosing when intake turbidity exceeds 20 NTU."
- Expert practice: acts earlier when the rate of rise, not the absolute value, is steep; checks SDI trend on the
  cartridge filters; checks tide and swell forecast; knows the Line 2 sensor reads low after storms because of
  biofouling on the probe.
- Rojas spotted the rate-of-rise and pre-emptively reduced Line 2 feed flow → evidence for level 4.
- Remaining gap: Emergency Plant Shutdown (cap-shutdown), Rojas level 1 Observed — can explain the triggers,
  has not demonstrated: isolating trains in order, notifying the grid operator, managing permeate storage,
  restart sequencing, regulator notification, shift handover.
- Next activity: tabletop shutdown scenario then supervised drill; Rojas leads, Voss observes.
- Proposed knowledge record: "Watch the Rate of Rise, Not the Threshold" (heuristic).
- Prior sessions (complete): sess-sdi 2026-09-12 "Cartridge filter SDI drift review" (cap-fouling);
  sess-erd 2026-09-03 "Pressure exchanger efficiency loss" (cap-erd, learner Ibarra);
  sess-alarm 2026-08-21 "Night-shift alarm flood triage" (cap-alarm, learner Fuentes).
- Session stage URLs: /sessions/<id>/<stage> where stage ∈ prepare, capture, expert-debrief, learner-debrief,
  synthesis, validation, next-action. Finding action_href: /sessions/sess-l2/findings/<fid>.

## Style
Sound like real process engineers. Specific numbers (not round everything), plausible dates Jan–Sep 2026.
No lorem. Short, dense sentences.
