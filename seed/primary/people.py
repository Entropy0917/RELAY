"""The engagement, and the five people in it.

The organisation is invented. RELAY.txt ("DEMO SCENARIO") is explicit that the
assignment is *inspired by* international technical-assistance work and must
not be presented as, or read as, any real programme or any real person -- so
the organisation, the districts, the clinics and everyone named here are
fictional, and nothing in the corpus claims otherwise.

Roles matter to scoring, not just to display: `app/readiness/inputs.py` treats
counterparts *and* managers as local, and only the expert as not. Efua Darko
is therefore a local owner for readiness purposes even though she never leads
a transfer session -- which is correct, and is the reason she exists.
"""

from __future__ import annotations

from contracts.vocabulary import Role

from seed.timeline import ASSIGNMENT_START, DEPARTURE

ENGAGEMENT_ID = "eng-ashanti-supply"

ENGAGEMENT = {
    "id": ENGAGEMENT_ID,
    "name": "Essential Medicines Supply Chain Handover",
    "org": "Adanse Community Health Network",
    "sector": "Community Health",
    "location": "Ashanti Region, Ghana",
    "mission": (
        "Adanse Community Health Network runs nineteen rural clinics and two "
        "district stores across the Ashanti Region. A nine-month technical "
        "assistance assignment was arranged to reduce stockouts of essential "
        "medicines. The point of the assignment is not that shortages fall "
        "while the specialist is here. It is that the Network can hold them "
        "down on its own after she has gone."
    ),
    "started_on": ASSIGNMENT_START,
    "ends_on": DEPARTURE,
    # Verbatim planv0.2.md section 4 B4. Stated per-engagement rather than
    # inherited so the "how this is calculated" popover has something to show
    # even for an engagement that never tuned anything.
    "readiness_weights": {
        "local_ownership": 0.25,
        "capability_localization": 0.30,
        "formal_transfer": 0.15,
        "informal_transfer": 0.20,
        "trainer_coverage": 0.10,
    },
    "is_primary": True,
}


MITCHELL = "p-mitchell"
KWAME = "p-kwame"
AMA = "p-ama"
KOJO = "p-kojo"
EFUA = "p-efua"

PEOPLE = [
    {
        "id": MITCHELL,
        "name": "Dr. Sarah Mitchell",
        "title": "Public Health Supply Chain Specialist",
        "role": Role.EXPERT,
        "departure_date": DEPARTURE,
        "bio": (
            "Eighteen years in public-health logistics, most of it in "
            "decentralised systems where the data arrives late and the "
            "roads decide what is possible. Placed with the Network for a "
            "nine-month assignment to rebuild the replenishment cycle. Her "
            "own stated objective for the engagement, recorded at intake: "
            "'nobody should need to call me.'"
        ),
    },
    {
        "id": KWAME,
        "name": "Kwame Mensah",
        "title": "Regional Supply Coordinator",
        "role": Role.COUNTERPART,
        "departure_date": None,
        "bio": (
            "Six years with the Network, the last two coordinating supply "
            "across all nineteen clinics. Came up through clinic dispensing, "
            "so he knows what the numbers look like from the shelf as well as "
            "from the extract. Reads the monthly data harder than anyone "
            "else in the office and is usually the first to notice when a "
            "site has gone quiet."
        ),
    },
    {
        "id": AMA,
        "name": "Ama Boateng",
        "title": "Clinic Operations Officer",
        "role": Role.COUNTERPART,
        "departure_date": None,
        "bio": (
            "Runs the clinic-side of reporting: the monthly report and "
            "requisition cycle, the stock cards, the physical count "
            "discipline. Rebuilt the count protocol after the 2025 "
            "reconciliation and now trains new dispensary staff on it "
            "herself. The most reliable source in the Network for whether a "
            "number can be believed."
        ),
    },
    {
        "id": KOJO,
        "name": "Kojo Asare",
        "title": "Health Logistics Officer",
        "role": Role.COUNTERPART,
        "departure_date": None,
        "bio": (
            "Handles the interface with the central medical store and the "
            "transport contractors. Joined eleven months ago from a "
            "commercial distributor, which shows -- he tracks supplier "
            "performance more closely than the Network ever has, and started "
            "the lead-time log that is now the basis for planning."
        ),
    },
    {
        "id": EFUA,
        "name": "Efua Darko",
        "title": "Programme Director",
        "role": Role.MANAGER,
        "departure_date": None,
        "bio": (
            "Accountable for the Network's clinical and operational "
            "performance. Chairs the quarterly supply performance review and "
            "signs off district escalations. Sponsored the assignment and is "
            "the person who has to answer for the supply chain after "
            "Dr. Mitchell's departure."
        ),
    },
]

LOCAL_COUNTERPARTS = (KWAME, AMA, KOJO)
