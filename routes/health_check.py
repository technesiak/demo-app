from http import HTTPStatus

from flask import Flask, jsonify

from infrastructure.mysql.mysql_repository import (
    MySQLRepository,
)
from infrastructure.redis.redis_repository import RedisRepository


def register_health_check_routes(
    app: Flask,
    mysql_repository: MySQLRepository,
    redis_repository: RedisRepository,
) -> None:
    @app.route("/health", methods=["GET"])
    def health_check() -> tuple:
        health_statuses = {}

        mysql_result = mysql_repository.health_check()
        health_statuses["database"] = "ok" if mysql_result else "error"

        redis_result = redis_repository.health_check()
        health_statuses["redis"] = "ok" if redis_result else "error"

        if "error" in health_statuses.values():
            return jsonify(health_statuses), HTTPStatus.INTERNAL_SERVER_ERROR

        return jsonify(health_statuses), HTTPStatus.OK
