from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from server.database import get_db
from server.dependencies import get_current_user
from server.models import Major, University, User
from server.schemas import (
    CreateMajorRequest,
    CreateUniversityRequest,
    MajorResponse,
    UniversityResponse,
    UpdateProfileRequest,
    UserProfile,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserProfile)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(User).filter(User.id == current_user.id).first()

    university_name = None
    major_name = None

    if profile.university_id:
        university = db.query(University).filter(University.id == profile.university_id).first()
        university_name = university.name if university else None

    if profile.major_id:
        major = db.query(Major).filter(Major.id == profile.major_id).first()
        major_name = major.name if major else None

    return UserProfile(
        id=profile.id,
        username=profile.username,
        university_name=university_name,
        major_name=major_name,
    )


@router.put("")
def update_profile(
    update_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if update_data.university_id is not None:
        user.university_id = update_data.university_id

    if update_data.major_id is not None:
        user.major_id = update_data.major_id

    db.commit()
    db.refresh(user)

    return {"message": "Profile updated"}


@router.delete("", status_code=204)
def delete_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.delete(current_user)
    db.commit()


@router.get("/universities", response_model=list[UniversityResponse])
def get_universities(db: Session = Depends(get_db)):
    return db.query(University).all()


@router.post("/universities", response_model=UniversityResponse)
def create_university(
    data: CreateUniversityRequest,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(University).filter(func.lower(University.name) == func.lower(data.name)).first()
    )
    if existing:
        return existing
    university = University(name=data.name)
    db.add(university)
    db.commit()
    db.refresh(university)
    return university


@router.get("/majors", response_model=list[MajorResponse])
def get_majors(db: Session = Depends(get_db)):
    return db.query(Major).all()


@router.post("/majors", response_model=MajorResponse)
def create_major(
    data: CreateMajorRequest,
    db: Session = Depends(get_db),
):
    existing = db.query(Major).filter(func.lower(Major.name) == func.lower(data.name)).first()
    if existing:
        return existing
    major = Major(name=data.name)
    db.add(major)
    db.commit()
    db.refresh(major)
    return major
