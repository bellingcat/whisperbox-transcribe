
dev:
	uvicorn app.main:app --reload

fmt:
	black app --check
	isort app

test:
	ENVIRONMENT=test pytest

lint:
	mypy app
	flake8 app

create_account:
	python -m scripts.create_account ${name}
