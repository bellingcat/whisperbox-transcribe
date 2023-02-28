FROM python:3.10

WORKDIR /code

ENV PYTHONIOENCODING=utf-8
ENV PATH=/root/.local/bin:$PATH

COPY pyproject.toml .
RUN pip install --no-cache-dir --user .[web]

CMD alembic upgrade head && uvicorn app.web.main:app --reload --host ${HOST:-0.0.0.0} --port ${PORT:-80} --log-level info
