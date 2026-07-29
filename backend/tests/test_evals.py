from evals.runner import run


def test_runner_has_the_required_fifteen_core_cases() -> None:
    result = run()
    core = [case for case in result["cases"] if case["category"] != "indic_asr"]
    assert len(core) == 15
    assert {case["category"] for case in core} == {"extraction", "matching", "classification", "end_to_end"}
    assert all(case["passed"] for case in core)


def test_indic_asr_comparison_runs_both_providers_over_the_same_voice_note() -> None:
    """SPEC-extension case: the seeded Hindi voice note through Sarvam and Whisper.

    The comparison is computed, not asserted into existence: each fixture transcript is
    run through the real amount extractor. Saaras normalizes "पच्चीस सौ" to digits so the
    ₹2,500 amount survives; Whisper's transcript spells the number out and extraction
    honestly yields nothing.
    """
    result = run()
    asr = {case["id"]: case for case in result["cases"] if case["category"] == "indic_asr"}
    assert set(asr) == {"ASR-SARVAM", "ASR-WHISPER"}

    sarvam = asr["ASR-SARVAM"]
    assert sarvam["provider"] == "sarvam (saaras:v3)"
    assert sarvam["actual"]["amount_paise"] == 250_000
    assert sarvam["passed"] is True
    assert sarvam["cost_inr"] > 0
    assert sarvam["cost_usd"] == 0

    whisper = asr["ASR-WHISPER"]
    assert whisper["provider"] == "openai (whisper-1)"
    assert whisper["actual"]["amount_paise"] is None
    assert whisper["passed"] is False
    assert "Sarvam" in whisper["note"]

    assert result["count"] == 17
