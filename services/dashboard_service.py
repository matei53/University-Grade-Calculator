class DashboardService:
    @staticmethod
    def calculate_stats(all_years_data, up_to_year, total_program_credits=180, passing_grade=5.0):
        total_weighted_points = 0
        total_credits_with_grades = 0
        total_credits_earned = 0
        
        for year_num, year_data in all_years_data.items():
            if year_num <= up_to_year:
                for subject in year_data['subjects']:
                    grade = subject.get('grade')
                    credits = subject.get('credits', 0)
                    
                    if grade is not None:
                        total_weighted_points += (grade * credits)
                        total_credits_with_grades += credits
                        
                        # FIX 2: Only count credits if they passed the subject
                        if grade >= passing_grade:
                            total_credits_earned += credits
        
        weighted_avg = total_weighted_points / total_credits_with_grades if total_credits_with_grades > 0 else 0.0
        
        return {
            "weighted_avg": weighted_avg,
            "credits": total_credits_earned,
            "progress": int((total_credits_earned / total_program_credits) * 100) if total_program_credits > 0 else 0
        }