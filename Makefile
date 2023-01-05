
dev:
	uvicorn app.main:app --reload

fmt:
	black app
	isort app

test:
	ENVIRONMENT=test pytest

lint:
	mypy app
	flake8 app
