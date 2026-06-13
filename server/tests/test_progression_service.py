"""
Tests for the year progression eligibility service.

Covers get/create/update of progression requirements, per-year and cumulative
credit calculations, eligibility checks, and the all-years summary.
"""

import pytest

from server.models import Assessment, Grade, YearProgressionRequirement
from server.services.auth_service import AuthService
from server.services.progression_service import ProgressionService
from server.services.subject_service import AssessmentService, SubjectService


@pytest.fixture(scope="function")
def user_3yr(test_db, test_user_data):
    """User with 3 academic years (each has 2 semesters via AuthService)."""
    return AuthService.sign_up(
        test_db,
        test_user_data["username"],
        test_user_data["password"],
        test_user_data["num_years"],
        test_user_data["credit_requirements"],
    )


def _add_graded_subject(test_db, user_id, year_level, credits, score, weight=100.0, passing=5.0):
    """Helper: create a subject with one fully-weighted assessment and a grade."""
    subject = SubjectService.add_subject(
        test_db, user_id, f"Subject Y{year_level}", credits,
        semester_index=1, year_level=year_level, passing_grade=passing,
    )
    # Fetch the ORM object so we can attach a grade directly
    from server.models import Subject
    orm_subject = test_db.query(Subject).filter(Subject.id == subject.id).first()

    assessment = Assessment(subject_id=orm_subject.id, name="Exam", weight=weight, max_score=10.0, passing_grade=passing)
    test_db.add(assessment)
    test_db.flush()
    grade = Grade(assessment_id=assessment.id, score=score)
    test_db.add(grade)
    test_db.commit()
    return orm_subject


class TestGetOrCreateProgressionRequirement:
    def test_creates_new_requirement_with_defaults(self, test_db, user_3yr):
        req = ProgressionService.get_or_create_progression_requirement(
            test_db, user_3yr.id, target_year=2
        )
        assert req.target_year == 2
        assert req.credit_percentage == 70.0
        assert req.cumulative is False

    def test_returns_existing_requirement_unchanged(self, test_db, user_3yr):
        req1 = ProgressionService.get_or_create_progression_requirement(
            test_db, user_3yr.id, target_year=2, credit_percentage=80.0
        )
        req2 = ProgressionService.get_or_create_progression_requirement(
            test_db, user_3yr.id, target_year=2, credit_percentage=50.0
        )
        assert req1.id == req2.id
        assert req2.credit_percentage == 80.0  # original value preserved

    def test_different_target_years_create_separate_requirements(self, test_db, user_3yr):
        req2 = ProgressionService.get_or_create_progression_requirement(test_db, user_3yr.id, 2)
        req3 = ProgressionService.get_or_create_progression_requirement(test_db, user_3yr.id, 3)
        assert req2.id != req3.id
        assert req2.target_year == 2
        assert req3.target_year == 3


class TestGetProgressionRequirements:
    def test_empty_for_new_user(self, test_db, user_3yr):
        requirements = ProgressionService.get_progression_requirements(test_db, user_3yr.id)
        assert requirements == []

    def test_returns_all_requirements(self, test_db, user_3yr):
        ProgressionService.get_or_create_progression_requirement(test_db, user_3yr.id, 3)
        ProgressionService.get_or_create_progression_requirement(test_db, user_3yr.id, 2)
        requirements = ProgressionService.get_progression_requirements(test_db, user_3yr.id)
        assert len(requirements) == 2

    def test_ordered_ascending_by_target_year(self, test_db, user_3yr):
        ProgressionService.get_or_create_progression_requirement(test_db, user_3yr.id, 3)
        ProgressionService.get_or_create_progression_requirement(test_db, user_3yr.id, 2)
        requirements = ProgressionService.get_progression_requirements(test_db, user_3yr.id)
        years = [r.target_year for r in requirements]
        assert years == sorted(years)


