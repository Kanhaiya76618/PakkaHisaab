from evals.runner import run


def test_runner_has_the_required_fifteen_core_cases() -> None:
    result = run()
    core = [case for case in result["cases"] if case["category"] != "indic_asr"]
    assert len(core) == 15
    assert {case["category"] for case in core} == {"extraction", "matching", "classification", "end_to_end"}
    assert all(case["passed"] for case in core)


def test_sarvam_live_recording_extracts_the_amount_through_the_digits_path() -> None:
    """Saaras normalized the seeded voice note to digits on 5 of 5 live calls."""
    asr = {case["id"]: case for case in run()["cases"] if case["category"] == "indic_asr"}
    sarvam = asr["ASR-SARVAM"]
    assert sarvam["provider"] == "sarvam (saaras:v3)"
    assert sarvam["measured"] is True
    assert "2500" in sarvam["actual"]["transcript"], "the live transcript carries digits"
    assert sarvam["actual"]["amount_paise"] == 250_000
    assert sarvam["actual"]["path"] == "digits"
    assert sarvam["passed"] is True
    assert sarvam["cost_inr"] > 0


def test_word_parser_recovers_the_amount_when_the_provider_does_not_normalize() -> None:
    """The measured failure mode: same sentence, different prosody, number left in words.
    Deterministic code recovers ₹2,500 so the ledger does not depend on provider formatting."""
    asr = {case["id"]: case for case in run()["cases"] if case["category"] == "indic_asr"}
    fallback = asr["ASR-WORDS-FALLBACK"]
    assert "पच्चीस सौ" in fallback["actual"]["transcript"]
    assert fallback["actual"]["parsed_rupees"] == 2500
    assert fallback["actual"]["amount_paise"] == 250_000
    assert fallback["actual"]["path"] == "word parser"
    assert fallback["passed"] is True


def test_whisper_is_reported_unmeasured_and_excluded_from_the_score() -> None:
    """No OpenAI key and no Azure whisper deployment. An unrun test must not be scored as a
    failure, and must never be given a fabricated result."""
    result = run()
    asr = {case["id"]: case for case in result["cases"] if case["category"] == "indic_asr"}
    whisper = asr["ASR-WHISPER"]
    assert whisper["measured"] is False
    assert whisper["actual"]["transcript"] is None
    assert "NOT MEASURED" in whisper["note"]

    # Score reflects only the two measured cases, so it is 100%, not 67%.
    assert result["summary"]["indic_asr"] == 1.0
    assert result["count"] == 18
    assert result["measured_count"] == 17
