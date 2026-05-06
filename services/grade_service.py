class GradeService:
    @staticmethod
    def validate_weights_total(assessments: list[dict]) -> bool:
        """Ensures all assessment weights for a subject equal exactly 100%."""
        total_weight = sum(float(assessment.get('weight', 0)) for assessment in assessments)
        return total_weight == 100.0

    @staticmethod
    def calculate_subject_average(assessments: list[dict], subject_max_grade: float = 10.0) -> float:
        """
        Calculates the weighted average for a subject, normalizing each assessment 
        score to the subject's max grade.
        """
        total_score = 0.0
        for a in assessments:
            score = a.get('score')
            weight = a.get('weight', 0.0)
            max_score = a.get('max_score', 10.0)
            
            if score is not None:
                # 1. Normalizăm nota la o fracție (ex: 45 / 100 = 0.45)
                normalized_score = (float(score) / float(max_score)) if float(max_score) > 0 else 0
                
                # 2. Aplicăm ponderea și scalăm la nota maximă a materiei (ex: 0.45 * 1.0 * 10 = 4.5)
                weighted_portion = normalized_score * (float(weight) / 100.0) * float(subject_max_grade)
                total_score += weighted_portion
                
        return round(total_score, 2)