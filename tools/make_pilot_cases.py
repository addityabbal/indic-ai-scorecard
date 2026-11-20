"""Writes cases/hinglish.jsonl: the 30-case Hinglish pilot (6 tasks x 5 cases).

Drafted by Claude and marked reviewed_by=None until a native speaker reviews them (plan: Aditya
reviews Hindi and Hinglish). Passages are written from scratch from public scheme facts.
Re-run only to regenerate the pilot; edit cases/hinglish.jsonl directly after review.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "cases" / "hinglish.jsonl"

PMK = ("PM-Kisan scheme: eligible farmer families get Rs 6,000 per year from the central government. "
       "The money is paid in three equal instalments of Rs 2,000 each, directly into the farmer's bank account. "
       "The bank account must be linked with Aadhaar, and e-KYC must be completed to receive instalments.")
PMSG = ("PM Surya Ghar Muft Bijli Yojana: households that put solar panels on their roof get a central subsidy of "
        "Rs 30,000 per kW for the first 2 kW and Rs 18,000 for the third kW. The subsidy is capped at Rs 78,000. "
        "Households can get up to 300 units of free electricity every month. Apply on the national portal with your "
        "electricity bill and bank details.")
PMJAY = ("Ayushman Bharat PM-JAY gives eligible families health cover of Rs 5 lakh per family per year for hospital "
         "treatment at empanelled government and private hospitals. Treatment is cashless and paperless at the hospital. "
         "There is no limit on family size or age.")
SSY = ("Sukanya Samriddhi Yojana: parents can open the account for a girl child below 10 years of age at a post office "
       "or bank. The minimum deposit is Rs 250 in a year and the maximum is Rs 1.5 lakh in a year. Deposits are made "
       "for 15 years, and the account matures 21 years after it is opened.")
UJJ = ("Pradhan Mantri Ujjwala Yojana gives a deposit-free LPG connection to adult women from poor households. "
       "The connection is in the woman's name. She needs Aadhaar and a bank account to apply at an LPG distributor.")

cases: list[dict] = []


def add(task, n, text, expected=None, context=None, checks=None, rubric=None, reference=None, instruction=None):
    cases.append({
        "id": f"hinglish-{task}-{n:03d}", "lang": "hinglish", "script": "latn", "task": task,
        "input": text, "instruction": instruction, "context": context, "expected": expected,
        "reference": reference, "checks": checks, "rubric": rubric,
        "author": "draft-claude", "reviewed_by": None,
    })


SUP_R = ("A good reply is polite, gives 1-3 concrete steps the user can take now, does not invent offers or "
         "amounts, and is in Roman-script Hinglish like the user.")
for i, msg in enumerate([
    "bhai mera recharge ho gaya par data nahi aaya, kya karu?",
    "order kiya tha 5 din pehle, abhi tak deliver nahi hua, tracking bhi update nahi ho raha",
    "UPI se payment kiya, paise kat gaye lekin merchant bol raha nahi mila. ab kya?",
    "bijli ka bill is mahine double aaya hai, meter galat chal raha lagta hai",
    "gas cylinder book kiya tha, delivery boy bola OTP do, mujhe OTP aaya hi nahi",
], 1):
    add("support", i, msg, checks=["script_match", "judge"], rubric=SUP_R)

for i, (q, ctx, facts) in enumerate([
    ("PM-Kisan mein saal ke kitne paise milte hai aur kitni kist mein?", PMK, ["6,000", ["3", "three", "teen", "तीन"]]),
    ("solar lagwaya 3 kW ka to subsidy kitni milegi total?", PMSG, ["78,000"]),
    ("Ayushman card se kitne tak ka ilaaj free hota hai?", PMJAY, ["5 lakh"]),
    ("beti ka Sukanya account kitni umar tak khol sakte hai aur minimum kitna jama karna padta hai?", SSY, ["10", "250"]),
    ("free bijli kitni units milti hai har mahine is yojana mein?", PMSG, ["300"]),
], 1):
    add("passage_qa", i, q, context=ctx, expected={"facts": facts},
        checks=["facts_present", "no_invented_numbers", "script_match", "judge"],
        rubric="Correct if it states the facts from the passage, adds no numbers that are not in the passage, "
               "and answers in Roman-script Hinglish.")

EXTRACT_I = "Is message se JSON nikalo with fields: name, paid_inr, due_inr, day. Sirf JSON do."
for i, (msg, exp) in enumerate([
    ("Ramesh ne 450 rs diye 12 tareekh ko, baaki 200 udhaar", {"name": "Ramesh", "paid_inr": 450, "due_inr": 200, "day": 12}),
    ("sunita bhabhi 3 tarik ko aayi thi, 1200 me se 800 diye, 400 baad me dengi", {"name": "Sunita", "paid_inr": 800, "due_inr": 400, "day": 3}),
    ("Pappu ka hisaab: 25 ko 150 rupay cash, 50 bacha hai", {"name": "Pappu", "paid_inr": 150, "due_inr": 50, "day": 25}),
    ("aaj 7 tareekh, Imran bhai ne poora 900 de diya, kuch baaki nahi", {"name": "Imran", "paid_inr": 900, "due_inr": 0, "day": 7}),
    ("Lakshmi aunty 19 ko 2000 ka saaman le gayi, 1500 diya, 500 next week", {"name": "Lakshmi", "paid_inr": 1500, "due_inr": 500, "day": 19}),
], 1):
    add("extract", i, msg, instruction=EXTRACT_I, expected=exp, checks=["json_fields"])

LABELS = ["bill_amount_query", "payment_failed", "new_connection", "outage_complaint", "plan_change"]
INTENT_I = "Is message ka intent batao. Sirf ek label likho in mein se: " + ", ".join(LABELS)
for i, (msg, label) in enumerate([
    ("is mahine ka current bill kitna aaya hai?", "bill_amount_query"),
    ("payment kiya par app pe failed dikha raha hai, paise bhi kat gaye", "payment_failed"),
    ("naye ghar ke liye meter lagwana hai, kaise apply karu", "new_connection"),
    ("subah se light nahi hai pure mohalle mein", "outage_complaint"),
    ("mujhe sasta wala plan chahiye, abhi wala bahut mehenga hai", "plan_change"),
], 1):
    add("intent", i, msg, instruction=INTENT_I, expected={"label": label, "labels": LABELS}, checks=["label_match"])

SIMPLE_I = "Isko simple Hinglish mein samjhao jaise 7th class ke bachche ko, 2-3 line mein."
for i, (notice, ref) in enumerate([
    ("Notice is hereby given that consumers failing to remit outstanding dues within 15 days of the issuance of this "
     "notice shall be liable for disconnection of supply without further intimation.",
     "Agar aapne 15 din ke andar baaki bill nahi bhara, to bina bataye aapki bijli kaat di jayegi."),
    ("The applicant is required to furnish self-attested copies of identity proof and address proof along with the duly "
     "filled application form at the time of submission.",
     "Form jama karte waqt apna ID proof aur address proof ki copy do, jis par aapne khud sign kiya ho."),
    ("Subsidy shall be credited to the beneficiary's bank account subsequent to physical verification of the installed "
     "system by the authorised agency.",
     "Jab sarkari team aakar lagaya hua system check kar legi, uske baad subsidy ke paise aapke bank khate mein aayenge."),
    ("Instalments shall be withheld in cases where e-KYC has not been completed or the bank account is not seeded with Aadhaar.",
     "Agar aapka e-KYC nahi hua ya bank khata Aadhaar se nahi juda, to agli kist ke paise ruk jayenge."),
    ("Consumers are advised that tampering with the metering equipment constitutes an offence punishable under the "
     "applicable provisions of law.",
     "Bijli ke meter se chhed-chhaad karna kanoon mein jurm hai, iske liye saza ho sakti hai."),
], 1):
    add("simplify", i, notice, instruction=SIMPLE_I, reference=ref, checks=["script_match", "chrf", "judge"],
        rubric="Good if a 12-year-old can follow it, keeps every key point of the notice (deadlines, conditions, "
               "consequences), adds nothing new, and is Roman-script Hinglish.")

for i, (q, ctx) in enumerate([
    ("PM-Kisan ki agli kist kis date ko aayegi?", PMK),
    ("Sukanya account pe kitna byaaj milta hai?", SSY),
    ("solar subsidy ka paisa kitne din mein aata hai?", PMSG),
    ("Ujjwala mein cylinder refill kitne ka padega?", UJJ),
    ("Ayushman card banane ka last date kya hai?", PMJAY),
], 1):
    add("refuse", i, q, context=ctx, checks=["refusal", "no_invented_numbers", "script_match"],
        rubric="The passage does not contain the answer; a good reply says the passage does not say, and invents no figure or date.")

OUT.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases), encoding="utf-8")
print(f"wrote {len(cases)} cases")
