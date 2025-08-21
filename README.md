# HackerNews API Test Framework

A testing framework for the HackerNews API built with Python 3.11, Poetry, and pytest.

## Installation

### Prerequisites

| Prerequisite  | Command                                   |
|---------------|-------------------------------------------|
| Python3.11+   | `pyenv install 3.11.x` (or system Python) |
| Poetry≥1.5    | `brew install poetry`                     |

Check Python version:
```bash
python3.11 --version
```

### Using Poetry 🏎️ (recommended for day‑to‑day development)

1. **Create virtual environment**
   ```bash
   # Use Python 3.11 for the project
   poetry env use $(pyenv which python3.11)
   ```

2. **Install dependencies**
   ```bash
   # Runtime + dev + test extras
   poetry install --with dev
   ```

### Using Docker

Build the Docker image:
```bash
docker build -t hackernews-api-test .
```

## Running Tests

### With Poetry

```bash
# Run all tests
poetry run pytest tests/

# Run specific test suites
poetry run pytest tests/top_stories/
poetry run pytest tests/comments/

# Run with verbose output
poetry run pytest tests/ -v

# Run single test file with detailed output
poetry run pytest tests/top_stories/test_current_top_story.py -svvv
```

### With Docker

```bash
# Run all tests
docker run --rm hackernews-api-test pytest tests/

# Run with specific environment
docker run --rm -e ENV=PROD hackernews-api-test pytest tests/

# Run with verbose output
docker run --rm hackernews-api-test pytest tests/ -v
```

## Code Quality

### Linting and Formatting

```bash
# Format code with Black
poetry run black .

# Run Ruff linter
poetry run ruff check .

# Fix linting issues automatically
poetry run ruff check . --fix
```

## CI/CD

The project includes GitHub Actions workflow with sequential execution:

1. **Lint** - Checks code quality with Black and Ruff
2. **Test** - Builds Docker image and runs tests (STAGE environment)
3. **Publish Report** - Generates JUnit test report

Workflow triggers:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual execution via `workflow_dispatch`

## Test Framework Features

- **Fixtures**: Pre-configured API client across all tests
- **Tunable API Client**: Environment-based configuration with automatic timeouts and retries
- **Schema Validation**: Pydantic models for type-safe response validation
- **Comprehensive Coverage**: API contract, functional, and negative testing
- **Multiple Environments**: Support for PROD/STAGE configurations via `ENV` variable