class TestUpdateProgressionRequirement:
    def test_creates_if_missing_then_applies_value(self, test_db, user_3yr):
        updated = ProgressionService.update_progression_requirement(
            test_db, user_3yr.id, target_year=2, credit_percentage=85.0
        )
        assert updated.credit_percentage == 85.0
        assert updated.cumulative is False

    def test_updates_existing_percentage(self, test_db, user_3yr):
        ProgressionService.get_or_create_progression_requirement(test_db, user_3yr.id, 2, 70.0)
        updated = ProgressionService.update_progression_requirement(
            test_db, user_3yr.id, target_year=2, credit_percentage=90.0
        )
        assert updated.credit_percentage == 90.0

    def test_sets_cumulative_flag(self, test_db, user_3yr):
        updated = ProgressionService.update_progression_requirement(
            test_db, user_3yr.id, target_year=2, credit_percentage=70.0, cumulative=True
        )
        assert updated.cumulative is True


class TestCalculateYearCredits:
    def test_missing_academic_year_returns_zeros(self, test_db, user_3yr):
        earned, total = ProgressionService.calculate_year_credits(test_db, user_3yr.id, year_level=99)
        assert earned == 0
        assert total == 0

    def test_year_with_no_subjects_returns_zero_earned(self, test_db, user_3yr):
        # credit_requirement=60 for year 1; no subjects → no credits earned
        earned, total = ProgressionService.calculate_year_credits(test_db, user_3yr.id, year_level=1)
        assert earned == 0
        assert total == 60  # uses academic_year.credit_requirement, not sum of subjects

    def test_passing_subject_earns_credits(self, test_db, user_3yr):
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=6, score=7.0, passing=5.0)
        earned, total = ProgressionService.calculate_year_credits(test_db, user_3yr.id, year_level=1)
        assert earned == 6
        assert total == 60  # denominator is credit_requirement, not subject credit sum

    def test_failing_subject_earns_no_credits(self, test_db, user_3yr):
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=6, score=3.0, passing=5.0)
        earned, total = ProgressionService.calculate_year_credits(test_db, user_3yr.id, year_level=1)
        assert earned == 0
        assert total == 60

    def test_incomplete_weight_does_not_count_as_earned(self, test_db, user_3yr):
        # weight=50 means only 50% of the grade is assessed → total_weight < 100 → not counted
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=6, score=9.0, weight=50.0)
        earned, total = ProgressionService.calculate_year_credits(test_db, user_3yr.id, year_level=1)
        assert earned == 0
        assert total == 60

    def test_multiple_subjects_partial_pass(self, test_db, user_3yr):
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=6, score=7.0)   # passes
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=4, score=3.0)   # fails
        earned, total = ProgressionService.calculate_year_credits(test_db, user_3yr.id, year_level=1)
        assert earned == 6
        assert total == 60

    def test_ungraded_assessment_not_counted(self, test_db, user_3yr):
        # score=None → grade exists but is ungraded → total_weight stays 0 → not >= 100
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=6, score=None)
        earned, total = ProgressionService.calculate_year_credits(test_db, user_3yr.id, year_level=1)
        assert earned == 0
        assert total == 60

    def test_failed_assessment_blocks_credits_despite_passing_average(self, test_db, user_3yr):
        # Set up a subject where weighted avg passes but one assessment score < its passing_grade
        from server.models import Subject
        subject = SubjectService.add_subject(
            test_db, user_3yr.id, "Mixed", 6, semester_index=1, year_level=1, passing_grade=5.0,
        )
        orm_subject = test_db.query(Subject).filter(Subject.id == subject.id).first()
        # Exam: 8/10 weight=70 → passes its own passing_grade=5
        exam = Assessment(subject_id=orm_subject.id, name="Exam", weight=70.0, max_score=10.0, passing_grade=5.0)
        test_db.add(exam)
        test_db.flush()
        test_db.add(Grade(assessment_id=exam.id, score=8.0))
        # Coursework: 3/10 weight=30 → below passing_grade=5 → assessment failed
        cw = Assessment(subject_id=orm_subject.id, name="CW", weight=30.0, max_score=10.0, passing_grade=5.0)
        test_db.add(cw)
        test_db.flush()
        test_db.add(Grade(assessment_id=cw.id, score=3.0))
        test_db.commit()

        # Weighted avg = (8*70 + 3*30)/100 = 6.5 >= 5.0 (would normally pass)
        earned, total = ProgressionService.calculate_year_credits(test_db, user_3yr.id, year_level=1)
        assert earned == 0  # blocked by failed coursework assessment
        assert total == 60


