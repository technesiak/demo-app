import logging
from unittest import TestCase

from flask import Flask
from sqlalchemy import NullPool, URL

from infrastructure.mysql.mysql_repository import (
    MySQLRepository,
)
from main import validate_env_variable
from models import db


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

    def test_health_check_success(self) -> None:
        with self.app.app_context():
            self.assertTrue(self.repo.health_check())
