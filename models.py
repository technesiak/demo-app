from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index

from sqlalchemy.sql import func

db = SQLAlchemy()


class Note(db.Model):  # type: ignore
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    comment = db.Column(db.Text(100), nullable=True)
