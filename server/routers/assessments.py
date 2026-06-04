from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Subject
from schemas import AssessmentRequest, AssessmentResponse
from services.subject_service import AssessmentService
from dependencies import get_current_user

router = APIRouter(prefix="/assessments", tags=["assessments"])

@router.post("/{subject_id}", response_model=AssessmentResponse)
def add_assessment(
    subject_id: int,
    assessment_data: AssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subject belongs to current user
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Check user has access
    if subject.academic_year.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        assessment = AssessmentService.add_assessment(
            db,
            subject_id,
            assessment_data.name,
            assessment_data.weight,
            assessment_data.score,
            assessment_data.max_score,
            assessment_data.passing_grade
        )
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
