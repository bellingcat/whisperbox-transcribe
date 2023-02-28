clean:
	docker compose -f docker/dev/docker-compose.yml down --volumes --remove-orphans

dev:
	docker compose -f docker/dev/docker-compose.yml build
	docker compose -f docker/dev/docker-compose.yml up --remove-orphans

fmt:
	black app
	isort app

lint:
	flake8 app
	mypy app

test:
	pytest

run:
	docker compose -f docker/prod/docker-compose.yml build
	docker compose -f docker/prod/docker-compose.yml up --remove-orphans
