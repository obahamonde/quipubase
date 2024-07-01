# Makefile for QuipuBase project

# Variables
PYTHON := python
PIP := pip
UVICORN := uvicorn
PROJECT_DIR := quipubase
REQUIREMENTS := requirements.txt
APP_MODULE := main:app
HOST := 0.0.0.0
DEV_PORT := 5454
SERVE_PORT := 5454
PYTHONDONTWRITEBYTECODE := 1
PYTHONUNBUFFERED := 1

.PHONY: build
build:
	@echo "Setting environment variables..."
	@export PYTHONDONTWRITEBYTECODE=1
	@export PYTHONUNBUFFERED=1
	@echo "Installing dependencies..."
	@$(PIP) install -r $(REQUIREMENTS)
	@echo "Building QuipuBase..."
	@cd $(PROJECT_DIR) && $(PYTHON) setup.py build_ext --inplace

.PHONY: dev
dev:
	@$(UVICORN) $(APP_MODULE) --reload --host $(HOST) --port $(DEV_PORT) --log-level debug

.PHONY: serve
serve:
	@$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(SERVE_PORT) --log-level info

.PHONY: test
test:
	@echo "Running tests..."
	@$(PYTHON) -m pytest tests

.PHONY: clean
clean:
	@echo "Cleaning up..."
	@rm -rf $(PROJECT_DIR)/build
	@rm -rf $(PROJECT_DIR)/*.so
	@rm -rf $(PROJECT_DIR)/*.cpp
	@rm -rf $(PROJECT_DIR)/*.c	
	@rm -rf $(PROJECT_DIR)/*.html
	@rm -rf $(PROJECT_DIR)/*.js
	@rm -rf $(PROJECT_DIR)/*.css
	@rm -rf $(PROJECT_DIR)/*.png
	@rm -rf $(PROJECT_DIR)/*.jpg
	@rm -rf $(PROJECT_DIR)/*.jpeg
	@rm -rf $(PROJECT_DIR)/*.gif
	@rm -rf $(PROJECT_DIR)/*.svg

.PHONY: push
push:
	@echo "Pushing to GitHub..."
	@git add .
	@git commit -m "Update"
	@git push
	@echo "Pushed to GitHub"
	@echo "Pushing to Docker Hub..."
	@docker build -t quipubase .
	@docker tag quipubase:latest quipu/quipubase:latest
	@docker push obahamonde/quipubase:latest
	@echo "Pushed to Docker Hub"

.PHONY: deploy
deploy:
	@echo "Deploying to Kubernetes..."
	@kubectl apply -f kubernetes/deployment.yaml
	

.PHONY: help
help:
	@echo "QuipuBase Makefile"
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build: Build the project"
	@echo "  dev: Run the project in development mode"
	@echo "  serve: Serve the project"
	@echo "  test: Run the tests"
	@echo "  clean: Clean up the project"
	@echo "  help: Show this help message"

.DEFAULT_GOAL := help