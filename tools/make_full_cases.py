"""Draft the full 300-case set: 6 tasks x 5 language variants x 10 cases.

Drafted by Claude (author "draft-claude", reviewed_by null). The plan's next step is a native
speaker rewriting each case so it sounds like a real message, then setting reviewed_by.

- Hinglish: keeps the published pilot cases 001-005 untouched and adds 006-010 per task.
- Hindi, Marathi, Bengali: 10 per task in their own script.
- Tamil: Tamil script for cases 001-007, romanized Tamil for 008-010 (plan: 3 of 10 romanized).
- The same 10 real-world scenarios per task run across languages, so results can be compared.
- Passages are in English (as most official scheme pages are), questions in the user's language.

Hidden set: cases 006 and 010 of every task and language (60 cases, 20%) go to cases/hidden.jsonl,
which is git-ignored and committed only encrypted (tools/hidden_set.py).

    python tools/make_full_cases.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases"
HIDDEN_NUMBERS = {6, 10}

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

NOTICES = [
    "Notice is hereby given that consumers failing to remit outstanding dues within 15 days of the issuance of this "
    "notice shall be liable for disconnection of supply without further intimation.",
    "The applicant is required to furnish self-attested copies of identity proof and address proof along with the duly "
    "filled application form at the time of submission.",
    "Subsidy shall be credited to the beneficiary's bank account subsequent to physical verification of the installed "
    "system by the authorised agency.",
    "Instalments shall be withheld in cases where e-KYC has not been completed or the bank account is not seeded with Aadhaar.",
    "Consumers are advised that tampering with the metering equipment constitutes an offence punishable under the "
    "applicable provisions of law.",
    "Applications received after the last date shall not be entertained under any circumstances.",
    "The benefit is admissible only to households whose annual income does not exceed Rs 2.5 lakh.",
    "Consumers shall ensure that the metering equipment is accessible to authorised personnel for the purpose of monthly reading.",
    "Any change in the bank account details of the beneficiary must be intimated to the office within 30 days.",
    "Duplicate cards will be issued upon payment of the prescribed fee of Rs 50 and submission of an affidavit.",
]

# (paid_inr, due_inr, day) for the 10 ledger messages, same in every language.
LEDGER = [(450, 200, 12), (800, 400, 3), (150, 50, 25), (900, 0, 7), (1500, 500, 19),
          (300, 100, 9), (2500, 0, 15), (600, 400, 28), (1000, 250, 4), (750, 250, 21)]
LABELS = ["bill_amount_query", "payment_failed", "new_connection", "outage_complaint", "plan_change"]
INTENTS = LABELS * 2
QA_CONTEXT = [PMK, PMSG, PMJAY, SSY, PMSG, PMK, SSY, SSY, PMSG, SSY]
REFUSE_CONTEXT = [PMK, SSY, PMSG, UJJ, PMJAY, PMK, SSY, PMSG, UJJ, PMJAY]


def qa_facts(three: list[str]) -> list[list]:
    return [["6,000", three], ["78,000"], ["5 lakh"], ["10", "250"], ["300"], ["2,000"],
            [["1.5 lakh", "1,50,000", "150000"]], ["21"], ["30,000"], ["15"]]


LANG = {
    "hinglish": {"name": "Hinglish (Roman-script Hindi-English mix)", "script": "latn"},
    "hi": {"name": "Hindi in Devanagari", "script": "deva"},
    "mr": {"name": "Marathi in Devanagari", "script": "deva"},
    "ta": {"name": "Tamil in Tamil script", "script": "taml"},
    "ta-latn": {"name": "Tamil written in Roman letters", "script": "latn"},
    "bn": {"name": "Bengali in Bengali script", "script": "beng"},
}

# ------------------------------------------------------------------ language packs
# Each pack: 10 entries per task. For Hinglish only entries 6-10 are new (pilot keeps 1-5).

PACKS: dict[str, dict] = {}

PACKS["hinglish"] = {
    "extract_i": "Is message se JSON nikalo with fields: name, paid_inr, due_inr, day. Sirf JSON do.",
    "intent_i": "Is message ka intent batao. Sirf ek label likho in mein se: ",
    "simplify_i": "Isko simple Hinglish mein samjhao jaise 7th class ke bachche ko, 2-3 line mein.",
    "three": ["3", "three", "teen", "तीन"],
    "support": [None] * 5 + [
        "ration card mein mera naam galat chhapa hai, kaise theek karwaun?",
        "ATM se paise nahi nikle par account se kat gaye",
        "teen din se paani nahi aa raha, complaint kahan karun?",
        "mobile number Aadhaar se link karna hai, kya karna padega?",
        "online class ke liye net bahut slow chal raha hai, kya karun?",
    ],
    "qa": [None] * 5 + [
        "PM-Kisan ki ek kist kitne ki hoti hai?",
        "Sukanya account mein saal mein zyada se zyada kitna daal sakte hai?",
        "Sukanya account kitne saal mein mature hota hai?",
        "solar mein pehle 2 kW pe har kW ka kitna subsidy milta hai?",
        "Sukanya mein kitne saal tak paise jama karne padte hai?",
    ],
    "extract": [None] * 5 + [
        ("Gopal bhaiya ne 9 tareekh ko 300 diye, 100 abhi baaki", "Gopal"),
        ("Meena didi ne 15 ko poora 2500 chuka diya", "Meena"),
        ("Raju 28 tarik ko aaya, 1000 ka maal liya, 600 diye", "Raju"),
        ("Salma ji 4 tareekh: 1250 me se 1000 diye, 250 udhaar", "Salma"),
        ("Kishore ne 21 ko 750 diye, 250 abhi dene hai", "Kishore"),
    ],
    "intent": [None] * 5 + [
        "pichle mahine ka bill kitna tha batao",
        "recharge ka paisa kat gaya par recharge hua nahi",
        "dukaan ke liye commercial connection chahiye",
        "transformer jal gaya hai, do din se bijli nahi",
        "mera plan postpaid se prepaid mein badalna hai",
    ],
    "simplify": [None] * 5 + [
        "Last date ke baad aaya form kisi bhi haal mein nahi liya jayega.",
        "Yeh fayda sirf unhi gharon ko milega jinki saal ki kamai 2.5 lakh rupaye ya usse kam hai.",
        "Har mahine meter padhne aane wale karmachari ko meter tak pahunchne dena aapki zimmedari hai.",
        "Agar aapka bank khata badle, to 30 din ke andar office ko batana zaroori hai.",
        "Duplicate card chahiye to 50 rupaye fees bharo aur ek affidavit (shapath patra) jama karo.",
    ],
    "refuse": [None] * 5 + [
        "kya bina zameen wale kisan ko bhi PM-Kisan milta hai?",
        "kya do betiyon ke liye alag alag Sukanya account khul sakta hai?",
        "solar panel kis company ka lagwana chahiye?",
        "Ujjwala ki helpline number kya hai?",
        "mere sheher mein kaun se hospital Ayushman mein hai?",
    ],
}

PACKS["hi"] = {
    "extract_i": "इस संदेश से JSON निकालें, फ़ील्ड: name, paid_inr, due_inr, day. नाम वैसे ही लिखें जैसे संदेश में है। सिर्फ़ JSON दें।",
    "intent_i": "इस संदेश का इरादा बताएँ। इनमें से सिर्फ़ एक लेबल लिखें: ",
    "simplify_i": "इसे आसान हिंदी में समझाएँ, जैसे सातवीं कक्षा के बच्चे को, 2-3 पंक्तियों में।",
    "three": ["3", "तीन", "three"],
    "support": [
        "मेरा रिचार्ज हो गया पर डेटा नहीं आया, क्या करूँ?",
        "पाँच दिन पहले ऑर्डर किया था, अब तक डिलीवरी नहीं हुई, ट्रैकिंग भी अपडेट नहीं हो रही।",
        "यूपीआई से पेमेंट किया, पैसे कट गए लेकिन दुकानदार कह रहा है मिला नहीं। अब क्या करूँ?",
        "इस महीने बिजली का बिल दोगुना आया है, लगता है मीटर गलत चल रहा है।",
        "गैस सिलेंडर बुक किया था, डिलीवरी वाला ओटीपी माँग रहा है पर मुझे ओटीपी आया ही नहीं।",
        "राशन कार्ड में मेरा नाम गलत छपा है, कैसे ठीक करवाऊँ?",
        "एटीएम से पैसे नहीं निकले पर खाते से कट गए।",
        "तीन दिन से पानी नहीं आ रहा, शिकायत कहाँ करूँ?",
        "मोबाइल नंबर आधार से जोड़ना है, क्या करना होगा?",
        "ऑनलाइन क्लास के लिए इंटरनेट बहुत धीमा चल रहा है, क्या करूँ?",
    ],
    "qa": [
        "पीएम-किसान में साल में कितने पैसे मिलते हैं और कितनी किस्तों में?",
        "मैंने 3 किलोवाट का सोलर लगवाया है, कुल कितनी सब्सिडी मिलेगी?",
        "आयुष्मान कार्ड से कितने तक का इलाज मुफ़्त होता है?",
        "सुकन्या खाता बेटी की किस उम्र तक खुल सकता है और कम से कम कितना जमा करना होता है?",
        "इस योजना में हर महीने कितनी यूनिट बिजली मुफ़्त मिलती है?",
        "पीएम-किसान की एक किस्त कितने की होती है?",
        "सुकन्या खाते में साल में ज़्यादा से ज़्यादा कितना जमा कर सकते हैं?",
        "सुकन्या खाता कितने साल में मैच्योर होता है?",
        "सोलर में पहले 2 किलोवाट पर हर किलोवाट की कितनी सब्सिडी मिलती है?",
        "सुकन्या में कितने साल तक पैसे जमा करने पड़ते हैं?",
    ],
    "extract": [
        ("रमेश ने 12 तारीख को 450 रुपये दिए, बाकी 200 उधार।", "रमेश"),
        ("सुनीता भाभी 3 तारीख को आई थीं, 1200 में से 800 दिए, 400 बाद में देंगी।", "सुनीता"),
        ("पप्पू का हिसाब: 25 को 150 रुपये नकद, 50 बाकी।", "पप्पू"),
        ("आज 7 तारीख, इमरान भाई ने पूरे 900 दे दिए, कुछ बाकी नहीं।", "इमरान"),
        ("लक्ष्मी आंटी 19 को 2000 का सामान ले गईं, 1500 दिए, 500 अगले हफ़्ते।", "लक्ष्मी"),
        ("गोपाल भैया ने 9 तारीख को 300 दिए, 100 अभी बाकी हैं।", "गोपाल"),
        ("मीना दीदी ने 15 को पूरे 2500 चुका दिए।", "मीना"),
        ("राजू 28 तारीख को आया, 1000 का माल लिया, 600 दिए।", "राजू"),
        ("सलमा जी 4 तारीख: 1250 में से 1000 दिए, 250 उधार।", "सलमा"),
        ("किशोर ने 21 को 750 दिए, 250 अभी देने हैं।", "किशोर"),
    ],
    "intent": [
        "इस महीने का बिजली बिल कितना आया है?",
        "पेमेंट किया पर ऐप पर फेल दिखा रहा है, पैसे भी कट गए।",
        "नए घर में मीटर लगवाना है, कैसे आवेदन करूँ?",
        "सुबह से पूरे मोहल्ले में बिजली नहीं है।",
        "मुझे सस्ता प्लान चाहिए, अभी वाला बहुत महंगा है।",
        "पिछले महीने का बिल कितना था बताइए।",
        "रिचार्ज का पैसा कट गया पर रिचार्ज नहीं हुआ।",
        "दुकान के लिए कमर्शियल कनेक्शन चाहिए।",
        "ट्रांसफ़ॉर्मर जल गया है, दो दिन से बिजली नहीं है।",
        "मेरा प्लान पोस्टपेड से प्रीपेड में बदलना है।",
    ],
    "simplify": [
        "अगर आपने 15 दिन के अंदर बकाया बिल नहीं भरा, तो बिना बताए आपकी बिजली काट दी जाएगी।",
        "फ़ॉर्म जमा करते समय अपने पहचान पत्र और पते के सबूत की ऐसी कॉपी दें जिस पर आपने खुद साइन किया हो।",
        "जब सरकारी टीम आकर लगाया हुआ सिस्टम जाँच लेगी, उसके बाद सब्सिडी के पैसे आपके बैंक खाते में आएँगे।",
        "अगर आपका ई-केवाईसी नहीं हुआ या बैंक खाता आधार से नहीं जुड़ा, तो किस्त के पैसे रुक जाएँगे।",
        "बिजली के मीटर से छेड़छाड़ करना कानूनन अपराध है, इसके लिए सज़ा हो सकती है।",
        "आख़िरी तारीख के बाद आया फ़ॉर्म किसी भी हालत में नहीं लिया जाएगा।",
        "यह फ़ायदा सिर्फ़ उन्हीं घरों को मिलेगा जिनकी साल की कमाई 2.5 लाख रुपये या उससे कम है।",
        "हर महीने मीटर पढ़ने आने वाले कर्मचारी को मीटर तक पहुँचने देना आपकी ज़िम्मेदारी है।",
        "अगर आपका बैंक खाता बदलता है, तो 30 दिन के अंदर दफ़्तर को बताना ज़रूरी है।",
        "डुप्लिकेट कार्ड के लिए 50 रुपये फ़ीस भरें और एक हलफ़नामा जमा करें।",
    ],
    "refuse": [
        "पीएम-किसान की अगली किस्त किस तारीख को आएगी?",
        "सुकन्या खाते पर कितना ब्याज मिलता है?",
        "सोलर सब्सिडी का पैसा कितने दिन में आता है?",
        "उज्ज्वला में सिलेंडर रीफ़िल कितने का पड़ेगा?",
        "आयुष्मान कार्ड बनाने की आख़िरी तारीख क्या है?",
        "क्या बिना ज़मीन वाले किसान को भी पीएम-किसान मिलता है?",
        "क्या दो बेटियों के लिए अलग-अलग सुकन्या खाते खुल सकते हैं?",
        "सोलर पैनल किस कंपनी का लगवाना चाहिए?",
        "उज्ज्वला की हेल्पलाइन नंबर क्या है?",
        "मेरे शहर में कौन से अस्पताल आयुष्मान में शामिल हैं?",
    ],
}

PACKS["mr"] = {
    "extract_i": "या संदेशातून JSON काढा, फील्ड: name, paid_inr, due_inr, day. नाव संदेशात आहे तसेच लिहा. फक्त JSON द्या.",
    "intent_i": "या संदेशाचा हेतू सांगा. यापैकी फक्त एक लेबल लिहा: ",
    "simplify_i": "हे सोप्या मराठीत समजवा, सातवीतल्या मुलाला सांगतो तसे, 2-3 ओळींत.",
    "three": ["3", "तीन", "three"],
    "support": [
        "माझं रिचार्ज झालं पण डेटा आला नाही, काय करू?",
        "पाच दिवसांपूर्वी ऑर्डर केली होती, अजून डिलिव्हरी झाली नाही, ट्रॅकिंगही अपडेट होत नाहीये.",
        "यूपीआयने पेमेंट केलं, पैसे कापले गेले पण दुकानदार म्हणतो मिळाले नाहीत. आता काय करू?",
        "या महिन्याचं वीज बिल दुप्पट आलं आहे, मीटर चुकीचं चालतंय असं वाटतं.",
        "गॅस सिलेंडर बुक केला होता, डिलिव्हरीवाला ओटीपी मागतोय पण मला ओटीपी आलाच नाही.",
        "रेशन कार्डवर माझं नाव चुकीचं छापलं आहे, कसं दुरुस्त करू?",
        "एटीएममधून पैसे निघाले नाहीत पण खात्यातून कापले गेले.",
        "तीन दिवसांपासून पाणी येत नाही, तक्रार कुठे करू?",
        "मोबाइल नंबर आधारशी जोडायचा आहे, काय करावं लागेल?",
        "ऑनलाइन क्लाससाठी इंटरनेट खूप हळू चालतंय, काय करू?",
    ],
    "qa": [
        "पीएम-किसानमध्ये वर्षाला किती पैसे मिळतात आणि किती हप्त्यांत?",
        "मी 3 किलोवॅटचं सोलर बसवलं आहे, एकूण किती सबसिडी मिळेल?",
        "आयुष्मान कार्डने किती रुपयांपर्यंतचे उपचार मोफत होतात?",
        "सुकन्या खातं मुलीच्या किती वयापर्यंत उघडता येतं आणि किमान किती भरावे लागतात?",
        "या योजनेत दर महिन्याला किती युनिट वीज मोफत मिळते?",
        "पीएम-किसानचा एक हप्ता किती रुपयांचा असतो?",
        "सुकन्या खात्यात वर्षाला जास्तीत जास्त किती भरू शकतो?",
        "सुकन्या खातं किती वर्षांनी मॅच्युअर होतं?",
        "सोलरमध्ये पहिल्या 2 किलोवॅटसाठी प्रत्येक किलोवॅटला किती सबसिडी मिळते?",
        "सुकन्यामध्ये किती वर्षं पैसे भरावे लागतात?",
    ],
    "extract": [
        ("रमेशने 12 तारखेला 450 रुपये दिले, बाकी 200 उधार.", "रमेश"),
        ("सुनीता ताई 3 तारखेला आल्या होत्या, 1200 पैकी 800 दिले, 400 नंतर देणार.", "सुनीता"),
        ("पप्पूचा हिशोब: 25 तारखेला 150 रुपये रोख, 50 बाकी.", "पप्पू"),
        ("आज 7 तारीख, इम्रान भाऊंनी पूर्ण 900 दिले, काही बाकी नाही.", "इम्रान"),
        ("लक्ष्मी मावशी 19 तारखेला 2000 चं सामान घेऊन गेल्या, 1500 दिले, 500 पुढच्या आठवड्यात.", "लक्ष्मी"),
        ("गोपाळ काकांनी 9 तारखेला 300 दिले, 100 अजून बाकी.", "गोपाळ"),
        ("मीना ताईंनी 15 तारखेला पूर्ण 2500 भरले.", "मीना"),
        ("राजू 28 तारखेला आला, 1000 चा माल घेतला, 600 दिले.", "राजू"),
        ("सलमा 4 तारखेला: 1250 पैकी 1000 दिले, 250 उधार.", "सलमा"),
        ("किशोरने 21 तारखेला 750 दिले, 250 अजून द्यायचे आहेत.", "किशोर"),
    ],
    "intent": [
        "या महिन्याचं वीज बिल किती आलं आहे?",
        "पेमेंट केलं पण ॲपवर फेल दाखवतंय, पैसेही कापले गेले.",
        "नवीन घरात मीटर बसवायचं आहे, अर्ज कसा करू?",
        "सकाळपासून संपूर्ण गल्लीत वीज नाही.",
        "मला स्वस्त प्लॅन हवा आहे, सध्याचा खूप महाग आहे.",
        "मागच्या महिन्याचं बिल किती होतं ते सांगा.",
        "रिचार्जचे पैसे कापले गेले पण रिचार्ज झालं नाही.",
        "दुकानासाठी कमर्शियल कनेक्शन हवं आहे.",
        "ट्रान्सफॉर्मर जळाला आहे, दोन दिवसांपासून वीज नाही.",
        "माझा प्लॅन पोस्टपेडवरून प्रीपेडमध्ये बदलायचा आहे.",
    ],
    "simplify": [
        "15 दिवसांत थकलेलं बिल भरलं नाही, तर न सांगता तुमची वीज कापली जाईल.",
        "अर्ज देताना ओळखपत्र आणि पत्त्याच्या पुराव्याच्या प्रती द्या, ज्यावर तुम्ही स्वतः सही केली आहे.",
        "सरकारी टीम येऊन बसवलेली यंत्रणा तपासेल, त्यानंतर सबसिडीचे पैसे तुमच्या बँक खात्यात येतील.",
        "तुमचं ई-केवायसी झालं नसेल किंवा बँक खातं आधारशी जोडलेलं नसेल, तर हप्त्याचे पैसे थांबवले जातील.",
        "वीज मीटरशी छेडछाड करणं हा कायद्याने गुन्हा आहे, त्यासाठी शिक्षा होऊ शकते.",
        "शेवटच्या तारखेनंतर आलेला अर्ज कोणत्याही परिस्थितीत घेतला जाणार नाही.",
        "हा फायदा फक्त अशाच घरांना मिळेल ज्यांचं वार्षिक उत्पन्न 2.5 लाख रुपये किंवा त्यापेक्षा कमी आहे.",
        "दर महिन्याला मीटर वाचायला येणाऱ्या कर्मचाऱ्याला मीटरपर्यंत पोहोचू देणं ही तुमची जबाबदारी आहे.",
        "तुमचं बँक खातं बदललं, तर 30 दिवसांत कार्यालयाला कळवणं आवश्यक आहे.",
        "डुप्लिकेट कार्डसाठी 50 रुपये फी भरा आणि एक प्रतिज्ञापत्र द्या.",
    ],
    "refuse": [
        "पीएम-किसानचा पुढचा हप्ता कोणत्या तारखेला येईल?",
        "सुकन्या खात्यावर किती व्याज मिळतं?",
        "सोलर सबसिडीचे पैसे किती दिवसांत येतात?",
        "उज्ज्वलामध्ये सिलेंडर रिफिल किती रुपयांना पडेल?",
        "आयुष्मान कार्ड काढण्याची शेवटची तारीख कोणती आहे?",
        "जमीन नसलेल्या शेतकऱ्यालाही पीएम-किसान मिळतं का?",
        "दोन मुलींसाठी वेगवेगळी सुकन्या खाती उघडता येतात का?",
        "कोणत्या कंपनीचे सोलर पॅनल बसवावेत?",
        "उज्ज्वलाचा हेल्पलाइन नंबर कोणता आहे?",
        "माझ्या शहरातील कोणती रुग्णालयं आयुष्मानमध्ये आहेत?",
    ],
}

# Tamil: entries 8-10 (index 7-9) are romanized Tamil, as typed on many phones.
PACKS["ta"] = {
    "extract_i": "இந்த செய்தியிலிருந்து JSON எடுக்கவும், புலங்கள்: name, paid_inr, due_inr, day. பெயரை செய்தியில் உள்ளபடியே எழுதவும். JSON மட்டும் தரவும்.",
    "extract_i_latn": "Indha message-la irundhu JSON edunga, fields: name, paid_inr, due_inr, day. Peyar message-la irukra maadhiri ezhudhunga. JSON mattum kudunga.",
    "intent_i": "இந்த செய்தியின் நோக்கம் என்ன? இவற்றில் ஒரு லேபிளை மட்டும் எழுதவும்: ",
    "intent_i_latn": "Indha message-oda intent enna? Idhula oru label mattum ezhudhunga: ",
    "simplify_i": "இதை ஏழாம் வகுப்பு மாணவருக்குப் புரியும்படி எளிய தமிழில் 2-3 வரிகளில் விளக்கவும்.",
    "simplify_i_latn": "Idha 7th standard paiyanukku puriyura maadhiri simple Tamil-la 2-3 line-la sollunga.",
    "three": ["3", "மூன்று", "moonu", "three"],
    "support": [
        "என் ரீசார்ஜ் ஆகிவிட்டது ஆனால் டேட்டா வரவில்லை, என்ன செய்வது?",
        "ஐந்து நாட்களுக்கு முன் ஆர்டர் செய்தேன், இன்னும் டெலிவரி ஆகவில்லை, டிராக்கிங்கும் அப்டேட் ஆகவில்லை.",
        "யுபிஐ மூலம் பணம் அனுப்பினேன், பணம் கழிந்துவிட்டது ஆனால் கடைக்காரர் வரவில்லை என்கிறார். இப்போது என்ன செய்வது?",
        "இந்த மாதம் மின் கட்டணம் இரண்டு மடங்கு வந்திருக்கிறது, மீட்டர் தவறாக ஓடுகிறது போல.",
        "கேஸ் சிலிண்டர் புக் செய்தேன், டெலிவரி செய்பவர் ஓடிபி கேட்கிறார் ஆனால் எனக்கு ஓடிபி வரவே இல்லை.",
        "ரேஷன் கார்டில் என் பெயர் தவறாக அச்சிடப்பட்டுள்ளது, எப்படி சரி செய்வது?",
        "ஏடிஎம்-இல் பணம் வரவில்லை ஆனால் கணக்கிலிருந்து கழிந்துவிட்டது.",
        "Moonu naala thanni varala, complaint enga kudukkanum?",
        "Mobile number-a Aadhaar-oda link pannanum, enna pannanum?",
        "Online class-ku internet romba slow-a irukku, enna pannalam?",
    ],
    "qa": [
        "பிஎம்-கிசானில் வருடத்திற்கு எவ்வளவு பணம் கிடைக்கும், எத்தனை தவணைகளில்?",
        "நான் 3 கிலோவாட் சோலார் போட்டிருக்கிறேன், மொத்தம் எவ்வளவு மானியம் கிடைக்கும்?",
        "ஆயுஷ்மான் கார்டு மூலம் எவ்வளவு வரை சிகிச்சை இலவசம்?",
        "சுகன்யா கணக்கை மகளின் எந்த வயது வரை திறக்கலாம், குறைந்தபட்சம் எவ்வளவு செலுத்த வேண்டும்?",
        "இந்தத் திட்டத்தில் மாதம் எத்தனை யூனிட் மின்சாரம் இலவசம்?",
        "பிஎம்-கிசானின் ஒரு தவணை எவ்வளவு?",
        "சுகன்யா கணக்கில் வருடத்திற்கு அதிகபட்சம் எவ்வளவு செலுத்தலாம்?",
        "Sukanya account evvalavu varushathula mature aagum?",
        "Solar-la mudhal 2 kW-ku ovvoru kW-kum evvalavu subsidy kidaikkum?",
        "Sukanya-la evvalavu varusham panam kattanum?",
    ],
    "extract": [
        ("முருகன் 12 ஆம் தேதி 450 ரூபாய் கொடுத்தார், மீதி 200 கடன்.", "முருகன்"),
        ("செல்வி அக்கா 3 ஆம் தேதி வந்தார், 1200-இல் 800 கொடுத்தார், 400 பிறகு தருவார்.", "செல்வி"),
        ("பாண்டியன் கணக்கு: 25 ஆம் தேதி 150 ரூபாய் ரொக்கம், 50 பாக்கி.", "பாண்டியன்"),
        ("இன்று 7 ஆம் தேதி, இம்ரான் அண்ணா முழு 900 கொடுத்துவிட்டார், பாக்கி இல்லை.", "இம்ரான்"),
        ("லட்சுமி 19 ஆம் தேதி 2000 ரூபாய் பொருள் வாங்கினார், 1500 கொடுத்தார், 500 அடுத்த வாரம்.", "லட்சுமி"),
        ("கோபால் 9 ஆம் தேதி 300 கொடுத்தார், 100 இன்னும் பாக்கி.", "கோபால்"),
        ("மீனா 15 ஆம் தேதி முழு 2500 செலுத்திவிட்டார்.", "மீனா"),
        ("Raju 28-aam thethi vandhaan, 1000 rupai saamaan vaangi 600 kuduthaan.", "Raju"),
        ("Salma akka 4-aam thethi: 1250-la 1000 kuduthaanga, 250 kadan.", "Salma"),
        ("Kishore 21-aam thethi 750 kuduthaan, 250 innum tharanum.", "Kishore"),
    ],
    "intent": [
        "இந்த மாத மின் கட்டணம் எவ்வளவு வந்திருக்கிறது?",
        "பணம் செலுத்தினேன் ஆனால் ஆப்பில் தோல்வி என்று காட்டுகிறது, பணமும் கழிந்துவிட்டது.",
        "புதிய வீட்டுக்கு மீட்டர் பொருத்த வேண்டும், எப்படி விண்ணப்பிப்பது?",
        "காலையிலிருந்து தெரு முழுக்க கரண்ட் இல்லை.",
        "எனக்கு மலிவான பிளான் வேண்டும், இப்போதையது மிகவும் விலை அதிகம்.",
        "கடந்த மாத பில் எவ்வளவு என்று சொல்லுங்கள்.",
        "ரீசார்ஜ் பணம் கழிந்துவிட்டது ஆனால் ரீசார்ஜ் ஆகவில்லை.",
        "Kadaikku commercial connection venum.",
        "Transformer erinjiduchu, rendu naala current illa.",
        "Ennoda plan-a postpaid-la irundhu prepaid-ku maathanum.",
    ],
    "simplify": [
        "15 நாட்களுக்குள் நிலுவைக் கட்டணத்தைச் செலுத்தாவிட்டால், முன்னறிவிப்பு இல்லாமல் உங்கள் மின்சாரம் துண்டிக்கப்படும்.",
        "விண்ணப்பம் கொடுக்கும்போது, நீங்களே கையெழுத்திட்ட அடையாள அட்டை மற்றும் முகவரிச் சான்றின் நகல்களைக் கொடுக்க வேண்டும்.",
        "அரசு குழு வந்து பொருத்திய அமைப்பைச் சரிபார்த்த பிறகு, மானியப் பணம் உங்கள் வங்கிக் கணக்கில் வரும்.",
        "உங்கள் இ-கேஒய்சி முடியவில்லை அல்லது வங்கிக் கணக்கு ஆதாருடன் இணைக்கப்படவில்லை என்றால், தவணைப் பணம் நிறுத்தப்படும்.",
        "மின் மீட்டரில் கைவைப்பது சட்டப்படி குற்றம், அதற்கு தண்டனை கிடைக்கலாம்.",
        "கடைசி தேதிக்குப் பிறகு வரும் விண்ணப்பம் எந்தச் சூழ்நிலையிலும் ஏற்றுக்கொள்ளப்படாது.",
        "ஆண்டு வருமானம் 2.5 லட்சம் ரூபாய் அல்லது அதற்குக் குறைவாக உள்ள குடும்பங்களுக்கு மட்டுமே இந்த நன்மை கிடைக்கும்.",
        "Maasam maasam meter padikka varra oozhiyar meter-a paakka vazhi vidanum, adhu ungal poruppu.",
        "Ungal bank account maarinaa, 30 naalukkulla office-ku sollanum.",
        "Duplicate card venumna 50 rupai fees kattunga, oru affidavit-um kudunga.",
    ],
    "refuse": [
        "பிஎம்-கிசானின் அடுத்த தவணை எந்த தேதியில் வரும்?",
        "சுகன்யா கணக்கிற்கு எவ்வளவு வட்டி கிடைக்கும்?",
        "சோலார் மானியப் பணம் எத்தனை நாட்களில் வரும்?",
        "உஜ்வாலாவில் சிலிண்டர் ரீஃபில் எவ்வளவு ஆகும்?",
        "ஆயுஷ்மான் கார்டு எடுக்க கடைசி தேதி என்ன?",
        "நிலம் இல்லாத விவசாயிக்கும் பிஎம்-கிசான் கிடைக்குமா?",
        "இரண்டு மகள்களுக்கு தனித்தனி சுகன்யா கணக்குகள் திறக்கலாமா?",
        "Endha company solar panel podanum?",
        "Ujjwala helpline number enna?",
        "En ooru-la endha hospital-lam Ayushman-la irukku?",
    ],
}

PACKS["bn"] = {
    "extract_i": "এই বার্তা থেকে JSON বের করুন, ফিল্ড: name, paid_inr, due_inr, day. নাম বার্তায় যেমন আছে তেমন লিখুন। শুধু JSON দিন।",
    "intent_i": "এই বার্তার উদ্দেশ্য কী? এগুলোর মধ্যে শুধু একটি লেবেল লিখুন: ",
    "simplify_i": "এটা সপ্তম শ্রেণির ছাত্রকে বোঝানোর মতো সহজ বাংলায় ২-৩ লাইনে বুঝিয়ে দিন।",
    "three": ["3", "তিন", "৩", "three"],
    "support": [
        "আমার রিচার্জ হয়ে গেছে কিন্তু ডেটা আসেনি, কী করব?",
        "পাঁচ দিন আগে অর্ডার করেছিলাম, এখনও ডেলিভারি হয়নি, ট্র্যাকিংও আপডেট হচ্ছে না।",
        "ইউপিআই দিয়ে পেমেন্ট করলাম, টাকা কেটে গেছে কিন্তু দোকানদার বলছে পায়নি। এখন কী করব?",
        "এই মাসে বিদ্যুতের বিল দ্বিগুণ এসেছে, মনে হচ্ছে মিটার ভুল চলছে।",
        "গ্যাস সিলিন্ডার বুক করেছিলাম, ডেলিভারির লোক ওটিপি চাইছে কিন্তু আমার ওটিপি আসেইনি।",
        "রেশন কার্ডে আমার নাম ভুল ছাপা হয়েছে, কীভাবে ঠিক করাব?",
        "এটিএম থেকে টাকা বের হয়নি কিন্তু অ্যাকাউন্ট থেকে কেটে গেছে।",
        "তিন দিন ধরে জল আসছে না, অভিযোগ কোথায় করব?",
        "মোবাইল নম্বর আধারের সঙ্গে লিঙ্ক করতে হবে, কী করতে হবে?",
        "অনলাইন ক্লাসের জন্য ইন্টারনেট খুব ধীরে চলছে, কী করব?",
    ],
    "qa": [
        "পিএম-কিষাণে বছরে কত টাকা পাওয়া যায় আর কয়টি কিস্তিতে?",
        "আমি 3 কিলোওয়াটের সোলার লাগিয়েছি, মোট কত ভর্তুকি পাব?",
        "আয়ুষ্মান কার্ডে কত টাকা পর্যন্ত চিকিৎসা বিনামূল্যে হয়?",
        "সুকন্যা অ্যাকাউন্ট মেয়ের কত বছর বয়স পর্যন্ত খোলা যায় আর কমপক্ষে কত জমা দিতে হয়?",
        "এই প্রকল্পে প্রতি মাসে কত ইউনিট বিদ্যুৎ বিনামূল্যে পাওয়া যায়?",
        "পিএম-কিষাণের একটি কিস্তি কত টাকার?",
        "সুকন্যা অ্যাকাউন্টে বছরে সর্বোচ্চ কত জমা দেওয়া যায়?",
        "সুকন্যা অ্যাকাউন্ট কত বছরে ম্যাচিওর হয়?",
        "সোলারে প্রথম 2 কিলোওয়াটের জন্য প্রতি কিলোওয়াটে কত ভর্তুকি পাওয়া যায়?",
        "সুকন্যায় কত বছর টাকা জমা দিতে হয়?",
    ],
    "extract": [
        ("রমেশ 12 তারিখে 450 টাকা দিয়েছে, বাকি 200 ধার।", "রমেশ"),
        ("সুনীতা বৌদি 3 তারিখে এসেছিলেন, 1200-র মধ্যে 800 দিয়েছেন, 400 পরে দেবেন।", "সুনীতা"),
        ("পাপ্পুর হিসাব: 25 তারিখে 150 টাকা নগদ, 50 বাকি।", "পাপ্পু"),
        ("আজ 7 তারিখ, ইমরান দা পুরো 900 দিয়ে দিয়েছেন, কিছু বাকি নেই।", "ইমরান"),
        ("লক্ষ্মী মাসি 19 তারিখে 2000 টাকার জিনিস নিয়েছেন, 1500 দিয়েছেন, 500 পরের সপ্তাহে।", "লক্ষ্মী"),
        ("গোপাল কাকা 9 তারিখে 300 দিয়েছেন, 100 এখনও বাকি।", "গোপাল"),
        ("মীনা দি 15 তারিখে পুরো 2500 মিটিয়ে দিয়েছেন।", "মীনা"),
        ("রাজু 28 তারিখে এসে 1000 টাকার মাল নিয়েছে, 600 দিয়েছে।", "রাজু"),
        ("সালমা 4 তারিখে: 1250-র মধ্যে 1000 দিয়েছেন, 250 ধার।", "সালমা"),
        ("কিশোর 21 তারিখে 750 দিয়েছে, 250 এখনও দিতে হবে।", "কিশোর"),
    ],
    "intent": [
        "এই মাসের বিদ্যুতের বিল কত এসেছে?",
        "পেমেন্ট করলাম কিন্তু অ্যাপে ফেল দেখাচ্ছে, টাকাও কেটে গেছে।",
        "নতুন বাড়িতে মিটার বসাতে হবে, কীভাবে আবেদন করব?",
        "সকাল থেকে পুরো পাড়ায় কারেন্ট নেই।",
        "আমার সস্তা প্ল্যান দরকার, এখনকারটা খুব দামি।",
        "গত মাসের বিল কত ছিল বলুন।",
        "রিচার্জের টাকা কেটে গেছে কিন্তু রিচার্জ হয়নি।",
        "দোকানের জন্য কমার্শিয়াল কানেকশন চাই।",
        "ট্রান্সফর্মার পুড়ে গেছে, দু'দিন ধরে কারেন্ট নেই।",
        "আমার প্ল্যান পোস্টপেড থেকে প্রিপেডে বদলাতে চাই।",
    ],
    "simplify": [
        "15 দিনের মধ্যে বকেয়া বিল না দিলে, না জানিয়েই আপনার বিদ্যুৎ সংযোগ কেটে দেওয়া হবে।",
        "আবেদন জমা দেওয়ার সময় পরিচয়পত্র আর ঠিকানার প্রমাণের কপি দিন, যেগুলোতে আপনি নিজে সই করেছেন।",
        "সরকারি দল এসে বসানো সিস্টেম পরীক্ষা করার পর ভর্তুকির টাকা আপনার ব্যাংক অ্যাকাউন্টে আসবে।",
        "আপনার ই-কেওয়াইসি না হলে বা ব্যাংক অ্যাকাউন্ট আধারের সঙ্গে যুক্ত না থাকলে কিস্তির টাকা আটকে যাবে।",
        "বিদ্যুতের মিটারে কারসাজি করা আইনত অপরাধ, এর জন্য শাস্তি হতে পারে।",
        "শেষ তারিখের পরে আসা আবেদন কোনো অবস্থাতেই নেওয়া হবে না।",
        "এই সুবিধা শুধু সেই পরিবারগুলোই পাবে যাদের বছরের আয় 2.5 লাখ টাকা বা তার কম।",
        "প্রতি মাসে মিটার পড়তে আসা কর্মীকে মিটার পর্যন্ত যেতে দেওয়া আপনার দায়িত্ব।",
        "আপনার ব্যাংক অ্যাকাউন্ট বদলালে 30 দিনের মধ্যে অফিসকে জানাতে হবে।",
        "ডুপ্লিকেট কার্ডের জন্য 50 টাকা ফি দিন আর একটি হলফনামা জমা দিন।",
    ],
    "refuse": [
        "পিএম-কিষাণের পরের কিস্তি কোন তারিখে আসবে?",
        "সুকন্যা অ্যাকাউন্টে কত সুদ পাওয়া যায়?",
        "সোলার ভর্তুকির টাকা কত দিনে আসে?",
        "উজ্জ্বলায় সিলিন্ডার রিফিল কত টাকা পড়বে?",
        "আয়ুষ্মান কার্ড করার শেষ তারিখ কবে?",
        "জমি নেই এমন কৃষকও কি পিএম-কিষাণ পান?",
        "দুই মেয়ের জন্য আলাদা আলাদা সুকন্যা অ্যাকাউন্ট খোলা যায় কি?",
        "কোন কোম্পানির সোলার প্যানেল লাগানো উচিত?",
        "উজ্জ্বলার হেল্পলাইন নম্বর কী?",
        "আমার শহরে কোন কোন হাসপাতাল আয়ুষ্মানে আছে?",
    ],
}


# ------------------------------------------------------------------ build

def rubric(task: str, lang_name: str) -> str:
    return {
        "support": f"A good reply is polite, gives 1-3 concrete steps the user can take now, does not invent offers, "
                   f"amounts or phone numbers, and is written in {lang_name} like the user.",
        "passage_qa": f"Correct if it states the facts from the passage, adds no numbers that are not in the passage, "
                      f"and answers in {lang_name}.",
        "simplify": f"Good if a 12-year-old can follow it, keeps every key point of the notice (deadlines, conditions, "
                    f"consequences), adds nothing new, and is in {lang_name}.",
        "refuse": "The passage does not contain the answer; a good reply says the passage does not say, and invents "
                  "no figure, date, name or phone number.",
    }[task]


def build_language(lang: str) -> list[dict]:
    pack = PACKS[lang]
    out = []
    for n in range(1, 11):
        i = n - 1
        variant = "ta-latn" if lang == "ta" and n >= 8 else lang
        script, lname = LANG[variant]["script"], LANG[variant]["name"]
        suffix = "_latn" if variant == "ta-latn" else ""

        def case(task, text, **kw):
            out.append({
                "id": f"{lang}-{task}-{n:03d}", "lang": lang, "script": script, "task": task, "input": text,
                "instruction": kw.get("instruction"), "context": kw.get("context"), "expected": kw.get("expected"),
                "reference": kw.get("reference"), "checks": kw["checks"], "rubric": kw.get("rubric"),
                "author": "draft-claude", "reviewed_by": None,
            })

        if pack["support"][i] is None:  # Hinglish pilot cases 001-005 already exist
            continue
        case("support", pack["support"][i], checks=["script_match", "judge"], rubric=rubric("support", lname))
        case("passage_qa", pack["qa"][i], context=QA_CONTEXT[i], expected={"facts": qa_facts(pack["three"])[i]},
             checks=["facts_present", "no_invented_numbers", "script_match", "judge"], rubric=rubric("passage_qa", lname))
        msg, name = pack["extract"][i]
        paid, due, day = LEDGER[i]
        case("extract", msg, instruction=pack["extract_i" + suffix] if ("extract_i" + suffix) in pack else pack["extract_i"],
             expected={"name": name, "paid_inr": paid, "due_inr": due, "day": day}, checks=["json_fields"])
        intent_i = pack.get("intent_i" + suffix, pack["intent_i"]) + ", ".join(LABELS)
        case("intent", pack["intent"][i], instruction=intent_i,
             expected={"label": INTENTS[i], "labels": LABELS}, checks=["label_match"])
        case("simplify", NOTICES[i], instruction=pack.get("simplify_i" + suffix, pack["simplify_i"]),
             reference=pack["simplify"][i], checks=["script_match", "chrf", "judge"], rubric=rubric("simplify", lname))
        case("refuse", pack["refuse"][i], context=REFUSE_CONTEXT[i],
             checks=["refusal", "no_invented_numbers", "script_match"], rubric=rubric("refuse", lname))
    return out


def main() -> None:
    pilot = [json.loads(l) for l in (CASES / "hinglish.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    pilot = [c for c in pilot if int(c["id"].rsplit("-", 1)[1]) <= 5]
    by_lang = {"hinglish": pilot + build_language("hinglish")}
    for lang in ("hi", "mr", "ta", "bn"):
        by_lang[lang] = build_language(lang)

    hidden = []
    for lang, cases in by_lang.items():
        public = []
        for c in sorted(cases, key=lambda c: c["id"]):
            (hidden if int(c["id"].rsplit("-", 1)[1]) in HIDDEN_NUMBERS else public).append(c)
        (CASES / f"{lang}.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in public), encoding="utf-8")
        print(f"{lang}: {len(public)} public")
    (CASES / "hidden.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in hidden), encoding="utf-8")
    print(f"hidden: {len(hidden)} (git-ignored; encrypt with tools/hidden_set.py)")


if __name__ == "__main__":
    main()
