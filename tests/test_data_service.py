"""Tests for services/data_service.py — APIClient mocked."""

import pytest
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


class TestAddUniversity:

    def test_returns_id_from_client(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.create_university.return_value = {"id": 5, "name": "MIT"}
            result = DataService.add_university("MIT")
        assert result == 5

    def test_delegates_name_to_client(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.create_university.return_value = {"id": 1, "name": "Oxford"}
            DataService.add_university("Oxford")
        MockClient.return_value.create_university.assert_called_once_with("Oxford")

    def test_propagates_value_error_from_client(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.create_university.side_effect = ValueError("server error")
            with pytest.raises(ValueError):
                DataService.add_university("Bad University")


class TestAddMajor:

    def test_returns_id_from_client(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.create_major.return_value = {"id": 7, "name": "Physics"}
            result = DataService.add_major("Physics")
        assert result == 7

    def test_delegates_name_to_client(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.create_major.return_value = {"id": 1, "name": "Law"}
            DataService.add_major("Law")
        MockClient.return_value.create_major.assert_called_once_with("Law")

    def test_propagates_value_error_from_client(self):
        with patch("services.data_service.APIClient") as MockClient:
            MockClient.return_value.create_major.side_effect = ValueError("server error")
            with pytest.raises(ValueError):
                DataService.add_major("Bad Major")
