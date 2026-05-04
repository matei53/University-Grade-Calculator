from database.db import get_connection

class DashboardService:
    @staticmethod
    def get_user_dashboard_data(user_id):
        """Fetches dynamic data from the database instead of hardcoded mocks."""
        all_data = {}
        with get_connection() as conn:
            # 1. Fetch Years for this user
            years = conn.execute("SELECT id, order_index, credit_requirement FROM academic_years WHERE user_id = ?", (user_id,)).fetchall()
            
            for y in years:
                year_num = y["order_index"]
                all_data[year_num] = {"target_credits": y["credit_requirement"], "subjects": []}
                
                # # 2. Fetch Subjects
                # subjects = conn.execute("""
                #     SELECT sub.id as subject_id, sub.name, sub.credit_value as credits, sem.order_index as semester
                #     FROM subjects sub
                #     JOIN semesters sem ON sub.semester_id = sem.id
                #     WHERE sem.academic_year_id = ?
                # """, (y["id"],)).fetchall()

                # 2. Fetch Subjects
                subjects = conn.execute("""
                    SELECT sub.id as subject_id, sub.name, sub.credit_value as credits, sem.order_index as semester
                    FROM subjects sub
                    LEFT JOIN semesters sem ON sub.semester_id = sem.id  
                    WHERE sub.academic_year_id = ?                      
                """, (y["id"],)).fetchall()
                
                for sub in subjects:
                    # 3. Fetch Grades and calculate average
                    assessments = conn.execute("""
                        SELECT a.weight, g.score 
                        FROM assessments a 
                        LEFT JOIN grades g ON g.assessment_id = a.id 
                        WHERE a.subject_id = ?
                    """, (sub["subject_id"],)).fetchall()
                    
                    total_grade = 0.0
                    has_grades = False
                    
                    for a in assessments:
                        if a["score"] is not None:
                            has_grades = True
                            total_grade += (a["score"] * a["weight"]) / 100.0
                    
                    all_data[year_num]["subjects"].append({
                        'name': sub["name"],
                        'credits': sub["credits"],
                        'grade': round(total_grade, 2) if has_grades else None,
                        'semester': sub["semester"]
                    })
        return all_data


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