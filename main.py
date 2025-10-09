import os

from flask import Flask
from flask.cli import with_appcontext
from flask_migrate import Migrate, upgrade  # type: ignore

from models import db
from sqlalchemy import NullPool, URL


def validate_env_variable(env: str) -> str:
    if env not in os.environ:
        raise ValueError("{} not found in environment variables.".format(env))
    return os.environ[env]


try:
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

except ValueError as e:
    print(f"Error: {e}")
    exit(1)

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = db_dsn
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"poolclass": NullPool}
db.init_app(app)
migrate = Migrate(app, db)


@app.route("/")
def hello() -> str:
    return "Hello World!"


@app.cli.command("migrate")
@with_appcontext
def run_migrations() -> None:
    upgrade()
