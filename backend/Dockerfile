# DevGuard AI backend image.
# Runs Alembic migrations then serves the FastAPI app with uvicorn on port 8009.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

# Copy the application (see .dockerignore for what is excluded).
COPY . .

EXPOSE 8009

# Apply migrations, then start the server. db readiness is enforced by the
# compose `depends_on: condition: service_healthy`.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8009"]
