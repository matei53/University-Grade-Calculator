from typing import Optional

from sqlalchemy.orm import Session

from models import Grade


class GradeService:
    @staticmethod
    def update_grade(
        db: Session, grade_id: int, score: Optional[float] = None
    ) -> Grade:
        grade = db.query(Grade).filter(Grade.id == grade_id).first()
        if not grade:
            raise ValueError("Grade not found")

        grade.score = score

        db.commit()
        db.refresh(grade)
        return grade

    @staticmethod
    def delete_grade(db: Session, grade_id: int) -> None:
        grade = db.query(Grade).filter(Grade.id == grade_id).first()
        if not grade:
            raise ValueError("Grade not found")

        db.delete(grade)
        db.commit()
