"""Tests for DashboardService.calculate_stats — pure static method."""

from services.dashboard_service import DashboardService


def _year(subjects):
    return {"subjects": subjects}


def _subject(name, credits, grade, passing_grade=5.0, assessments=None):
    return {
        "name": name,
        "credits": credits,
        "grade": grade,
        "passing_grade": passing_grade,
        "assessments": assessments or [],
    }


def _assessment(grade_score, passing_grade=5.0):
    return {"grade_score": grade_score, "passing_grade": passing_grade}


class TestCalculateStats:

    def test_single_graded_subject(self):
        data = {1: _year([_subject("Math", 6, 8.0)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["weighted_avg"] == 8.0
        assert stats["credits"] == 6

    def test_two_subjects_weighted_average(self):
        # (8*6 + 6*5) / (6+5) = 78/11 ≈ 7.09
        data = {
            1: _year(
                [
                    _subject("Math", 6, 8.0),
                    _subject("Physics", 5, 6.0),
                ]
            )
        }
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert abs(stats["weighted_avg"] - 78 / 11) < 0.01
        assert stats["credits"] == 11

    def test_ungraded_subject_excluded_from_average_and_credits(self):
        data = {
            1: _year(
                [
                    _subject("Math", 6, 8.0),
                    _subject("Physics", 5, None),
                ]
            )
        }
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["weighted_avg"] == 8.0
        assert stats["credits"] == 6

    def test_failing_subject_counts_in_average_not_credits(self):
        # Both contribute to weighted avg; only passing subject earns credits
        data = {
            1: _year(
                [
                    _subject("Math", 6, 8.0),
                    _subject("Physics", 5, 4.0),  # below passing_grade=5.0
                ]
            )
        }
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        # (8*6 + 4*5) / 11 = 68/11 ≈ 6.18
        assert abs(stats["weighted_avg"] - 68 / 11) < 0.01
        assert stats["credits"] == 6  # only Math credits

    def test_up_to_year_excludes_later_years(self):
        data = {
            1: _year([_subject("Math", 6, 8.0)]),
            2: _year([_subject("Physics", 5, 6.0)]),
        }
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["weighted_avg"] == 8.0
        assert stats["credits"] == 6

    def test_multiple_years_cumulative(self):
        # (8*6 + 6*4) / 10 = 7.2
        data = {
            1: _year([_subject("Math", 6, 8.0)]),
            2: _year([_subject("Physics", 4, 6.0)]),
        }
        stats = DashboardService.calculate_stats(data, up_to_year=2)
        assert stats["weighted_avg"] == 7.2
        assert stats["credits"] == 10

    def test_empty_data_returns_zeros(self):
        stats = DashboardService.calculate_stats({}, up_to_year=1)
        assert stats["weighted_avg"] == 0.0
        assert stats["credits"] == 0
        assert stats["progress"] == 0

    def test_progress_percentage(self):
        # 60 earned out of 180 total = 33%
        data = {1: _year([_subject("Math", 60, 8.0)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1, total_program_credits=180)
        assert stats["progress"] == 33

    def test_zero_total_program_credits_does_not_divide_by_zero(self):
        data = {1: _year([_subject("Math", 6, 8.0)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1, total_program_credits=0)
        assert stats["progress"] == 0

    def test_custom_passing_grade_per_subject(self):
        # passing_grade=7.0, grade=6.0 → fails, no credits earned
        data = {1: _year([_subject("Math", 6, 6.0, passing_grade=7.0)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["credits"] == 0
        assert stats["weighted_avg"] == 6.0  # still contributes to avg

    def test_all_subjects_ungraded_average_is_zero(self):
        data = {
            1: _year(
                [
                    _subject("Math", 6, None),
                    _subject("Physics", 5, None),
                ]
            )
        }
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["weighted_avg"] == 0.0
        assert stats["credits"] == 0

    def test_year_exactly_at_boundary_included(self):
        data = {3: _year([_subject("Math", 6, 9.0)])}
        stats = DashboardService.calculate_stats(data, up_to_year=3)
        assert stats["weighted_avg"] == 9.0


class TestCalculateStatsAssessmentFailure:
    """A subject is failed (credits not earned) if any single assessment score is below
    that assessment's passing_grade, even when the weighted average passes."""

    def test_failed_assessment_blocks_credits_even_with_passing_average(self):
        # Weighted avg: (8*0.7 + 3*0.3)*10/10 = (5.6+0.9) = 6.5 >= 5.0 (passes)
        # But assessment 2 score=3 < passing_grade=5 → no credits earned
        assessments = [
            _assessment(grade_score=8.0, passing_grade=5.0),
            _assessment(grade_score=3.0, passing_grade=5.0),
        ]
        data = {1: _year([_subject("Math", 6, 6.5, assessments=assessments)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["credits"] == 0
        assert abs(stats["weighted_avg"] - 6.5) < 0.01  # avg still contributes

    def test_all_passing_assessments_earns_credits(self):
        assessments = [
            _assessment(grade_score=7.0, passing_grade=5.0),
            _assessment(grade_score=6.0, passing_grade=5.0),
        ]
        data = {1: _year([_subject("Math", 6, 8.0, assessments=assessments)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["credits"] == 6

    def test_ungraded_assessment_does_not_trigger_failure(self):
        # grade_score=None means not yet graded — should not count as a failure
        assessments = [
            _assessment(grade_score=8.0, passing_grade=5.0),
            _assessment(grade_score=None, passing_grade=5.0),
        ]
        data = {1: _year([_subject("Math", 6, 8.0, assessments=assessments)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["credits"] == 6

    def test_no_assessments_falls_back_to_subject_grade_only(self):
        # Existing behaviour: subjects without assessments list use grade >= passing_grade
        data = {1: _year([_subject("Math", 6, 8.0)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        assert stats["credits"] == 6

    def test_assessment_failure_uses_assessment_passing_grade_not_subject(self):
        # Assessment has a stricter passing_grade than the subject
        assessments = [_assessment(grade_score=6.0, passing_grade=7.0)]
        data = {1: _year([_subject("Math", 6, 6.0, passing_grade=5.0, assessments=assessments)])}
        stats = DashboardService.calculate_stats(data, up_to_year=1)
        # subject grade 6.0 >= 5.0 passes, but assessment 6.0 < 7.0 → fails
        assert stats["credits"] == 0
