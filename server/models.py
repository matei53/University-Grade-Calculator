from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from server.database import Base


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="university")


class Major(Base):
    __tablename__ = "majors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    users: Mapped[list[User]] = relationship(back_populates="major")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    university_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("universities.id"), nullable=True
    )
    major_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("majors.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    leaderboard_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    university: Mapped[University | None] = relationship(back_populates="users")
    major: Mapped[Major | None] = relationship(back_populates="users")
    academic_years: Mapped[list[AcademicYear]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    graduation_settings: Mapped[GraduationSettings | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    final_assessments: Mapped[list[FinalAssessment]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # credit passing percentage
    progression_requirements: Mapped[list[YearProgressionRequirement]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_requirement: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped[User] = relationship(back_populates="academic_years")
    semesters: Mapped[list[Semester]] = relationship(
        back_populates="academic_year",
        cascade="all, delete-orphan",
    )
    subjects: Mapped[list[Subject]] = relationship(
        back_populates="academic_year",
        cascade="all, delete-orphan",
    )


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)

    academic_year: Mapped[AcademicYear] = relationship(back_populates="semesters")
    subjects: Mapped[list[Subject]] = relationship(back_populates="semester")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    semester_id: Mapped[int] = mapped_column(Integer, ForeignKey("semesters.id"), nullable=False)
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    credit_value: Mapped[int] = mapped_column(Integer, nullable=False)
    passing_grade: Mapped[float] = mapped_column(Float, default=5.0)
    max_grade: Mapped[float] = mapped_column(Float, default=10.0)

    semester: Mapped[Semester] = relationship(back_populates="subjects")
    academic_year: Mapped[AcademicYear] = relationship(back_populates="subjects")
    assessments: Mapped[list[Assessment]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
    )


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject_id: Mapped[int] = mapped_column(Integer, ForeignKey("subjects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=10.0)
    passing_grade: Mapped[float] = mapped_column(Float, default=5.0)

    subject: Mapped[Subject] = relationship(back_populates="assessments")
    grade: Mapped[Grade | None] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        uselist=False,
    )


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    assessment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessments.id"),
        nullable=False,
        unique=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=True)

    assessment: Mapped[Assessment] = relationship(back_populates="grade")


class GraduationSettings(Base):
    __tablename__ = "graduation_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, unique=True
    )
    subject_average_weight: Mapped[float] = mapped_column(Float, default=100.0)
    max_grade: Mapped[float] = mapped_column(Float, default=10.0)

    user: Mapped[User] = relationship(back_populates="graduation_settings")


class FinalAssessment(Base):
    __tablename__ = "final_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, default=10.0)
    passing_grade: Mapped[float] = mapped_column(Float, default=5.0)

    user: Mapped[User] = relationship(back_populates="final_assessments")
    grade: Mapped[FinalAssessmentGrade | None] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        uselist=False,
    )


class FinalAssessmentGrade(Base):
    __tablename__ = "final_assessment_grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    final_assessment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("final_assessments.id"),
        nullable=False,
        unique=True,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    assessment: Mapped[FinalAssessment] = relationship(back_populates="grade")


# credit passing percentage
class YearProgressionRequirement(Base):
    __tablename__ = "year_progression_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_percentage: Mapped[float] = mapped_column(Float, default=70.0)
    cumulative: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="progression_requirements")
