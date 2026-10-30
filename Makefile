.PHONY: run test lint clean

run:
	python3 src/main.py

test:
	python3 -m pytest tests/ -v

lint:
	python3 -m flake8 src/ tests/ --max-line-length=80

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
