"""
Tests and evaluation for agents/career_advisor.py.

Unit tests (no LLM required) cover the rule-based fallback and the API
integration in run_career_guidance().
Eval tests (marked @pytest.mark.slow) invoke the real LLM and require a
running Ollama instance with llama3.2.
"""

from unittest.mock import MagicMock, patch

import pytest

from agents.career_advisor import generate_career_guidance, run_career_guidance

# ---------------------------------------------------------------------------
# Fixtures / data builders
# ---------------------------------------------------------------------------


def _subject(name: str, grade_score) -> dict:
    """Build a subject dict with a single assessment, matching the API response shape."""
    return {
        "name": name,
        "credit_value": 5,
        "assessments": [
            {
                "id": 1,
                "name": "Final Exam",
                "weight": 100.0,
                "max_score": 10.0,
                "grade_score": grade_score,
            }
        ],
    }


def _student(*subjects: dict) -> dict:
    return {"years": [{"id": 1, "label": "Year 1", "order_index": 1, "subjects": list(subjects)}]}


# Representative datasets used across multiple test classes
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
# TestFallbackGuidance — behaviour when ChatOllama is unavailable
# ---------------------------------------------------------------------------


class TestFallbackGuidance:
    """Rule-based fallback used when Ollama is not running."""

    @pytest.fixture(autouse=True)
    def disable_llm(self):
        with patch("agents.career_advisor.ChatOllama", None):
            yield

    def test_returns_non_empty_string(self):
        assert len(generate_career_guidance(MEDICINE_DATA)) > 0

    def test_output_contains_required_sections(self):
        result = generate_career_guidance(MEDICINE_DATA)
        assert "Strengths" in result
        assert "Career Path" in result
        assert "Elective" in result
        assert "Motivational" in result

    def test_identifies_high_scoring_subjects_as_strengths(self):
        result = generate_career_guidance(MEDICINE_DATA)
        # Every medicine subject scores >= 7.0 — at least one should appear
        assert any(
            name in result
            for name in ("Anatomy", "Physiology", "Biochemistry", "Clinical Practice")
        )

    def test_low_scoring_subjects_absent_from_strengths(self):
        result = generate_career_guidance(MIXED_SCORES_DATA)
        # Strengths section is between "## Strengths" and the next "##"
        strengths_section = result.split("## Strengths")[1].split("##")[0]
        # Literature (4.0) and History (5.0) are below the 7.0 threshold
        assert "Literature" not in strengths_section
        assert "History" not in strengths_section

    def test_high_scoring_subjects_present_in_strengths(self):
        result = generate_career_guidance(MIXED_SCORES_DATA)
        strengths_section = result.split("## Strengths")[1].split("##")[0]
        assert "Mathematics" in strengths_section or "Statistics" in strengths_section

    def test_handles_empty_student_data(self):
        result = generate_career_guidance(EMPTY_DATA)
        assert isinstance(result, str)
        assert "Strengths" in result

    def test_handles_subjects_with_no_grades(self):
        result = generate_career_guidance(NO_GRADES_DATA)
        # No graded subjects → fallback strength is the generic "consistent effort" message
        assert "Consistent" in result


# ---------------------------------------------------------------------------
# TestRunCareerGuidance — API client integration
# ---------------------------------------------------------------------------


class TestRunCareerGuidance:
    """run_career_guidance() must fetch years via the API client and pass them on."""

    def test_calls_get_academic_years_once(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = []
        with patch("agents.career_advisor.ChatOllama", None):
            run_career_guidance(mock_client)
        mock_client.get_academic_years.assert_called_once()

    def test_wraps_years_under_years_key(self):
        years = [{"id": 1, "label": "Year 1", "subjects": []}]
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = years
        with patch("agents.career_advisor.generate_career_guidance") as mock_gen:
            mock_gen.return_value = "# Guidance"
            run_career_guidance(mock_client)
        assert mock_gen.call_args[0][0] == {"years": years}

    def test_returns_string(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = []
        with patch("agents.career_advisor.ChatOllama", None):
            assert isinstance(run_career_guidance(mock_client), str)


# ---------------------------------------------------------------------------
# TestCareerAdvisorLLM — integration eval (requires Ollama + llama3.2)
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestCareerAdvisorLLM:
    """
    Eval tests that invoke the real LLM.
    Run with: pytest -m slow tests/test_career_advisor_eval.py
    These tests verify output quality, not exact wording.
    """

    def test_returns_non_empty_markdown(self):
        result = generate_career_guidance(MEDICINE_DATA)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_output_contains_required_sections(self):
        result = generate_career_guidance(MEDICINE_DATA)
        assert "Strengths" in result
        assert "Career" in result
        # Accept either "Elective" or "Recommended" header
        assert "Elective" in result or "Recommended" in result
        assert "Advice" in result or "Motivational" in result

    def test_output_is_field_agnostic_for_medicine_student(self):
        """The LLM must not default to CS careers when all subjects are medical."""
        result = generate_career_guidance(MEDICINE_DATA)
        result_lower = result.lower()
        # Should reference health/medicine domain
        assert any(
            kw in result_lower
            for kw in (
                "medicine",
                "medical",
                "health",
                "clinical",
                "doctor",
                "physician",
                "pharmacist",
                "biology",
                "research",
            )
        ), "LLM produced no health-related career terms for a medicine student"
        # Must not be a pure CS response with zero health context
        pure_cs = (
            "software engineer" in result_lower
            and "data scientist" in result_lower
            and not any(kw in result_lower for kw in ("health", "medical", "biology", "clinical"))
        )
        assert not pure_cs, "LLM defaulted to CS-only careers for a medicine student"

    def test_output_references_actual_subjects(self):
        """The LLM should acknowledge the student's real subjects."""
        result = generate_career_guidance(MEDICINE_DATA)
        result_lower = result.lower()
        subject_names = ["anatomy", "physiology", "biochemistry", "clinical"]
        assert any(
            name in result_lower for name in subject_names
        ), "LLM output does not reference any of the student's actual subjects"
