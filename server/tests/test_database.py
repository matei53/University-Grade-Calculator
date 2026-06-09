"""
Tests for database models and database operations.
"""

from datetime import datetime

import pytest

from server.models import (
    AcademicYear,
    Assessment,
    Grade,
    Major,
    Semester,
    Subject,
    University,
    User,
)


class TestUserModel:
    """Test User model."""

    def test_user_creation(self, test_db):
        """Test creating a user."""
        user = User(username="testuser", password_hash="hashed_password")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert isinstance(user.created_at, datetime)

    def test_user_unique_username(self, test_db):
        """Test that usernames must be unique."""
        user1 = User(username="testuser", password_hash="hash1")
        test_db.add(user1)
        test_db.commit()

        user2 = User(username="testuser", password_hash="hash2")
        test_db.add(user2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()

    def test_user_with_university(self, test_db, test_university):
        """Test user with associated university."""
        user = User(
            username="testuser",
            password_hash="hash",
            university_id=test_university.id,
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        assert user.university_id == test_university.id
        assert user.university.name == test_university.name

    def test_user_with_major(self, test_db, test_major):
        """Test user with associated major."""
        user = User(
            username="testuser",
            password_hash="hash",
            major_id=test_major.id,
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        assert user.major_id == test_major.id
        assert user.major.name == test_major.name


class TestUniversityModel:
    """Test University model."""

    def test_university_creation(self, test_db):
        """Test creating a university."""
        university = University(name="MIT")
        test_db.add(university)
        test_db.commit()
        test_db.refresh(university)

        assert university.id is not None
        assert university.name == "MIT"

    def test_university_unique_name(self, test_db):
        """Test that university names must be unique."""
        uni1 = University(name="MIT")
        test_db.add(uni1)
        test_db.commit()

        uni2 = University(name="MIT")
        test_db.add(uni2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()


class TestMajorModel:
    """Test Major model."""

    def test_major_creation(self, test_db):
        """Test creating a major."""
        major = Major(name="Computer Science")
        test_db.add(major)
        test_db.commit()
        test_db.refresh(major)

        assert major.id is not None
        assert major.name == "Computer Science"

    def test_major_unique_name(self, test_db):
        """Test that major names must be unique."""
        major1 = Major(name="Computer Science")
        test_db.add(major1)
        test_db.commit()

        major2 = Major(name="Computer Science")
        test_db.add(major2)

        with pytest.raises(Exception):  # IntegrityError
            test_db.commit()


class TestAcademicYearModel:
    """Test AcademicYear model."""

    def test_academic_year_creation(self, test_db):
        """Test creating an academic year."""
        user = User(username="testuser", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        year = AcademicYear(
            user_id=user.id,
            label="Year 1",
            order_index=1,
            credit_requirement=60,
        )
        test_db.add(year)
        test_db.commit()
        test_db.refresh(year)

        assert year.id is not None
        assert year.label == "Year 1"
        assert year.order_index == 1
        assert year.credit_requirement == 60

    def test_academic_year_with_user(self, test_db):
        """Test academic year relationship with user."""
        user = User(username="testuser", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        year = AcademicYear(user_id=user.id, label="Year 1", order_index=1)
        test_db.add(year)
        test_db.commit()
        test_db.refresh(year)

        assert year.user.id == user.id


class TestSemesterModel:
    """Test Semester model."""

    def test_semester_creation(self, test_db):
        """Test creating a semester."""
        user = User(username="testuser", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        year = AcademicYear(user_id=user.id, label="Year 1", order_index=1)
        test_db.add(year)
        test_db.commit()
        test_db.refresh(year)

        semester = Semester(
            academic_year_id=year.id,
            label="Semester 1",
            order_index=1,
        )
        test_db.add(semester)
        test_db.commit()
        test_db.refresh(semester)

        assert semester.id is not None
        assert semester.label == "Semester 1"
        assert semester.order_index == 1


class TestSubjectModel:
    """Test Subject model."""

    def test_subject_creation(self, test_db):
        """Test creating a subject."""
        user = User(username="testuser", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        year = AcademicYear(user_id=user.id, label="Year 1", order_index=1)
        test_db.add(year)
        test_db.commit()
        test_db.refresh(year)

        semester = Semester(
            academic_year_id=year.id,
            label="Semester 1",
            order_index=1,
        )
        test_db.add(semester)
        test_db.commit()
        test_db.refresh(semester)

        subject = Subject(
            semester_id=semester.id,
            academic_year_id=year.id,
            name="Mathematics",
            credit_value=6,
            passing_grade=5.0,
            max_grade=10.0,
        )
        test_db.add(subject)
        test_db.commit()
        test_db.refresh(subject)

        assert subject.id is not None
        assert subject.name == "Mathematics"
        assert subject.credit_value == 6


class TestAssessmentModel:
    """Test Assessment model."""

    def test_assessment_creation(self, test_db):
        """Test creating an assessment."""
        user = User(username="testuser", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        year = AcademicYear(user_id=user.id, label="Year 1", order_index=1)
        test_db.add(year)
        test_db.commit()
        test_db.refresh(year)

        semester = Semester(
            academic_year_id=year.id,
            label="Semester 1",
            order_index=1,
        )
        test_db.add(semester)
        test_db.commit()
        test_db.refresh(semester)

        subject = Subject(
            semester_id=semester.id,
            academic_year_id=year.id,
            name="Mathematics",
            credit_value=6,
        )
        test_db.add(subject)
        test_db.commit()
        test_db.refresh(subject)

        assessment = Assessment(
            subject_id=subject.id,
            name="Midterm",
            weight=0.4,
            max_score=10.0,
            passing_grade=5.0,
        )
        test_db.add(assessment)
        test_db.commit()
        test_db.refresh(assessment)

        assert assessment.id is not None
        assert assessment.name == "Midterm"
        assert assessment.weight == 0.4


class TestGradeModel:
    """Test Grade model."""

    def test_grade_creation(self, test_db):
        """Test creating a grade."""
        user = User(username="testuser", password_hash="hash")
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        year = AcademicYear(user_id=user.id, label="Year 1", order_index=1)
        test_db.add(year)
        test_db.commit()
        test_db.refresh(year)

        semester = Semester(
            academic_year_id=year.id,
            label="Semester 1",
            order_index=1,
        )
        test_db.add(semester)
        test_db.commit()
        test_db.refresh(semester)

        subject = Subject(
            semester_id=semester.id,
            academic_year_id=year.id,
            name="Mathematics",
            credit_value=6,
        )
        test_db.add(subject)
        test_db.commit()
        test_db.refresh(subject)

        assessment = Assessment(subject_id=subject.id, name="Midterm", weight=0.4)
        test_db.add(assessment)
        test_db.commit()
        test_db.refresh(assessment)

        grade = Grade(assessment_id=assessment.id, score=8.5)
        test_db.add(grade)
        test_db.commit()
        test_db.refresh(grade)

        assert grade.id is not None
        assert grade.score == 8.5
