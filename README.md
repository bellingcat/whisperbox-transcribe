# whisperbox-transcribe 

> HTTP wrapper around [openai/whisper](https://github.com/openai/whisper).

## Overview

This project wraps OpenAI's `whisper` speech-to-text models with a HTTP API.

The API design of this service draws inspiration from the [rev.ai async speech-to-text API](https://docs.rev.ai/api/asynchronous/get-started/). Transcription jobs are submitted by making a HTTP POST request to the service. Once the job is accepted, an ID is returned, which can be later utilized to retrieve the transcription results. These results are stored in an internal database until they are retrieved and can optionally be deleted afterwards.

It is assumed that the service is used by exactly one consumer, so a pre-shared API key is used as authentication method. OpenAPI documentation for the service is available at `<service_url>/docs`.

## Deploy

<details>
<summary>0. Choose model & instance size</summary>
Whisper offers a range of models in [different sizes](https://github.com/openai/whisper#available-models-and-languages). The model size affects factors such as accuracy, resource usage, and transcription speed. Smaller models are generally faster and consume fewer resources, but they may be less accurate, especially when working with non-English languages or translation tasks.

Whisper supports inference on both CPU and GPU, and this project includes slightly modified Docker Compose configurations to enable both options. CPU inference is slower but usually more cost-effective for hosting purposes. CPU inference performance typically scales well with the CPU speed.

When selecting an instance for your application, it's important to consider the disk size. Media files need to be downloaded before they can be transcribed, so the disk must have sufficient free space to accommodate them.

As a starting point, the "small" model can run on a 4GB Digital Ocean droplet with, achieving approximately a 1-2x speed-up over to the original audio length when transcribing.
</details>

### 1. Prepare host environment

This project is intended to be run via [docker compose](https://docs.docker.com/compose/). In order to get started, [install](https://docs.docker.com/engine/install/) docker engine on your VPS. Then, clone this repository to the machine.

 > **Note**  
 > If you want to use a GPU, uncomment the sections tagged with _<GPU SUPPORT>_ in docker-compose.prod.yml

### 2. Configure service

2. Create an `.env` file from `.env.example` and configure it:
 - `API_SECRET`: the API key used to authenticate against the API.
 - `WHISPER_MODEL`: the whisper model size you want to use.
 - `TRAEFIK_DOMAIN`: the domain you want to access the service from. Its A records need to point to the host IP.
 - `TRAEFIK_SSLEMAIL`: an email which is used to verify domain ownership before a TLS certificate is issued.

### 3. Run service

Run `make run` to start the server. To launch at system startup, wrap it in a systemd launch service.

## Develop

[docker compose](https://docs.docker.com/get-started/08_using_compose/) is required for local development.

It is recommended to setup a virtual environment for python tooling. To install dependencies in your virtual env, run `pip install -e .[tooling,web,worker]`.

Copy `.env.dev` to `.env` to configure the service.

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

#### Clean

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
