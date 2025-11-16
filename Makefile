.PHONY: help install dev build start stop clean migrate db-studio

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	npm install

dev: ## Run development servers
	npm run dev

build: ## Build all applications
	npm run build

start: ## Start production with Docker Compose
	docker-compose up -d

stop: ## Stop Docker Compose services
	docker-compose down

clean: ## Clean all build artifacts and node_modules
	rm -rf node_modules apps/*/node_modules packages/*/node_modules
	rm -rf apps/*/.next apps/*/dist packages/*/dist
	rm -rf .turbo

migrate: ## Run database migrations
	cd packages/database && npx prisma migrate dev

db-studio: ## Open Prisma Studio
	cd packages/database && npx prisma studio

logs: ## Show Docker logs
	docker-compose logs -f

restart: stop start ## Restart all services
