
# Trip Itinerary Planner
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![codecov](https://codecov.io/gh/SWEN-732-Group-5/trip-itinerary-planner/graph/badge.svg?token=R7EDDD69AC)](https://codecov.io/gh/SWEN-732-Group-5/trip-itinerary-planner) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=SWEN-732-Group-5_trip-itinerary-planner&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=SWEN-732-Group-5_trip-itinerary-planner)

A project for planning and organizing trip itineraries.

## Subpackages

This project contains the following subpackages:

- **[backend/](./backend/README.md)** - python backend
- **[frontend/](./frontend/README.md)** - vite frontend

Navigate to each subpackage directory for more details.

## Available Scripts

Run the following options using `pnpm run <option>`

options:
- `prod` - Run fully containerized application on ghcr(open `localhost:4173`)
- `preview` - Run fully containerized application on local(open `localhost:4173`)
- `dev` - Run development environment for all subpackages
- `dev:backend` - Run backend development environment
- `dev:frontend` - Run frontend development environment
- `test` - Run test suite for all subpackages

## Dependencies

Required installation:
1. [node.js](https://nodejs.org/en/download)
2. [docker](https://docs.docker.com/engine/install/)
3. [uv](https://docs.astral.sh/uv/getting-started/installation/)(optional if running in container)

### pnpm
This project uses [pnpm](https://pnpm.io/) as the package manager.

**Installation:**
run
```bash
npm install -g pnpm
```

After installing pnpm globally, you can install project dependencies by running:

```bash
pnpm install
```

See [backend](./backend/README.md#Installation) for more required dependencies and setups.

## Technologies Used
Python, FastAPI, PyTest, MongoDB, MinIO, React, Vite, Zod, react-hook-form, TailwindCSS, Shadcn UI

## Contributing
If you want to propose code changes, please open a PR. Due to this being a college project, I would not guarantee a response.

## Support
This project comes with no support. If you would like to bring an issue to our attention please open an issue on GitHub. Due to this being a college project, we may not get back to you.
