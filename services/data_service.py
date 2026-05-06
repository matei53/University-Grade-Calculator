import json
import os
from database.db import get_connection

class DataService:
    """Service for managing custom universities and majors"""
    
    UNIVERSITIES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "universities.json")
    MAJORS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "majors.json")

    @staticmethod
    def add_university(name: str) -> int:
        """
        Add a university to the database and JSON file if it doesn't already exist.
        Returns the university ID (new or existing).
        Raises ValueError if the name is empty.
        """
        if not name or not name.strip():
            raise ValueError("University name cannot be empty.")
        
        name = name.strip()
        
        # Check if university already exists (case-insensitive)
        existing_id = DataService._find_existing_university(name)
        if existing_id is not None:
            return existing_id
        
        # Add to database
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO universities (name) VALUES (?)",
                (name,)
            )
            university_id = cursor.lastrowid
        
        # Add to JSON file
        DataService._add_to_json(DataService.UNIVERSITIES_PATH, name, university_id)
        
        return university_id

    @staticmethod
    def add_major(name: str) -> int:
        """
        Add a major to the database and JSON file if it doesn't already exist.
        Returns the major ID (new or existing).
        Raises ValueError if the name is empty.
        """
        if not name or not name.strip():
            raise ValueError("Major name cannot be empty.")
        
        name = name.strip()
        
        # Check if major already exists (case-insensitive)
        existing_id = DataService._find_existing_major(name)
        if existing_id is not None:
            return existing_id
        
        # Add to database
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO majors (name) VALUES (?)",
                (name,)
            )
            major_id = cursor.lastrowid
        
        # Add to JSON file
        DataService._add_to_json(DataService.MAJORS_PATH, name, major_id)
        
        return major_id

    @staticmethod
    def _find_existing_university(name: str):
        """Find university ID by name (case-insensitive). Returns None if not found."""
        with get_connection() as conn:
            result = conn.execute(
                "SELECT id FROM universities WHERE LOWER(name) = LOWER(?)",
                (name,)
            ).fetchone()
        return result[0] if result else None

    @staticmethod
    def _find_existing_major(name: str):
        """Find major ID by name (case-insensitive). Returns None if not found."""
        with get_connection() as conn:
            result = conn.execute(
                "SELECT id FROM majors WHERE LOWER(name) = LOWER(?)",
                (name,)
            ).fetchone()
        return result[0] if result else None

    @staticmethod
    def _add_to_json(file_path: str, name: str, item_id: int):
        """Add a new entry to the JSON file."""
        try:
            # Load existing data
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    data = json.load(f)
            else:
                data = []
            
            # Add new entry
            data.append({"id": item_id, "name": name})
            
            # Write back to file
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to update JSON file: {str(e)}")
