"""
LangChain tools for the grade simulator agent.
Provides a tool to fetch current grades for verification by the agent.
"""

from typing import Any, Optional

from langchain_core.tools import tool

_api_client: Optional[Any] = None


def set_api_client(client: Any) -> None:
    """
    Set the API client instance for use in tools.
    Must be called before using any tools.
    """
    global _api_client
    _api_client = client


def _get_api_client() -> Any:
    """Get the current API client instance."""
    if _api_client is None:
        raise RuntimeError("API client not set. Call set_api_client() first.")
    return _api_client


def _filter_years(years_data: list[dict], year_id: Optional[int]) -> list[dict]:
    """Return academic years, optionally filtered to a single year."""
    if year_id is None:
        return years_data
    return [year for year in years_data if year.get("id") == year_id]


def _assessment_score(assessment: dict) -> Optional[float]:
    """Return the assessment score if one exists."""
    grade_obj = assessment.get("grade")
    if grade_obj is None:
        return None
    score = grade_obj.get("score")
    return float(score) if score is not None else None


@tool
def get_current_grades(year_id: Optional[int] = None) -> str:
    """
    Fetch the student's current grades for subjects.
    Optionally filter to a single academic year by year_id.

    Args:
        year_id: Optional academic year ID to limit results to one year.
    """
    client = _get_api_client()

    try:
        years_data = client.get_academic_years()
    except Exception as e:
        return f"Error fetching grades: {e}"

    years_data = _filter_years(years_data, year_id)
    grades_info = []

    for year in years_data:
        year_num = year.get("order_index", "?")

        for subject in year.get("subjects", []):
            name = subject.get("name", "Unknown")
            credits = subject.get("credit_value", 0)
            passing_grade = subject.get("passing_grade", 5.0)
            subject_max = subject.get("max_grade", 10.0)

            assessments = subject.get("assessments", [])
            total_grade = 0.0
            has_grades = False

            for assessment in assessments:
                score = _assessment_score(assessment)
                if score is None:
                    continue
                has_grades = True
                max_score = assessment.get("max_score", 10.0)
                normalized_score = (float(score) / float(max_score)) if float(max_score) > 0 else 0
                total_grade += (
                    normalized_score
                    * (float(assessment.get("weight", 0)) / 100.0)
                    * float(subject_max)
                )

            grade_value = round(total_grade, 2) if has_grades else None

            if grade_value is not None:
                grades_info.append(
                    f"- {name} (Year {year_num}, {credits} credits): "
                    f"{grade_value}/{subject_max} (passing: {passing_grade})"
                )
            else:
                grades_info.append(
                    f"- {name} (Year {year_num}, {credits} credits): "
                    f"No grade yet (passing: {passing_grade})"
                )

    if not grades_info:
        return "No subjects found."

    return "Current grades:\n" + "\n".join(grades_info)
