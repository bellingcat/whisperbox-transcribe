FROM python:3.11-slim as python-build

WORKDIR /etc/whisperbox-transcribe

COPY pyproject.toml .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install -U pip wheel && \
    /opt/venv/bin/pip install -U .[web]

FROM python:3.11-slim as python-deploy

WORKDIR /etc/whisperbox-transcribe

COPY --from=python-build /opt/venv /opt/venv

COPY app ./app
COPY alembic.ini .

ENV VIRTUAL_ENV /opt/venv
ENV PATH /opt/venv/bin:$PATH

CMD alembic upgrade head && uvicorn app.web.main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8000} --log-level info --workers 4 --proxy-headers
