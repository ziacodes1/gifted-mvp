# Gifted API — production-style image (gunicorn, non-root, DJANGO_ENV=production).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_ENV=production \
    PRIVATE_MEDIA_ROOT=/data/private_media

WORKDIR /app
COPY requirements.txt requirements-optional.txt ./
RUN pip install -r requirements.txt
# Optional integrations (Sentry, S3 private storage): build with --build-arg WITH_OPTIONAL=1
ARG WITH_OPTIONAL=0
RUN if [ "$WITH_OPTIONAL" = "1" ]; then pip install -r requirements-optional.txt; fi

COPY . .
RUN useradd --create-home --uid 10001 gifted \
    && mkdir -p /app/staticfiles /data/private_media \
    && chown -R gifted /app /data \
    && chmod +x /app/docker-entrypoint.sh
USER gifted

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live/').status==200 else 1)"
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT:-60} --access-logfile - --error-logfile -"]
