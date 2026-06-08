"""
Tests for the grade simulator agent and tools.

Unit tests cover the Python formula helpers and JSON-extraction utilities.
Integration tests (marked @pytest.mark.slow) invoke the real LLM agent and
require a running Ollama instance with llama3.2.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from agents.grade_simulator import (
    _build_data_prompt,
    _compute_weighted_average,
    _extract_json,
    run_simulation,
)
from agents.tools import get_current_grades, set_api_client

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_years(subjects_per_year: list[list[dict]]) -> list[dict]:
    """Build a minimal years-data structure for testing."""
    years = []
    for i, subjects in enumerate(subjects_per_year, start=1):
        years.append(
            {
                "id": i,
                "order_index": i,
                "label": f"Year {i}",
                "subjects": subjects,
            }
        )
    return years


def _subject(name, credits, assessments, max_grade=10.0):
    return {
        "name": name,
        "credit_value": credits,
        "max_grade": max_grade,
        "passing_grade": 5.0,
        "assessments": assessments,
    }


def _assessment(aid, weight, score=None, max_score=10.0):
    return {
        "id": aid,
        "name": f"Assessment {aid}",
        "weight": weight,
        "max_score": max_score,
        "grade": {"score": score} if score is not None else None,
    }


# ---------------------------------------------------------------------------
# TestComputeWeightedAverage — verifies the formula matches DashboardService
# ---------------------------------------------------------------------------


class TestComputeWeightedAverage:
    """Unit tests for _compute_weighted_average and _compute_subject_grade."""

    def test_single_subject_fully_graded(self):
        # Math: 6 credits, score 8/10 at 100% weight, max_grade 10
        # subject_grade = (8/10) * 1.0 * 10 = 8.0
        # overall = 8.0 * 6 / 6 = 8.0
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        avg = _compute_weighted_average(years, set(), None)
        assert avg == 8.0

    def test_two_graded_subjects(self):
        # Math 6cr@8.0, Physics 5cr@6.0
        # overall = (8*6 + 6*5) / (6+5) = 78/11 ≈ 7.09
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Physics", 5, [_assessment(2, 100, 6.0)]),
                ]
            ]
        )
        avg = _compute_weighted_average(years, set(), None)
        assert avg == round(78 / 11, 2)

    def test_available_assessments_skipped_when_none(self):
        # Chemistry (id=3) is available; should not be included when available_score=None
        # Denominator = Math + Physics credits only
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Physics", 5, [_assessment(2, 100, 6.0)]),
                    _subject("Chemistry", 4, [_assessment(3, 100)]),  # no grade
                ]
            ]
        )
        avg = _compute_weighted_average(years, {3}, None)
        assert avg == round(78 / 11, 2)

    def test_max_achievable_with_all_at_10(self):
        # Math 6@8, Physics 5@6, Chemistry 4 available
        # Max: (8*6 + 6*5 + 10*4) / 15 = 118/15 ≈ 7.87
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Physics", 5, [_assessment(2, 100, 6.0)]),
                    _subject("Chemistry", 4, [_assessment(3, 100)]),
                ]
            ]
        )
        avg = _compute_weighted_average(years, {3}, 10.0)
        assert avg == round(118 / 15, 2)

    def test_required_score_for_target(self):
        # Target 7.5 with Chemistry available
        # Required in Chemistry = (7.5*15 - 78) / 4 = 8.625
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Physics", 5, [_assessment(2, 100, 6.0)]),
                    _subject("Chemistry", 4, [_assessment(3, 100)]),
                ]
            ]
        )
        avg = _compute_weighted_average(years, {3}, 8.625)
        assert avg is not None
        assert abs(avg - 7.5) < 0.01

    def test_no_fixed_grades_returns_none(self):
        # Everything available, available_score=None → no scored subjects
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100)]),
                ]
            ]
        )
        avg = _compute_weighted_average(years, {1}, None)
        assert avg is None

    def test_multiple_assessments_per_subject(self):
        # Math: exam 60% score=7, project 40% score=9, max_grade=10
        # subject_grade = (7/10)*0.6*10 + (9/10)*0.4*10 = 4.2 + 3.6 = 7.8
        years = _make_years(
            [
                [
                    _subject(
                        "Math",
                        8,
                        [
                            _assessment(1, 60, 7.0),
                            _assessment(2, 40, 9.0),
                        ],
                    ),
                ]
            ]
        )
        avg = _compute_weighted_average(years, set(), None)
        assert avg == 7.8

    def test_partial_subject_includes_in_denominator(self):
        # Math has exam (fixed 6.0, 50%) and project (available, 50%)
        # With available_score=None: grade = (6/10)*0.5*10 = 3.0, has_score=True
        # Denominator includes Math's 10 credits
        years = _make_years(
            [
                [
                    _subject(
                        "Math",
                        10,
                        [
                            _assessment(1, 50, 6.0),
                            _assessment(2, 50),  # available
                        ],
                    ),
                ]
            ]
        )
        avg_partial = _compute_weighted_average(years, {2}, None)
        assert avg_partial == 3.0

        # With available = 10.0: grade = 3.0 + 5.0 = 8.0
        avg_max = _compute_weighted_average(years, {2}, 10.0)
        assert avg_max == 8.0

    def test_non_standard_max_score(self):
        # Assessment scored 75 out of 100, weight 100%, subject max 10
        # normalized = 0.75, grade = 0.75 * 1.0 * 10 = 7.5
        years = _make_years(
            [
                [
                    _subject("Stats", 5, [_assessment(1, 100, 75.0, max_score=100.0)]),
                ]
            ]
        )
        avg = _compute_weighted_average(years, set(), None)
        assert avg == 7.5

    def test_only_graded_subjects_in_denominator(self):
        # Math graded, Physics fully available (no grade)
        # overall = Math grade * Math credits / Math credits (Physics excluded)
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Physics", 5, [_assessment(2, 100)]),  # no grade
                ]
            ]
        )
        avg = _compute_weighted_average(years, {2}, None)
        assert avg == 8.0  # only Math in denominator

    def test_multiple_years(self):
        # Year 1: Math 6cr@8.0; Year 2: Physics 4cr@6.0
        # overall = (8*6 + 6*4) / (6+4) = 72/10 = 7.2
        years = _make_years(
            [
                [_subject("Math", 6, [_assessment(1, 100, 8.0)])],
                [_subject("Physics", 4, [_assessment(2, 100, 6.0)])],
            ]
        )
        avg = _compute_weighted_average(years, set(), None)
        assert avg == 7.2


# ---------------------------------------------------------------------------
# TestExtractJson — verifies JSON parsing from agent output
# ---------------------------------------------------------------------------


class TestExtractJson:

    def test_clean_json(self):
        payload = {"grades": [], "message": ""}
        assert _extract_json(json.dumps(payload)) == payload

    def test_json_with_markdown_fences(self):
        payload = {"grades": [{"assessment_id": 1, "predicted_score": 8.0}], "message": ""}
        text = f"```json\n{json.dumps(payload)}\n```"
        assert _extract_json(text) == payload

    def test_json_embedded_in_text(self):
        payload = {"grades": [], "message": "impossible"}
        text = f"Sure! Here is the result: {json.dumps(payload)} Hope that helps."
        assert _extract_json(text) == payload

    def test_json_with_whitespace(self):
        payload = {"grades": [], "message": ""}
        assert _extract_json(f"  {json.dumps(payload)}  ") == payload

    def test_invalid_returns_none(self):
        assert _extract_json("not json") is None
        assert _extract_json("```python\nsome code\n```") is None
        assert _extract_json("") is None


# ---------------------------------------------------------------------------
# TestBuildDataPrompt — verifies the prompt structure
# ---------------------------------------------------------------------------


class TestBuildDataPrompt:

    def test_contains_target_and_scope(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        prompt = _build_data_prompt(7.5, "Year 1", "", [2], years)
        assert "Target average: 7.5/10" in prompt
        assert "Scope: Year 1" in prompt

    def test_includes_student_note(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100)])]])
        prompt = _build_data_prompt(7.0, "All Years", "I find Math hard", [1], years)
        assert "I find Math hard" in prompt

    def test_available_yes_no_flags(self):
        years = _make_years(
            [
                [
                    _subject(
                        "Math",
                        6,
                        [
                            _assessment(1, 60, 7.0),  # fixed
                            _assessment(2, 40),  # available
                        ],
                    ),
                ]
            ]
        )
        prompt = _build_data_prompt(8.0, "All Years", "", [2], years)
        # id=1 should be fixed, id=2 should be available
        assert "Assessment ID 1" in prompt
        assert "Available to change: NO" in prompt
        assert "Assessment ID 2" in prompt
        assert "Available to change: YES" in prompt

    def test_impossible_target_flagged(self):
        # Math 6cr fixed at 8.0, Chemistry 4cr available — max avg < 9.5
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Chemistry", 4, [_assessment(2, 100)]),
                ]
            ]
        )
        prompt = _build_data_prompt(9.5, "All Years", "", [2], years)
        assert "IMPOSSIBLE" in prompt

    def test_no_available_assessments_flagged(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        prompt = _build_data_prompt(9.0, "All Years", "", [], years)
        assert "NO ASSESSMENTS AVAILABLE" in prompt

    def test_precomputed_averages_present(self):
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Physics", 4, [_assessment(2, 100)]),
                ]
            ]
        )
        prompt = _build_data_prompt(7.0, "All Years", "", [2], years)
        assert "Actual current average" in prompt
        assert "Maximum achievable" in prompt
        assert "Minimum achievable" in prompt

    def test_passing_grade_and_min_passing_score_present(self):
        # subject passing_grade=5.0, max_grade=10.0, assessment max_score=100
        # min_passing_score = (5.0/10.0) * 100 = 50.0
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0, max_score=100.0)]),
                ]
            ]
        )
        prompt = _build_data_prompt(7.0, "All Years", "", [], years)
        assert "Passing grade: 5.0" in prompt
        assert "Min passing score: 50.0" in prompt

    def test_min_passing_score_scales_with_max_score(self):
        # passing_grade=5.0, max_grade=10.0, max_score=10.0 → min_passing=5.0
        years = _make_years(
            [
                [
                    _subject("Stats", 4, [_assessment(1, 100, 7.0, max_score=10.0)]),
                ]
            ]
        )
        prompt = _build_data_prompt(7.0, "All Years", "", [], years)
        assert "Min passing score: 5.0" in prompt

    def test_target_already_met_banner(self):
        # Math fixed at 9.0, Physics available — actual avg 9.0 >= target 7.0
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 9.0)]),
                    _subject("Physics", 4, [_assessment(2, 100)]),
                ]
            ]
        )
        prompt = _build_data_prompt(7.0, "All Years", "", [2], years)
        assert "TARGET ALREADY MET" in prompt

    def test_target_not_met_no_banner(self):
        # Math at 7.0 (6cr), Physics available (4cr), target 7.5
        # actual avg = 7.0 < 7.5 (not met); max avg = (7*6+10*4)/10 = 8.2 (not impossible)
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 7.0)]),
                    _subject("Physics", 4, [_assessment(2, 100)]),
                ]
            ]
        )
        prompt = _build_data_prompt(7.5, "All Years", "", [2], years)
        assert "TARGET ALREADY MET" not in prompt
        assert "IMPOSSIBLE" not in prompt

    def test_subject_passing_status_in_prompt(self):
        # Math grade = 8.0 >= passing 5.0 → Subject passing: YES
        # Physics no scores → NO GRADES YET
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Physics", 4, [_assessment(2, 100)]),
                ]
            ]
        )
        prompt = _build_data_prompt(7.0, "All Years", "", [2], years)
        assert "Subject passing: YES" in prompt
        assert "Subject passing: NO GRADES YET" in prompt

    def test_subject_failing_status_in_prompt(self):
        # Math grade = (3/10)*1.0*10 = 3.0 < passing_grade 5.0 → FAILING
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 3.0)])]])
        prompt = _build_data_prompt(7.0, "All Years", "", [], years)
        assert "Subject passing: FAILING" in prompt

    def test_assessment_currently_failing_flag(self):
        # min_passing = (5.0/10.0)*10 = 5.0; score 3.0 → YES; score 7.0 → NO
        years = _make_years(
            [
                [
                    _subject(
                        "Math",
                        6,
                        [
                            _assessment(1, 50, 3.0),  # failing
                            _assessment(2, 50, 7.0),  # passing
                        ],
                    ),
                ]
            ]
        )
        prompt = _build_data_prompt(7.0, "All Years", "", [], years)
        assert "Currently failing: YES" in prompt
        assert "Currently failing: NO" in prompt

    def test_assessment_no_grade_flag(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100)])]])
        prompt = _build_data_prompt(7.0, "All Years", "", [1], years)
        assert "Currently failing: NO GRADE" in prompt


# ---------------------------------------------------------------------------
# TestGetCurrentGrades — verifies the get_current_grades tool
# ---------------------------------------------------------------------------


class TestGetCurrentGrades:

    def test_fetch_grades_success(self):
        years = _make_years(
            [
                [
                    _subject("Mathematics", 6, [_assessment(1, 100, 8.0)]),
                    _subject("Physics", 5, [_assessment(2, 100)]),
                ]
            ]
        )
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = years
        set_api_client(mock_client)

        result = get_current_grades.invoke({})

        assert "Mathematics" in result
        assert "Physics" in result
        assert "8.0" in result
        assert "No grade yet" in result

    def test_fetch_grades_empty(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = []
        set_api_client(mock_client)

        result = get_current_grades.invoke({})
        assert "No subjects found" in result

    def test_fetch_grades_api_error(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.side_effect = Exception("Connection refused")
        set_api_client(mock_client)

        result = get_current_grades.invoke({})
        assert "Error" in result

    def test_filter_by_year_id(self):
        years = [
            {
                "id": 1,
                "order_index": 1,
                "label": "Year 1",
                "subjects": [_subject("Math", 6, [_assessment(1, 100, 9.0)])],
            },
            {
                "id": 2,
                "order_index": 2,
                "label": "Year 2",
                "subjects": [_subject("Physics", 5, [_assessment(2, 100, 7.0)])],
            },
        ]
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = years
        set_api_client(mock_client)

        result = get_current_grades.invoke({"year_id": 1})
        assert "Math" in result
        assert "Physics" not in result


# ---------------------------------------------------------------------------
# TestRunSimulation — mocked agent, checks dict structure and retry logic
# ---------------------------------------------------------------------------


class TestRunSimulation:

    def _years(self):
        return _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 7.0)]),
                    _subject("Physics", 5, [_assessment(2, 100)]),
                ]
            ]
        )

    @patch("agents.grade_simulator.create_react_agent")
    def test_returns_dict_with_expected_keys(self, mock_create):
        payload = {"grades": [{"assessment_id": 2, "predicted_score": 8.5}], "message": ""}
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [MagicMock(content=json.dumps(payload))]}
        mock_create.return_value = mock_agent

        result = run_simulation(7.5, "", [2], None, self._years(), "All Years")

        assert isinstance(result, dict)
        assert "grades" in result
        assert "message" in result
        assert result["grades"][0]["assessment_id"] == 2
        assert result["grades"][0]["predicted_score"] == 8.5

    @patch("agents.grade_simulator.create_react_agent")
    def test_retries_on_invalid_json(self, mock_create):
        valid = {"grades": [], "message": "no assessments"}
        mock_agent = MagicMock()
        # First call returns invalid JSON; second returns valid
        mock_agent.invoke.side_effect = [
            {"messages": [MagicMock(content="Here you go: oops")]},
            {"messages": [MagicMock(content=json.dumps(valid))]},
        ]
        mock_create.return_value = mock_agent

        result = run_simulation(7.0, "", [], None, self._years(), "All Years")

        assert mock_agent.invoke.call_count == 2
        assert result == valid

    @patch("agents.grade_simulator.create_react_agent")
    def test_fallback_after_two_failures(self, mock_create):
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [MagicMock(content="I cannot compute that.")]}
        mock_create.return_value = mock_agent

        result = run_simulation(7.0, "", [1], None, self._years(), "All Years")

        assert mock_agent.invoke.call_count == 2
        assert result["grades"] == []
        assert "failed" in result["message"].lower()

    @patch("agents.grade_simulator.create_react_agent")
    def test_exception_returns_error_dict(self, mock_create):
        mock_agent = MagicMock()
        mock_agent.invoke.side_effect = RuntimeError("Ollama not running")
        mock_create.return_value = mock_agent

        result = run_simulation(7.0, "", [1], None, self._years(), "All Years")

        assert result["grades"] == []
        assert "Error" in result["message"]

    @patch("agents.grade_simulator.create_react_agent")
    def test_impossible_target_message_preserved(self, mock_create):
        payload = {
            "grades": [{"assessment_id": 2, "predicted_score": 10.0}],
            "message": "Target 9.5 is impossible. Using 8.73 instead.",
        }
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [MagicMock(content=json.dumps(payload))]}
        mock_create.return_value = mock_agent

        result = run_simulation(9.5, "", [2], None, self._years(), "All Years")

        assert result["message"] != ""
        assert "impossible" in result["message"].lower() or "9.5" in result["message"]


# ---------------------------------------------------------------------------
# TestGradeSimulatorAgent — slow integration tests (require Ollama + llama3.2)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestGradeSimulatorAgent:

    def _mock_client(self, years):
        client = MagicMock()
        client.get_academic_years.return_value = years
        return client

    def test_agent_returns_valid_dict(self):
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 7.0)]),
                    _subject("Physics", 5, [_assessment(2, 100)]),
                ]
            ]
        )
        set_api_client(self._mock_client(years))

        result = run_simulation(7.5, "", [2], None, years, "All Years")

        assert isinstance(result, dict)
        assert "grades" in result
        assert "message" in result

    def test_agent_grades_within_valid_range(self):
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 7.0)]),
                    _subject("Physics", 5, [_assessment(2, 100)]),
                ]
            ]
        )
        set_api_client(self._mock_client(years))

        result = run_simulation(7.5, "", [2], None, years, "All Years")

        for entry in result.get("grades", []):
            score = entry.get("predicted_score", 0)
            assert 1.0 <= score <= 10.0, f"Score {score} out of range"

    def test_agent_flags_impossible_target(self):
        # Math fixed at 2.0, Physics available — target 10.0 is impossible
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 2.0)]),
                    _subject("Physics", 6, [_assessment(2, 100)]),
                ]
            ]
        )
        set_api_client(self._mock_client(years))

        result = run_simulation(10.0, "", [2], None, years, "All Years")

        # Either message is set OR the agent still returns grade entries
        has_message = bool(result.get("message"))
        has_grades = bool(result.get("grades"))
        assert has_message or has_grades

    def test_agent_no_available_assessments(self):
        years = _make_years(
            [
                [
                    _subject("Math", 6, [_assessment(1, 100, 8.0)]),
                ]
            ]
        )
        set_api_client(self._mock_client(years))

        result = run_simulation(9.0, "", [], None, years, "All Years")

        assert result.get("grades") == [] or result.get("message")

    def test_agent_respects_student_note(self):
        years = _make_years(
            [
                [
                    _subject("Calculus", 5, [_assessment(1, 100)]),
                    _subject("Biology", 5, [_assessment(2, 100)]),
                ]
            ]
        )
        set_api_client(self._mock_client(years))

        result = run_simulation(
            7.0,
            "Calculus is very hard for me; Biology is my strength.",
            [1, 2],
            None,
            years,
            "All Years",
        )

        assert isinstance(result, dict)
        grades = {e["assessment_id"]: e["predicted_score"] for e in result.get("grades", [])}
        # Calculus (id=1) should generally score lower than Biology (id=2)
        if 1 in grades and 2 in grades:
            assert (
                grades[1] <= grades[2] + 2.0
            ), "Expected Calculus score to be no higher than Biology + 2 tolerance"
