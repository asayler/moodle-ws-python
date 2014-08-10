# Andy Sayler
# Summer 2014
# Univerity of Colorado

ECHO = @echo

PYTHON = python
PIP = pip

REQUIRMENTS = requirments.txt

UNITTEST_PATTERN = '*_test.py'

MOODLE = ./moodle

.PHONY: all reqs test clean

all:
	$(ECHO) "This is a python project; nothing to build!"

reqs: $(REQUIRMENTS)
	$(PIP) install -r $(REQUIRMENTS)

test:
	$(PYTHON) -m unittest discover -v -p $(UNITTEST_PATTERN)

clean:
	$(RM) *.pyc
	$(RM) *~
