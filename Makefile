clean:
	docker-compose -f docker/dev.docker-compose.yml down --volumes --remove-orphans
dev:
	docker-compose -f docker/dev.docker-compose.yml build --progress tty
	docker-compose -f docker/dev.docker-compose.yml up --remove-orphans

fmt:
	black app
	isort app

lint:
	flake8 app
	mypy app

test:
	pytest
