"""
Tests for the career advisor agent and tools.

Unit tests cover:
  - get_academic_profile tool
  - generate_career_guidance: rule-based fallback (always rule-based, no LLM)
  - run_career_guidance: API client integration and fallback behaviour

Integration tests (marked @pytest.mark.slow) invoke the real LLM agent and
require a running Ollama instance with llama3.2.
"""

from unittest.mock import MagicMock, patch

import pytest

from agents.career_advisor import generate_career_guidance, run_career_guidance
from agents.tools import get_academic_profile, set_api_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _subject(name: str, grade_score) -> dict:
    """Build a subject dict with a single assessment in the correct API format."""
    return {
        "name": name,
        "credit_value": 5,
        "assessments": [
            {
                "id": 1,
                "name": "Final Exam",
                "weight": 100.0,
                "max_score": 10.0,
                "grade": {"id": 1, "score": grade_score} if grade_score is not None else None,
            }
        ],
    }


def _student(*subjects: dict) -> dict:
    return {"years": [{"id": 1, "label": "Year 1", "order_index": 1, "subjects": list(subjects)}]}


MEDICINE_DATA = _student(
    _subject("Anatomy", 9.0),
    _subject("Physiology", 8.5),
    _subject("Biochemistry", 7.5),
    _subject("Clinical Practice", 9.2),
)

MIXED_SCORES_DATA = _student(
    _subject("Advanced Mathematics", 9.5),
    _subject("Statistics", 9.0),
    _subject("Literature", 4.0),
    _subject("History", 5.0),
)

EMPTY_DATA: dict = {"years": []}
NO_GRADES_DATA = _student(_subject("Physics", None))


# ---------------------------------------------------------------------------
# TestGetAcademicProfile — profile tool formats student data correctly
# ---------------------------------------------------------------------------


class TestGetAcademicProfile:

    def _set_client(self, years):
        client = MagicMock()
        client.get_academic_years.return_value = years
        set_api_client(client)

    def test_shows_year_label_and_subject_names(self):
        self._set_client(MEDICINE_DATA["years"])
        result = get_academic_profile.invoke({})
        assert "Year 1" in result
        assert "Anatomy" in result
        assert "Physiology" in result

    def test_shows_credit_value_per_subject(self):
        self._set_client(MEDICINE_DATA["years"])
        result = get_academic_profile.invoke({})
        assert "5 credits" in result

    def test_shows_numeric_score_for_graded_assessment(self):
        self._set_client(MEDICINE_DATA["years"])
        result = get_academic_profile.invoke({})
        assert "9.0" in result   # Anatomy score

    def test_shows_not_graded_for_ungraded_assessment(self):
        self._set_client(NO_GRADES_DATA["years"])
        result = get_academic_profile.invoke({})
        assert "not graded" in result

    def test_computes_subject_average_correctly(self):
        # Two assessments with scores 8.0 and 6.0 → average 7.0
        years = [{"id": 1, "label": "Year 1", "subjects": [
            {"name": "Math", "credit_value": 5, "assessments": [
                {"id": 1, "name": "Exam 1", "weight": 50, "max_score": 10,
                 "grade": {"id": 1, "score": 8.0}},
                {"id": 2, "name": "Exam 2", "weight": 50, "max_score": 10,
                 "grade": {"id": 2, "score": 6.0}},
            ]}
        ]}]
        self._set_client(years)
        result = get_academic_profile.invoke({})
        assert "average: 7.0" in result

    def test_shows_no_grades_yet_for_fully_ungraded_subject(self):
        self._set_client(NO_GRADES_DATA["years"])
        result = get_academic_profile.invoke({})
        assert "no grades yet" in result

    def test_empty_years_returns_no_data_message(self):
        self._set_client([])
        result = get_academic_profile.invoke({})
        assert "No academic data found" in result

    def test_api_error_returns_error_message(self):
        client = MagicMock()
        client.get_academic_years.side_effect = Exception("Timeout")
        set_api_client(client)
        result = get_academic_profile.invoke({})
        assert "Error" in result


# ---------------------------------------------------------------------------
# TestFallbackGuidance — generate_career_guidance is always rule-based
# ---------------------------------------------------------------------------


class TestFallbackGuidance:

    def test_returns_non_empty_string(self):
        assert len(generate_career_guidance(MEDICINE_DATA)) > 0

    def test_output_contains_required_sections(self):
        result = generate_career_guidance(MEDICINE_DATA)
        assert "Strengths" in result
        assert "Career Path" in result
        assert "Elective" in result
        assert "Motivational" in result

    def test_high_scoring_subjects_appear_in_strengths(self):
        result = generate_career_guidance(MEDICINE_DATA)
        # Every medicine subject scores ≥ 7.0 — at least one must be listed
        assert any(
            name in result
            for name in ("Anatomy", "Physiology", "Biochemistry", "Clinical Practice")
        )

    def test_low_scoring_subjects_absent_from_strengths_section(self):
        result = generate_career_guidance(MIXED_SCORES_DATA)
        strengths_section = result.split("## Strengths")[1].split("##")[0]
        # Literature (4.0) and History (5.0) are below the 7.0 threshold
        assert "Literature" not in strengths_section
        assert "History" not in strengths_section

    def test_high_scoring_subjects_present_in_strengths_section(self):
        result = generate_career_guidance(MIXED_SCORES_DATA)
        strengths_section = result.split("## Strengths")[1].split("##")[0]
        assert "Mathematics" in strengths_section or "Statistics" in strengths_section

    def test_handles_empty_years_list(self):
        result = generate_career_guidance(EMPTY_DATA)
        assert isinstance(result, str) and "Strengths" in result

    def test_handles_subjects_with_no_grades(self):
        result = generate_career_guidance(NO_GRADES_DATA)
        # No scored subjects → generic "consistent effort" fallback strength
        assert "Consistent" in result

    def test_uses_correct_api_grade_format(self):
        """generate_career_guidance must read grade.score, not grade_score."""
        # Build data with a high score only accessible via grade.score
        data = _student(_subject("Top Subject", 9.5))
        result = generate_career_guidance(data)
        assert "Top Subject" in result


