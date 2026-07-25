from evals.runner import run

def test_runner_has_the_required_fifteen_cases() -> None:
    result = run()
    assert result["count"] == 15
    assert {case["category"] for case in result["cases"]} == {"extraction", "matching", "classification", "end_to_end"}
    assert all(case["passed"] for case in result["cases"])
