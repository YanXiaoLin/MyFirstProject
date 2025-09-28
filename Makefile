PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install dev run run-prod test clean

install:
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

dev:
	iwheregis-api

run:
	$(PYTHON) api_server.py

run-prod:
	gunicorn -w 2 -k gthread -b 0.0.0.0:5000 wsgi:app

test:
	$(PYTHON) test_api.py | cat

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache