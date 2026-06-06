from dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException
from schemas import (
    AcademicYearResponse,
    SubjectRequest,
    SubjectResponse,
)
from sqlalchemy.orm import Session

from database import get_db
from models import User
from services.subject_service import SubjectService

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.post("", response_model=SubjectResponse)
def add_subject(
    subject_data: SubjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        subject = SubjectService.add_subject(
            db,
            current_user.id,
            subject_data.name,
            subject_data.credits,
            subject_data.semester_index,
            subject_data.year_level,
            subject_data.passing_grade,
            subject_data.max_grade,
        )
        return subject
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/years", response_model=list[AcademicYearResponse])
def get_academic_years(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    years = SubjectService.get_user_years(db, current_user.id)
    return [AcademicYearResponse.from_orm(year) for year in years]
