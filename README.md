# whisperbox-transcribe 

> HTTP wrapper around [openai/whisper](https://github.com/openai/whisper).

## Overview

This project wraps OpenAI's `whisper` speech-to-text models with a HTTP API.

The API design takes inspiration from the [rev.ai async speech-to-text API](https://docs.rev.ai/api/asynchronous/get-started/). Transcription jobs are submitted via a HTTP `POST` request. After the job is accepted, an id is returned, which can later be used to retrieve the transcription results from the service. Results are stored in an internal database until retrieved, and can optionally be deleted afterwards.

It is assumed that the service is used by exactly one consumer, so a pre-shared API key is used as authentication method. OpenAPI documentation for the service is available at `<service_url>/docs`.

## Deploy

### 0. Choose model & instance size

Whisper provides [several sizes](https://github.com/openai/whisper#available-models-and-languages) of their model where size is a trade-off between model accuracy, resource usage and transcription speed. Smaller models are generally faster and lighter, but more inaccurate, especially for non-english languages and translation tasks.

Whisper inference can be run on both CPU and GPU, and this project supports both via slightly altered docker compose configurations. CPU inference is slower, but easier and cheaper to host. CPU inference, while overall slower than the GPU, generally scales well with CPU speed.

Another consideration when choosing your instance is disk size. In order to transcribe media, it first needs to be downloaded to a temporary file, so the HDD needs to have enough free space to allow for that. For some hosting environments (e.g. Digital Ocean), it can make sense to mount an additional disk in the VM instead of choosing a larger instance.

As a baseline, the `small` model can run on a `4GB` Digital Ocean droplet, achieving roughly a 1-2x speedup over original audio when transcribing.

### 1. Prepare host environment

This project is intended to be run via [docker compose](https://docs.docker.com/compose/). To get started:
 1. [Install](https://docs.docker.com/engine/install/) docker engine.
 2. Clone this repository to the machine.

 > **Note**  
 > If you want to use the GPU, uncomment the sections tagged with _<GPU SUPPORT>_ in docker-compose.prod.yml

### 2. Configure service

2. Create an `.env` file from `.env.example` and configure it:
 - `API_SECRET`: the API key used to authenticate against the API.
 - `WHISPER_MODEL`: the whisper model size you want to use.
 - `TRAEFIK_DOMAIN`: the domain you want to access the service from. Its A records need to point to the host IP.
 - `TRAEFIK_SSLEMAIL`: an email which is used to verify domain ownership before a TLS certificate is issued.

### 3. Run service

Run `make run` to start the server.4. To launch at system startup, wrap it in a systemd launch service.

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
http://localhost:5555                        => Celery dashboard
http://whisperbox-transcribe.localhost       => API
http://whisperbox-transcribe.localhost/docs  => API docs
./whisperbox-transcribe.sqlite               => Database
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
