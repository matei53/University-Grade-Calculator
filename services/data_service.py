from client.api_client import APIClient


class DataService:
    """Service for managing universities and majors via API"""

    def __init__(self):
        self.client = APIClient()

    @staticmethod
    def get_universities():
        """Get list of universities from server"""
        client = APIClient()
        try:
            return client.get_universities()
        except Exception as e:
            print(f"Error fetching universities: {e}")
            return []

    @staticmethod
    def get_majors():
        """Get list of majors from server"""
        client = APIClient()
        try:
            return client.get_majors()
        except Exception as e:
            print(f"Error fetching majors: {e}")
            return []

    @staticmethod
    def add_university(name: str) -> int:
        """Add a new university and return its ID"""
        client = APIClient()
        result = client.create_university(name)
        return result["id"]

    @staticmethod
    def add_major(name: str) -> int:
        """Add a new major and return its ID"""
        client = APIClient()
        result = client.create_major(name)
        return result["id"]
