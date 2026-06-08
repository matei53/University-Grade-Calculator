import math

from sqlalchemy.orm import Session

from models import Major, University, User
from services.subject_service import SubjectService

_KNOWN_ABBREVIATIONS = {
    "Universitatea din Bucuresti": "UB",
    "Universitatea Politehnica": "UPB",
    "UBB": "UBB",
}

DEFAULT_PAGE_SIZE = 2
MAX_PAGE_SIZE = 20


def university_short(name: str | None) -> str:
    """Return a short label for a university name."""
    if not name:
        return "—"

    if name in _KNOWN_ABBREVIATIONS:
        return _KNOWN_ABBREVIATIONS[name]

    if name.upper() == name and len(name) <= 6:
        return name

    capitalized_words = [word for word in name.split() if word and word[0].isupper()]

    if len(capitalized_words) > 1:
        abbreviation = "".join(word[0] for word in capitalized_words)
        if abbreviation == "UDB":
            return "UB"
        return abbreviation

    return name[:4].upper()


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


def _sort_key(row: dict) -> tuple:
    """Primary: weighted average. Secondary: credits earned."""
    return (
        -row["weighted_avg"],
        -row["credits"],
        row["display_name"].lower(),
    )


def build_leaderboard(
    db: Session,
    current_user: User,
    *,
    year_level: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    empty = {
        "podium": [],
        "entries": [],
        "total": 0,
        "page": page,
        "page_size": min(page_size, MAX_PAGE_SIZE),
        "total_pages": 0,
        "current_user_visible": bool(current_user.leaderboard_visible),
        "filter_university": None,
        "filter_major": None,
        "filter_year_level": None,
        "current_user_year_level": 1,
        "available_year_levels": [],
    }

    if not current_user.university_id or not current_user.major_id:
        return empty

    uni = current_user.university
    major = current_user.major
    if not uni or not major:
        return empty

    current_stats = compute_user_stats(db, current_user.id)
    current_user_year_level = current_stats["year_level"]
    filter_year_level = (
        year_level if year_level is not None else current_user_year_level
    )

    peers = (
        db.query(User)
        .join(University, User.university_id == University.id)
        .join(Major, User.major_id == Major.id)
        .filter(University.name == uni.name, Major.name == major.name)
        .all()
    )

    all_rows = []
    for u in peers:
        if not u.leaderboard_visible and u.id != current_user.id:
            continue
        stats = compute_user_stats(db, u.id)
        peer_uni = db.query(University).filter(University.id == u.university_id).first()
        all_rows.append({
            "user_id": u.id,
            "display_name": u.username.replace("_", " ").title(),
            "university_short": university_short(peer_uni.name if peer_uni else None),
            "year_level": stats["year_level"],
            "weighted_avg": stats["weighted_avg"],
            "credits": stats["credits"],
            "is_current_user": u.id == current_user.id,
        })

    available_year_levels = sorted({r["year_level"] for r in all_rows})

    rows = [r for r in all_rows if r["year_level"] == filter_year_level]

    rows.sort(key=_sort_key)
    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    page = max(page, 1)

    if search and search.strip():
        needle = search.strip().lower()
        exact_matches = [r for r in rows if r["display_name"].lower() == needle]
        if exact_matches and page == 1:
            match_rank = exact_matches[0]["rank"]
            if match_rank > 3:
                page = math.ceil((match_rank - 3) / page_size)

        if not exact_matches:
            rows = [r for r in rows if needle in r["display_name"].lower()]

    total = len(rows)
    podium = rows[:3]
    table_rows = rows[3:]

    total_table = len(table_rows)
    total_pages = math.ceil(total_table / page_size) if total_table else 0
    if total_pages and page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    paginated_table = table_rows[start:start + page_size]

    return {
        "podium": podium,
        "entries": paginated_table,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "current_user_visible": bool(current_user.leaderboard_visible),
        "filter_university": uni.name,
        "filter_major": major.name,
        "filter_year_level": filter_year_level,
        "current_user_year_level": current_user_year_level,
        "available_year_levels": available_year_levels,
    }