FROM python:3.10 AS compile-image

ARG WHISPER_MODEL

WORKDIR /code

COPY --from=mwader/static-ffmpeg:5.1.2 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:5.1.2 /ffprobe /usr/local/bin/

COPY pyproject.toml .
RUN pip install --no-cache-dir --user .[worker,worker_dev]

COPY scripts/download_model.py .
RUN chmod +x download_model.py && python download_model.py ${WHISPER_MODEL}

ENV PYTHONIOENCODING=utf-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH=/root/.local/bin:$PATH

ENTRYPOINT ["watchmedo", "auto-restart", "-d" , "app/worker", "-p", "*.py", "--recursive", "celery", "--", "--app=app.worker.main.celery", "worker", "--loglevel=info", "--concurrency=1"]
