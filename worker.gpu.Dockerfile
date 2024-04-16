# TODO: clean up
FROM nvidia/cuda:11.8.0-base-ubuntu22.04 AS python-deploy

ENV PYTHON_VERSION=3.11

ARG WHISPER_MODEL

WORKDIR /etc/whisperbox-transcribe

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get -qq update \
    && apt-get -qq install --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s -f /usr/bin/python${PYTHON_VERSION} /usr/bin/python3 && \
    ln -s -f /usr/bin/python${PYTHON_VERSION} /usr/bin/python && \
    ln -s -f /usr/bin/pip3 /usr/bin/pip

COPY pyproject.toml .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install -U pip wheel && \
    /opt/venv/bin/pip install -U .[worker]

COPY --from=mwader/static-ffmpeg:latest /ffmpeg /usr/local/bin/
COPY --from=mwader/static-ffmpeg:latest /ffprobe /usr/local/bin/

COPY app ./app

ENV VIRTUAL_ENV /opt/venv
ENV PATH /opt/venv/bin:$PATH

COPY scripts/download_models.py .
RUN python download_models.py ${WHISPER_MODEL}

CMD celery --app=app.worker.main.celery worker --loglevel=info --concurrency=1 --pool=prefork
