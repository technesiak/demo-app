import datetime
import logging
import os
import unittest
from http import HTTPStatus
from unittest import TestCase

import requests
from flask import Flask
from sqlalchemy import URL, text

from infrastructure.mysql.mysql_repository import MySQLRepository
from main import get_env_value
from models.models import db, Note
from routes.notes import register_notes_routes

APP_URL = os.getenv("URL", "")


class TestNotesRoutes(TestCase):
    app: Flask
    logger: logging.Logger

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = Flask(__name__)
        cls.app.config["TESTING"] = True
        db_host = get_env_value("DB_HOST")
        db_port = int(get_env_value("DB_PORT"))
        db_name = get_env_value("DB_DATABASE")
        db_user = get_env_value("DB_USERNAME")
        db_password = get_env_value("DB_PASSWORD")
        db_url = URL.create(
            drivername="mysql+pymysql",
            username=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name,
        )
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = db_url
        cls.logger = logging.getLogger(__name__)
        db.init_app(cls.app)

        mysql_repository = MySQLRepository(db, cls.logger)

        register_notes_routes(cls.app, mysql_repository, logger=cls.logger)

        with cls.app.app_context():
            db.create_all()

    def setUp(self) -> None:
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.execute(text("TRUNCATE TABLE notes"))
            db.session.commit()

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.app.app_context():
            db.session.query(Note).delete()
            db.session.commit()

    def test_get_note_success_without_comment(self) -> None:
        # given
        given_note_id = 1

        with self.app.app_context():
            note = Note(title="Test Note", content="Test Content")
            result_before = (
                db.session.query(Note).filter(Note.id == given_note_id).first()
            )

            self.assertIsNone(result_before)

            db.session.add(note)
            db.session.commit()
            if note.id is None:
                raise RuntimeError("Database did not return an ID")

        # when
        res = requests.get(APP_URL + f"/api/v1/notes/{int(note.id)}")
        # then

        self.assertEqual(res.status_code, HTTPStatus.OK)

        data = res.json()

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Test Note")
        self.assertEqual(data["content"], "Test Content")
        self.assertIsInstance(data["created_at"], str)
        try:
            datetime.datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            self.fail(
                f"created_at '{data['created_at']}' is not a valid RFC3339 string"
            )
        self.assertIsNone(data["comment"])

    def test_get_note_success_with_comment(self) -> None:
        # given
        given_note_id = 1

        with self.app.app_context():
            note = Note(
                title="Test Note", content="Test Content", comment="Test Comment"
            )
            result_before = (
                db.session.query(Note).filter(Note.id == given_note_id).first()
            )

            self.assertIsNone(result_before)

            db.session.add(note)
            db.session.commit()
            if note.id is None:
                raise RuntimeError("Database did not return an ID")

        # when
        res = requests.get(APP_URL + f"/api/v1/notes/{int(note.id)}")
        # then

        self.assertEqual(res.status_code, HTTPStatus.OK)

        data = res.json()

        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Test Note")
        self.assertEqual(data["content"], "Test Content")
        self.assertIsInstance(data["created_at"], str)
        try:
            datetime.datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            self.fail(
                f"created_at '{data['created_at']}' is not a valid RFC3339 string"
            )
        self.assertEqual(data["comment"], "Test Comment")

    def test_add_note_success_without_comment(self) -> None:
        # given
        payload = {"title": "test title", "content": "This is a test note."}

        # when
        res = requests.post(
            url=APP_URL + f"/api/v1/notes",
            json=payload,
        )

        # then
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)

    def test_add_note_success_with_comment(self) -> None:
        # given
        payload = {
            "title": "test title",
            "content": "This is a test note.",
            "comment": "Test Comment",
        }

        # when
        res = requests.post(
            url=APP_URL + f"/api/v1/notes",
            json=payload,
        )

        # then
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)

    def test_add_note_missing_fields(self) -> None:
        # given
        payload = {"title": "No Content"}

        # when
        res = requests.post(
            url=APP_URL + f"/api/v1/notes",
            json=payload,
        )

        # then
        self.assertEqual(res.status_code, 400)
        data = res.json()
        assert data == {"error": "Missing content"}

    def test_add_note_invalid_request(self) -> None:
        # given
        payload = ""

        # when
        res = requests.post(
            url=APP_URL + f"/api/v1/notes",
            json=payload,
        )

        # then
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data, {"error": "Invalid request body"})

    def test_get_notes_returned_empty_list(self) -> None:
        # given
        expected_result = {"has_more": False, "notes": []}

        # when
        res = requests.get(url=APP_URL + f"/api/v1/notes")

        # then
        self.assertEqual(res.status_code, HTTPStatus.OK)
        data = res.json()

        self.assertEqual(data, expected_result)

    def test_get_notes_success_with_data(self) -> None:
        # given
        with self.app.app_context():
            note1 = Note(title="First", content="first content")
            note2 = Note(
                title="Second", content="second content", comment="second comment"
            )
            db.session.add_all([note1, note2])
            db.session.commit()

            created_at_1 = note1.created_at.astimezone(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            created_at_2 = note2.created_at.astimezone(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        expected_result: dict = {
            "has_more": False,
            "notes": [
                {
                    "id": note2.id,
                    "title": "Second",
                    "content": "second content",
                    "comment": "second comment",
                    "created_at": created_at_2,
                },
                {
                    "id": note1.id,
                    "title": "First",
                    "content": "first content",
                    "comment": None,
                    "created_at": created_at_1,
                },
            ],
        }

        # when
        res = requests.get(url=APP_URL + "/api/v1/notes")

        # then
        self.assertEqual(res.status_code, HTTPStatus.OK)

        data: dict = res.json()
        self.assertEqual(len(data["notes"]), 2)
        self.assertEqual(data["has_more"], expected_result["has_more"])

        expected_notes: list[dict] = expected_result["notes"]
        actual_notes: list[dict] = list(data["notes"])

        for expected, actual in zip(expected_notes, actual_notes):
            self.assertEqual(expected["id"], actual["id"])
            self.assertEqual(expected["title"], actual["title"])
            self.assertEqual(expected["content"], actual["content"])
            self.assertEqual(expected["comment"], actual["comment"])
            self.assertEqual(expected["created_at"], actual["created_at"])

    def test_get_notes_with_limit_and_last_id(self) -> None:
        # given
        with self.app.app_context():
            for i in range(1, 6):
                db.session.add(Note(title=f"Note {i}", content=f"Content {i}"))
            db.session.commit()

            notes = Note.query.order_by(Note.id.desc()).all()
            notes_dict: list[dict] = [
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content,
                    "comment": note.comment,
                    "created_at": note.created_at.astimezone(
                        datetime.timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                }
                for note in notes
            ]

        res = requests.get(APP_URL + "/api/v1/notes?limit=2&last_id=3")

        # then
        self.assertEqual(res.status_code, HTTPStatus.OK)
        data: dict = res.json()

        expected_notes: list[dict] = [n for n in notes_dict if n["id"] < 3]
        expected_notes = expected_notes[:2]
        expected_result: dict = {
            "has_more": False,
            "notes": expected_notes,
        }

        self.assertIn("notes", data)
        self.assertIn("has_more", data)
        self.assertLessEqual(len(data["notes"]), 2)

        actual_notes: list[dict] = list(data["notes"])
        for expected, actual in zip(expected_notes, actual_notes):
            self.assertEqual(expected["id"], actual["id"])
            self.assertEqual(expected["title"], actual["title"])
            self.assertEqual(expected["content"], actual["content"])
            self.assertEqual(expected["comment"], actual["comment"])
            self.assertEqual(expected["created_at"], actual["created_at"])

        self.assertEqual(data["has_more"], expected_result["has_more"])

    def test_get_notes_max_limit_exceeded(self) -> None:
        # when
        res = requests.get(url=APP_URL + f"/api/v1/notes?limit=9999")

        # then
        self.assertEqual(res.status_code, HTTPStatus.CONFLICT)
        data = res.json()
        self.assertEqual(data["error"], "Max limit exceeded")

    def test_get_notes_invalid_limit(self) -> None:
        # when
        res = requests.get(url=APP_URL + f"/api/v1/notes?limit=abc")

        # then
        data = res.json()
        self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(data["error"], "Invalid limit parameter")

    def test_get_notes_invalid_last_id(self) -> None:
        # when
        res = requests.get(url=APP_URL + f"/api/v1/notes?limit=1&last_id=abc")

        # then
        data = res.json()
        self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(data["error"], "Invalid last_id parameter")


if __name__ == "__main__":
    unittest.main()
