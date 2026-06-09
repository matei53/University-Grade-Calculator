"""
Tests for the graduation feature:
  - DashboardService.calculate_graduation_grade  (pure function, no API)
  - GraduationService  (API client mocked)
"""

from unittest.mock import MagicMock, patch

import pytest

from services.dashboard_service import DashboardService
from services.graduation_service import GraduationService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(subject_weight: float = 100.0, max_grade: float = 10.0) -> dict:
    return {"subject_average_weight": subject_weight, "max_grade": max_grade}


def _fa(
    fa_id: int,
    weight: float,
    max_score: float = 10.0,
    passing_grade: float = 5.0,
    score=None,
) -> dict:
    return {
        "id": fa_id,
        "name": f"Assessment {fa_id}",
        "weight": weight,
        "max_score": max_score,
        "passing_grade": passing_grade,
        "grade": {"score": score} if score is not None else None,
    }


# ---------------------------------------------------------------------------
# DashboardService.calculate_graduation_grade
# ---------------------------------------------------------------------------


class TestCalculateGraduationGrade:

    def test_returns_none_when_no_avg_and_no_assessments(self):
        assert DashboardService.calculate_graduation_grade(None, _settings(), []) is None

    def test_full_weight_on_subject_avg(self):
        result = DashboardService.calculate_graduation_grade(8.0, _settings(100.0), [])
        assert result == pytest.approx(8.0)

    def test_zero_subject_weight_no_graded_assessments(self):
        result = DashboardService.calculate_graduation_grade(8.0, _settings(0.0), [])
        assert result == pytest.approx(0.0)

    def test_single_assessment_contribution(self):
        # subject 60%, exam 40% (score=8/10), max_grade=10
        # expected: 0.6×7.0 + 0.4×(8/10)×10 = 4.2 + 3.2 = 7.4
        fa = _fa(1, weight=40.0, max_score=10.0, score=8.0)
        result = DashboardService.calculate_graduation_grade(7.0, _settings(60.0), [fa])
        assert result == pytest.approx(7.4, abs=0.01)

    def test_ungraded_assessment_is_skipped(self):
        # weight 30% has no score → contributes 0
        # expected: 0.7×8.0 + 0 = 5.6
        fa = _fa(1, weight=30.0, score=None)
        result = DashboardService.calculate_graduation_grade(8.0, _settings(70.0), [fa])
        assert result == pytest.approx(5.6, abs=0.01)

    def test_overall_avg_none_treated_as_zero(self):
        # overall_avg absent but assessment has grade
        # expected: 0.7×0 + 0.3×(9/10)×10 = 2.7
        fa = _fa(1, weight=30.0, max_score=10.0, score=9.0)
        result = DashboardService.calculate_graduation_grade(None, _settings(70.0), [fa])
        assert result == pytest.approx(2.7, abs=0.01)

    def test_non_standard_max_grade_scale(self):
        # max_grade=100, subject 60%, exam 40% (score=80/100)
        # expected: 0.6×60 + 0.4×(80/100)×100 = 36 + 32 = 68
        fa = _fa(1, weight=40.0, max_score=100.0, score=80.0)
        result = DashboardService.calculate_graduation_grade(
            60.0, _settings(60.0, max_grade=100.0), [fa]
        )
        assert result == pytest.approx(68.0, abs=0.01)

    def test_multiple_assessments_summed(self):
        # subject 60%, exam 30% (85/100), project 10% (9.5/10), max_grade=10
        # expected: 0.6×7.5 + 0.3×(85/100)×10 + 0.1×(9.5/10)×10
        #         = 4.5 + 2.55 + 0.95 = 8.0
        fa1 = _fa(1, weight=30.0, max_score=100.0, score=85.0)
        fa2 = _fa(2, weight=10.0, max_score=10.0, score=9.5)
        result = DashboardService.calculate_graduation_grade(7.5, _settings(60.0), [fa1, fa2])
        assert result == pytest.approx(8.0, abs=0.01)

    def test_result_is_rounded_to_two_decimal_places(self):
        fa = _fa(1, weight=33.3, max_score=3.0, score=1.0)
        result = DashboardService.calculate_graduation_grade(None, _settings(0.0), [fa])
        assert result is not None
        # Two decimal places means at most 2 digits after the dot
        parts = f"{result:.10f}".split(".")
        assert float(f"0.{parts[1]}") == pytest.approx(result % 1, abs=0.005)

    def test_weights_below_100_give_proportional_result(self):
        # Only 50% of score covered (25% subj + 25% assessment)
        fa = _fa(1, weight=25.0, max_score=10.0, score=10.0)
        result = DashboardService.calculate_graduation_grade(8.0, _settings(25.0), [fa])
        # 0.25×8 + 0.25×(10/10)×10 = 2.0 + 2.5 = 4.5
        assert result == pytest.approx(4.5, abs=0.01)


