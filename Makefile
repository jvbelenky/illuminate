 .PHONY: test clean
#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PYTHON_INTERPRETER = python3

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install package
## Lint using flake8 and black
lint:
	black guv_app.py app/*
	flake8 --ignore=E114,E116,E117,E231,E266,E303,E501,W293,W291,W503 guv_app.py app/*

build:
	pip install -r requirements.txt

## Remove compiled python files
clean:
	@echo "Cleaning directory..."
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type f -name "*~" -delete
	@find . -type f -name "*.kate-swp" -delete
	@echo "Done"

run: 
	$(PYTHON_INTERPRETER) -m streamlit run guv_app.py --server.headless true 
	
all: build lint run