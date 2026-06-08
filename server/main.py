from contextlib import asynccontextmanager
from typing import Any

from dependencies import get_current_user
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import assessments, auth, graduation, profile, subjects
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import AcademicYear, Major, Subject, University, User

_SEED_UNIVERSITIES = [
    "University of Bucharest",
    "Polytechnic University",
    "UBB",
]

_SEED_MAJORS = [
    "Computer Science",
    "Law",
    "Medicine",
    "Economics",
    "Mathematics",
    "Physics",
    "Psychology",
    "Architecture",
    "Political Science",
    "Business Administration",
    "Geography",
]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage startup and shutdown events"""
    # Startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(University).count() == 0:
            for name in _SEED_UNIVERSITIES:
                db.add(University(name=name))

        if db.query(Major).count() == 0:
            for name in _SEED_MAJORS:
                db.add(Major(name=name))

        db.commit()
    finally:
        db.close()

    yield


app = FastAPI(title="UniGrade API", version="1.0.0", lifespan=lifespan)

# Enable CORS for desktop app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(subjects.router)
app.include_router(assessments.router)
app.include_router(graduation.router)


@app.get("/debug/user-data")
def debug_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Debug endpoint to see user's data"""
    user = db.query(User).filter(User.id == current_user.id).first()

    academic_years = db.query(AcademicYear).filter(AcademicYear.user_id == current_user.id).all()

    result: dict[str, Any] = {
        "user_id": user.id,
        "username": user.username,
        "major_id": user.major_id,
        "university_id": user.university_id,
        "academic_years": [],
    }

    for year in academic_years:
        year_data: dict[str, Any] = {
            "id": year.id,
            "order_index": year.order_index,
            "label": year.label,
            "subjects": [],
        }

        subjects = db.query(Subject).filter(Subject.academic_year_id == year.id).all()

        for subject in subjects:
            year_data["subjects"].append(
                {
                    "id": subject.id,
                    "name": subject.name,
                    "credit_value": subject.credit_value,
                }
            )

        result["academic_years"].append(year_data)

    return result


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "UniGrade API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
