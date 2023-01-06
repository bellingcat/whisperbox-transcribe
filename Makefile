dev:
	docker-compose -f dev.docker-compose.yml up --build --remove-orphans

fmt:
	black app
	isort app

test:
	ENVIRONMENT=test pytest

lint:
	mypy app
	flake8 app
