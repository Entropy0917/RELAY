"""The Clinic 14 session, as it was recorded.

This is the one piece of the corpus an audience reads word for word
(RELAY.txt, "FLAGSHIP DEMO SESSION"; planv0.2.md section 4 B3). Everything the
AI layer later claims to have found has to be visibly *in* here, or the
synthesis step is theatre:

  * the 18-day cover and the 14-day reorder point;
  * a 30-day average masking a 14-day acceleration -- Kwame splits it himself;
  * a physical count that is six days old;
  * the rains starting, and what that did to consumption last year;
  * two consecutive supplier lead times at 19 and 22 days against a
    planning assumption of 14;
  * Kwame reaching the recommendation on his own;
  * Mitchell adding the one move he did not make -- look for genuine surplus
    nearby before paying for an emergency order -- and the four tests that
    separate "has stock" from "has surplus".

It is written to be read aloud: people talk over each other, somebody
recalculates mid-sentence, and nobody speaks in bullet points.
"""

from __future__ import annotations

CLINIC_14_TRANSCRIPT = """\
[Recorded with the consent of both participants. Regional supply office,
Thursday morning. Present: Dr. Sarah Mitchell, Kwame Mensah.]

MITCHELL: -- right. Clinic 14. You pulled the extract?

KWAME: This morning. It's the Thursday file, so it's got Tuesday's count in
it. Not yesterday's.

MITCHELL: Noted. Go on. And tell me what you'd do, not what the sheet says.

KWAME: Okay. AL, the twenty-four-pack. Stock on hand four hundred and twelve.
Thirty-day ADC is twenty-three point one. So it gives them seventeen point
eight days. Call it eighteen.

MITCHELL: And the reorder point at 14 is?

KWAME: Fourteen.

MITCHELL: So?

KWAME: So on paper, nothing. We leave it, they submit the R and R on the
twenty-fifth, stock lands nine, ten days after that.

MITCHELL: Mm.

KWAME: ...I don't want to leave it.

MITCHELL: Tell me why.

KWAME: The average. It's flat because the first half of the month was quiet.
If I split it -- give me a second.

[keyboard]

KWAME: Days one to fifteen, ADC nineteen point four. Days sixteen to thirty,
twenty-eight point six. That's nearly fifty per cent up.

MITCHELL: So your eighteen days is --

KWAME: It's not eighteen. At twenty-eight point six it's fourteen point four.
They're at the threshold today. Not next week. Today.

MITCHELL: Good. What else is in that number that you don't like?

KWAME: The count itself. Four-one-two is a physical count, but it's dated --
hold on -- the fourth. That's six days. Six days at twenty-eight a day is a
hundred and seventy packs of movement that the number doesn't know about, so
the figure is wrong --

MITCHELL: It's not wrong.

KWAME: No. Sorry, you're right. It isn't wrong, it's stale. And if it's
drifted it's drifted one way.

MITCHELL: How would you know which way?

KWAME: I wouldn't, from here. I'd call Esi and have her count the AL shelf
before I do anything else. Twenty minutes.

MITCHELL: Do that first. What's the third thing?

KWAME: The rain.

MITCHELL: Say more.

KWAME: It started eight days ago. Nine. And 14 sits low -- the whole catchment
floods, you've seen the road. Last year their ACT consumption more than
doubled between the first week of the rains and the peak. I'd want to check
the exact figure. But roughly. So twenty-eight isn't the ceiling. It's the
start of the curve.

MITCHELL: That is the part most people miss. Anything on the supply side?

KWAME: Yes, and this one worries me more. The last two orders out of CMS came
in at nineteen days and twenty-two days. Our planning assumption is fourteen.

MITCHELL: Both of them?

KWAME: Both. The one before that was fifteen. So it isn't a bad week, it's a
direction.

MITCHELL: And if you assume fourteen and they take twenty-two --

KWAME: Then fourteen days of cover is eight days short. With consumption
flat, which it isn't.

MITCHELL: So what's your recommendation?

KWAME: Don't wait for the threshold. The threshold assumes three things:
consumption is steady, the count is current, and the supplier does what it
said it would. None of the three is true at 14 this week. I'd treat them as
already below reorder and act today.

MITCHELL: I agree with you. And I want you to notice you got there without me.
That's the first time on one of these.

KWAME: [laughs]

MITCHELL: Can I put one thing in front of it, though?

KWAME: Please.

MITCHELL: Before you raise an emergency order -- look sideways first. An
emergency requisition costs you three things. The freight premium, which
somebody pays. Your credibility with CMS the next time you tell them
something is urgent. And about two weeks of somebody's attention. A
redistribution costs a driver and a form.

KWAME: Clinic 9 has AL. They were over four months of stock at the last
review, I think.

MITCHELL: Maybe. "Has stock" and "has surplus" are not the same sentence,
though. What would you need to know before you moved a single pack out of 9?

KWAME: Whether they're going to need it.

MITCHELL: How would you establish that?

KWAME: Their consumption trend, not their stock level. Honestly -- the same
thing I just did to 14. Their ADC, whether it's moving, their own lead time.

MITCHELL: And?

KWAME: Expiry. If the AL at 9 is short-dated, then moving it to a
lower-volume site is just choosing where it gets written off.

MITCHELL: Good. That one catches people.

KWAME: And the road. If the catchment is flooding then the reason 14 needs
it is the same reason the truck can't reach them.

MITCHELL: That is exactly it. You're lucky on cold chain -- AL doesn't care.
You are not lucky on the road. There's also an approval.

KWAME: District. Though I'd have to check whether an inter-facility transfer
goes through the DHMT or the regional store.

MITCHELL: Find out. Don't be looking that up on the day you need it.

KWAME: No.

MITCHELL: Alright. What are you actually doing this afternoon?

KWAME: Physical count at 14 first -- everything else is guessing until that
lands. Then I pull 9 and 22, consumption and expiry, and the road report. If 9
has real surplus and the road is passable I propose a transfer. If not I go to
CMS, and I go today, not on the twenty-fifth, because if they're running at
twenty-two days then I need those twenty-two days to start now.

MITCHELL: And if the district says no to the transfer?

KWAME: Then I've lost half a day and I raise the order anyway.

MITCHELL: Then you've lost nothing. Go.

[ends]
"""


CLINIC_14_NOTES = """\
Kwame led throughout; I asked six questions and answered none of them.

Worth recording: he found the consumption split on his own, and he found it by
distrusting the average rather than by checking a rule. That is the difference
between someone who applies the SOP and someone who can be left with the
region.

He did not go looking for surplus at neighbouring sites before reaching for an
emergency order. Not a gap in judgment -- he simply has not had to run a
redistribution. That is the next thing to hand over, and it should be his to
lead, not mine.
"""
