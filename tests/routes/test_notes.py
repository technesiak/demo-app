import logging
import os
import unittest
from http import HTTPStatus
from unittest import TestCase

import requests
from flask import Flask
from sqlalchemy import URL, text, Nullable

from infrastructure.mysql.mysql_repository import MySQLRepository
from main import validate_env_variable
from models import db, Note
from routes.notes import register_notes_routes

APP_URL = os.getenv("URL", "")


class TestNotesRoutes(TestCase):
    app: Flask
    logger: logging.Logger

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = Flask(__name__)
        cls.app.config["TESTING"] = True
        db_host = validate_env_variable("DB_HOST")
        db_port = int(validate_env_variable("DB_PORT"))
        db_name = validate_env_variable("DB_DATABASE")
        db_user = validate_env_variable("DB_USERNAME")
        db_password = validate_env_variable("DB_PASSWORD")
        db_dsn = URL.create(
            drivername="mysql+pymysql",
            username=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            database=db_name,
        )
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = db_dsn
        cls.logger = logging.getLogger(__name__)
        db.init_app(cls.app)

        mysql_repository = MySQLRepository(db, cls.logger)

        register_notes_routes(cls.app, mysql_repository)

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
        expected_result: dict = {"has_more": False, "notes": []}
        # when
        res = requests.get(APP_URL + f"/api/v1/notes")
        # then
        self.assertEqual(res.status_code, HTTPStatus.OK)

        data = res.json()

        self.assertEqual(len(data), len(expected_result))
        self.assertEqual(data, expected_result)

    def test_get_notes_success(self) -> None:
        # given
        expected_result: dict = {
            "has_more": False,
            "notes": [
                {
                    "comment": "second comment",
                    "content": "second content",
                    "created_at": "Tue, 28 Oct 2025 18:27:22 GMT",
                    "id": 2,
                    "title": "Second",
                },
                {
                    "comment": None,
                    "content": "first content",
                    "created_at": "Tue, 28 Oct 2025 18:27:22 GMT",
                    "id": 1,
                    "title": "First",
                },
            ],
        }
        with self.app.app_context():
            note1 = Note(title="First", content="first content")
            note2 = Note(
                title="Second", content="second content", comment="second comment"
            )

            db.session.add(note1)
            db.session.add(note2)
            db.session.commit()

        # when
        res = requests.get(APP_URL + f"/api/v1/notes")
        # then

        self.assertEqual(res.status_code, HTTPStatus.OK)

        data = res.json()

        self.assertEqual(len(data["notes"]), len(expected_result["notes"]))


if __name__ == "__main__":
    unittest.main()
