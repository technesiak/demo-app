import unittest
from unittest.mock import MagicMock

from applications.notes import (
    get_note,
    NotFoundError,
    add_note,
    ValidationError,
    MIN_TITLE_LEN,
    MAX_TITLE_LEN,
)
from models import Note


class TestNote(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = MagicMock()

    def test_get_note_success(self) -> None:
        # given
        expected_title = "Test Title"
        expected_content = "Test Content"
        note = Note(title=expected_title, content=expected_content)
        self.repo.get_by_id.return_value = note

        # when
        result = get_note(self.repo, 1)

        # then
        self.repo.get_by_id.assert_called_once_with(1)
        self.assertEqual(result.title, expected_title)
        self.assertEqual(result.content, expected_content)

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
        with self.assertRaises(ValidationError) as context:
            add_note(self.repo, "", "Some content")
        self.assertEqual(str(context.exception), "Title is required")

    def test_add_note_too_short_title(self) -> None:
        with self.assertRaises(ValidationError) as context:
            add_note(self.repo, "12", "Lorem ipsum dolor sit amet")
        self.assertEqual(
            str(context.exception),
            f"Title must be between {MIN_TITLE_LEN} and {MAX_TITLE_LEN} characters",
        )


# todo: additional test for 'content required' and 'MIN/MAX content check'

if __name__ == "__main__":
    unittest.main()
