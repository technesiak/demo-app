from http import HTTPStatus

from flask import Flask, jsonify

from infrastructure.mysql.mysql_repository import (
    MySQLRepository,
)


def register_health_check_routes(
    app: Flask,
    mysql_repository: MySQLRepository,
) -> None:
    @app.route("/health", methods=["GET"])
    def health_check() -> tuple:
        health_statuses = {}

        mysql_result = mysql_repository.health_check()
        if mysql_result:
            health_statuses["database"] = "ok"
        else:
            health_statuses["database"] = "error"

        if "error" in health_statuses.values():
            return jsonify(health_statuses), HTTPStatus.INTERNAL_SERVER_ERROR

        return jsonify(health_statuses), HTTPStatus.OK
