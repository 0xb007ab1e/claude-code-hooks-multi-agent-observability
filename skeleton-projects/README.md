# Skeleton Projects

This directory contains skeleton projects for five different web frameworks, each with complete setup including Dockerfiles, Make/NPM scripts, CI stubs, and pre-wired environment loading.

## Projects

### 1. [Express.js](./express/) - Node.js
- **Framework**: Express.js
- **Port**: 3000
- **Features**: JWT middleware, CORS, helmet, morgan logging
- **Testing**: Jest with supertest
- **Commands**: `npm run dev`, `npm test`, `make docker-run`

### 2. [FastAPI](./fastapi/) - Python
- **Framework**: FastAPI with Pydantic
- **Port**: 8000
- **Features**: Automatic OpenAPI docs, type validation, async support
- **Testing**: pytest with httpx
- **Commands**: `make dev`, `make test`, `make docker-run`

### 3. [Gin](./gin/) - Go
- **Framework**: Gin
- **Port**: 8080
- **Features**: JSON binding, middleware, CORS
- **Testing**: Go testing with testify
- **Commands**: `make dev`, `make test`, `make docker-run`

### 4. [Axum](./axum/) - Rust
- **Framework**: Axum with Tokio
- **Port**: 3000
- **Features**: Async handlers, JSON serialization, tracing
- **Testing**: Axum test framework
- **Commands**: `make dev`, `make test`, `make docker-run`

### 5. [ASP.NET Core](./aspnet-core/) - C#
- **Framework**: ASP.NET Core
- **Port**: 80 (Docker), 5000 (dev)
- **Features**: Entity Framework, Swagger, dependency injection
- **Testing**: xUnit with WebApplicationFactory
- **Commands**: `make dev`, `make test`, `make docker-run`

## Common Features

All projects include:

✅ **Basic REST API** endpoints (`/`, `/health`, `/api/users`)  
✅ **Environment variable** loading (`.env.example` files)  
✅ **Docker** support with multi-stage builds  
✅ **Makefile** with common commands  
✅ **CI/CD** GitHub Actions workflows  
✅ **Testing** with framework-specific test runners  
✅ **CORS** enabled  
✅ **Logging/Monitoring** middleware  
✅ **Health check** endpoint  

## Quick Start

Each project can be run with:

```bash
cd {project-name}
make install  # Install dependencies
make dev      # Start development server
make test     # Run tests
make docker-build && make docker-run  # Run with Docker
```

## API Endpoints

All projects expose the same basic API:

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /api/users` - List users (empty by default)
- `POST /api/users` - Create user (body: `{"name": "...", "email": "..."}`)

## Environment Variables

Each project includes a `.env.example` file with common variables:
- `PORT` - Server port
- `DATABASE_URL` - Database connection string
- `JWT_SECRET` - JWT signing secret
- `API_KEY` - Generic API key

## CI/CD

All projects include GitHub Actions workflows that:
- Run tests on multiple runtime versions
- Build Docker images
- Test Docker containers
- Upload test coverage (where applicable)

## Development

Each project is set up for immediate development with:
- Hot reloading/watching
- Linting and formatting
- Test coverage reports
- Docker development environment
