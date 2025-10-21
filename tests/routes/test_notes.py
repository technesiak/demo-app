import logging
import os
from http import HTTPStatus
from unittest import TestCase

import requests
from flask import Flask
from sqlalchemy import URL, text

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

    def test_get_note_success(self) -> None:
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

        # Rozpakuj JSON
        data = res.json()

        # Sprawdzenia pola po polu
        self.assertIn("id", data)
        self.assertIsInstance(data["id"], int)
        self.assertEqual(data["id"], 1)

        self.assertIn("title", data)
        self.assertEqual(data["title"], "Test Note")

        self.assertIn("content", data)
        self.assertEqual(data["content"], "Test Content")

        self.assertIn("created_at", data)
        self.assertIsInstance(data["created_at"], str)
