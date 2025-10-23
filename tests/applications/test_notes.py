import unittest
from unittest.mock import MagicMock

from applications.notes import (
    get_note,
    NotFoundError,
    add_note,
    ValidationError,
    MIN_TITLE_LEN,
    MAX_TITLE_LEN,
    MIN_CONTENT_LEN,
    MAX_CONTENT_LEN,
    get_all_notes,
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

    def test_add_note_invalid_content_raises(self) -> None:
        with self.assertRaises(ValidationError) as context:
            add_note(self.repo, "Some title", "")
        self.assertEqual(str(context.exception), "Content is required")

    def test_add_content_too_short_content(self) -> None:
        with self.assertRaises(ValidationError) as context:
            add_note(self.repo, "Some title", "abcd")
        self.assertEqual(
            str(context.exception),
            f"Content must be between {MIN_CONTENT_LEN} and {MAX_CONTENT_LEN} characters",
        )

    def test_get_all_notes_returns_list_of_dicts(self) -> None:
        # given
        created_at_1 = "2025-10-23T17:50:37+00:00"
        created_at_2 = "2025-10-23T18:50:37+00:00"

        notes = [
            Note(id=2, title="Title 1", content="Content 1", created_at=created_at_2),
            Note(id=1, title="Title 2", content="Content 2", created_at=created_at_1),
        ]

        self.repo.get_notes.return_value = notes

        # when
        result = get_all_notes(self.repo)

        # then
        expected = [
            {
                "id": 2,
                "title": "Title 1",
                "content": "Content 1",
                "created_at": created_at_2,
            },
            {
                "id": 1,
                "title": "Title 2",
                "content": "Content 2",
                "created_at": created_at_1,
            },
        ]

        self.assertEqual(result, expected)
        self.repo.get_notes.assert_called_once()

    def test_get_all_notes_returns_empty_list(self) -> None:
        # given
        notes: list[Note] = []

        self.repo.get_notes.return_value = notes

        # when
        result = get_all_notes(self.repo)

        # then
        self.assertEqual(result, [])
        self.repo.get_notes.assert_called_once()


if __name__ == "__main__":
    unittest.main()
