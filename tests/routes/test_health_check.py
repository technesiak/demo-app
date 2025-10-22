from http import HTTPStatus
from unittest import TestCase
from unittest.mock import MagicMock

from flask import Flask

from routes.health_check import register_health_check_routes


class TestHealthCheckControllers(TestCase):
    def setUp(self) -> None:
        self.app = Flask(__name__)

        self.mysql_repository = MagicMock()

        register_health_check_routes(self.app, self.mysql_repository)

        self.client = self.app.test_client()

    def test_health_check_service_is_ok(self) -> None:
        # given
        self.mysql_repository.health_check.return_value = True

        # when
        response = self.client.get("/health")

        # then
        self.assertEqual(response.status_code, HTTPStatus.OK)
        data = response.get_json()
        self.assertEqual(data, {"database": "ok"})

    def test_health_check_mysql_error(self) -> None:
        # given
        self.mysql_repository.health_check.return_value = False

        # when
        response = self.client.get("/health")

        # then
        self.assertEqual(response.status_code, HTTPStatus.INTERNAL_SERVER_ERROR)
        data = response.get_json()
        self.assertEqual(data, {"database": "error"})
