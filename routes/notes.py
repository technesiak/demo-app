import logging
import os
from http import HTTPStatus

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman  # type: ignore

from services.notes import (
    get_note,
    NotFoundError,
    add_note,
    ValidationError,
    get_all_notes,
    MaxLimitExceededError,
)
from infrastructure.mysql.mysql_repository import (
    MySQLRepository,
)

KEY_PREFIX = "flask-limiter"


def _get_env_value(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def register_notes_routes(
    app: Flask, repository: MySQLRepository, redis_url: str, logger: logging.Logger
) -> None:
    # Enable CORS in dev environment for Swagger UI only
    # THIS IS ONLY FOR DEMO APP PURPOSE
    environment = _get_env_value("SERVICE_ENVIRONMENT")
    if environment == "dev":
        CORS(app, resources={r"/api/*": {"origins": "http://localhost:8081"}})

    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100 per hour"],
        storage_uri=redis_url,
        key_prefix=KEY_PREFIX,
        app=app,
    )

    Talisman(app, force_https=False)

    @app.route("/api/v1/notes/<int:note_id>", methods=["GET"])
    @limiter.limit("50 per minute")
    def get_note_route(note_id: int) -> tuple:
        try:
            note = get_note(repository, note_id)
            return (
                jsonify(note),
                HTTPStatus.OK,
            )
        except Exception as error:
            if isinstance(error, NotFoundError):
                return jsonify({"error": str(error)}), HTTPStatus.NOT_FOUND

            logger.error(error, exc_info=True)
            return (
                jsonify({"error": "Internal error"}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    @app.route("/api/v1/notes", methods=["POST"])
    @limiter.limit("20 per minute")
    def add_note_route() -> tuple:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid request body"}), HTTPStatus.BAD_REQUEST

        title = data.get("title")
        content = data.get("content")
        comment = data.get("comment")

        if title is None:
            return jsonify({"error": "Missing title"}), HTTPStatus.BAD_REQUEST
        if content is None:
            return jsonify({"error": "Missing content"}), HTTPStatus.BAD_REQUEST

        try:
            note_id = add_note(repository, title, content, comment)
            return jsonify({"id": note_id}), HTTPStatus.OK
        except Exception as error:
            if isinstance(error, ValidationError):
                return jsonify({"error": str(error)}), HTTPStatus.BAD_REQUEST

            logger.error(error, exc_info=True)
            return (
                jsonify({"error": "Internal error"}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    @app.route("/api/v1/notes", methods=["GET"])
    @limiter.limit("50 per minute")
    def get_notes() -> tuple:
        try:
            limit_raw = request.args.get("limit")
            last_id_raw = request.args.get("last_id")

            if limit_raw is not None:
                try:
                    limit = int(limit_raw)
                except ValueError:
                    return (
                        jsonify({"error": "Invalid limit parameter"}),
                        HTTPStatus.BAD_REQUEST,
                    )
            else:
                limit = None

            if last_id_raw is not None:
                try:
                    last_id = int(last_id_raw)
                except ValueError:
                    return (
                        jsonify({"error": "Invalid last_id parameter"}),
                        HTTPStatus.BAD_REQUEST,
                    )
            else:
                last_id = None

            notes_data = get_all_notes(repository, limit, last_id)

            return jsonify(notes_data), HTTPStatus.OK
        except Exception as error:
            if isinstance(error, MaxLimitExceededError):

                logger.warning(error, exc_info=True)
                return jsonify({"error": str(error)}), HTTPStatus.CONFLICT

            logger.error(error, exc_info=True)
            return (
                jsonify({"error": "Internal error"}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
