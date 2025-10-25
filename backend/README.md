README.md
# Backend

## Overview

The backend is the server-side component of the application. It is responsible for handling the business logic and data storage.

## Technologies

- FastAPI
- SQLAlchemy
- PostgreSQL

## Architecture

The backend is built with FastAPI and SQLAlchemy. It is responsible for handling the business logic and data storage.

## Installation

```bash
uv venv
uv sync -r requirements.txt
```

## Running the backend

```bash
uv run main.py
```

## Testing

To run the tests, use the following command:   
```bash
uv run pytest
uv run pytest --cov=app tests/
```

## Documentation

To generate the documentation, use the following command:
```bash
uv run sphinx-build -b html docs/ build/html
```

## Linting

To lint the code, use the following command:
```bash
uv run ruff check .
```

## Formatting

To format the code, use the following command:
```bash
uv run ruff format .
```

## Security

To scan the code for security vulnerabilities, use the following command:   
```bash
uv run bandit -r .
```

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.