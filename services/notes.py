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


class MaxLimitExceededError(Exception):
    def __init__(self, message: str = "Max limit exceeded") -> None:
        self.message = message
        super().__init__(self.message)


MIN_CONTENT_LEN = 5
MAX_CONTENT_LEN = 2000
MIN_TITLE_LEN = 3
MAX_TITLE_LEN = 255
MIN_COMMENT_LEN = 3
MAX_COMMENT_LEN = 100
MAX_LIMIT = 10
DEFAULT_LIMIT = 5


def get_note(
    repository: MySQLRepository,
    note_id: int,
) -> dict:
    note = repository.get_by_id(note_id)
    if not note:
        raise NotFoundError()
    return _to_dict(note)


def add_note(
    repository: MySQLRepository, title: str, content: str, comment: str | None = None
) -> int:
    _validate(title, content, comment)
    new_note = Note(title=title, content=content, comment=comment)
    return repository.add(new_note)


def _validate(title: str, content: str, comment: str | None = None) -> None:
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

    if comment:
        if len(comment) < MIN_COMMENT_LEN or len(comment) > MAX_COMMENT_LEN:
            raise ValidationError(
                f"Comment must be between {MIN_COMMENT_LEN} and {MAX_COMMENT_LEN} characters"
            )


def get_all_notes(
    repository: MySQLRepository, limit: int | None, last_id: int | None = None
) -> dict:
    if limit and limit > MAX_LIMIT:
        raise MaxLimitExceededError()
    if not limit:
        limit = DEFAULT_LIMIT
    notes, has_more = repository.get_notes(limit, last_id)
    return {
        "notes": [_to_dict(note) for note in notes],
        "has_more": has_more,
    }


def _to_dict(note: Note) -> dict:
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at,
        "comment": note.comment,
    }
