# syntax=docker/dockerfile:1.6
#
# Multi-stage build for the Kenya Community in Korea (KCK) Django platform.
#   - Stage 1 (builder): installs build tooling + Python deps into a venv
#   - Stage 2 (runtime): copies the venv into a slim runtime image
#
# Total image size: ~180-220 MB.
# Build:  docker build -t kck:latest .
# Run:    docker compose up
#

# ------------------------------------------------------------------- #
# Stage 1 — builder
# ------------------------------------------------------------------- #
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Build deps for Pillow + reportlab + (future) psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libtiff5-dev \
        libwebp-dev libopenjp2-7-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps into an isolated venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /tmp/requirements.txt


# ------------------------------------------------------------------- #
# Stage 2 — runtime
# ------------------------------------------------------------------- #
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=kck_project.settings \
    PORT=8000

# Runtime deps only — no compilers
RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo libfreetype6 liblcms2-2 libtiff6 libwebp7 libopenjp2-7 \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for safer runtime
RUN groupadd --system kck && useradd --system --gid kck --home /app --shell /sbin/nologin kck

# Copy the venv from the builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy project code (ownership chown-ed in one pass)
COPY --chown=kck:kck . /app

# Make the writable dirs exist with the right ownership
RUN mkdir -p /app/media /app/staticfiles /app/data && chown -R kck:kck /app/media /app/staticfiles /app/data

# Make the entrypoint executable
RUN chmod +x /app/docker/entrypoint.sh

USER kck

EXPOSE 8000

# Basic healthcheck — asks gunicorn to serve /accounts/login/ (always 200)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/accounts/login/" || exit 1

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "kck_project.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
