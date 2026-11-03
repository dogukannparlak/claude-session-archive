.PHONY: run test lint clean

PY ?= python3
export PYTHONPATH := src

run:  ## start the viewer (opens the browser)
	$(PY) -m session_archive

test:  ## run the unit tests (stdlib unittest, no dependencies)
	$(PY) -m unittest discover -s tests -t . -v

lint:  ## syntax-check every Python file
	$(PY) -m compileall -q src tests

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf build dist *.egg-info src/*.egg-info
