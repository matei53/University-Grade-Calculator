"""
Tests for the grade simulator agent and tools.

Unit tests cover:
  - _compute_weighted_average / _compute_subject_grade: formula helpers
  - _build_data_prompt: context builder including the MANDATORY IDs checklist
  - _extract_json: JSON extraction from LLM output
  - verify_simulation tool
  - get_current_grades tool
  - run_simulation (mocked ReAct agent)

Integration tests (marked @pytest.mark.slow) invoke the real LLM agent and
require a running Ollama instance with llama3.2.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("langchain_core")

from agents.grade_simulator import (
    _build_data_prompt,
    _compute_weighted_average,
    _extract_json,
    run_simulation,
    verify_simulation,
)
from agents.tools import get_current_grades, set_api_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_years(subjects_per_year: list[list[dict]]) -> list[dict]:
    years = []
    for i, subjects in enumerate(subjects_per_year, start=1):
        years.append({"id": i, "order_index": i, "label": f"Year {i}", "subjects": subjects})
    return years


def _subject(name, credits, assessments, max_grade=10.0, passing_grade=5.0):
    return {
        "name": name,
        "credit_value": credits,
        "max_grade": max_grade,
        "passing_grade": passing_grade,
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
# TestComputeWeightedAverage — formula must match DashboardService exactly
# ---------------------------------------------------------------------------


class TestComputeWeightedAverage:

    def test_single_subject_fully_graded(self):
        # subject_grade = (8/10)*1.0*10 = 8.0; overall = 8.0*6/6 = 8.0
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        assert _compute_weighted_average(years, set(), None) == 8.0

    def test_two_graded_subjects_weighted_by_credits(self):
        # Math 6cr@8.0, Physics 5cr@6.0 → (8*6 + 6*5) / 11 = 78/11
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0)]),
            _subject("Physics", 5, [_assessment(2, 100, 6.0)]),
        ]])
        assert _compute_weighted_average(years, set(), None) == round(78 / 11, 2)

    def test_ungraded_available_assessment_excluded_from_denominator(self):
        # Physics (id=2) is available with no score → excluded entirely
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0)]),
            _subject("Physics", 5, [_assessment(2, 100)]),
        ]])
        assert _compute_weighted_average(years, {2}, None) == 8.0

    def test_available_assessment_included_when_score_provided(self):
        # Chemistry (id=2) available; assigning 10.0 → (8*6 + 10*4) / 10 = 8.8
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0)]),
            _subject("Chemistry", 4, [_assessment(2, 100)]),
        ]])
        assert _compute_weighted_average(years, {2}, 10.0) == 8.8

    def test_multiple_assessments_per_subject(self):
        # exam 60%@7.0 + project 40%@9.0 = 4.2 + 3.6 = 7.8
        years = _make_years([[
            _subject("Math", 8, [_assessment(1, 60, 7.0), _assessment(2, 40, 9.0)])
        ]])
        assert _compute_weighted_average(years, set(), None) == 7.8

    def test_partial_subject_counted_in_denominator(self):
        # Math has one scored (50%) and one available (50%); with available=None:
        # grade = (6/10)*0.5*10 = 3.0; subject has a score → still in denominator
        years = _make_years([[
            _subject("Math", 10, [_assessment(1, 50, 6.0), _assessment(2, 50)])
        ]])
        assert _compute_weighted_average(years, {2}, None) == 3.0
        # With available scored at 10: grade = 3.0 + 5.0 = 8.0
        assert _compute_weighted_average(years, {2}, 10.0) == 8.0

    def test_non_standard_max_score(self):
        # score 75/100, weight 100%, max_grade 10 → (75/100)*1.0*10 = 7.5
        years = _make_years([[
            _subject("Stats", 5, [_assessment(1, 100, 75.0, max_score=100.0)])
        ]])
        assert _compute_weighted_average(years, set(), None) == 7.5

    def test_returns_none_when_no_subject_has_score(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100)])]])
        assert _compute_weighted_average(years, {1}, None) is None

    def test_multiple_years_combined(self):
        # Year1: Math 6cr@8; Year2: Physics 4cr@6 → (8*6+6*4)/10 = 7.2
        years = _make_years([
            [_subject("Math", 6, [_assessment(1, 100, 8.0)])],
            [_subject("Physics", 4, [_assessment(2, 100, 6.0)])],
        ])
        assert _compute_weighted_average(years, set(), None) == 7.2

    def test_achievable_score_for_target(self):
        # Target 7.5 with Chemistry (4cr) available on top of Math(6cr)@8 + Physics(5cr)@6
        # Required chem grade = (7.5*15 - 78) / 4 = 8.625
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0)]),
            _subject("Physics", 5, [_assessment(2, 100, 6.0)]),
            _subject("Chemistry", 4, [_assessment(3, 100)]),
        ]])
        avg = _compute_weighted_average(years, {3}, 8.625)
        assert avg is not None and abs(avg - 7.5) < 0.01


# ---------------------------------------------------------------------------
# TestBuildDataPrompt — context builder structure and MANDATORY IDs checklist
# ---------------------------------------------------------------------------


class TestBuildDataPrompt:

    def test_contains_target_and_scope(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        prompt = _build_data_prompt(7.5, "Year 1", "", [2], years)
        assert "Target average: 7.5/10" in prompt
        assert "Scope: Year 1" in prompt

    def test_includes_student_note_when_provided(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100)])]])
        prompt = _build_data_prompt(7.0, "All Years", "Math is very hard for me", [1], years)
        assert "Math is very hard for me" in prompt

    def test_target_not_met_banner(self):
        # Math@6.0 (6cr) + Physics available (4cr): max achievable = (6*6+10*4)/10 = 7.6
        # target 7.0 is below max → achievable → TARGET NOT MET
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 6.0)]),
            _subject("Physics", 4, [_assessment(2, 100)]),
        ]])
        prompt = _build_data_prompt(7.0, "All Years", "", [2], years)
        assert "TARGET NOT MET" in prompt
        assert "TARGET ALREADY MET" not in prompt
        assert "IMPOSSIBLE" not in prompt

    def test_target_already_met_banner(self):
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 9.0)]),
            _subject("Physics", 4, [_assessment(2, 100)]),
        ]])
        prompt = _build_data_prompt(7.0, "All Years", "", [2], years)
        assert "TARGET ALREADY MET" in prompt

    def test_impossible_target_banner(self):
        # Max achievable with Chemistry at 10.0: (8*6+10*4)/10 = 8.8 < 9.5
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0)]),
            _subject("Chemistry", 4, [_assessment(2, 100)]),
        ]])
        prompt = _build_data_prompt(9.5, "All Years", "", [2], years)
        assert "IMPOSSIBLE" in prompt

    def test_no_available_assessments_banner(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        prompt = _build_data_prompt(9.0, "All Years", "", [], years)
        assert "NO AVAILABLE ASSESSMENTS" in prompt

    def test_mandatory_ids_present_for_ungraded_available_assessment(self):
        years = _make_years([[_subject("Math", 6, [_assessment(2, 100)])]])
        prompt = _build_data_prompt(7.0, "All Years", "", [2], years)
        assert "MANDATORY IDs" in prompt
        mandatory_line = next(l for l in prompt.split("\n") if "MANDATORY IDs" in l)
        assert "2" in mandatory_line

    def test_mandatory_ids_covers_all_subjects_and_assessments(self):
        # Both subjects have multiple ungraded available assessments
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 50), _assessment(2, 50)]),
            _subject("Physics", 4, [_assessment(3, 100)]),
        ]])
        prompt = _build_data_prompt(7.0, "All Years", "", [1, 2, 3], years)
        mandatory_line = next(l for l in prompt.split("\n") if "MANDATORY IDs" in l)
        assert "1" in mandatory_line
        assert "2" in mandatory_line
        assert "3" in mandatory_line

    def test_mandatory_ids_absent_when_all_available_are_already_graded(self):
        # Assessment 1 is available but already has a grade → not in mandatory list
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        prompt = _build_data_prompt(7.0, "All Years", "", [1], years)
        assert "MANDATORY IDs" not in prompt

    def test_mandatory_ids_absent_when_no_available_assessments(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        prompt = _build_data_prompt(7.0, "All Years", "", [], years)
        assert "MANDATORY IDs" not in prompt

    def test_mandatory_ids_excludes_graded_available_assessments(self):
        # ID 10: graded + available; ID 2: ungraded + available — only ID 2 is mandatory
        years = _make_years([[
            _subject("Math", 6, [_assessment(10, 50, 7.0), _assessment(2, 50)])
        ]])
        prompt = _build_data_prompt(7.0, "All Years", "", [10, 2], years)
        assert "MANDATORY IDs" in prompt
        mandatory_line = next(l for l in prompt.split("\n") if "MANDATORY IDs" in l)
        assert "2" in mandatory_line
        assert "10" not in mandatory_line

    def test_available_yes_no_flags(self):
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 60, 7.0), _assessment(2, 40)])
        ]])
        prompt = _build_data_prompt(8.0, "All Years", "", [2], years)
        assert "Assessment ID 1" in prompt and "Available to change: NO" in prompt
        assert "Assessment ID 2" in prompt and "Available to change: YES" in prompt

    def test_precomputed_averages_present(self):
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0)]),
            _subject("Physics", 4, [_assessment(2, 100)]),
        ]])
        prompt = _build_data_prompt(7.0, "All Years", "", [2], years)
        assert "Actual current average" in prompt
        assert "Maximum achievable" in prompt
        assert "Minimum achievable" in prompt

    def test_min_passing_score_scales_with_max_score(self):
        # passing_grade=5.0, max_grade=10.0, max_score=100.0 → min_passing=50.0
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0, max_score=100.0)])
        ]])
        prompt = _build_data_prompt(7.0, "All Years", "", [], years)
        assert "Min passing score: 50.0" in prompt

    def test_subject_passing_statuses(self):
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0)]),   # passing
            _subject("Physics", 4, [_assessment(2, 100, 3.0)]),  # failing
            _subject("Chemistry", 3, [_assessment(3, 100)]),   # no grades yet
        ]])
        prompt = _build_data_prompt(7.0, "All Years", "", [], years)
        assert "Subject passing: YES" in prompt
        assert "Subject passing: FAILING" in prompt
        assert "Subject passing: NO GRADES YET" in prompt

    def test_assessment_failing_flags(self):
        # min_passing = 5.0; score 3.0 → failing; score 7.0 → not failing; None → ungraded
        years = _make_years([[
            _subject("Math", 6, [
                _assessment(1, 34, 3.0),   # failing
                _assessment(2, 33, 7.0),   # passing
                _assessment(3, 33),         # ungraded
            ])
        ]])
        prompt = _build_data_prompt(7.0, "All Years", "", [3], years)
        assert "Currently failing: YES" in prompt
        assert "Currently failing: NO" in prompt
        assert "Currently failing: NO GRADE" in prompt


# ---------------------------------------------------------------------------
# TestExtractJson — JSON extraction from varied LLM output formats
# ---------------------------------------------------------------------------


class TestExtractJson:

    def test_clean_json_object(self):
        payload = {"grades": [], "message": ""}
        assert _extract_json(json.dumps(payload)) == payload

    def test_json_in_markdown_fences(self):
        payload = {"grades": [{"assessment_id": 1, "predicted_score": 8.0}], "message": ""}
        assert _extract_json(f"```json\n{json.dumps(payload)}\n```") == payload

    def test_json_embedded_in_prose(self):
        payload = {"grades": [], "message": "impossible"}
        assert _extract_json(f"Result: {json.dumps(payload)} Done.") == payload

    def test_json_with_surrounding_whitespace(self):
        payload = {"grades": [], "message": ""}
        assert _extract_json(f"  {json.dumps(payload)}  ") == payload

    def test_invalid_text_returns_none(self):
        assert _extract_json("not json") is None

    def test_empty_string_returns_none(self):
        assert _extract_json("") is None

    def test_code_block_without_json_returns_none(self):
        assert _extract_json("```python\nprint('hello')\n```") is None


# ---------------------------------------------------------------------------
# TestVerifySimulation — verify_simulation tool correctness
# ---------------------------------------------------------------------------


class TestVerifySimulation:

    def _set_client(self, years):
        client = MagicMock()
        client.get_academic_years.return_value = years
        set_api_client(client)

    def test_existing_grade_reflected_in_average(self):
        # Math: score 8.0, 100% weight, max_grade 10 → subject grade 8.0; avg = 8.0
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        self._set_client(years)
        result = verify_simulation.invoke({"proposed_scores_json": "{}"})
        assert "Weighted average: 8.00" in result

    def test_proposed_score_overrides_existing_grade(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 5.0)])]])
        self._set_client(years)
        result = verify_simulation.invoke({"proposed_scores_json": '{"1": 9.0}'})
        assert "9.00" in result
        assert "5.00" not in result

    def test_proposed_score_activates_ungraded_assessment(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100)])]])
        self._set_client(years)
        result = verify_simulation.invoke({"proposed_scores_json": '{"1": 8.0}'})
        assert "Weighted average: 8.00" in result

    def test_multiple_assessments_per_subject(self):
        # exam 60%@7.0 + project 40%@9.0 = 7.8
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 60, 7.0), _assessment(2, 40, 9.0)])
        ]])
        self._set_client(years)
        result = verify_simulation.invoke({"proposed_scores_json": "{}"})
        assert "7.80" in result

    def test_no_scores_at_all_returns_no_graded_message(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100)])]])
        self._set_client(years)
        result = verify_simulation.invoke({"proposed_scores_json": "{}"})
        assert "No graded subjects" in result

    def test_pass_fail_status_reported_per_subject(self):
        # Math proposed 9.0 → PASS; Physics proposed 2.0 → FAIL (below passing 5.0)
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100)]),
            _subject("Physics", 5, [_assessment(2, 100)]),
        ]])
        self._set_client(years)
        result = verify_simulation.invoke({"proposed_scores_json": '{"1": 9.0, "2": 2.0}'})
        assert "PASS" in result
        assert "FAIL" in result

    def test_invalid_json_returns_error_message(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        self._set_client(years)
        result = verify_simulation.invoke({"proposed_scores_json": "not json"})
        assert "Invalid input" in result

    def test_two_subjects_weighted_average_correct(self):
        # Math 6cr@8.0, Chemistry 4cr proposed 6.0 → (8*6+6*4)/10 = 7.2
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 8.0)]),
            _subject("Chemistry", 4, [_assessment(2, 100)]),
        ]])
        self._set_client(years)
        result = verify_simulation.invoke({"proposed_scores_json": '{"2": 6.0}'})
        assert "Weighted average: 7.20" in result


# ---------------------------------------------------------------------------
# TestGetCurrentGrades — assessment-level detail from the tool
# ---------------------------------------------------------------------------


class TestGetCurrentGrades:

    def test_shows_assessment_id_weight_and_score(self):
        years = _make_years([[_subject("Mathematics", 6, [_assessment(1, 100, 8.0)])]])
        client = MagicMock()
        client.get_academic_years.return_value = years
        set_api_client(client)

        result = get_current_grades.invoke({})
        assert "Mathematics" in result
        assert "[ID:1]" in result
        assert "weight: 100%" in result
        assert "8.0" in result

    def test_shows_no_grade_yet_for_ungraded_assessment(self):
        years = _make_years([[_subject("Physics", 5, [_assessment(2, 100)])]])
        client = MagicMock()
        client.get_academic_years.return_value = years
        set_api_client(client)

        result = get_current_grades.invoke({})
        assert "No grade yet" in result

    def test_shows_min_passing_score(self):
        # passing_grade=5.0, max_grade=10.0, max_score=10.0 → min passing = 5.0
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        client = MagicMock()
        client.get_academic_years.return_value = years
        set_api_client(client)

        result = get_current_grades.invoke({})
        assert "min passing: 5.0" in result

    def test_empty_years_returns_no_data_message(self):
        client = MagicMock()
        client.get_academic_years.return_value = []
        set_api_client(client)

        result = get_current_grades.invoke({})
        assert "No academic data found" in result

    def test_api_error_returns_error_message(self):
        client = MagicMock()
        client.get_academic_years.side_effect = Exception("Connection refused")
        set_api_client(client)

        result = get_current_grades.invoke({})
        assert "Error" in result

    def test_filter_by_year_id_excludes_other_years(self):
        years = [
            {"id": 1, "order_index": 1, "label": "Year 1",
             "subjects": [_subject("Math", 6, [_assessment(1, 100, 9.0)])]},
            {"id": 2, "order_index": 2, "label": "Year 2",
             "subjects": [_subject("Physics", 5, [_assessment(2, 100, 7.0)])]},
        ]
        client = MagicMock()
        client.get_academic_years.return_value = years
        set_api_client(client)

        result = get_current_grades.invoke({"year_id": 1})
        assert "Math" in result
        assert "Physics" not in result


# ---------------------------------------------------------------------------
# TestRunSimulation — mocked ReAct agent, verifies control flow
# ---------------------------------------------------------------------------


class TestRunSimulation:

    def _years(self):
        return _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 7.0)]),
            _subject("Physics", 5, [_assessment(2, 100)]),
        ]])

    def _msg(self, content):
        """Create a mock final agent message (no tool_calls)."""
        return MagicMock(content=content, tool_calls=None)

    @patch("agents.grade_simulator.create_react_agent")
    def test_returns_dict_with_grades_and_message_keys(self, mock_create_agent):
        payload = {"grades": [{"assessment_id": 2, "predicted_score": 8.5}], "message": ""}
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [self._msg(json.dumps(payload))]}
        mock_create_agent.return_value = mock_agent

        result = run_simulation(7.5, "", [2], None, self._years(), "All Years")

        assert isinstance(result, dict)
        assert "grades" in result and "message" in result
        assert result["grades"][0]["assessment_id"] == 2
        assert result["grades"][0]["predicted_score"] == 8.5

    @patch("agents.grade_simulator.create_react_agent")
    def test_retries_once_on_invalid_json(self, mock_create_agent):
        valid = {"grades": [], "message": "no assessments available"}
        mock_agent = MagicMock()
        mock_agent.invoke.side_effect = [
            {"messages": [self._msg("Here is my analysis: sorry, I cannot output JSON")]},
            {"messages": [self._msg(json.dumps(valid))]},
        ]
        mock_create_agent.return_value = mock_agent

        result = run_simulation(7.0, "", [], None, self._years(), "All Years")

        assert mock_agent.invoke.call_count == 2
        assert result == valid

    @patch("agents.grade_simulator.create_react_agent")
    def test_returns_fallback_after_two_json_failures(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [self._msg("I am unable to provide JSON.")]}
        mock_create_agent.return_value = mock_agent

        result = run_simulation(7.0, "", [1], None, self._years(), "All Years")

        assert mock_agent.invoke.call_count == 2
        assert result["grades"] == []
        assert "failed" in result["message"].lower()

    @patch("agents.grade_simulator.create_react_agent")
    def test_exception_from_agent_returns_error_dict(self, mock_create_agent):
        mock_agent = MagicMock()
        mock_agent.invoke.side_effect = RuntimeError("Ollama is not running")
        mock_create_agent.return_value = mock_agent

        result = run_simulation(7.0, "", [1], None, self._years(), "All Years")

        assert result["grades"] == []
        assert "Error" in result["message"]

    @patch("agents.grade_simulator.create_react_agent")
    def test_impossible_target_message_forwarded(self, mock_create_agent):
        payload = {
            "grades": [{"assessment_id": 2, "predicted_score": 10.0}],
            "message": "Target 9.5 is impossible. Best achievable is 8.73.",
        }
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [self._msg(json.dumps(payload))]}
        mock_create_agent.return_value = mock_agent

        result = run_simulation(9.5, "", [2], None, self._years(), "All Years")

        assert result["message"] != ""
        assert "impossible" in result["message"].lower() or "9.5" in result["message"]

    @patch("agents.grade_simulator.create_react_agent")
    def test_tool_call_messages_skipped_for_final_answer(self, mock_create_agent):
        """Messages with tool_calls set are not treated as the final answer."""
        payload = {"grades": [{"assessment_id": 2, "predicted_score": 7.0}], "message": ""}
        tool_msg = MagicMock(content="calling verify_simulation", tool_calls=[{"name": "verify_simulation"}])
        final_msg = MagicMock(content=json.dumps(payload), tool_calls=None)
        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {"messages": [tool_msg, final_msg]}
        mock_create_agent.return_value = mock_agent

        result = run_simulation(7.0, "", [2], None, self._years(), "All Years")

        assert result["grades"][0]["predicted_score"] == 7.0


# ---------------------------------------------------------------------------
# TestGradeSimulatorAgent — slow integration tests (require Ollama + llama3.2)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestGradeSimulatorAgent:

    def _client(self, years):
        client = MagicMock()
        client.get_academic_years.return_value = years
        return client

    def test_returns_valid_dict_structure(self):
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 7.0)]),
            _subject("Physics", 5, [_assessment(2, 100)]),
        ]])
        set_api_client(self._client(years))
        result = run_simulation(7.5, "", [2], None, years, "All Years")
        assert isinstance(result, dict)
        assert "grades" in result and "message" in result

    def test_predicted_scores_within_valid_range(self):
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 7.0)]),
            _subject("Physics", 5, [_assessment(2, 100)]),
        ]])
        set_api_client(self._client(years))
        result = run_simulation(7.5, "", [2], None, years, "All Years")
        for entry in result.get("grades", []):
            assert 1.0 <= entry["predicted_score"] <= 10.0, (
                f"Predicted score {entry['predicted_score']} out of [1, 10] range"
            )

    def test_no_available_assessments_returns_empty_grades(self):
        years = _make_years([[_subject("Math", 6, [_assessment(1, 100, 8.0)])]])
        set_api_client(self._client(years))
        result = run_simulation(9.0, "", [], None, years, "All Years")
        assert result.get("grades") == [] or result.get("message")

    def test_impossible_target_sets_message(self):
        # Math fixed at 2.0 (6cr), Physics available (6cr) — target 10.0 impossible
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 100, 2.0)]),
            _subject("Physics", 6, [_assessment(2, 100)]),
        ]])
        set_api_client(self._client(years))
        result = run_simulation(10.0, "", [2], None, years, "All Years")
        assert bool(result.get("message")) or bool(result.get("grades"))

    def test_predicts_all_ungraded_assessments_across_subjects(self):
        """
        All ungraded available assessments in every subject must appear in the output.
        Leaving any subject entirely ungraded inflates the average via a smaller
        denominator — the agent must not exploit this.
        """
        years = _make_years([[
            _subject("Math", 6, [_assessment(1, 50), _assessment(2, 50)]),
            _subject("Physics", 4, [_assessment(3, 40), _assessment(4, 60)]),
        ]])
        set_api_client(self._client(years))
        result = run_simulation(7.0, "", [1, 2, 3, 4], None, years, "All Years")
        predicted_ids = {e["assessment_id"] for e in result.get("grades", [])}
        assert predicted_ids == {1, 2, 3, 4}, (
            f"Expected all 4 assessment IDs in output, got: {predicted_ids}"
        )

    def test_predicts_every_assessment_within_a_subject(self):
        """
        Even when a single high-weight assessment could push a subject above its
        passing grade, every ungraded assessment in the subject must be predicted.
        """
        years = _make_years([[
            _subject("Math", 6, [
                _assessment(1, 30),
                _assessment(2, 40),
                _assessment(3, 30),
            ]),
        ]])
        set_api_client(self._client(years))
        result = run_simulation(6.0, "", [1, 2, 3], None, years, "All Years")
        predicted_ids = {e["assessment_id"] for e in result.get("grades", [])}
        assert {1, 2, 3}.issubset(predicted_ids), (
            f"Expected IDs 1, 2, 3 in output, got: {predicted_ids}"
        )

    def test_respects_student_note_for_score_distribution(self):
        years = _make_years([[
            _subject("Calculus", 5, [_assessment(1, 100)]),
            _subject("Biology", 5, [_assessment(2, 100)]),
        ]])
        set_api_client(self._client(years))
        result = run_simulation(
            7.0,
            "Calculus is very hard for me; Biology is my strength.",
            [1, 2], None, years, "All Years",
        )
        assert isinstance(result, dict)
        grades = {e["assessment_id"]: e["predicted_score"] for e in result.get("grades", [])}
        if 1 in grades and 2 in grades:
            assert grades[1] <= grades[2] + 2.0, (
                "Expected Calculus score no higher than Biology + 2 tolerance"
            )
