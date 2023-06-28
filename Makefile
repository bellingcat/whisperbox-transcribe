clean:
	docker compose  -f docker-compose.base.yml -f docker-compose.dev.yml down --volumes --remove-orphans

dev:
	docker compose -f docker-compose.base.yml -f docker-compose.dev.yml build
	docker compose -f docker-compose.base.yml -f docker-compose.dev.yml up --remove-orphans

fmt:
	black app
	ruff check app --fix

lint:
	black --check app
	ruff check app
	mypy app

test:
	pytest

run:
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml build
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml up --remove-orphans

stop:
	docker compose -f docker-compose.base.yml -f docker-compose.prod.yml down
