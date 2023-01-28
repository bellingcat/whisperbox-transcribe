FROM python:3.10 AS compile-image

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

COPY pyproject.toml .
RUN pip install --no-cache-dir --user .[worker,worker_dev]

COPY scripts/download_model.py .
RUN chmod +x download_model.py && python download_model.py small small.en

ENV PYTHONIOENCODING=utf-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH=/root/.local/bin:$PATH

ENTRYPOINT ["watchmedo", "auto-restart", "-d" , "app/worker", "-p", "*.py", "--recursive", "celery", "--", "--app=app.worker.main.celery", "worker", "--loglevel=info", "--concurrency=1"]
