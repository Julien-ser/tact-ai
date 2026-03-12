# tact-ai

**AI-Powered Eisenhower Matrix Scheduler**

An intelligent scheduling application that organizes tasks based on the Eisenhower Matrix principle, using AI to classify tasks and advanced optimization to generate optimal schedules considering dependencies, deadlines, and priorities.

## Features

- AI-powered task classification (GPT-4 + fallback keyword-based)
- Eisenhower Quadrant organization (Urgent/Important matrix)
- Task chains and dependency resolution
- Optimal schedule generation using OR-Tools CP-SAT
- Conflict detection (overlaps, resource allocation, missed deadlines)
- Real-time updates via WebSocket
- Drag-and-drop interface (React DnD)
- Gantt chart visualization (D3.js)
- JWT authentication with user isolation

## Tech Stack

**Frontend**: React 18+, Vite, Tailwind CSS, D3.js  
**Backend**: FastAPI (Python 3.11+), async/await  
**Database**: PostgreSQL 15+  
**Cache**: Redis  
**AI**: OpenAI GPT-4 API  
**Scheduling**: Google OR-Tools CP-SAT  
**Infrastructure**: Docker, Docker Compose, Nginx  
**Monitoring**: Prometheus, Grafana, Sentry  

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- OpenAI API key

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate
cd tact-ai

# Copy environment file
cp .env.example .env
# Edit .env and add your OpenAI API key

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv venv          # Optional but recommended
pip install -r requirements.txt
# Create .env file with required variables
uvicorn main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

### Option 3: Production Deployment

See [docs/deployment.md](./docs/deployment.md) for optimized Docker multi-stage builds, Nginx configuration, and production hardening.

## Project Structure

```
tact-ai/
├── backend/                 # FastAPI application
│   ├── ai/                 # AI classifier module
│   ├── scheduler/          # Scheduling engine
│   ├── auth/              # Authentication
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   └── tests/             # Backend tests
├── frontend/               # React application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API clients
│   │   └── hooks/         # Custom hooks
│   └── public/
├── shared/                 # Shared types/utilities
├── docker/                 # Docker configurations
├── docker-compose.yml      # Development compose
├── docker-compose.prod.yml # Production compose
├── docs/                   # Documentation
│   ├── architecture.md    # This document
│   ├── database.md        # Database schema
│   ├── deployment.md      # Deployment guide
│   └── operations.md      # Operations runbooks
├── tests/                  # Integration tests
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Python project config
└── .env.example           # Environment template
```

## Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` - Your OpenAI API key
- `SECRET_KEY` - JWT signing secret (generate with: `openssl rand -hex 32`)
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiry (default: 30)

Optional:
- `WORK_HOURS_START` - Daily start time (default: 09:00)
- `WORK_HOURS_END` - Daily end time (default: 17:00)
- `MAX_TASKS_PER_SCHEDULE` - Limit for scheduling (default: 100)
- `ENABLE_FALLBACK_CLASSIFIER` - Use keyword fallback (default: false)

## API Endpoints

### Authentication
- `POST /auth/register` - Create user account
- `POST /auth/login` - Obtain JWT tokens
- `POST /auth/refresh` - Refresh access token

### Tasks
- `GET /tasks/` - List user's tasks (with filters)
- `POST /tasks/` - Create task (AI classification)
- `GET /tasks/{id}` - Get task details
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task

### Scheduling
- `POST /scheduler/generate` - Generate optimized schedule
- `GET /scheduler/history` - View past schedules

### Real-Time
- `WS /ws` - WebSocket for live updates

Swagger UI: http://localhost:8000/docs (when running)

## Database Schema

See [docs/database.md](./docs/database.md) for the complete ER diagram and schema details.

### Core Tables
- `users` - User accounts
- `tasks` - Task definitions with AI-classified quadrant
- `task_chains` - Dependency relationships between tasks
- `timelines` - Generated schedules
- `time_blocks` - User working hours

## Development Workflow

1. **Create feature branch**
2. **Make changes** - Backend or frontend
3. **Run tests**:
   ```bash
   pytest backend/tests/              # Backend tests
   npm test                          # Frontend tests
   pytest tests/                     # Integration tests
   ```
4. **Lint & type check**:
   ```bash
   black backend/                    # Code formatting
   ruff backend/                     # Linting
   mypy backend/                     # Type checking
   npm run lint                      # Frontend linting
   ```
5. **Pre-commit hooks** - Automatically format and lint on commit (configured in `.pre-commit-config.yaml`)
6. **Commit** with conventional commit message
7. **Push** and create PR

See [TASKS.md](./TASKS.md) for the current development roadmap.

## CI/CD

The project uses GitHub Actions for continuous integration and delivery:

- **Linting**: Black (formatting) and Ruff (linting) on all Python code
- **Type checking**: mypy strict mode on backend and shared modules
- **Testing**: pytest with PostgreSQL and Redis services, coverage reporting to Codecov
- **Docker builds**: Automated multi-arch builds for backend and frontend images, pushed to Docker Hub on merges to main

Pre-commit hooks run locally to ensure code quality before commits. All checks must pass before PRs can be merged.

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for the full pipeline configuration.

## Architecture

See [docs/architecture.md](./docs/architecture.md) for detailed system architecture, component diagrams, and design decisions.

## Testing

- **Unit Tests**: Backend (pytest), Frontend (Jest)
- **Integration Tests**: API endpoints, database operations
- **Coverage Target**: >80%

Run tests:
```bash
pytest --cov=backend --cov-report=html
npm test -- --coverage
```

## Monitoring & Operations

Production monitoring includes:
- **Metrics**: Prometheus metrics exposed at `/metrics`
- **Errors**: Sentry error tracking
- **Logs**: JSON structured logs
- **Dashboard**: Grafana dashboards

See [docs/operations.md](./docs/operations.md) for runbooks and alert procedures.

## Contributing

This project follows the autonomous agent workflow. Tasks are tracked in `TASKS.md`. Each task should:
- Include unit tests
- Update documentation
- Follow code style guidelines (black, ruff)
- Pass all checks before merging

## License

Proprietary - All rights reserved

## Support

For issues, feature requests, or questions, please open an issue on GitHub or contact the development team.

---

**Status**: In active development - Phase 3: User Interface & Task Management (React Component Library Complete)
