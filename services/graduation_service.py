from typing import Optional

from client.api_client import APIClient


class GraduationService:
    def __init__(self):
        self._client = APIClient()

    def get_settings(self) -> dict:
        return self._client.get_graduation_settings()

    def update_settings(self, subject_average_weight: float, max_grade: float = 10.0) -> dict:
        return self._client.update_graduation_settings(subject_average_weight, max_grade)

    def get_final_assessments(self) -> list[dict]:
        return self._client.get_final_assessments()

    def add_final_assessment(
        self,
        name: str,
        weight: float,
        max_score: float = 10.0,
        passing_grade: float = 5.0,
    ) -> dict:
        return self._client.add_final_assessment(name, weight, max_score, passing_grade)

    def update_final_assessment(
        self,
        assessment_id: int,
        name: Optional[str] = None,
        weight: Optional[float] = None,
        max_score: Optional[float] = None,
        passing_grade: Optional[float] = None,
    ) -> dict:
        return self._client.update_final_assessment(
            assessment_id, name, weight, max_score, passing_grade
        )

    def delete_final_assessment(self, assessment_id: int) -> None:
        self._client.delete_final_assessment(assessment_id)

    def set_grade(self, assessment_id: int, score: Optional[float]) -> dict:
        return self._client.set_final_assessment_grade(assessment_id, score)
