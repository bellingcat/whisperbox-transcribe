FROM python:3.10 AS compile-image

WORKDIR /code

COPY pyproject.toml .
RUN pip install --no-cache-dir --user .[web]

ENV PYTHONIOENCODING=utf-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH=/root/.local/bin:$PATH

CMD alembic upgrade head && uvicorn app.web.main:app --reload --host ${HOST:-0.0.0.0} --port ${PORT:-80} --log-level info
