from database.db import get_connection


class SubjectRepo:

    @staticmethod
    def create_years_for_user(user_id, num_years, credit_requirements=None):
        """
        Creează anii și semestrele la crearea contului (Sign Up),
        folosind creditele personalizate introduse de utilizator.
        """
        if credit_requirements is None:
            credit_requirements = [60] * num_years

        with get_connection() as conn:
            cursor = conn.cursor()
            for year_index in range(1, num_years + 1):
                # Preia creditele pentru anul curent (sau 60 default)
                credit_req = (
                    credit_requirements[year_index - 1]
                    if year_index - 1 < len(credit_requirements)
                    else 60
                )

                # Creează anul
                cursor.execute(
                    "INSERT INTO academic_years \
                    (user_id, label, order_index, credit_requirement) \
                    VALUES (?, ?, ?, ?)",
                    (
                        user_id,
                        f"Anul {year_index}",
                        year_index,
                        credit_req,
                    ),
                )
                year_id = cursor.lastrowid

                # Creează cele 2 semestre pentru acest an
                cursor.execute(
                    "INSERT INTO semesters \
                    (academic_year_id, label, order_index) \
                    VALUES (?, 'Semestrul 1', 1)",
                    (year_id,),
                )
                cursor.execute(
                    "INSERT INTO semesters \
                    (academic_year_id, label, order_index) \
                    VALUES (?, 'Semestrul 2', 2)",
                    (year_id,),
                )
            conn.commit()

    @staticmethod
    def _ensure_year_and_semesters_exist(conn, user_id, year_level):
        """
        Internal function: Checks if the Academic Year exists for the user.
        If it doesn't exist, it creates it automatically (fallback).
        """
        label = f"Anul {year_level}"

        # 1. Caută anul existent
        year_row = conn.execute(
            "SELECT id FROM academic_years WHERE user_id = ? \
                AND order_index = ?",
            (user_id, year_level),
        ).fetchone()

        if year_row:
            return year_row["id"]

        # 2. Dacă nu există, creează anul cu 60 de credite default
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO academic_years \
            (user_id, label, order_index, credit_requirement) \
                VALUES (?, ?, ?, ?)",
            (user_id, label, year_level, 60),
        )
        year_id = cursor.lastrowid

        # 3. Creează automat semestrele pentru acest nou an
        cursor.execute(
            "INSERT INTO semesters \
            (academic_year_id, label, order_index) \
            VALUES (?, 'Semestrul 1', 1)",
            (year_id,),
        )
        cursor.execute(
            "INSERT INTO semesters \
            (academic_year_id, label, order_index) \
            VALUES (?, 'Semestrul 2', 2)",
            (year_id,),
        )

        return year_id

    @staticmethod
    def add_subject(
        user_id,
        subject_name,
        credits,
        semester_index,
        year_level,
        passing_grade=5.0,
        max_grade=10.0,
    ):
        """
        Adaugă o materie. Creează anul automat dacă e nevoie prin fallback.
        """
        with get_connection() as conn:
            year_id = SubjectRepo._ensure_year_and_semesters_exist(conn, user_id, year_level)
            cursor = conn.cursor()

            sem_row = cursor.execute(
                "SELECT id FROM semesters WHERE academic_year_id = ? \
                    AND order_index = ?",
                (year_id, semester_index),
            ).fetchone()

            if not sem_row:
                raise ValueError(f"Nu am găsit semestrul {semester_index} \
                        pentru Anul {year_level}.")

            cursor.execute(
                "INSERT INTO subjects \
                (semester_id, academic_year_id, name, credit_value, \
                    passing_grade, max_grade) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    sem_row["id"],
                    year_id,
                    subject_name,
                    credits,
                    passing_grade,
                    max_grade,
                ),
            )
            conn.commit()
            return cursor.lastrowid
