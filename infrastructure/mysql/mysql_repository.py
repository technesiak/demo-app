import logging
from datetime import timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

from models import Note

# todo: proper solution for created_at


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
        if result:
            result.created_at = result.created_at.astimezone(timezone.utc)

        return result

    def add(self, note: Note) -> int:
        self.db.session.add(note)
        self.db.session.commit()
        if note.id is None:
            raise RuntimeError("Database did not return an ID")
        return int(note.id)

    def get_notes(self) -> list[Note]:
        return self.db.session.query(Note).order_by(Note.id.desc()).all()
