class GradeService:
    @staticmethod
    def validate_weights_total(assessments: list[dict]) -> bool:
        """Ensures all assessment weights for a subject equal exactly 100%."""
        total_weight = sum(float(assessment.get('weight', 0)) for assessment in assessments)
        return total_weight == 100.0

    @staticmethod
    def calculate_subject_average(assessments: list[dict], grades: dict) -> float:
        """
        Calculates the weighted average for a subject.
        'grades' is a dict mapping assessment_id to raw_score.
        """
        total_score = 0.0
        for assessment in assessments:
            a_id = assessment['id']
            if a_id in grades and grades[a_id] is not None:
                weighted_portion = (float(grades[a_id]) * float(assessment['weight'])) / 100.0
                total_score += weighted_portion
        return round(total_score, 2)