# ---------------------------------------------------------------------------
# GraduationService (client-side)
# ---------------------------------------------------------------------------


@pytest.fixture
def service():
    with patch("services.graduation_service.APIClient") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client
        svc = GraduationService()
        yield svc, mock_client


class TestGraduationService:

    def test_get_settings_delegates_to_client(self, service):
        svc, client = service
        client.get_graduation_settings.return_value = {
            "subject_average_weight": 80.0,
            "max_grade": 10.0,
        }
        result = svc.get_settings()
        client.get_graduation_settings.assert_called_once()
        assert result["subject_average_weight"] == 80.0

    def test_update_settings_passes_both_params(self, service):
        svc, client = service
        client.update_graduation_settings.return_value = {
            "subject_average_weight": 70.0,
            "max_grade": 10.0,
        }
        result = svc.update_settings(70.0, 10.0)
        client.update_graduation_settings.assert_called_once_with(70.0, 10.0)
        assert result["subject_average_weight"] == 70.0

    def test_get_final_assessments_returns_list(self, service):
        svc, client = service
        client.get_final_assessments.return_value = [{"id": 1, "name": "Exam"}]
        result = svc.get_final_assessments()
        client.get_final_assessments.assert_called_once()
        assert len(result) == 1 and result[0]["name"] == "Exam"

    def test_add_final_assessment_passes_all_fields(self, service):
        svc, client = service
        client.add_final_assessment.return_value = {"id": 2}
        svc.add_final_assessment("Project", 20.0, 50.0, 25.0)
        client.add_final_assessment.assert_called_once_with("Project", 20.0, 50.0, 25.0)

    def test_update_final_assessment_passes_partial_fields(self, service):
        svc, client = service
        client.update_final_assessment.return_value = {"id": 1}
        svc.update_final_assessment(1, name="New Name", weight=15.0)
        client.update_final_assessment.assert_called_once_with(1, "New Name", 15.0, None, None)

    def test_delete_final_assessment_calls_client(self, service):
        svc, client = service
        svc.delete_final_assessment(3)
        client.delete_final_assessment.assert_called_once_with(3)

    def test_set_grade_passes_score(self, service):
        svc, client = service
        client.set_final_assessment_grade.return_value = {
            "id": 1,
            "grade": {"score": 8.5},
        }
        result = svc.set_grade(1, 8.5)
        client.set_final_assessment_grade.assert_called_once_with(1, 8.5)
        assert result["grade"]["score"] == 8.5

    def test_set_grade_none_clears_score(self, service):
        svc, client = service
        client.set_final_assessment_grade.return_value = {
            "id": 1,
            "grade": {"score": None},
        }
        svc.set_grade(1, None)
        client.set_final_assessment_grade.assert_called_once_with(1, None)

    def test_get_settings_propagates_exception(self, service):
        svc, client = service
        client.get_graduation_settings.side_effect = ValueError("server error")
        with pytest.raises(ValueError, match="server error"):
            svc.get_settings()

    def test_add_assessment_propagates_exception(self, service):
        svc, client = service
        client.add_final_assessment.side_effect = ValueError("bad request")
        with pytest.raises(ValueError, match="bad request"):
            svc.add_final_assessment("Exam", 30.0)
