FROM python:3.10 AS compile-image

COPY pyproject.toml .
RUN pip install --user .[test,web]

FROM python:3.10 AS build-image

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY --from=compile-image /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

ENTRYPOINT ["bash", "./app/web/start.sh"]
