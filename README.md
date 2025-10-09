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