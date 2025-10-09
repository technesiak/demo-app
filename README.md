# Notes service

### Run project locally

build:
```commandline
docker compose build
```

start:
```commandline
docker compose up
```

stop:
```commandline
docker compose down
```

run-background:
```commandline
docker compose up --detach
```

Run black formatter:

```commandline
docker compose exec -T application sh -c "python -m black ."
```

Run mypy for static type checking:

```commandline
docker compose exec -T application sh -c "mypy --config-file mypy.ini ."
```

To init SQLAlchemy (one time job):
```commandline
docker compose run --rm -e FLASK_APP=main application flask db init
```

Database migrations should be generated whenever SQLAlchemy models are altered:
```commandline
docker compose exec -e FLASK_APP=main application flask db migrate
```

Apply any new migrations to the database if they exist since the last application launch:
```commandline
docker compose exec -e FLASK_APP=main application flask db upgrade
```