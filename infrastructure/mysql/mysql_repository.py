import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text


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