# ---------------------------------------------------------------------------
# TestRunCareerGuidance — API client integration in the fallback path
# ---------------------------------------------------------------------------


class TestRunCareerGuidance:

    def test_always_returns_a_string(self):
        client = MagicMock()
        client.get_academic_years.return_value = []
        with patch("agents.career_advisor.ChatOllama", None):
            assert isinstance(run_career_guidance(client), str)

    def test_fallback_path_calls_get_academic_years(self):
        client = MagicMock()
        client.get_academic_years.return_value = []
        with patch("agents.career_advisor.ChatOllama", None):
            run_career_guidance(client)
        client.get_academic_years.assert_called_once()

    def test_fallback_output_contains_required_sections(self):
        client = MagicMock()
        client.get_academic_years.return_value = []
        with patch("agents.career_advisor.ChatOllama", None):
            result = run_career_guidance(client)
        assert "Strengths" in result
        assert "Career" in result

    def test_fallback_guidance_reflects_api_data(self):
        """High-scoring subjects from the API must appear in the fallback output."""
        years = [{"id": 1, "label": "Year 1", "subjects": [
            {"name": "Distinctive Subject", "credit_value": 5, "assessments": [
                {"id": 1, "name": "Exam", "weight": 100, "max_score": 10,
                 "grade": {"id": 1, "score": 9.5}}
            ]}
        ]}]
        client = MagicMock()
        client.get_academic_years.return_value = years
        with patch("agents.career_advisor.ChatOllama", None):
            result = run_career_guidance(client)
        assert "Distinctive Subject" in result

    def test_fallback_passes_years_to_generate_career_guidance(self):
        """In the fallback path, generate_career_guidance must receive {"years": <api_years>}."""
        years = [{"id": 1, "label": "Year 1", "subjects": []}]
        client = MagicMock()
        client.get_academic_years.return_value = years
        with patch("agents.career_advisor.ChatOllama", None):
            with patch("agents.career_advisor.generate_career_guidance") as mock_gen:
                mock_gen.return_value = "# Guidance"
                run_career_guidance(client)
        assert mock_gen.call_args[0][0] == {"years": years}


# ---------------------------------------------------------------------------
# TestCareerAdvisorLLM — slow integration tests (require Ollama + llama3.2)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestCareerAdvisorLLM:
    """
    Eval tests that invoke the real career advisor ReAct agent.
    Run with: pytest -m slow tests/test_career_advisor_eval.py
    These tests verify output quality, not exact wording.
    """

    def _client(self, student_data: dict) -> MagicMock:
        client = MagicMock()
        client.get_academic_years.return_value = student_data.get("years", [])
        return client

    def test_returns_non_empty_markdown(self):
        result = run_career_guidance(self._client(MEDICINE_DATA))
        assert isinstance(result, str) and len(result) > 100

    def test_output_contains_required_sections(self):
        result = run_career_guidance(self._client(MEDICINE_DATA))
        result_lower = result.lower()
        # Strengths may appear as a heading, inline keyword, or as "strong/strength/excel/perform"
        assert "strength" in result_lower or "perform" in result_lower or "excel" in result_lower
        assert "career" in result_lower
        assert "elective" in result_lower or "recommend" in result_lower or "course" in result_lower
        assert "motivat" in result_lower or "advice" in result_lower

    def test_field_agnostic_for_medicine_student(self):
        """Must not default to CS careers when all subjects are medical."""
        result = run_career_guidance(self._client(MEDICINE_DATA))
        result_lower = result.lower()
        assert any(
            kw in result_lower
            for kw in ("medicine", "medical", "health", "clinical", "doctor",
                        "physician", "pharmacist", "biology", "research")
        ), "Agent produced no health-related career terms for a medicine student"
        pure_cs = (
            "software engineer" in result_lower
            and "data scientist" in result_lower
            and not any(kw in result_lower for kw in ("health", "medical", "biology", "clinical"))
        )
        assert not pure_cs, "Agent defaulted to CS-only careers for a medicine student"

    def test_output_references_actual_subjects(self):
        """The agent should acknowledge the student's real subjects."""
        result = run_career_guidance(self._client(MEDICINE_DATA))
        result_lower = result.lower()
        assert any(
            name in result_lower
            for name in ("anatomy", "physiology", "biochemistry", "clinical")
        ), "Agent output does not reference any of the student's actual subjects"
