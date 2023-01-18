dev:
	docker-compose -f docker/dev.docker-compose.yml build --progress tty
	docker-compose -f docker/dev.docker-compose.yml up --remove-orphans

fmt:
	black app
	isort app

lint:
	mypy app
	flake8 app

test:
	pytest
