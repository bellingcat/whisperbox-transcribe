FROM python:3.10

ARG WHISPER_MODELS

WORKDIR /code

ENV PYTHONIOENCODING=utf-8
ENV PATH=/root/.local/bin:$PATH

COPY --from=mwader/static-ffmpeg:5.1.2 /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:5.1.2 /ffprobe /usr/local/bin/

COPY pyproject.toml .
RUN pip install --no-cache-dir --user .[worker,worker_dev]

COPY scripts/download_models.py .
RUN python download_models.py ${WHISPER_MODELS}

CMD watchmedo auto-restart -d app/worker -p *.py --recursive celery -- --app=app.worker.main.celery worker --loglevel=info --concurrency=1
