"""
Seed script — run from the server/ directory:
    python seed.py

Creates universities, majors, and 40 test users (20 CS + 20 Maths at University of Bucharest).
Each user gets subjects, assessments, and grades covering 1, 2, or 3 years:
  - users 1-7:  grades for Year 1 only
  - users 8-14: grades for Years 1-2
  - users 15-20: grades for all 3 years

Safe to re-run: skips anything that already exists.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

import bcrypt
from database import Base, SessionLocal, engine

from models import AcademicYear, Assessment, Grade, Major, Semester, Subject, University, User

random.seed(42)

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

UNIVERSITIES = [
    "University of Bucharest",
    "Polytechnic University",
    "UBB",
]

MAJORS = [
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

# Subjects per major: { year_index: { sem_index: [(name, credits)] } }
SUBJECTS = {
    "Computer Science": {
        1: {
            1: [("Algorithms", 6), ("Programming Fundamentals", 6)],
            2: [("Data Structures", 6), ("Discrete Mathematics", 6)],
        },
        2: {
            1: [("Object-Oriented Programming", 6), ("Databases", 6)],
            2: [("Computer Networks", 6), ("Operating Systems", 6)],
        },
        3: {
            1: [("Artificial Intelligence", 6), ("Software Engineering", 6)],
            2: [("Distributed Systems", 6), ("Machine Learning", 6)],
        },
    },
    "Mathematics": {
        1: {
            1: [("Calculus I", 6), ("Linear Algebra", 6)],
            2: [("Calculus II", 6), ("Geometry", 6)],
        },
        2: {
            1: [("Real Analysis", 6), ("Abstract Algebra", 6)],
            2: [("Complex Analysis", 6), ("Topology", 6)],
        },
        3: {
            1: [("Differential Equations", 6), ("Probability Theory", 6)],
            2: [("Statistics", 6), ("Numerical Methods", 6)],
        },
    },
}

# 20 CS users + 20 Maths users at University of Bucharest
CS_USERS = [
    "alice_pop",
    "bogdan_ion",
    "catalina_rus",
    "dan_marin",
    "elena_dima",
    "florin_toma",
    "georgiana_vlad",
    "horia_stan",
    "ioana_popa",
    "iulian_neag",
    "jana_cretu",
    "liviu_barbu",
    "mihaela_enache",
    "nicu_stoica",
    "oana_lungu",
    "petru_ciobanu",
    "raluca_gheorghe",
    "silviu_matei",
    "teodora_anghel",
    "vasile_tudor",
]

MATHS_USERS = [
    "alex_balan",
    "bianca_fota",
    "cosmin_dragan",
    "diana_moldovan",
    "eugen_lazar",
    "florentina_oprea",
    "gabriel_dinu",
    "hana_dobre",
    "ion_cristea",
    "julia_roman",
    "kosta_ionescu",
    "laura_chiriac",
    "marius_ciuraru",
    "nicoleta_stan",
    "octavian_bratu",
    "paula_alexe",
    "razvan_stefan",
    "simona_ene",
    "titus_filip",
    "ursula_mihu",
]


# How many years of grades each user gets (index matches position in user list)
# users 0-6  → 1 year,  users 7-13 → 2 years,  users 14-19 → 3 years
def _grade_years_for(index: int) -> int:
    if index < 7:
        return 1
    if index < 14:
        return 2
    return 3


PASSWORD = "Test1234!"
NUM_YEARS = 3
CREDIT_REQUIREMENTS = [60, 60, 60]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def get_or_create_university(db, name: str) -> University:
    uni = db.query(University).filter(University.name == name).first()
    if not uni:
        uni = University(name=name)
        db.add(uni)
        db.flush()
    return uni


def get_or_create_major(db, name: str) -> Major:
    major = db.query(Major).filter(Major.name == name).first()
    if not major:
        major = Major(name=name)
        db.add(major)
        db.flush()
    return major


def _random_score() -> float:
    """Return a realistic grade score between 5.0 and 10.0."""
    return round(random.uniform(5.0, 10.0), 2)


def create_user(
    db,
    username: str,
    university: University,
    major: Major,
    grade_years: int,
) -> User | None:
    if db.query(User).filter(User.username == username).first():
        print(f"  skip (exists): {username}")
        return None

    user = User(
        username=username,
        password_hash=hash_password(PASSWORD),
        university_id=university.id,
        major_id=major.id,
        leaderboard_visible=True,
    )
    db.add(user)
    db.flush()

    subject_templates = SUBJECTS.get(major.name, {})

    for year_index in range(1, NUM_YEARS + 1):
        credit_req = CREDIT_REQUIREMENTS[year_index - 1]
        academic_year = AcademicYear(
            user_id=user.id,
            label=f"Year {year_index}",
            order_index=year_index,
            credit_requirement=credit_req,
        )
        db.add(academic_year)
        db.flush()

        semesters = {}
        for sem_index in range(1, 3):
            semester = Semester(
                academic_year_id=academic_year.id,
                label=f"Semester {sem_index}",
                order_index=sem_index,
            )
            db.add(semester)
            db.flush()
            semesters[sem_index] = semester

        # Add subjects + assessments for this year
        year_subjects = subject_templates.get(year_index, {})
        for sem_index, subject_list in year_subjects.items():
            semester = semesters[sem_index]
            for subj_name, credits in subject_list:
                subject = Subject(
                    semester_id=semester.id,
                    academic_year_id=academic_year.id,
                    name=subj_name,
                    credit_value=credits,
                    passing_grade=5.0,
                    max_grade=10.0,
                )
                db.add(subject)
                db.flush()

                for assess_name, weight in [("Partial Exam", 40.0), ("Final Exam", 60.0)]:
                    assessment = Assessment(
                        subject_id=subject.id,
                        name=assess_name,
                        weight=weight,
                        max_score=10.0,
                        passing_grade=5.0,
                    )
                    db.add(assessment)
                    db.flush()

                    # Only add a grade if this year is within the user's coverage
                    if year_index <= grade_years:
                        db.add(Grade(assessment_id=assessment.id, score=_random_score()))

    return user


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def seed():
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("\nSeeding universities...")
        for name in UNIVERSITIES:
            if not db.query(University).filter(University.name == name).first():
                db.add(University(name=name))
                print(f"  created: {name}")
            else:
                print(f"  skip (exists): {name}")
        db.flush()

        print("\nSeeding majors...")
        for name in MAJORS:
            if not db.query(Major).filter(Major.name == name).first():
                db.add(Major(name=name))
                print(f"  created: {name}")
            else:
                print(f"  skip (exists): {name}")
        db.flush()

        ub = get_or_create_university(db, "University of Bucharest")
        cs = get_or_create_major(db, "Computer Science")
        maths = get_or_create_major(db, "Mathematics")

        print("\nSeeding Computer Science users...")
        for i, username in enumerate(CS_USERS):
            grade_years = _grade_years_for(i)
            user = create_user(db, username, ub, cs, grade_years)
            if user:
                print(f"  created: {username} (grades up to Year {grade_years})")

        print("\nSeeding Mathematics users...")
        for i, username in enumerate(MATHS_USERS):
            grade_years = _grade_years_for(i)
            user = create_user(db, username, ub, maths, grade_years)
            if user:
                print(f"  created: {username} (grades up to Year {grade_years})")

        db.commit()
        print("\nDone.")
    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
