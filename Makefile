
all: install

deps:
	pip install -r requirements.txt --user

install:
	pip install . --user --upgrade

uninstall:
	pip uninstall pixel-reader

doc: docs

docs:
	cd ./docs && make latexpdf && evince build/latex/pixel_reader.pdf &

test:
	nosetests --rednose tests

.PHONY: init install uninstall test doc docs