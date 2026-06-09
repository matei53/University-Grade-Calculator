from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.database import get_db
from server.dependencies import get_current_user
from server.models import Assessment, Grade, User
from server.schemas import GradeResponse, UpdateGradeRequest
from server.services.grade_service import GradeService

router = APIRouter(prefix="/grades", tags=["grades"])


@router.put("/{grade_id}", response_model=GradeResponse)
def update_grade(
    grade_id: int,
    grade_data: UpdateGradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify grade belongs to current user
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    assessment = db.query(Assessment).filter(Assessment.id == grade.assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if assessment.subject.academic_year.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        updated_grade = GradeService.update_grade(db, grade_id, score=grade_data.score)
        return updated_grade
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{grade_id}", status_code=204)
def delete_grade(
    grade_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    assessment = db.query(Assessment).filter(Assessment.id == grade.assessment_id).first()
    if not assessment or assessment.subject.academic_year.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        GradeService.delete_grade(db, grade_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
