from scoring import checks


def test_script_share_latin_vs_devanagari():
    assert checks.script_match("bhai recharge karo", "latn")[0]
    ok, detail = checks.script_match("पहले वैलिडिटी चेक करो", "latn")
    assert not ok and detail.startswith("0%")
    assert checks.script_match("आप ग्राहक सेवा से बात करें", "deva")[0]
    assert checks.script_match("வணக்கம்", "taml")[0]
    assert checks.script_match("আমি জানি না", "beng")[0]


def test_script_mixed_threshold():
    # mostly Devanagari with one English word: still Devanagari
    assert checks.script_match("आपका OTP नहीं आया तो दोबारा कोशिश करें", "deva")[0]


def test_numbers_and_invented():
    assert checks.numbers("Rs 6,000 aur ३ kist") == {6000.0, 3.0}
    passage = "Rs 6,000 per year in three instalments of Rs 2,000"
    assert checks.no_invented_numbers("6000 rupaye, 2,000 ki kist", passage)[0]
    ok, detail = checks.no_invented_numbers("6000 rupaye, agli kist 15 march", passage)
    assert not ok and "15" in detail


def test_question_numbers_are_allowed():
    assert checks.no_invented_numbers("3 kW par 78,000", "capped at Rs 78,000", "3 kW ka solar")[0]


def test_facts_present_ignores_commas_and_spaces():
    assert checks.facts_present("Aapko 6000 milenge, 2 000 ki kist", ["6,000", "2,000"])[0]
    assert not checks.facts_present("Aapko paise milenge", ["6,000"])[0]


def test_json_fields():
    exp = {"name": "Ramesh", "paid_inr": 450, "due_inr": 200, "day": 12}
    good = '```json\n{"name": "ramesh", "paid_inr": "450", "due_inr": 200, "day": 12}\n```'
    assert checks.json_fields(good, exp)[0]
    ok, detail = checks.json_fields('{"name": "Ramesh", "paid_inr": 450, "due_inr": 250, "day": 12}', exp)
    assert not ok and "due_inr" in detail
    assert checks.json_fields("Ramesh ne 450 diye", exp) == (False, "not valid JSON")


def test_label_match_requires_exactly_the_expected_label():
    labels = ["bill_amount_query", "payment_failed"]
    assert checks.label_match("bill_amount_query", "bill_amount_query", labels)[0]
    assert not checks.label_match("payment_failed", "bill_amount_query", labels)[0]
    assert not checks.label_match("bill_amount_query or payment_failed", "bill_amount_query", labels)[0]


def test_refusal_phrases():
    assert checks.refusal("Passage mein iski jaankari nahi di gayi hai.", "hinglish")[0]
    assert checks.refusal("मुझे पता नहीं", "hi")[0]
    assert not checks.refusal("Agli kist 15 march ko aayegi.", "hinglish")[0]


def test_chrf_is_between_0_and_1():
    s = checks.chrf("15 din mein bill bharo warna bijli kategi", "Agar aapne 15 din ke andar bill nahi bhara to bijli kaat di jayegi")
    assert 0 < s < 1


def test_run_checks_on_a_case():
    case = {"script": "latn", "lang": "hinglish", "checks": ["facts_present", "no_invented_numbers", "script_match", "judge"],
            "expected": {"facts": ["78,000"]}, "context": "capped at Rs 78,000", "input": "3 kW ka subsidy?"}
    out = checks.run_checks(case, "3 kW par subsidy 78,000 rupaye tak milegi")
    assert set(out) == {"facts_present", "no_invented_numbers", "script_match"}
    assert all(v["pass"] for v in out.values())


def test_one_step_arithmetic_is_not_invented():
    passage = "Rs 30,000 per kW for the first 2 kW and Rs 18,000 for the third kW, capped at Rs 78,000"
    assert checks.no_invented_numbers("2 kW x 30,000 = 60,000, plus 18,000 = 78,000", passage)[0]
    assert not checks.no_invented_numbers("subsidy 95,000 milegi", passage)[0]


def test_names_ignore_trailing_honorifics():
    assert checks.same_name("Sunita Bhabhi", "Sunita")
    assert checks.same_name("Imran bhai", "Imran")
    assert not checks.same_name("Sunita Devi", "Sunita")


def test_hinglish_refusal_in_devanagari_counts_as_refusal():
    assert checks.refusal("मुझे नहीं पता।", "hinglish")[0]
    assert not checks.script_match("मुझे नहीं पता।", "latn")[0]   # but the script check still fails it


def test_number_words_and_hindi_units():
    assert checks.no_invented_numbers("3 kist mein 2,000 each", "three equal instalments of Rs 2,000")[0]
    assert checks.facts_present("har saal **5 लाख रुपये** tak", ["5 lakh"])[0]


def test_fact_alternatives():
    facts = ["6,000", ["3", "three", "teen", "तीन"]]
    assert checks.facts_present("साल में 6,000 रुपये, तीन किस्तों में", facts)[0]
    assert not checks.facts_present("साल में 6,000 रुपये मिलते हैं", facts)[0]
