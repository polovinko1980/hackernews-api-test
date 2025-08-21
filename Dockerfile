###############################################################################
# Stage 1 – builder (installs Poetry + dependencies)
###############################################################################
FROM python:3.11-alpine AS builder

# Install build dependencies only (minimal set for Poetry and Python packages)
RUN apk add --no-cache \
        build-base \
        curl \
        libffi-dev

# ── Install Poetry ───────────────────────────────────────────────────────────
ENV POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 -

# ── Project files & deps  ────────────────────────────────────────────────────
WORKDIR /hackernews-api-test

# Copy only the dependency metadata first (keeps cache efficient)
COPY pyproject.toml poetry.lock* ./

# Install only main dependencies (no dev dependencies for smaller image)
RUN poetry install --no-root --only main

###############################################################################
# Stage 2 – final runtime image (tiny)
###############################################################################
FROM python:3.11-alpine

WORKDIR /hackernews-api-test
ENV PYTHONPATH="/hackernews-api-test"

# Copy installed site-packages and scripts from builder layer
COPY --from=builder /usr/local/lib/python3.11/site-packages \
                    /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY . .

# Default command opens a shell for interactive testing
CMD [ "/bin/sh" ]

# ═══════════════════════════════════════════════════════════════════════════
# Build and Run Instructions:
# ═══════════════════════════════════════════════════════════════════════════
#
# 1. Build the Docker image:
#    docker build -t hackernews-api-test .
#
# 2. Run the container interactively:
#    docker run -it --rm hackernews-api-test
#
# 3. Inside the container, run tests:
#    pytest tests/
#    pytest tests/top_stories/
#    pytest tests/comments/
#
# 4. Run tests directly (one-liner):
#    docker run --rm hackernews-api-test pytest tests/
#
# 5. Run with specific environment:
#    docker run --rm -e ENV=STAGE hackernews-api-test pytest tests/
#
# 6. Run linting:
#    docker run --rm hackernews-api-test poetry run black --check .
#    docker run --rm hackernews-api-test poetry run ruff check .
#
# 7. Mount local code for development:
#    docker run -it --rm -v $(pwd):/hackernews-api-test hackernews-api-test
#