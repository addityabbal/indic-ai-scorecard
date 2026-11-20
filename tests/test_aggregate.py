from scoring import aggregate, judge


def test_case_score_combines_checks_and_judge():
    checks = {"script_match": {"score": 1.0}, "chrf": {"score": 0.4}}
    assert aggregate.case_score(checks, 0.5, True) == 0.75
    assert aggregate.case_score(checks, None, True) is None      # waits for the judge
    assert aggregate.case_score({"json_fields": {"score": 0.0}}, None, False) == 0.0


def test_model_score_weights_tasks_equally():
    by_task = {"extract": [1.0] * 10, "support": [0.0, 0.0]}
    assert aggregate.model_score(by_task) == 0.5


def test_bootstrap_range_contains_score():
    by_task = {"a": [0.2, 0.4, 0.6, 0.8, 1.0], "b": [0.0, 1.0, 1.0, 0.0, 1.0]}
    lo, hi = aggregate.bootstrap(by_task)
    assert lo <= aggregate.model_score(by_task) <= hi and hi - lo > 0


def test_judge_mapping_and_parsing():
    g = judge.parse_grade('{"helpful":5,"correct":3,"natural":1,"reason":"ok"}')
    assert judge.judge_score(g) == 0.5
    assert judge.parse_grade('{"helpful":7,"correct":3,"natural":1}') is None
    assert judge.parse_grade("no json") is None


def test_judge_prompt_is_blind():
    case = {"lang": "hinglish", "input": "bill kitna hai", "rubric": "r", "context": None, "instruction": None}
    text = " ".join(m["content"] for m in judge.judge_messages(case, "answer text"))
    assert "llama" not in text.lower() and "model" not in text.lower()


def test_headline_prefers_cheapest_tied_model():
    ranked = [
        {"id": "big", "score": 0.80, "range": (0.70, 0.88), "usd_per_1000": 2.0},
        {"id": "small", "score": 0.76, "range": (0.68, 0.84), "usd_per_1000": 0.2},
        {"id": "weak", "score": 0.40, "range": (0.30, 0.50), "usd_per_1000": 0.01},
    ]
    text = aggregate.headline(ranked, ["hinglish"])
    assert "Top Hinglish quality: big" in text and "small" in text and "weak" not in text


def test_empty_answer_scores_zero_and_is_a_failure(tmp_path, monkeypatch):
    import json
    case = {"id": "hinglish-support-001", "lang": "hinglish", "script": "latn", "task": "support", "input": "x",
            "checks": ["script_match", "judge"], "rubric": "r", "context": None, "instruction": None}
    monkeypatch.setattr(aggregate, "load_cases", lambda which: [case])
    monkeypatch.setattr(aggregate, "load_models", lambda: ({}, [{"id": "m", "provider": "workers-ai", "model": "x"}]))
    monkeypatch.setattr(aggregate, "load_prices", lambda: {"workers_ai": {"usd_per_1000_neurons": 0.011}})
    row = {"key": "m|hinglish-support-001|h", "model_id": "m", "case_id": case["id"], "text": "", "finish_reason": "length"}
    (tmp_path / "answers.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    scores, _ = aggregate.build(tmp_path)
    model = scores["models"][0]
    assert model["score"] == 0.0 and model["pending_judge"] == 0
    assert scores["failures"][0]["what"] == "Gave no answer"
