from infrastructure.mysql.mysql_repository import MySQLRepository
from models import Note


class ValidationError(Exception):
    def __init__(self, message: str = "Validation Error") -> None:
        self.message = message
        super().__init__(self.message)


class NotFoundError(Exception):
    def __init__(self, message: str = "Data not found") -> None:
        self.message = message
        super().__init__(self.message)


MIN_CONTENT_LEN = 5
MAX_CONTENT_LEN = 2000
MIN_TITLE_LEN = 3
MAX_TITLE_LEN = 255


def get_note(
    repository: MySQLRepository,
    note_id: int,
) -> Note:
    note = repository.get_by_id(note_id)
    if not note:
        raise NotFoundError()
    return note


def add_note(repository: MySQLRepository, title: str, content: str) -> int:
    _validate(title, content)
    new_note = Note(title=title, content=content)
    return repository.add(new_note)


def _validate(title: str, content: str) -> None:
    if not title:
        raise ValidationError("Title is required")
    if not content:
        raise ValidationError("Content is required")

    if len(title) < MIN_TITLE_LEN or len(title) > MAX_TITLE_LEN:
        raise ValidationError(
            f"Title must be between {MIN_TITLE_LEN} and {MAX_TITLE_LEN} characters"
        )

    if len(content) < MIN_CONTENT_LEN or len(content) > MAX_CONTENT_LEN:
        raise ValidationError(
            f"Content must be between {MIN_CONTENT_LEN} and {MAX_CONTENT_LEN} characters"
        )
