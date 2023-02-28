FROM python:3.10 AS python-build

WORKDIR /etc/whisperbox

COPY pyproject.toml .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install -U pip wheel && \
    /opt/venv/bin/pip install -U .[worker]

FROM python:3.10 as python-deploy

ARG WHISPER_MODELS

WORKDIR /etc/whisperbox

COPY --from=python-build /opt/venv /opt/venv

COPY --from=mwader/static-ffmpeg:latest /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:latest /ffprobe /usr/local/bin/

COPY app ./app

ENV VIRTUAL_ENV /opt/venv
ENV PATH /opt/venv/bin:$PATH

COPY scripts/download_models.py .
RUN python download_models.py ${WHISPER_MODELS}

CMD celery --app=app.worker.main.celery worker --loglevel=info --concurrency=1
