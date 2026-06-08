"""Tests for services/graduation_service.py."""

import pytest

from models import User
from services.auth_service import AuthService
from services.graduation_service import GraduationService


class TestGraduationSettings:

    @pytest.fixture
    def user(self, test_db, test_user_data):
        return AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
            test_user_data["credit_requirements"],
        )

    def test_get_or_create_settings_creates_with_defaults(self, test_db, user):
        settings = GraduationService.get_or_create_settings(test_db, user.id)

        assert settings.user_id == user.id
        assert settings.subject_average_weight == 100.0
        assert settings.max_grade == 10.0

    def test_get_or_create_settings_returns_existing(self, test_db, user):
        first = GraduationService.get_or_create_settings(test_db, user.id)
        second = GraduationService.get_or_create_settings(test_db, user.id)

        assert first.id == second.id

    def test_update_settings_changes_weight(self, test_db, user):
        settings = GraduationService.update_settings(test_db, user.id, 60.0)

        assert settings.subject_average_weight == 60.0

    def test_update_settings_changes_max_grade(self, test_db, user):
        settings = GraduationService.update_settings(test_db, user.id, 80.0, max_grade=20.0)

        assert settings.max_grade == 20.0

    def test_update_settings_creates_if_not_exist(self, test_db, user):
        settings = GraduationService.update_settings(test_db, user.id, 50.0)

        assert settings.subject_average_weight == 50.0
        assert settings.id is not None


class TestFinalAssessments:

    @pytest.fixture
    def user(self, test_db, test_user_data):
        return AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
            test_user_data["credit_requirements"],
        )

    @pytest.fixture
    def other_user(self, test_db):
        u = User(username="other", password_hash="hash")
        test_db.add(u)
        test_db.commit()
        test_db.refresh(u)
        return u

    @pytest.fixture
    def assessment(self, test_db, user):
        return GraduationService.add_final_assessment(
            test_db, user.id, "Thesis", weight=0.5
        )

    def test_add_final_assessment_stores_fields(self, test_db, user):
        a = GraduationService.add_final_assessment(
            test_db, user.id, "Thesis", weight=0.5, max_score=20.0, passing_grade=10.0
        )

        assert a.name == "Thesis"
        assert a.weight == 0.5
        assert a.max_score == 20.0
        assert a.passing_grade == 10.0
        assert a.user_id == user.id

    def test_add_final_assessment_default_values(self, test_db, user):
        a = GraduationService.add_final_assessment(test_db, user.id, "Oral Exam", weight=0.3)

        assert a.max_score == 10.0
        assert a.passing_grade == 5.0

    def test_get_final_assessments_empty(self, test_db, user):
        result = GraduationService.get_final_assessments(test_db, user.id)

        assert result == []

    def test_get_final_assessments_returns_added(self, test_db, user, assessment):
        result = GraduationService.get_final_assessments(test_db, user.id)

        assert len(result) == 1
        assert result[0].id == assessment.id

    def test_get_final_assessments_isolated_per_user(self, test_db, user, other_user, assessment):
        result = GraduationService.get_final_assessments(test_db, other_user.id)

        assert result == []

    def test_update_final_assessment_name(self, test_db, user, assessment):
        updated = GraduationService.update_final_assessment(
            test_db, user.id, assessment.id, name="Dissertation"
        )

        assert updated.name == "Dissertation"

    def test_update_final_assessment_partial_leaves_other_fields(self, test_db, user, assessment):
        original_weight = assessment.weight
        GraduationService.update_final_assessment(
            test_db, user.id, assessment.id, name="New Name"
        )

        result = GraduationService.get_final_assessments(test_db, user.id)[0]
        assert result.weight == original_weight

    def test_update_final_assessment_not_found_raises(self, test_db, user):
        with pytest.raises(ValueError, match="not found"):
            GraduationService.update_final_assessment(test_db, user.id, 9999, name="X")

    def test_update_final_assessment_wrong_user_raises(self, test_db, other_user, assessment):
        with pytest.raises(ValueError, match="not found"):
            GraduationService.update_final_assessment(
                test_db, other_user.id, assessment.id, name="X"
            )

    def test_delete_final_assessment_removes_it(self, test_db, user, assessment):
        GraduationService.delete_final_assessment(test_db, user.id, assessment.id)

        assert GraduationService.get_final_assessments(test_db, user.id) == []

    def test_delete_final_assessment_not_found_raises(self, test_db, user):
        with pytest.raises(ValueError, match="not found"):
            GraduationService.delete_final_assessment(test_db, user.id, 9999)

    def test_delete_final_assessment_wrong_user_raises(self, test_db, other_user, assessment):
        with pytest.raises(ValueError, match="not found"):
            GraduationService.delete_final_assessment(test_db, other_user.id, assessment.id)

    def test_set_grade_creates_grade_entry(self, test_db, user, assessment):
        result = GraduationService.set_grade(test_db, user.id, assessment.id, score=8.5)

        assert result.grade is not None
        assert result.grade.score == 8.5

    def test_set_grade_updates_existing_grade(self, test_db, user, assessment):
        GraduationService.set_grade(test_db, user.id, assessment.id, score=7.0)
        result = GraduationService.set_grade(test_db, user.id, assessment.id, score=9.0)

        assert result.grade.score == 9.0

    def test_set_grade_allows_none_score(self, test_db, user, assessment):
        GraduationService.set_grade(test_db, user.id, assessment.id, score=8.0)
        result = GraduationService.set_grade(test_db, user.id, assessment.id, score=None)

        assert result.grade.score is None

    def test_set_grade_not_found_raises(self, test_db, user):
        with pytest.raises(ValueError, match="not found"):
            GraduationService.set_grade(test_db, user.id, 9999, score=5.0)
