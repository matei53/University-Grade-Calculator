"""Tests for services/grade_service.py — pure static methods."""

from services.grade_service import GradeService


class TestValidateWeightsTotal:

    def test_two_assessments_summing_to_100(self):
        assert GradeService.validate_weights_total([{"weight": 60}, {"weight": 40}]) is True

    def test_three_assessments_summing_to_100(self):
        assert (
            GradeService.validate_weights_total([{"weight": 40}, {"weight": 30}, {"weight": 30}])
            is True
        )

    def test_single_assessment_at_100(self):
        assert GradeService.validate_weights_total([{"weight": 100}]) is True

    def test_float_weights_summing_to_100(self):
        assert (
            GradeService.validate_weights_total(
                [{"weight": 33.33}, {"weight": 33.33}, {"weight": 33.34}]
            )
            is True
        )

    def test_sum_below_100_returns_false(self):
        assert GradeService.validate_weights_total([{"weight": 60}, {"weight": 30}]) is False

    def test_sum_above_100_returns_false(self):
        assert GradeService.validate_weights_total([{"weight": 60}, {"weight": 50}]) is False

    def test_empty_list_returns_false(self):
        assert GradeService.validate_weights_total([]) is False

    def test_missing_weight_key_treated_as_zero(self):
        # One assessment has no weight key → defaults to 0 → total = 60 ≠ 100
        assert GradeService.validate_weights_total([{"score": 8}, {"weight": 60}]) is False


class TestCalculateSubjectAverage:

    def test_single_full_weight_assessment(self):
        # (8/10) * 1.0 * 10 = 8.0
        a = [{"score": 8, "weight": 100, "max_score": 10}]
        assert GradeService.calculate_subject_average(a) == 8.0

    def test_two_assessments_standard_scale(self):
        # exam: (7/10)*0.6*10=4.2, project: (9/10)*0.4*10=3.6 → 7.8
        a = [
            {"score": 7, "weight": 60, "max_score": 10},
            {"score": 9, "weight": 40, "max_score": 10},
        ]
        assert GradeService.calculate_subject_average(a) == 7.8

    def test_non_standard_max_score(self):
        # (75/100) * 1.0 * 10 = 7.5
        a = [{"score": 75, "weight": 100, "max_score": 100}]
        assert GradeService.calculate_subject_average(a) == 7.5

    def test_ungraded_assessment_skipped(self):
        # Only the 60%-weight assessment has a score: (8/10)*0.6*10 = 4.8
        a = [
            {"score": 8, "weight": 60, "max_score": 10},
            {"score": None, "weight": 40, "max_score": 10},
        ]
        assert GradeService.calculate_subject_average(a) == 4.8

    def test_all_ungraded_returns_zero(self):
        a = [{"score": None, "weight": 100, "max_score": 10}]
        assert GradeService.calculate_subject_average(a) == 0.0

    def test_empty_assessments_returns_zero(self):
        assert GradeService.calculate_subject_average([]) == 0.0

    def test_custom_subject_max_grade(self):
        # (8/10) * 1.0 * 20 = 16.0
        a = [{"score": 8, "weight": 100, "max_score": 10}]
        assert GradeService.calculate_subject_average(a, subject_max_grade=20.0) == 16.0

    def test_perfect_score(self):
        a = [{"score": 10, "weight": 100, "max_score": 10}]
        assert GradeService.calculate_subject_average(a) == 10.0

    def test_minimum_score(self):
        a = [{"score": 1, "weight": 100, "max_score": 10}]
        assert GradeService.calculate_subject_average(a) == 1.0
