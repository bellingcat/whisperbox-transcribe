FROM python:3.11

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
COPY pyproject.toml .
RUN pip install -U pip
RUN pip install .[test]

# The source code is mounted as a volume at /code, no need to copy.

ENTRYPOINT ["bash", "./app/start.sh"]
