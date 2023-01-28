FROM python:3.10 AS compile-image

WORKDIR /code

COPY pyproject.toml .
RUN pip install --no-cache-dir --user .[web]

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH=/root/.local/bin:$PATH

ENTRYPOINT ["bash", "./app/web/start.sh"]
