import datetime
import logging
import unittest
from http import HTTPStatus
from unittest import TestCase

import redis
import requests
from flask import Flask
from sqlalchemy import URL, text

from infrastructure.mysql.mysql_repository import MySQLRepository
from main import get_env_value
from models.models import db, Note
from routes.notes import register_notes_routes

APP_URL = get_env_value("URL")


def get_redis_client_and_url() -> tuple[redis.Redis, str]:
    redis_host = get_env_value("REDIS_HOST")
    redis_port = int(get_env_value("REDIS_PORT"))
    redis_password = get_env_value("REDIS_PASSWORD")
    redis_db = int(get_env_value("REDIS_DB"))

    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        password=redis_password,
        db=redis_db,
        decode_responses=True,
    )

    redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"

    return redis_client, redis_url


def flush_redis() -> None:
    client, _ = get_redis_client_and_url()
    client.ping()
    client.flushdb()


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
        _, redis_url = get_redis_client_and_url()
        register_notes_routes(cls.app, mysql_repository, redis_url, logger=cls.logger)

        with cls.app.app_context():
            db.create_all()

    def setUp(self) -> None:
        self.app_context = self.app.app_context()
        self.app_context.push()
        with self.app.app_context():
            flush_redis()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.execute(text("TRUNCATE TABLE notes"))
            db.session.commit()
            flush_redis()

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

    def test_get_note_with_negative_id(self) -> None:
        # when
        res = requests.get(APP_URL + "/api/v1/notes/-1")

        # then
        # Flask does not match negative numbers for <int:note_id>, so the route is never reached
        # and Flask returns 404 before the validation logic runs.
        self.assertEqual(res.status_code, HTTPStatus.NOT_FOUND)

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

    def test_add_note_without_json_content_type(self) -> None:
        # given
        payload = '{"title": "no json header", "content": "test"}'

        # when
        res = requests.post(
            APP_URL + "/api/v1/notes",
            data=payload,
            headers={"Content-Type": "text/plain"},
        )

        # then
        self.assertEqual(res.status_code, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        self.assertEqual(res.json(), {"error": "Content-Type must be application/json"})

    def test_add_note_with_empty_or_whitespace_title(self) -> None:
        # given
        payload_empty = {"title": "", "content": "data"}
        payload_space = {"title": "   ", "content": "data"}

        # when
        res_empty = requests.post(APP_URL + "/api/v1/notes", json=payload_empty)
        res_space = requests.post(APP_URL + "/api/v1/notes", json=payload_space)

        # then
        for res in [res_empty, res_space]:
            self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)
            self.assertEqual(res.json(), {"error": "title cannot be empty"})

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

    def test_get_notes_with_zero_or_negative_limit(self) -> None:
        # when
        res_zero = requests.get(APP_URL + "/api/v1/notes?limit=0")
        # then
        self.assertEqual(res_zero.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(res_zero.json(), {"error": "limit must be a positive integer"})

        # and when
        res_neg = requests.get(APP_URL + "/api/v1/notes?limit=-5")
        # then
        self.assertEqual(res_neg.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(res_neg.json(), {"error": "limit must be a positive integer"})

    def test_get_notes_with_negative_last_id(self) -> None:
        # when
        res = requests.get(APP_URL + "/api/v1/notes?last_id=-10")
        # then
        self.assertEqual(res.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(res.json(), {"error": "last_id must be a positive integer"})

    def test_rate_limit_exceeded(self) -> None:
        # given
        with self.app.app_context():
            # when
            for i in range(21):
                res = requests.post(
                    APP_URL + "/api/v1/notes",
                    json={"title": f"Title {i}", "content": "Some content"},
                )
                # then
                if i < 20:
                    self.assertEqual(
                        res.status_code, 200, f"Request {i} returned {res.status_code}"
                    )
                else:
                    self.assertEqual(
                        res.status_code, 429, f"Request {i} should trigger rate limit"
                    )

    def test_security_headers_present(self) -> None:
        # given
        with self.app.app_context():
            # when
            res = requests.get(url=APP_URL + f"/api/v1/notes?limit=abc")
        # then
        assert "Content-Security-Policy" in res.headers
        assert "X-Frame-Options" in res.headers
        assert "X-Content-Type-Options" in res.headers
        assert "Referrer-Policy" in res.headers

        self.assertEqual(res.headers["X-Frame-Options"], "SAMEORIGIN")
        self.assertEqual(res.headers["X-Content-Type-Options"], "nosniff")

    def test_sql_injection_in_get_note(self) -> None:
        # Invalid route because of string part -> should return 404, not 500
        res1 = requests.get(APP_URL + "/api/v1/notes/1 OR 1=1")
        self.assertEqual(res1.status_code, HTTPStatus.NOT_FOUND)

        res2 = requests.get(APP_URL + "/api/v1/notes/1; DELETE FROM notes;")
        self.assertEqual(res2.status_code, HTTPStatus.NOT_FOUND)

    def test_sql_injection_in_post_payload(self) -> None:
        # given
        payload = {"title": "abc'); DROP TABLE notes; --", "content": "Hello"}

        # when
        res = requests.post(APP_URL + "/api/v1/notes", json=payload)

        # then
        # should succeed as normal note (since ORM parameterizes safely)
        self.assertEqual(res.status_code, HTTPStatus.OK)
        data = res.json()
        self.assertIn("id", data)

        # ensure table still exists
        with self.app.app_context():
            count = db.session.query(Note).count()
            self.assertGreaterEqual(count, 1, "Table 'notes' may have been dropped!")


if __name__ == "__main__":
    unittest.main()
