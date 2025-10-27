import os
from http import HTTPStatus

from flask import Flask, jsonify, request
from flask_cors import CORS

from applications.notes import (
    get_note,
    NotFoundError,
    add_note,
    ValidationError,
    get_all_notes,
)
from infrastructure.mysql.mysql_repository import (
    MySQLRepository,
)

# todo: add proper logs for errors


def _validate_env_variable(env: str) -> str:
    if env not in os.environ:
        raise ValueError("{} not found in environment variables.".format(env))
    return os.environ[env]


def register_notes_routes(app: Flask, repository: MySQLRepository) -> None:
    # Enable CORS in dev environment for Swagger UI only
    # THIS IS ONLY FOR DEMO APP PURPOSE
    environment = _validate_env_variable("SERVICE_ENVIRONMENT")
    if environment == "dev":
        CORS(app, resources={r"/api/*": {"origins": "http://localhost:8081"}})

    @app.route("/api/v1/notes/<int:note_id>", methods=["GET"])
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
            return (
                jsonify({"error": "Internal error"}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    @app.route("/api/v1/notes", methods=["POST"])
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
            return (
                jsonify({"error": "Internal error"}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    @app.route("/api/v1/notes", methods=["GET"])
    def get_notes() -> tuple:
        try:
            notes = get_all_notes(repository)
            return jsonify(notes), 200
        except Exception as error:
            return (
                jsonify({"error": "Internal error"}),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )
