"""Tests for services/data_service.py — APIClient mocked."""

from unittest.mock import patch

from services.data_service import DataService


class TestGetUniversities:

    def test_returns_list_from_client(self):
        unis = [{"id": 1, "name": "MIT"}, {"id": 2, "name": "Oxford"}]
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.get_universities.return_value = unis
            result = DataService.get_universities()
        assert result == unis

    def test_returns_empty_list_on_exception(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.get_universities.side_effect = Exception("network error")
            result = DataService.get_universities()
        assert result == []

    def test_returns_empty_list_when_server_raises_value_error(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.get_universities.side_effect = ValueError("500")
            result = DataService.get_universities()
        assert result == []


class TestGetMajors:

    def test_returns_list_from_client(self):
        majors = [{"id": 1, "name": "Computer Science"}]
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.get_majors.return_value = majors
            result = DataService.get_majors()
        assert result == majors

    def test_returns_empty_list_on_exception(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.get_majors.side_effect = Exception("server down")
            result = DataService.get_majors()
        assert result == []

    def test_returns_empty_list_when_server_raises_value_error(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.get_majors.side_effect = ValueError("503")
            result = DataService.get_majors()
        assert result == []
