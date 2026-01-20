FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=2.1.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# Install Poetry via pip (no curl/apt), and keep pip lean
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install "poetry==${POETRY_VERSION}"

# Copy only dependency files first for better layer caching
COPY pyproject.toml poetry.lock ./

# Install project dependencies system-wide (no virtualenv)
RUN poetry install --only main --no-ansi --no-root \
 && rm -rf /root/.cache/pip /root/.cache/pypoetry

# Now copy source
COPY . .

# Runtime env
ENV PYTHONPATH="/app/src:${PYTHONPATH}"
EXPOSE 80

# Gunicorn entrypoint (Flask app factory)
CMD ["gunicorn", "--config", "gunicorn.conf.py", "src.app:create_app()"]
# For FastAPI instead:
# CMD ["uvicorn", "src.fastapi_app:app", "--host", "0.0.0.0", "--port", "80", "--workers", "2"]
