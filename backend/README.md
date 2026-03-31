# Backend

## Installation

### Required
- [uv](https://docs.astral.sh/uv/) - Python package manager

### Optional
- [Docker](https://www.docker.com/) - For containerized deployment

### Container Configuration

Run `cp example.env .env` or copy example.env to .env

> [!NOTE] If you want to use a mongo db running else where set .env with
> `MONGODB_URL=mongodb://admin:password@mongodb:27017`

## Available Scripts

Run the following options using `pnpm run <option>`

options:
- `prepare` - Install and sync dependencies using uv
- `uv` - Run uv package manager commands additional arguments can be added
- `dev` - Run development environment with both Python app and database concurrently
- `dev:uv` - Run Python development server
- `dev:db` - Start the database container (idempotent check included)
- `main` - Run the main Python application
- `db` - Start the database container same as dev:db
- `db:status` - View docker status
- `db:up` - Start the database container (Docker Compose)
- `db:down` - Stop the database container
- `test` - Run pytest test suite
