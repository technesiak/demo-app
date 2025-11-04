import logging
import os

from flask import Flask
from flask.cli import with_appcontext
from flask_migrate import Migrate, upgrade  # type: ignore
from sqlalchemy import URL

from models.models import db
from infrastructure.mysql.mysql_repository import MySQLRepository
from routes.health_check import register_health_check_routes
from routes.notes import register_notes_routes


def get_env_value(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


try:
    db_url = URL.create(
        drivername="mysql+pymysql",
        username=get_env_value("DB_USERNAME"),
        password=get_env_value("DB_PASSWORD"),
        host=get_env_value("DB_HOST"),
        port=int(get_env_value("DB_PORT")),
        database=get_env_value("DB_DATABASE"),
    )
except Exception as err:
    print(f"[Startup Error] {err}")
    exit(1)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url

db.init_app(app)
migrate = Migrate(app, db)


logger = logging.getLogger("demo_app_logger")
logger.setLevel(logging.INFO)


repository = MySQLRepository(db, logger)
register_health_check_routes(app, repository)
register_notes_routes(app, repository, logger)


@app.route("/")
def index() -> str:
    return "API works!"


@app.cli.command("migrate")
@with_appcontext
def perform_migration() -> None:
    upgrade()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
