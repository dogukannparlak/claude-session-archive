.PHONY: run test lint demo clean

PY ?= python3
export PYTHONPATH := src

run:  ## start the viewer (opens the browser)
	$(PY) -m session_archive

test:  ## run the unit tests (stdlib unittest, no dependencies)
	$(PY) -m unittest discover -s tests -t . -v

lint:  ## syntax-check every Python file
	$(PY) -m compileall -q src tests

demo:  ## serve synthetic demo data on port 8770 (for screenshots)
	$(PY) scripts/make_demo_data.py /tmp/session-archive-demo/projects
	$(PY) -m session_archive --projects-dir /tmp/session-archive-demo/projects --port 8770

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf build dist *.egg-info src/*.egg-info
