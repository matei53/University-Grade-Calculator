from database.db import get_connection


class UserRepo:
    def create(self, username: str, password_hash: str) -> dict:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            return {"id": cursor.lastrowid, "username": username}

    def find_by_username(self, username: str):
        with get_connection() as conn:
            return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    def update_university(self, user_id: int, university_id: int):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET university_id = ? WHERE id = ?",
                (university_id, user_id),
            )

    def update_major(self, user_id: int, major_id: int):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET major_id = ? WHERE id = ?",
                (major_id, user_id),
            )

    # Added this
    def get_profile_info(self, user_id: int):
        with get_connection() as conn:
            # We use LEFT JOIN so the user is still returned even if
            # they haven't picked a uni or major yet.
            return conn.execute(
                """
                    SELECT
                    u.username,
                    univ.name AS university_name,
                    m.name AS major_name
                FROM users u
                LEFT JOIN universities univ ON u.university_id = univ.id
                LEFT JOIN majors m ON u.major_id = m.id
                WHERE u.id = ?
            """,
                (user_id,),
            ).fetchone()
