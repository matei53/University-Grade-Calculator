from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, University, Major
from schemas import UniversityResponse, MajorResponse, UserProfile, UpdateProfileRequest
from dependencies import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("", response_model=UserProfile)
def get_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
        major_name=major_name
    )

@router.put("")
def update_profile(
    update_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if update_data.university_id is not None:
        user.university_id = update_data.university_id
    
    if update_data.major_id is not None:
        user.major_id = update_data.major_id
    
    db.commit()
    db.refresh(user)
    
    return {"message": "Profile updated"}

@router.get("/universities", response_model=list[UniversityResponse])
def get_universities(db: Session = Depends(get_db)):
    return db.query(University).all()

@router.get("/majors", response_model=list[MajorResponse])
def get_majors(db: Session = Depends(get_db)):
    return db.query(Major).all()
