"""
Tests for the subject and assessment services.
"""

import pytest

from models import Assessment, User
from services.auth_service import AuthService
from services.subject_service import AssessmentService, SubjectService


class TestSubjectService:
    """Test subject management service."""

    @pytest.fixture(scope="function")
    def user_with_years(self, test_db, test_user_data):
        """Create a user with academic years."""
        user = AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
            test_user_data["credit_requirements"],
        )
        return user

    def test_add_subject_success(self, test_db, user_with_years):
        """Test adding a subject successfully."""
        subject = SubjectService.add_subject(
            test_db,
            user_with_years.id,
            "Mathematics",
            6,
            semester_index=1,
            year_level=1,
            passing_grade=5.0,
            max_grade=10.0,
        )

        assert subject.name == "Mathematics"
        assert subject.credit_value == 6
        assert subject.passing_grade == 5.0
        assert subject.max_grade == 10.0

    def test_add_subject_creates_academic_year(self, test_db):
        """Test that add_subject creates academic year if needed."""
        # Create a user without academic years
        user = User(username="newuser", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # Add a subject without existing years
        with pytest.raises(ValueError, match="Semester .* not found"):
            SubjectService.add_subject(
                test_db,
                user.id,
                "Physics",
                6,
                semester_index=1,
                year_level=1,
            )

    def test_add_subject_invalid_semester(self, test_db, user_with_years):
        """Test adding subject with invalid semester."""
        with pytest.raises(ValueError, match="Semester .* not found"):
            SubjectService.add_subject(
                test_db,
                user_with_years.id,
                "Chemistry",
                6,
                semester_index=5,  # Invalid semester
                year_level=1,
            )

    def test_add_subject_with_default_grades(self, test_db, user_with_years):
        """Test adding subject uses default grade values."""
        subject = SubjectService.add_subject(
            test_db,
            user_with_years.id,
            "Biology",
            4,
            semester_index=1,
            year_level=1,
            # Not specifying passing_grade and max_grade
        )

        assert subject.passing_grade == 5.0
        assert subject.max_grade == 10.0

    def test_get_user_years(self, test_db, user_with_years):
        """Test retrieving user's academic years."""
        years = SubjectService.get_user_years(test_db, user_with_years.id)

        assert len(years) == 3
        for year in years:
            assert year.user_id == user_with_years.id

    def test_get_user_years_with_subjects(self, test_db, user_with_years):
        """Test getting years loads all subjects."""
        # Add a subject
        SubjectService.add_subject(
            test_db,
            user_with_years.id,
            "Mathematics",
            6,
            semester_index=1,
            year_level=1,
        )

        years = SubjectService.get_user_years(test_db, user_with_years.id)

        # Should have at least one year with a subject
        assert len(years) > 0
        assert any(len(year.subjects) > 0 for year in years)


class TestAssessmentService:
    """Test assessment management service."""

    @pytest.fixture(scope="function")
    def subject_with_user(self, test_db, test_user_data):
        """Create a subject for testing."""
        user = AuthService.sign_up(
            test_db,
            test_user_data["username"],
            test_user_data["password"],
            test_user_data["num_years"],
            test_user_data["credit_requirements"],
        )

        subject = SubjectService.add_subject(
            test_db,
            user.id,
            "Mathematics",
            6,
            semester_index=1,
            year_level=1,
        )

        return subject

    def test_add_assessment_success(self, test_db, subject_with_user):
        """Test adding an assessment successfully."""
        assessment = AssessmentService.add_assessment(
            test_db,
            subject_with_user.id,
            "Midterm Exam",
            weight=0.4,
            score=8.5,
            max_score=10.0,
            passing_grade=5.0,
        )

        assert assessment.name == "Midterm Exam"
        assert assessment.weight == 0.4
        assert assessment.max_score == 10.0

    def test_add_assessment_creates_grade(self, test_db, subject_with_user):
        """Test that assessment creation creates a grade."""
        assessment = AssessmentService.add_assessment(
            test_db,
            subject_with_user.id,
            "Quiz",
            weight=0.2,
            score=7.5,
        )

        # Reload and check
        db_assessment = test_db.query(Assessment).filter(Assessment.id == assessment.id).first()

        assert len(db_assessment.grades) > 0
        assert db_assessment.grades[0].score == 7.5

    def test_add_assessment_with_default_values(self, test_db, subject_with_user):
        """Test assessment creation with default values."""
        assessment = AssessmentService.add_assessment(
            test_db,
            subject_with_user.id,
            "Final Exam",
            weight=0.6,
            score=9.0,
            # Not specifying max_score and passing_grade
        )

        assert assessment.max_score == 10.0
        assert assessment.passing_grade == 5.0

    def test_add_assessment_multiple_same_subject(self, test_db, subject_with_user):
        """Test adding multiple assessments to same subject."""
        assessment1 = AssessmentService.add_assessment(
            test_db,
            subject_with_user.id,
            "Quiz 1",
            weight=0.2,
            score=8.0,
        )

        assessment2 = AssessmentService.add_assessment(
            test_db,
            subject_with_user.id,
            "Quiz 2",
            weight=0.2,
            score=7.5,
        )

        assert assessment1.id != assessment2.id
        assert assessment1.subject_id == assessment2.subject_id

    def test_add_assessment_high_score(self, test_db, subject_with_user):
        """Test assessment with high score."""
        assessment = AssessmentService.add_assessment(
            test_db,
            subject_with_user.id,
            "Perfect Score",
            weight=0.5,
            score=10.0,
        )

        assert assessment.grades[0].score == 10.0

    def test_add_assessment_zero_score(self, test_db, subject_with_user):
        """Test assessment with zero score."""
        assessment = AssessmentService.add_assessment(
            test_db,
            subject_with_user.id,
            "Failed Assessment",
            weight=0.3,
            score=0.0,
        )

        assert assessment.grades[0].score == 0.0
