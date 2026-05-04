from database.db import get_connection

class UserRepo:
    def create(self, username: str, password_hash: str) -> dict:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            return {"id": cursor.lastrowid, "username": username}

    def find_by_username(self, username: str):
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()

    def update_university(self, user_id: int, university_id: int):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET university_id = ? WHERE id = ?",
                (university_id, user_id)
            )
    def update_major(self, user_id: int, major_id: int):
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET major_id = ? WHERE id = ?",
                (major_id, user_id)
            )