# Notes REST API Demo

This repository contains a demo REST API built with Python (Flask), MySQL and containerized service design.
It provides a minimal example of CRUD operations for managing notes — including note creation, single note retrieval, and paginated listing.

> *Authentication and authorization are intentionally omitted for demo purposes.*

---

## Overview

The Notes Service exposes endpoints for:

* Creating a new note
* Retrieving a note by ID
* Listing notes with pagination
* Healthcheck endpoint for system readiness

All endpoints are documented with OpenAPI 3.0, viewable through an integrated Swagger UI container.

---

## Run Project Locally

### Build containers

```bash
docker compose build
```

### Start the project

```bash
docker compose up
```

### Stop the project

```bash
docker compose down
```

### Run in background

```bash
docker compose up --detach
```

---

## Development Commands

### Run Black formatter

```bash
docker compose exec -T application sh -c "python -m black ."
```

### Run Mypy static type checks

```bash
docker compose exec -T application sh -c "mypy --config-file mypy.ini ."
```

---

## Database Management

Initialize SQLAlchemy migrations (first-time setup):

```bash
docker compose run --rm -e FLASK_APP=main application flask db init
```

Generate a new migration after changing models:

```bash
docker compose exec -e FLASK_APP=main application flask db migrate
```

Apply migrations:

```bash
docker compose exec -e FLASK_APP=main application flask db upgrade
```

---

## Running Tests

To execute all test suites (unit, integration, e2e):

```bash
docker compose up --detach
docker compose exec -e FLASK_APP=main application flask db upgrade
docker compose exec -T application python -m unittest
```

Tests run against the containerized environment to ensure consistent results.

---

## API Documentation

* [OpenAPI:](documentation/openapi/openapi.yaml)
* [Postman Collection:](documentation/Demo%20App.postman_collection.json)
* [HTTP Examples:](documentation/api.http)

Swagger UI is automatically hosted within the Docker Compose stack and available at:
 
[http://localhost:8081](http://localhost:8081)

---

## Key Features

* Modular Flask + SQLAlchemy structure
* Containerized local environment (API + MySQL + Docs)
* Automated tests (unit, integration, e2e)
* Type checking (`mypy`) and formatting (`black`)
* OpenAPI spec & Swagger UI integration
* GitHub Actions CI with lint & test stages