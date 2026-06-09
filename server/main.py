import json
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

# Ensure the repository root is on sys.path when running this file directly.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from server.dependencies import get_current_user
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routers import assessments, auth, grades, graduation, profile, subjects
from sqlalchemy.orm import Session

from server.database import Base, SessionLocal, engine, get_db
from server.models import AcademicYear, Major, Subject, University, User

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Manage startup and shutdown events"""
    # Startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if universities exist
        if db.query(University).count() == 0:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            with open(os.path.join(data_dir, "universities.json"), "r") as f:
                universities = json.load(f)
            for uni in universities:
                db.add(University(name=uni["name"]))

        # Check if majors exist
        if db.query(Major).count() == 0:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            with open(os.path.join(data_dir, "majors.json"), "r") as f:
                majors = json.load(f)
            for major in majors:
                db.add(Major(name=major["name"]))

        db.commit()
    finally:
        db.close()

    yield

    # Shutdown (if needed, add cleanup code here)


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
app.include_router(grades.router)
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
