FROM python:3.12-slim

ARG APP_VERSION=0.2.0-dev
ARG VCS_REF=unknown
LABEL org.opencontainers.image.source="https://github.com/Malaber/what-should-we-eat"
LABEL org.opencontainers.image.version=$APP_VERSION
LABEL org.opencontainers.image.revision=$VCS_REF
ENV APP_VERSION=$APP_VERSION
WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY alembic.ini .
COPY alembic/ alembic/
COPY execution/ execution/
COPY frontend/ frontend/

EXPOSE 8000

CMD ["uvicorn", "execution.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
