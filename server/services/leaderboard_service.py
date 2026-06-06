from sqlalchemy.orm import Session
from models import User, AcademicYear, University
from services.subject_service import SubjectService

def _university_short(name: str | None) -> str:
    if not name:
        return "—"
    if name.upper() == name and len(name) <= 6:
        return name
    mapping = {
        "Universitatea din Bucuresti": "UBB",
        "Universitatea Politehnica": "UPB",
        "UBB": "UBB",
    }
    return mapping.get(name, name[:4].upper())

def _subject_grade(subject) -> float | None:
    total = 0.0
    has = False
    subject_max = float(subject.max_grade or 10.0)
    for assessment in subject.assessments:
        if not assessment.grades:
            continue
        score = assessment.grades[0].score
        if score is None:
            continue
        has = True
        max_score = float(assessment.max_score or 10.0)
        normalized = (float(score) / max_score) if max_score > 0 else 0.0
        total += normalized * (float(assessment.weight) / 100.0) * subject_max
    return round(total, 2) if has else None

def compute_user_stats(db: Session, user_id: int) -> dict:
    years = SubjectService.get_user_years(db, user_id)
    total_program_credits = sum(y.credit_requirement or 0 for y in years) or 180

    total_weighted_points = 0.0
    total_credits_with_grades = 0
    total_credits_earned = 0
    max_year_with_data = 1

    for year in years:
        for subject in year.subjects:
            grade = _subject_grade(subject)
            credits = int(subject.credit_value)
            passing = float(subject.passing_grade or 5.0)
            if grade is not None:
                total_weighted_points += grade * credits
                total_credits_with_grades += credits
                if grade >= passing:
                    total_credits_earned += credits
                max_year_with_data = max(max_year_with_data, year.order_index)

    weighted_avg = (
        total_weighted_points / total_credits_with_grades
        if total_credits_with_grades > 0 else 0.0
    )
    return {
        "weighted_avg": round(weighted_avg, 2),
        "credits": total_credits_earned,
        "total_credits_with_grades": total_credits_with_grades,
        "year_level": max_year_with_data,
        "total_program_credits": total_program_credits,
    }

def build_leaderboard(db: Session, current_user: User) -> dict:
    if not current_user.university_id or not current_user.major_id:
        return {
            "entries": [],
            "current_user_visible": bool(current_user.leaderboard_visible),
            "filter_university": None,
            "filter_major": None,
        }

    uni = db.query(University).filter(University.id == current_user.university_id).first()
    uni_short = _university_short(uni.name if uni else None)

    peers = (
        db.query(User)
        .filter(
            User.university_id == current_user.university_id,
            User.major_id == current_user.major_id,
        )
        .all()
    )

    rows = []
    for u in peers:
        if not u.leaderboard_visible and u.id != current_user.id:
            continue
        stats = compute_user_stats(db, u.id)
        if stats["total_credits_with_grades"] == 0 and u.id != current_user.id:
            continue
        rows.append({
            "user_id": u.id,
            "display_name": u.username.replace("_", " ").title(),
            "university_short": uni_short,
            "year_level": stats["year_level"],
            "weighted_avg": stats["weighted_avg"],
            "credits": stats["credits"],
            "is_current_user": u.id == current_user.id,
        })

    rows.sort(key=lambda r: (-r["weighted_avg"], -r["credits"]))
    entries = []
    for i, r in enumerate(rows, start=1):
        entries.append({**r, "rank": i})

    major = current_user.major
    return {
        "entries": entries,
        "current_user_visible": bool(current_user.leaderboard_visible),
        "filter_university": uni.name if uni else None,
        "filter_major": major.name if major else None,
    }