# Stufe 1: Basis-Image mit gesetzten Python-Umgebungsvariablen
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Stufe 2: Builder - Installiert Abhängigkeiten isoliert
FROM base AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stufe 3: Runtime - Schlankes Produktions-Image ohne Compiler
FROM base AS runtime
# Nicht als root laufen (Least Privilege)
RUN useradd --create-home --uid 10001 appuser

# Nur die fertigen Pakete aus dem Builder übernehmen
COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser wsgi.py ./

USER appuser
EXPOSE 8000

ARG APP_VERSION=0.0.0-dev
ENV APP_VERSION=${APP_VERSION}
ENV GUNICORN_WORKERS=1

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status == 200 else 1)"

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} wsgi:app"]
