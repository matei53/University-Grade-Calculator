class Session:
    _current_user: dict | None = None

    @classmethod
    def login(cls, user: dict):
        cls._current_user = user

    @classmethod
    def logout(cls):
        cls._current_user = None

    @classmethod
    def get_user(cls) -> dict:
        if not cls._current_user:
            raise RuntimeError("No user is logged in.")
        return cls._current_user

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls._current_user is not None