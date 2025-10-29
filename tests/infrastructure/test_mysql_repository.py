import logging
from unittest import TestCase

from flask import Flask
from sqlalchemy import URL, text
from sqlalchemy.exc import IntegrityError

from infrastructure.mysql.mysql_repository import (
    MySQLRepository,
)
from main import validate_env_variable
from models import db, Note


class TestMySQLRepository(TestCase):
    app: Flask
    repo: MySQLRepository
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
        db.init_app(cls.app)
        cls.logger = logging.getLogger(__name__)

        with cls.app.app_context():
            db.create_all()
            cls.repo = MySQLRepository(db, cls.logger)

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.app.app_context():
            db.session.execute(text("TRUNCATE TABLE notes"))
            db.session.commit()

    def tearDown(self) -> None:
        with self.app.app_context():
            db.session.execute(text("TRUNCATE TABLE notes"))
            db.session.commit()

    def test_health_check_success(self) -> None:
        with self.app.app_context():
            self.assertTrue(self.repo.health_check())

    def test_get_by_id_success(self) -> None:
        # given
        note1 = Note(title="Test1", content="Some content1")
        note2 = Note(title="Test2", content="Some content2")
        note3 = Note(title="Test3", content="Some content3", comment="Comment")

        with self.app.app_context():
            self.repo.add(note1)
            added_note2_id = self.repo.add(note2)
            added_note3_id = self.repo.add(note3)

            # when
            fetched = self.repo.get_by_id(added_note2_id)
            # then
            if fetched is None:
                self.fail("Note not found in database")
            self.assertEqual(fetched.content, "Some content2")
            self.assertEqual(fetched.title, "Test2")
            self.assertIsNone(fetched.comment)
            # and when
            fetched_note_3 = self.repo.get_by_id(added_note3_id)
            # and then
            if fetched_note_3 is None:
                self.fail("Note not found in database")
            self.assertEqual(fetched_note_3.content, "Some content3")
            self.assertEqual(fetched_note_3.title, "Test3")
            self.assertEqual(fetched_note_3.comment, "Comment")

    def test_get_by_id_not_found(self) -> None:
        # given
        note_id = 1000
        with self.app.app_context():

            # when
            fetched = self.repo.get_by_id(note_id)
            self.assertEqual(fetched, None)

    def test_add_success_without_comment(self) -> None:
        # given
        note = Note(title="Test", content="Some content")
        # when
        with self.app.app_context():
            added_note_id = self.repo.add(note)

            # then
            fetched = self.repo.get_by_id(added_note_id)
            if fetched is None:
                self.fail("Note not found in database")
            self.assertEqual(fetched.content, "Some content")
            self.assertEqual(fetched.title, "Test")
            self.assertIsNone(fetched.comment)

    def test_add_success_with_comment(self) -> None:
        # given
        note = Note(title="Test", content="Some content", comment="Comment")
        # when
        with self.app.app_context():
            added_note_id = self.repo.add(note)

            # then
            fetched = self.repo.get_by_id(added_note_id)
            if fetched is None:
                self.fail("Note not found in database")
            self.assertEqual(fetched.content, "Some content")
            self.assertEqual(fetched.title, "Test")
            self.assertEqual(fetched.comment, "Comment")

    def test_add_note_without_title(self) -> None:
        note = Note(content="Some content")
        with self.app.app_context():
            with self.assertRaises(IntegrityError):
                self.repo.add(note)

    def test_get_notes_returns_ordered_list(self) -> None:
        # given
        note1 = Note(title="First", content="first content")
        note2 = Note(title="Second", content="second content", comment="comment")
        with self.app.app_context():
            self.repo.add(note1)
            self.repo.add(note2)

            # when
            notes, has_more = self.repo.get_notes()

            # then
            self.assertEqual(len(notes), 2)
            self.assertFalse(has_more)
            self.assertEqual(notes[0].id, 2)
            self.assertEqual(notes[0].title, "Second")
            self.assertEqual(notes[0].content, "second content")
            self.assertEqual(notes[0].comment, "comment")
            self.assertEqual(notes[1].id, 1)
            self.assertEqual(notes[1].title, "First")
            self.assertEqual(notes[1].content, "first content")
            self.assertIsNone(notes[1].comment)

    def test_get_notes_empty_list(self) -> None:

        # when
        with self.app.app_context():
            notes, has_more = self.repo.get_notes()

            # then
            self.assertEqual(notes, [])
            self.assertFalse(has_more)

    def test_get_notes_returns_ordered_list_limit_was_given(self) -> None:
        # given
        note1 = Note(title="First", content="first content")
        note2 = Note(title="Second", content="second content", comment="comment")
        with self.app.app_context():
            self.repo.add(note1)
            self.repo.add(note2)

            # when
            notes, has_more = self.repo.get_notes(limit=1)

            # then
            self.assertEqual(len(notes), 1)
            self.assertTrue(has_more)
            self.assertEqual(notes[0].id, 2)
            self.assertEqual(notes[0].title, "Second")
            self.assertEqual(notes[0].content, "second content")
            self.assertEqual(notes[0].comment, "comment")

    def test_get_notes_returns_ordered_list_limit_and_last_id_were_given(self) -> None:
        # given
        note1 = Note(title="First", content="first content")
        note2 = Note(title="Second", content="second content", comment="comment")
        note3 = Note(title="Third", content="third content", comment="comment2")
        note4 = Note(title="Fourth", content="fourth content")
        note5 = Note(title="Fifth", content="fifth content")
        with self.app.app_context():
            self.repo.add(note1)
            self.repo.add(note2)
            note3_id = self.repo.add(note3)
            self.repo.add(note4)
            self.repo.add(note5)

            # when
            notes, has_more = self.repo.get_notes(limit=2, last_id=note3_id)

            # then
            self.assertEqual(len(notes), 2)
            self.assertFalse(has_more)
            self.assertEqual(notes[0].id, 2)
            self.assertEqual(notes[0].title, "Second")
            self.assertEqual(notes[0].content, "second content")
            self.assertEqual(notes[0].comment, "comment")
            self.assertEqual(notes[1].id, 1)
            self.assertEqual(notes[1].title, "First")
            self.assertEqual(notes[1].content, "first content")
            self.assertIsNone(notes[1].comment)
