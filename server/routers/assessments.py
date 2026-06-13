from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.database import get_db
from server.dependencies import get_current_user
from server.models import Subject, User
from server.schemas import AssessmentRequest, AssessmentResponse, AssessmentUpdateRequest
from server.services.subject_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/{subject_id}", response_model=AssessmentResponse)
def add_assessment(
    subject_id: int,
    assessment_data: AssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify subject belongs to current user
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Check user has access
    if subject.academic_year.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return AssessmentService.add_assessment(
        db,
        subject_id,
        assessment_data.name,
        assessment_data.weight,
        assessment_data.score,
        assessment_data.max_score,
        assessment_data.passing_grade,
    )


@router.put("/{assessment_id}", response_model=AssessmentResponse)
def update_assessment(
    assessment_id: int,
    assessment_data: AssessmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        updated = AssessmentService.update_assessment(
            db,
            current_user.id,
            assessment_id,
            name=assessment_data.name,
            weight=assessment_data.weight,
            max_score=assessment_data.max_score,
            passing_grade=assessment_data.passing_grade,
        )
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{assessment_id}", status_code=204)
def delete_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        AssessmentService.delete_assessment(db, current_user.id, assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
