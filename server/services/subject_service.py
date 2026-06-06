from schemas import AssessmentResponse, SubjectResponse
from sqlalchemy.orm import Session

from models import AcademicYear, Assessment, Grade, Semester, Subject


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
                label=f"Anul {year_level}",
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
            raise ValueError(
                f"Semester {semester_index} not found for year {year_level}"
            )

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
                    # Access grades for each assessment
                    for grade in assessment.grades:
                        pass

        return years


class AssessmentService:
    @staticmethod
    def add_assessment(
        db: Session,
        subject_id: int,
        name: str,
        weight: float,
        score: float,
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

        grade = Grade(assessment_id=assessment.id, score=score)
        db.add(grade)
        db.commit()
        db.refresh(assessment)

        return AssessmentResponse.from_orm(assessment)
