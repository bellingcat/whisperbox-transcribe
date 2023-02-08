# whisper-api

> HTTP wrapper around [openai/whisper](https://github.com/openai/whisper).

## API documentation

OpenAPI documentation can be accessed via `<service_url>/docs`.

## Deploy

// TODO

## Develop

It is recommended to setup a virtual environment for python tooling. To install dependencies dependencies in your virtual env, run `pip install -e .[tooling,web,worker]`

[docker-compose](https://docs.docker.com/get-started/08_using_compose/) is required for local development. Configuration such as `API_SECRET` can be adjusted in `./docker/dev/docker-compose.yml`.

### Start

```
make dev
```

Builds and starts the docker containers.

```
# Bindings
http://localhost:8000 => API
http://localhost:8000/docs => API docs
http://localhost:5555 => Celery dashboard
./whisperbox.sqlite => Database
```

## Destroy

This removes all containers and attached volumes.

```
make clean
```

### Test

```
make test
```

### Lint

```
make lint
```

### Format

```
make fmt
```
