"""
LangChain tools shared by the grade simulator and career advisor agents.
"""

from typing import Any, Optional

from langchain_core.tools import tool

_api_client: Optional[Any] = None


def set_api_client(client: Any) -> None:
    """Set the API client instance used by all tools. Must be called before running agents."""
    global _api_client
    _api_client = client


def _get_api_client() -> Any:
    if _api_client is None:
        raise RuntimeError("API client not set. Call set_api_client() first.")
    return _api_client


def _filter_years(years_data: list[dict], year_id: Optional[int]) -> list[dict]:
    if year_id is None:
        return years_data
    return [y for y in years_data if y.get("id") == year_id]


def _assessment_score(assessment: dict) -> Optional[float]:
    grade_obj = assessment.get("grade")
    if grade_obj is None:
        return None
    score = grade_obj.get("score")
    return float(score) if score is not None else None


@tool
def get_current_grades(year_id: Optional[int] = None) -> str:
    """
    Fetch the student's current grades at the assessment level.
    Returns each subject with its individual assessments, weights, max scores,
    min passing scores, and current grades (or 'No grade yet').
    Optionally filter to a single academic year by year_id.

    Args:
        year_id: Optional academic year ID to limit results to one year.
    """
    try:
        years_data = _get_api_client().get_academic_years()
    except Exception as e:
        return f"Error fetching grades: {e}"

    years_data = _filter_years(years_data, year_id)
    if not years_data:
        return "No academic data found."

    lines: list[str] = []
    for year in years_data:
        lines.append(f"\n[{year.get('label', 'Year ?')}]")
        for subject in year.get("subjects", []):
            name = subject.get("name", "Unknown")
            credits = subject.get("credit_value", 0)
            max_grade = float(subject.get("max_grade", 10.0))
            passing_grade = float(subject.get("passing_grade", 5.0))
            lines.append(
                f"  {name} | {credits} credits | "
                f"passing grade: {passing_grade}/{max_grade}"
            )
            for a in subject.get("assessments", []):
                a_id = a.get("id")
                a_name = a.get("name", "Assessment")
                weight = a.get("weight", 0)
                max_score = float(a.get("max_score", 10.0))
                min_passing = round((passing_grade / max_grade) * max_score, 2)
                score = _assessment_score(a)
                score_str = f"{score}" if score is not None else "No grade yet"
                lines.append(
                    f"    [ID:{a_id}] {a_name} | weight: {weight}% | "
                    f"max score: {max_score} | min passing: {min_passing} | "
                    f"score: {score_str}"
                )

    return "\n".join(lines) if lines else "No subjects found."


@tool
def get_academic_profile() -> str:
    """
    Fetch the student's complete academic history for career analysis.
    Returns all years, subjects (with credit values), and per-assessment scores.
    """
    try:
        years = _get_api_client().get_academic_years()
    except Exception as e:
        return f"Error fetching profile: {e}"

    if not years:
        return "No academic data found."

    lines: list[str] = []
    for year in years:
        lines.append(f"\n[{year.get('label', 'Year ?')}]")
        for subject in year.get("subjects", []):
            name = subject.get("name", "Unknown")
            credits = subject.get("credit_value", 0)
            assessments = subject.get("assessments", [])
            scored = [
                float(a["grade"]["score"])
                for a in assessments
                if a.get("grade") and a["grade"].get("score") is not None
            ]
            avg = f"{sum(scored) / len(scored):.1f}" if scored else "no grades yet"
            lines.append(f"  {name} ({credits} credits) | average: {avg}")
            for a in assessments:
                score = (
                    a["grade"]["score"]
                    if a.get("grade") and a["grade"].get("score") is not None
                    else "not graded"
                )
                lines.append(f"    - {a.get('name', '?')} ({a.get('weight', 0)}%): {score}")

    return "\n".join(lines)
