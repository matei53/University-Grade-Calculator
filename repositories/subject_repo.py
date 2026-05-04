from database.db import get_connection

class SubjectRepo:

    @staticmethod
    def _ensure_year_and_semesters_exist(conn, user_id, year_level):
        """
        Funcție internă: Verifică dacă Anul (1, 2, 3, 4) există pentru utilizator.
        Dacă nu, îl creează automat împreună cu cele 2 semestre.
        """
        label = f"Anul {year_level}"
        
        # 1. Caută anul existent
        year_row = conn.execute(
            "SELECT id FROM academic_years WHERE user_id = ? AND order_index = ?",
            (user_id, year_level)
        ).fetchone()

        if year_row:
            return year_row['id']

        # 2. Dacă nu există, creează anul (presupunem un target implicit de 60 de credite)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO academic_years (user_id, label, order_index, credit_requirement) VALUES (?, ?, ?, ?)",
            (user_id, label, year_level, 60)
        )
        year_id = cursor.lastrowid

        # 3. Creează automat semestrele pentru acest nou an
        cursor.execute("INSERT INTO semesters (academic_year_id, label, order_index) VALUES (?, 'Semestrul 1', 1)", (year_id,))
        cursor.execute("INSERT INTO semesters (academic_year_id, label, order_index) VALUES (?, 'Semestrul 2', 2)", (year_id,))

        return year_id

    @staticmethod
    def add_subject(user_id, subject_name, credits, semester_index, year_level):
        """
        Adaugă o materie. Creează anul automat dacă e nevoie.
        """
        with get_connection() as conn:
            # 1. Asigură-te că anul există (sau creează-l)
            year_id = SubjectRepo._ensure_year_and_semesters_exist(conn, user_id, year_level)

            cursor = conn.cursor()
            
            # 2. Găsește ID-ul semestrului corect
            sem_row = cursor.execute(
                "SELECT id FROM semesters WHERE academic_year_id = ? AND order_index = ?", 
                (year_id, semester_index)
            ).fetchone()

            if not sem_row:
                raise ValueError(f"Nu am găsit semestrul {semester_index} pentru Anul {year_level}.")

            # 3. Inserează materia
            cursor.execute(
                "INSERT INTO subjects (semester_id, name, credit_value) VALUES (?, ?, ?)",
                (sem_row['id'], subject_name, credits)
            )
            conn.commit()
            return cursor.lastrowid