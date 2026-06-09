from server.dependencies import get_current_user
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from server.schemas import (
    MajorResponse,
    UniversityResponse,
    UpdateProfileRequest,
    UserProfile,
)
from sqlalchemy.orm import Session

from server.database import get_db
from server.models import Major, University, User

# career advisor agent
from server.agents.career_advisor import generate_career_guidance

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


@router.get("/career-guidance", response_class=PlainTextResponse)
def career_guidance(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Fetch the authenticated user's academic history, format it, and return AI career guidance as Markdown."""
    user = db.query(User).filter(User.id == current_user.id).first()

    # Build a serializable student data structure
    student = {"username": user.username, "years": []}
    for ay in sorted(user.academic_years, key=lambda y: y.order_index):
        year_entry = {"label": ay.label, "order_index": ay.order_index, "subjects": []}
        for subj in ay.subjects:
            subj_entry = {
                "id": subj.id,
                "name": subj.name,
                "credits": subj.credit_value,
                "semester_index": subj.semester_id and getattr(subj.semester, "order_index", None) or None,
                "year_level": ay.order_index,
                "passing_grade": subj.passing_grade,
                "max_grade": subj.max_grade,
                "assessments": [],
            }
            for a in subj.assessments:
                grade_score = None
                if getattr(a, "grade", None) is not None:
                    grade_score = getattr(a.grade, "score", None)
                subj_entry["assessments"].append(
                    {
                        "id": a.id,
                        "name": a.name,
                        "weight": a.weight,
                        "max_score": a.max_score,
                        "passing_grade": a.passing_grade,
                        "grade_score": grade_score,
                    }
                )
            year_entry["subjects"].append(subj_entry)
        student["years"].append(year_entry)

    guidance_md = generate_career_guidance(student)
    return PlainTextResponse(guidance_md)


@router.get("/universities", response_model=list[UniversityResponse])
def get_universities(db: Session = Depends(get_db)):
    return db.query(University).all()


@router.get("/majors", response_model=list[MajorResponse])
def get_majors(db: Session = Depends(get_db)):
    return db.query(Major).all()
