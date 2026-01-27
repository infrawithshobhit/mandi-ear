# MANDI EAR™ Development Makefile

.PHONY: help install start stop logs test clean build

help: ## Show this help message
	@echo "MANDI EAR™ Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

start: ## Start all services
	docker-compose up -d
	@echo "Services starting... API available at http://localhost:8080"

stop: ## Stop all services
	docker-compose down

logs: ## View service logs
	docker-compose logs -f

test: ## Run tests
	python -m pytest tests/ -v

test-property: ## Run property-based tests only
	python -m pytest tests/ -v -m property

test-integration: ## Run integration tests
	python run_integration_tests.py -v

test-integration-full: ## Run full integration tests including performance
	python run_integration_tests.py -v --performance --slow

test-performance: ## Run performance tests only
	python -m pytest tests/test_performance_load.py -v

test-all: ## Run all tests (unit, property, integration)
	python -m pytest tests/ -v
	python run_integration_tests.py -v

validate-flows: ## Validate end-to-end data flows
	@echo "Validating data flows..."
	@curl -s -X POST http://localhost:8080/health/validate-flows | python -m json.tool || echo "Flow validation failed"

clean: ## Clean up containers and volumes
	docker-compose down -v
	docker system prune -f

build: ## Build all service images
	docker-compose build

dev-setup: ## Initial development setup
	cp .env.example .env
	docker-compose up -d postgres mongodb redis influxdb
	@echo "Waiting for databases..."
	sleep 10
	@echo "Development environment ready!"

health: ## Check service health
	@echo "Checking service health..."
	@curl -s http://localhost:8080/health | python -m json.tool || echo "API Gateway not responding"

health-detailed: ## Check detailed service health
	@echo "Checking detailed service health..."
	@curl -s http://localhost:8080/health/services | python -m json.tool || echo "Service health check failed"

api-docs: ## Open API documentation
	@echo "Opening API documentation at http://localhost:8000/docs"