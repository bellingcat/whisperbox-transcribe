FROM python:3.10 AS compile-image

RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends ffmpeg

COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache \
    pip install --user .[worker,worker_dev]

FROM python:3.10 AS build-image

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY --from=compile-image /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

ENTRYPOINT ["watchmedo", "auto-restart", "-d" , "app/worker", "-p", "*.py", "celery", "--", "--app=app.worker.main.celery", "worker", "--loglevel=info"]
