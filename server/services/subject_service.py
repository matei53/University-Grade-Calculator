from typing import Optional

from server.schemas import AssessmentResponse, SubjectResponse
from sqlalchemy.orm import Session

from server.models import AcademicYear, Assessment, Grade, Semester, Subject


class SubjectService:
    @staticmethod
    def add_subject(
        db: Session,
        user_id: int,
        subject_name: str,
        credits: int,
        semester_index: int,
        year_level: int,
        passing_grade: float = 5.0,
        max_grade: float = 10.0,
    ) -> SubjectResponse:
        # Get or create academic year
        academic_year = (
            db.query(AcademicYear)
            .filter(
                AcademicYear.user_id == user_id,
                AcademicYear.order_index == year_level,
            )
            .first()
        )

        if not academic_year:
            academic_year = AcademicYear(
                user_id=user_id,
                label=f"Year {year_level}",
                order_index=year_level,
                credit_requirement=60,
            )
            db.add(academic_year)
            db.flush()

        # Get semester
        semester = (
            db.query(Semester)
            .filter(
                Semester.academic_year_id == academic_year.id,
                Semester.order_index == semester_index,
            )
            .first()
        )

        if not semester:
            raise ValueError(f"Semester {semester_index} not found for year {year_level}")

        # Create subject
        subject = Subject(
            semester_id=semester.id,
            academic_year_id=academic_year.id,
            name=subject_name,
            credit_value=credits,
            passing_grade=passing_grade,
            max_grade=max_grade,
        )
        db.add(subject)
        db.commit()
        db.refresh(subject)

        return SubjectResponse.from_orm(subject)

    @staticmethod
    def update_subject(
        db: Session,
        user_id: int,
        subject_id: int,
        name: Optional[str] = None,
        credits: Optional[int] = None,
        semester_index: Optional[int] = None,
        year_level: Optional[int] = None,
        passing_grade: Optional[float] = None,
        max_grade: Optional[float] = None,
    ) -> SubjectResponse:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject or subject.academic_year.user_id != user_id:
            raise ValueError("Subject not found")

        if name is not None:
            subject.name = name
        if credits is not None:
            subject.credit_value = credits
        if passing_grade is not None:
            subject.passing_grade = passing_grade
        if max_grade is not None:
            subject.max_grade = max_grade

        if year_level is not None or semester_index is not None:
            target_year_level = year_level if year_level is not None else subject.academic_year.order_index
            target_semester_index = semester_index if semester_index is not None else subject.semester.order_index

            target_year = (
                db.query(AcademicYear)
                .filter(
                    AcademicYear.user_id == user_id,
                    AcademicYear.order_index == target_year_level,
                )
                .first()
            )
            if not target_year:
                raise ValueError(f"Academic year {target_year_level} not found")

            target_semester = (
                db.query(Semester)
                .filter(
                    Semester.academic_year_id == target_year.id,
                    Semester.order_index == target_semester_index,
                )
                .first()
            )
            if not target_semester:
                raise ValueError(
                    f"Semester {target_semester_index} not found for year {target_year_level}"
                )

            subject.academic_year_id = target_year.id
            subject.semester_id = target_semester.id

        db.commit()
        db.refresh(subject)
        return SubjectResponse.from_orm(subject)

    @staticmethod
    def delete_subject(db: Session, user_id: int, subject_id: int) -> None:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject or subject.academic_year.user_id != user_id:
            raise ValueError("Subject not found")

        db.delete(subject)
        db.commit()

    @staticmethod
    def get_user_years(db: Session, user_id: int):
        years = (
            db.query(AcademicYear)
            .filter(AcademicYear.user_id == user_id)
            .order_by(AcademicYear.order_index)
            .all()
        )

        # Explicitly load all subjects/assessments to avoid lazy loading issues
        for year in years:
            # Access the subjects to trigger loading
            for subject in year.subjects:
                # Access assessments for each subject
                for assessment in subject.assessments:
                    # Access grade for each assessment to trigger loading
                    _ = assessment.grade

        return years


class AssessmentService:
    @staticmethod
    def add_assessment(
        db: Session,
        subject_id: int,
        name: str,
        weight: float,
        score: Optional[float] = None,
        max_score: float = 10.0,
        passing_grade: float = 5.0,
    ) -> AssessmentResponse:
        assessment = Assessment(
            subject_id=subject_id,
            name=name,
            weight=weight,
            max_score=max_score,
            passing_grade=passing_grade,
        )
        db.add(assessment)
        db.flush()

        grade = Grade(assessment_id=assessment.id, score=score)  # score=None → ungraded
        db.add(grade)
        db.commit()
        db.refresh(assessment)

        return AssessmentResponse.from_orm(assessment)

    @staticmethod
    def update_assessment(
        db: Session,
        user_id: int,
        assessment_id: int,
        name: Optional[str] = None,
        weight: Optional[float] = None,
        max_score: Optional[float] = None,
        passing_grade: Optional[float] = None,
    ) -> AssessmentResponse:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment or assessment.subject.academic_year.user_id != user_id:
            raise ValueError("Assessment not found")

        if name is not None:
            assessment.name = name
        if weight is not None:
            assessment.weight = weight
        if max_score is not None:
            assessment.max_score = max_score
        if passing_grade is not None:
            assessment.passing_grade = passing_grade

        db.commit()
        db.refresh(assessment)
        return AssessmentResponse.from_orm(assessment)

    @staticmethod
    def delete_assessment(db: Session, user_id: int, assessment_id: int) -> None:
        assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment or assessment.subject.academic_year.user_id != user_id:
            raise ValueError("Assessment not found")

        db.delete(assessment)
        db.commit()
