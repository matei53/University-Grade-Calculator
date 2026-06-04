from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


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
    username: Mapped[str] = mapped_column(
        String, unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    university_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("universities.id"), nullable=True
    )
    major_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("majors.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    university: Mapped[University | None] = relationship(
        back_populates="users"
    )
    major: Mapped[Major | None] = relationship(back_populates="users")
    academic_years: Mapped[list[AcademicYear]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(String, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    credit_requirement: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

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

    academic_year: Mapped[AcademicYear] = relationship(
        back_populates="semesters"
    )
    subjects: Mapped[list[Subject]] = relationship(back_populates="semester")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    semester_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("semesters.id"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    credit_value: Mapped[int] = mapped_column(Integer, nullable=False)
    passing_grade: Mapped[float] = mapped_column(Float, default=5.0)
    max_grade: Mapped[float] = mapped_column(Float, default=10.0)

    semester: Mapped[Semester] = relationship(back_populates="subjects")
    academic_year: Mapped[AcademicYear] = relationship(
        back_populates="subjects"
    )
    assessments: Mapped[list[Assessment]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
    )


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[float] = mapped_column(Float, default=10.0)
    passing_grade: Mapped[float] = mapped_column(Float, default=5.0)

    subject: Mapped[Subject] = relationship(back_populates="assessments")
    grades: Mapped[list[Grade]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
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
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    assessment: Mapped[Assessment] = relationship(back_populates="grades")
