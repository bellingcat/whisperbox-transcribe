FROM python:3.10-slim AS python-build

WORKDIR /etc/whisperbox-transcribe

# Create and build virtual env from requirements.
COPY pyproject.toml .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install -U pip wheel && \
    /opt/venv/bin/pip install -U .[worker]

FROM python:3.10-slim as python-deploy

ARG WHISPER_MODEL

WORKDIR /etc/whisperbox-transcribe

COPY --from=python-build /opt/venv /opt/venv

COPY --from=mwader/static-ffmpeg:latest /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:latest /ffprobe /usr/local/bin/

ENV VIRTUAL_ENV /opt/venv
ENV PATH /opt/venv/bin:$PATH

COPY scripts/download_models.py .
RUN python download_models.py ${WHISPER_MODEL}

COPY app ./app

CMD celery --app=app.worker.main.celery worker --loglevel=info --concurrency=1 --pool=solo
