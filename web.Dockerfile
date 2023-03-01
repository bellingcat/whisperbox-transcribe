FROM python:3.10 as python-build

WORKDIR /etc/whisperbox

COPY pyproject.toml .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install -U pip wheel && \
    /opt/venv/bin/pip install -U .[web]

FROM python:3.10 as python-deploy

WORKDIR /etc/whisperbox

COPY --from=python-build /opt/venv /opt/venv

COPY app ./app
COPY alembic.ini ./

ENV VIRTUAL_ENV /opt/venv
ENV PATH /opt/venv/bin:$PATH

CMD alembic upgrade head && gunicorn -k uvicorn.workers.UvicornWorker app.web.main:app --bind ${HOST:-0.0.0.0}:${PORT:-8000} --log-level info
