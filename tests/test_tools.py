"""
Unit tests for agents/tools.py helper functions and the get_current_grades tool.

All tests reset the module-level _api_client between runs so state doesn't leak.
"""

import pytest
from unittest.mock import MagicMock

import agents.tools as tools_module
from agents.tools import (
    _filter_years,
    _assessment_score,
    _get_api_client,
    set_api_client,
    get_current_grades,
)


@pytest.fixture(autouse=True)
def reset_api_client():
    """Restore _api_client to None after every test."""
    original = tools_module._api_client
    tools_module._api_client = None
    yield
    tools_module._api_client = original


class TestSetAndGetApiClient:
    def test_get_client_before_set_raises_runtime_error(self):
        with pytest.raises(RuntimeError, match="API client not set"):
            _get_api_client()

    def test_set_then_get_returns_client(self):
        mock = MagicMock()
        set_api_client(mock)
        assert _get_api_client() is mock

    def test_set_overwrites_previous_client(self):
        first = MagicMock(name="first")
        second = MagicMock(name="second")
        set_api_client(first)
        set_api_client(second)
        assert _get_api_client() is second


class TestFilterYears:
    def test_no_filter_returns_all(self):
        years = [{"id": 1}, {"id": 2}]
        assert _filter_years(years, None) == years

    def test_filter_by_matching_id_returns_one(self):
        years = [{"id": 1, "label": "Y1"}, {"id": 2, "label": "Y2"}]
        result = _filter_years(years, year_id=2)
        assert result == [{"id": 2, "label": "Y2"}]

    def test_filter_by_nonmatching_id_returns_empty(self):
        years = [{"id": 1}, {"id": 2}]
        assert _filter_years(years, year_id=99) == []

    def test_empty_list_returns_empty(self):
        assert _filter_years([], None) == []
        assert _filter_years([], year_id=1) == []


class TestAssessmentScore:
    def test_no_grade_key_returns_none(self):
        assert _assessment_score({}) is None

    def test_grade_is_none_returns_none(self):
        assert _assessment_score({"grade": None}) is None

    def test_grade_score_is_none_returns_none(self):
        assert _assessment_score({"grade": {"score": None}}) is None

    def test_grade_with_score_returns_float(self):
        assert _assessment_score({"grade": {"score": 7.5}}) == 7.5

    def test_integer_score_converted_to_float(self):
        result = _assessment_score({"grade": {"score": 8}})
        assert result == 8.0
        assert isinstance(result, float)

    def test_zero_score_returns_zero(self):
        assert _assessment_score({"grade": {"score": 0}}) == 0.0


class TestGetCurrentGradesTool:
    def test_no_client_set_returns_error_string(self):
        # LangChain tools must not raise — they return an error description instead.
        result = get_current_grades.invoke({"year_id": None})
        assert "Error" in result

    def test_returns_no_subjects_message_when_empty(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = []
        set_api_client(mock_client)

        result = get_current_grades.invoke({"year_id": None})
        assert "No academic data found" in result

    def test_returns_grades_for_graded_assessment(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = [
            {
                "id": 1,
                "label": "Year 1",
                "order_index": 1,
                "subjects": [
                    {
                        "name": "Maths",
                        "credit_value": 6,
                        "passing_grade": 5.0,
                        "max_grade": 10.0,
                        "assessments": [
                            {"id": 1, "name": "Exam", "weight": 100.0, "max_score": 10.0,
                             "grade": {"score": 8.0}},
                        ],
                    }
                ],
            }
        ]
        set_api_client(mock_client)

        result = get_current_grades.invoke({"year_id": None})
        assert "Maths" in result
        assert "score: 8.0" in result
        assert "Year 1" in result

    def test_returns_no_grade_message_for_ungraded_assessment(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = [
            {
                "id": 1,
                "order_index": 1,
                "subjects": [
                    {
                        "name": "Physics",
                        "credit_value": 4,
                        "passing_grade": 5.0,
                        "max_grade": 10.0,
                        "assessments": [
                            {"weight": 100.0, "max_score": 10.0, "grade": {"score": None}},
                        ],
                    }
                ],
            }
        ]
        set_api_client(mock_client)

        result = get_current_grades.invoke({"year_id": None})
        assert "Physics" in result
        assert "No grade yet" in result

    def test_filter_by_year_id_excludes_other_years(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.return_value = [
            {"id": 1, "order_index": 1, "subjects": [
                {"name": "Year1Subject", "credit_value": 4, "passing_grade": 5.0,
                 "max_grade": 10.0, "assessments": []}
            ]},
            {"id": 2, "order_index": 2, "subjects": [
                {"name": "Year2Subject", "credit_value": 4, "passing_grade": 5.0,
                 "max_grade": 10.0, "assessments": []}
            ]},
        ]
        set_api_client(mock_client)

        result = get_current_grades.invoke({"year_id": 2})
        assert "Year2Subject" in result
        assert "Year1Subject" not in result

    def test_api_error_returns_error_string(self):
        mock_client = MagicMock()
        mock_client.get_academic_years.side_effect = ConnectionError("server down")
        set_api_client(mock_client)

        result = get_current_grades.invoke({"year_id": None})
        assert "Error fetching grades" in result
