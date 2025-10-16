from http import HTTPStatus

from flask import Flask, jsonify, request

from applications.notes import get_note, NotFoundError, add_note, ValidationError
from infrastructure.mysql.mysql_repository import (
    MySQLRepository,
)


def register_notes_routes(app: Flask, repository: MySQLRepository) -> None:
    @app.route("/api/v1/notes/<int:note_id>", methods=["GET"])
    def get_note_route(note_id):
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
        except NotFoundError as e:
            return jsonify({"error": str(e)}), HTTPStatus.NOT_FOUND

    @app.route("/api/v1/notes", methods=["POST"])
    def add_note_route():
        data = request.get_json() or {}
        title = data.get("title")
        content = data.get("content")

        try:
            note_id = add_note(repository, title, content)
            return jsonify({"id": note_id}), HTTPStatus.CREATED
        except ValidationError as e:
            return jsonify({"error": str(e)}), HTTPStatus.BAD_REQUEST