class TestCalculateCumulativeCredits:
    def test_sums_passing_credits_across_years(self, test_db, user_3yr):
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=6, score=7.0)
        _add_graded_subject(test_db, user_3yr.id, year_level=2, credits=8, score=8.0)
        earned, total = ProgressionService.calculate_cumulative_credits(test_db, user_3yr.id, up_to_year=2)
        assert earned == 14
        assert total == 120  # credit_requirement 60 per year × 2 years

    def test_empty_years_return_zero_earned(self, test_db, user_3yr):
        # No subjects added; earned=0 but total = sum of credit_requirements for all 3 years
        earned, total = ProgressionService.calculate_cumulative_credits(test_db, user_3yr.id, up_to_year=3)
        assert earned == 0
        assert total == 180  # 60 × 3 years


class TestCheckYearEligibility:
    def test_eligible_when_percentage_met(self, test_db, user_3yr):
        # Add 50 credits of passing subjects in year 1 (credit_requirement=60) → 83.3% > 70%
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=50, score=7.0)
        result = ProgressionService.check_year_eligibility(test_db, user_3yr.id, target_year=2)
        assert result["is_eligible"] is True
        assert result["credits_earned"] == 50
        assert result["credits_required"] == 60  # academic_year.credit_requirement
        assert abs(result["current_percentage"] - 83.33) < 0.1
        assert result["target_year"] == 2

    def test_not_eligible_when_percentage_not_met(self, test_db, user_3yr):
        # 5 earned out of 60 required → ~8.3% < 70%
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=5, score=7.0)
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=5, score=2.0)
        result = ProgressionService.check_year_eligibility(test_db, user_3yr.id, target_year=2)
        assert result["is_eligible"] is False
        assert result["credits_earned"] == 5
        assert result["credits_required"] == 60

    def test_no_credits_not_eligible(self, test_db, user_3yr):
        result = ProgressionService.check_year_eligibility(test_db, user_3yr.id, target_year=2)
        assert result["is_eligible"] is False
        assert result["credits_earned"] == 0
        assert result["credits_required"] == 60  # still the credit_requirement, not 0
        assert result["current_percentage"] == 0.0

    def test_cumulative_mode_sums_prior_years(self, test_db, user_3yr):
        _add_graded_subject(test_db, user_3yr.id, year_level=1, credits=6, score=7.0)
        _add_graded_subject(test_db, user_3yr.id, year_level=2, credits=4, score=2.0)  # fails

        ProgressionService.update_progression_requirement(
            test_db, user_3yr.id, target_year=3, credit_percentage=70.0, cumulative=True
        )

        result = ProgressionService.check_year_eligibility(test_db, user_3yr.id, target_year=3)
        # Cumulative: Y1 earned 6, Y2 earned 0; total_required = 60+60 = 120; 6/120 = 5% < 70%
        assert result["cumulative"] is True
        assert result["is_eligible"] is False
        assert result["credits_earned"] == 6
        assert result["credits_required"] == 120

    def test_creates_default_requirement_on_first_check(self, test_db, user_3yr):
        ProgressionService.check_year_eligibility(test_db, user_3yr.id, target_year=2)
        reqs = test_db.query(YearProgressionRequirement).filter(
            YearProgressionRequirement.user_id == user_3yr.id
        ).all()
        assert len(reqs) == 1
        assert reqs[0].credit_percentage == 70.0


class TestGetAllYearEligibility:
    def test_returns_empty_for_nonexistent_user(self, test_db):
        result = ProgressionService.get_all_year_eligibility(test_db, user_id=9999)
        assert result == []

    def test_returns_empty_when_no_academic_years(self, test_db):
        from server.models import User
        user = User(username="noyr_user", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        result = ProgressionService.get_all_year_eligibility(test_db, user.id)
        assert result == []

    def test_returns_eligibility_for_years_2_and_3(self, test_db, user_3yr):
        # user_3yr has 3 academic years → eligibility for advancing to Year 2 and Year 3
        result = ProgressionService.get_all_year_eligibility(test_db, user_3yr.id)
        assert len(result) == 2
        target_years = {r["target_year"] for r in result}
        assert target_years == {2, 3}
