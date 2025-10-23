from http import HTTPStatus

from flask import Flask, jsonify, request

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


def register_notes_routes(app: Flask, repository: MySQLRepository) -> None:
    @app.route("/api/v1/notes/<int:note_id>", methods=["GET"])
    def get_note_route(note_id: int) -> tuple:
        try:
            note = get_note(repository, note_id)
            return (
                jsonify(
                    {
                        "id": note.id,
                        "title": note.title,
                        "content": note.content,
                        "created_at": (
                            note.created_at.isoformat() if note.created_at else None
                        ),
                    }
                ),
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

        if title is None:
            return jsonify({"error": "Missing title"}), HTTPStatus.BAD_REQUEST
        if content is None:
            return jsonify({"error": "Missing content"}), HTTPStatus.BAD_REQUEST

        try:
            note_id = add_note(repository, title, content)
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
