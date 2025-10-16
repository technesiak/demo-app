import unittest
from unittest.mock import MagicMock

from applications.notes import get_note, NotFoundError, add_note, ValidationError
from models import Note


class TestNote(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = MagicMock()

    def test_get_note_success(self) -> None:
        # given
        note = Note(title="Mocked", content="Mock content")
        self.repo.get_by_id.return_value = note

        # when
        result = get_note(self.repo, 1)

        # then
        self.repo.get_by_id.assert_called_once_with(1)
        self.assertEqual(result.title, "Mocked")
        self.assertEqual(result.content, "Mock content")

    def test_get_note_not_found_raises(self) -> None:
        # given
        self.repo.get_by_id.return_value = None

        # then
        with self.assertRaises(NotFoundError):
            get_note(self.repo, 42)
        self.repo.get_by_id.assert_called_once_with(42)

    def test_add_note_success(self) -> None:
        # given
        expected_note_id = 123
        self.repo.add.return_value = expected_note_id

        # when
        note_id = add_note(self.repo, "Valid Title", "Valid content")

        # then
        self.assertEqual(note_id, expected_note_id)

        added_note = self.repo.add.call_args[0][0]
        self.assertEqual(added_note.title, "Valid Title")
        self.assertEqual(added_note.content, "Valid content")

    def test_add_note_invalid_title_raises(self) -> None:
        with self.assertRaises(ValidationError):
            add_note(self.repo, "", "Some content")

    def test_add_note_invalid_content_raises(self) -> None:
        with self.assertRaises(ValidationError):
            add_note(self.repo, "Title", "")


if __name__ == "__main__":
    unittest.main()
