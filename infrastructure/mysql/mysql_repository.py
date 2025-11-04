import logging
from datetime import timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

from models.models import Note


class MySQLRepository:
    def __init__(self, db: SQLAlchemy, logger: logging.Logger):
        self.db = db
        self.logger = logger

    def health_check(self) -> bool:
        try:
            self.db.session.execute(text("SELECT 1"))
            return True
        except Exception as error:
            self.logger.error(error, exc_info=True)
            return False

    def get_by_id(self, note_id: int) -> Note | None:
        result = (
            self.db.session.query(Note)
            .filter(
                Note.id == note_id,
            )
            .first()
        )
        if result and result.created_at:
            if result.created_at.tzinfo is None:
                result.created_at = result.created_at.replace(tzinfo=timezone.utc)
            else:
                result.created_at = result.created_at.astimezone(timezone.utc)

        return result

    def add(self, note: Note) -> int:
        if note.created_at is not None and note.created_at.tzinfo is not None:
            note.created_at = note.created_at.astimezone(timezone.utc).replace(
                tzinfo=None
            )
        self.db.session.add(note)
        self.db.session.commit()
        if note.id is None:
            raise RuntimeError("Database did not return an ID")
        return int(note.id)

    def get_notes(
        self, limit: int = 5, last_id: int | None = None
    ) -> tuple[list["Note"], bool]:
        query = self.db.session.query(Note).order_by(Note.id.desc())

        if last_id is not None:
            query = query.filter(Note.id < last_id)

        results: list[Note] = query.limit(limit + 1).all()
        has_more = len(results) > limit
        notes = results[:limit]

        for note in notes:
            if note.created_at:
                if note.created_at.tzinfo is None:
                    note.created_at = note.created_at.replace(tzinfo=timezone.utc)
                else:
                    note.created_at = note.created_at.astimezone(timezone.utc)

        return notes, has_more
