# whisperbox-transcribe 

> HTTP wrapper around [openai/whisper](https://github.com/openai/whisper).

## API documentation

OpenAPI documentation can be accessed via `<service_url>/docs`.

## Deploy

 1. Clone this repository to the host machine.
 2. Create an `.env` file from `.env.example`.
 3. Run `make run` to start the server.
 4. Wrap in a systemd service to launch at startup.

## Develop

[docker compose](https://docs.docker.com/get-started/08_using_compose/) is required for local development.

It is recommended to setup a virtual environment for python tooling. To install dependencies in your virtual env, run `pip install -e .[tooling,web,worker]`.

Copy `.env.test` to `.env` to configure the service.

### Start

```
make dev
```

Builds and starts the docker containers.

```
# Bindings
http://localhost:5555                   => Celery dashboard
http://whisperbox-transcribe.localhost  => API
http://whisperbox-transcribe.localhost  => API docs
./whisperbox-transcribe.sqlite          => Database
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
