from dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from schemas import (
    FinalAssessmentGradeUpdate,
    FinalAssessmentRequest,
    FinalAssessmentResponse,
    FinalAssessmentUpdate,
    GraduationSettingsResponse,
    GraduationSettingsUpdate,
)
from sqlalchemy.orm import Session

from database import get_db
from models import User
from services.graduation_service import GraduationService

router = APIRouter(prefix="/graduation", tags=["graduation"])


@router.get("/settings", response_model=GraduationSettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GraduationService.get_or_create_settings(db, current_user.id)


@router.put("/settings", response_model=GraduationSettingsResponse)
def update_settings(
    data: GraduationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GraduationService.update_settings(
        db, current_user.id, data.subject_average_weight, data.max_grade
    )


@router.get("/assessments", response_model=list[FinalAssessmentResponse])
def get_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GraduationService.get_final_assessments(db, current_user.id)


@router.post("/assessments", response_model=FinalAssessmentResponse)
def add_assessment(
    data: FinalAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return GraduationService.add_final_assessment(
        db,
        current_user.id,
        data.name,
        data.weight,
        data.max_score,
        data.passing_grade,
    )


@router.put("/assessments/{assessment_id}", response_model=FinalAssessmentResponse)
def update_assessment(
    assessment_id: int,
    data: FinalAssessmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return GraduationService.update_final_assessment(
            db,
            current_user.id,
            assessment_id,
            data.name,
            data.weight,
            data.max_score,
            data.passing_grade,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/assessments/{assessment_id}", status_code=204)
def delete_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        GraduationService.delete_final_assessment(db, current_user.id, assessment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/assessments/{assessment_id}/grade", response_model=FinalAssessmentResponse)
def set_grade(
    assessment_id: int,
    data: FinalAssessmentGradeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return GraduationService.set_grade(db, current_user.id, assessment_id, data.score)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
