from typing import Optional

from sqlalchemy.orm import Session

from server.models import FinalAssessment, FinalAssessmentGrade, GraduationSettings


class GraduationService:
    @staticmethod
    def get_or_create_settings(db: Session, user_id: int) -> GraduationSettings:
        settings = (
            db.query(GraduationSettings).filter(GraduationSettings.user_id == user_id).first()
        )
        if not settings:
            settings = GraduationSettings(
                user_id=user_id,
                subject_average_weight=100.0,
                max_grade=10.0,
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def update_settings(
        db: Session,
        user_id: int,
        subject_average_weight: float,
        max_grade: float = 10.0,
    ) -> GraduationSettings:
        settings = GraduationService.get_or_create_settings(db, user_id)
        settings.subject_average_weight = subject_average_weight
        settings.max_grade = max_grade
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def get_final_assessments(db: Session, user_id: int) -> list[FinalAssessment]:
        assessments = db.query(FinalAssessment).filter(FinalAssessment.user_id == user_id).all()
        for a in assessments:
            _ = a.grade  # eagerly load
        return assessments

    @staticmethod
    def add_final_assessment(
        db: Session,
        user_id: int,
        name: str,
        weight: float,
        max_score: float = 10.0,
        passing_grade: float = 5.0,
    ) -> FinalAssessment:
        assessment = FinalAssessment(
            user_id=user_id,
            name=name,
            weight=weight,
            max_score=max_score,
            passing_grade=passing_grade,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        _ = assessment.grade
        return assessment

    @staticmethod
    def update_final_assessment(
        db: Session,
        user_id: int,
        assessment_id: int,
        name: Optional[str] = None,
        weight: Optional[float] = None,
        max_score: Optional[float] = None,
        passing_grade: Optional[float] = None,
    ) -> FinalAssessment:
        assessment = (
            db.query(FinalAssessment)
            .filter(
                FinalAssessment.id == assessment_id,
                FinalAssessment.user_id == user_id,
            )
            .first()
        )
        if not assessment:
            raise ValueError("Final assessment not found")
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
        _ = assessment.grade
        return assessment

    @staticmethod
    def delete_final_assessment(db: Session, user_id: int, assessment_id: int) -> None:
        assessment = (
            db.query(FinalAssessment)
            .filter(
                FinalAssessment.id == assessment_id,
                FinalAssessment.user_id == user_id,
            )
            .first()
        )
        if not assessment:
            raise ValueError("Final assessment not found")
        db.delete(assessment)
        db.commit()

    @staticmethod
    def set_grade(
        db: Session,
        user_id: int,
        assessment_id: int,
        score: Optional[float],
    ) -> FinalAssessment:
        assessment = (
            db.query(FinalAssessment)
            .filter(
                FinalAssessment.id == assessment_id,
                FinalAssessment.user_id == user_id,
            )
            .first()
        )
        if not assessment:
            raise ValueError("Final assessment not found")

        existing = (
            db.query(FinalAssessmentGrade)
            .filter(FinalAssessmentGrade.final_assessment_id == assessment_id)
            .first()
        )
        if existing:
            existing.score = score
        else:
            db.add(FinalAssessmentGrade(final_assessment_id=assessment_id, score=score))

        db.commit()
        db.refresh(assessment)
        _ = assessment.grade
        return assessment
