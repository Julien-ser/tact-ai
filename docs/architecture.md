# tact-ai Architecture

## Overview

tact-ai is an AI-based scheduling application built on the Eisenhower Matrix principle. The system intelligently classifies, organizes, and schedules tasks based on urgency and importance, while handling task dependencies and optimizing schedules.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
  - Modern, high-performance async framework
  - Automatic OpenAPI/Swagger documentation
  - Built-in validation with Pydantic
- **Language**: Python 3.11+
- **API Style**: RESTful with WebSocket support for real-time updates

### Frontend
- **Framework**: React 18+
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **Visualization**: D3.js for Gantt charts
- **Drag & Drop**: React DnD
- **State Management**: React Context + Hooks

### Data & Storage
- **Primary Database**: PostgreSQL 15+
  - ACID compliance for task integrity
  - Advanced querying capabilities
- **Cache/Message Queue**: Redis
  - Session storage
  - AI classification caching
  - Pub/Sub for real-time updates

### AI & Scheduling
- **AI Classifier**: OpenAI GPT-4 API
  - Eisenhower quadrant classification
  - Natural language task parsing
  - Fallback: Keyword-based classifier
- **Optimization Engine**: Google OR-Tools CP-SAT
  - Constraint programming for optimal scheduling
  - Handles dependencies, deadlines, working hours

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Deployment**: Multi-stage builds
  - Backend: Gunicorn + Uvicorn workers
  - Frontend: Nginx static file serving
- **CI/CD**: GitHub Actions
  - Linting: Black, Ruff
  - Type checking: Mypy
  - Testing: Pytest with coverage
- **Monitoring**: Prometheus + Grafana
- **Error Tracking**: Sentry
- **Load Testing**: k6

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Users                                    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS/REST + WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Load Balancer / Nginx                        │
│                     (Reverse Proxy + Static Files)                  │
└──────────────┬──────────────────────────────┬──────────────────────┘
               │                              │
               ▼                              ▼
    ┌──────────────────┐          ┌─────────────────────┐
    │   Frontend (SPA) │          │   Backend API      │
    │  React + Vite    │          │   FastAPI          │
    │  Port: 3000      │          │   Port: 8000       │
    └──────────────────┘          └─────────┬───────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                              │                              │
              ▼                              ▼                              ▼
    ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
    │    PostgreSQL   │◄────────►│      Redis      │◄────────►│   OpenAI API    │
    │   Port: 5432    │          │   Port: 6379    │          │   (External)    │
    │   User Data     │          │   Cache/Session │          │   GPT-4 Model   │
    │   Tasks         │          │   Pub/Sub       │          │   Classification│
    │   Timelines     │          │   Rate Limiting │          │                 │
    └─────────────────┘          └─────────────────┘          └─────────────────┘
                                             │
                                             ▼
                                  ┌─────────────────────┐
                                  │    OR-Tools CP-SAT  │
                                  │  (Embedded Library) │
                                  │  Schedule Engine    │
                                  └─────────────────────┘
```

## Component Details

### 1. Frontend (React Application)
- **Entry Point**: `frontend/`
- **Key Components**:
  - `QuadrantBoard` - Drag-and-drop Eisenhower matrix (4 quadrants)
  - `TimelineView` - D3.js Gantt chart visualization
  - `TaskCard` - Individual task display/edit
  - `ChainVisualizer` - Task dependency graph
  - Natural language input with AI classification
- **State**: React Context for user data, tasks, UI state
- **API Client**: Axios for REST, Socket.IO for WebSocket

### 2. Backend API (FastAPI)
- **Entry Point**: `backend/main.py`
- **Key Modules**:
  - `backend/ai/classifier.py` - Eisenhower quadrant classification
  - `backend/scheduler/dependency.py` - Task chain resolution
  - `backend/scheduler/engine.py` - OR-Tools CP-SAT scheduler
  - `backend/scheduler/conflicts.py` - Conflict detection
  - `backend/auth/` - JWT authentication
- **Database Models**: Pydantic schemas + SQLAlchemy ORM
- **Middleware**: CORS, Authentication, Error handling

### 3. Database Schema (PostgreSQL)
- **Tables**:
  - `users` - User accounts (id, email, hashed_password, created_at)
  - `tasks` - Individual tasks (id, user_id, title, description, quadrant, priority, estimated_duration, due_date, created_at, updated_at)
  - `task_chains` - Task dependencies (id, task_id, prerequisite_task_id, relationship_type)
  - `timelines` - Schedule outputs (id, user_id, name, start_date, end_date, generated_at)
  - `time_blocks` - User availability/working hours (id, user_id, day_of_week, start_time, end_time)
- **Indexes**: user_id on all user-scoped tables, due_date on tasks

### 4. AI Classification Engine
- **Primary**: OpenAI GPT-4 with structured prompts
  - Input: Task title + description (natural language)
  - Output: Quadrant (Q1: Urgent/Important, Q2: Not Urgent/Important, Q3: Urgent/Not Important, Q4: Not Urgent/Not Important), estimated duration, suggested deadline
  - Caching: Redis (24h TTL) to reduce API costs
- **Fallback**: Keyword-based classifier for offline/backup mode
  - Rule-based matrix with common keywords

### 5. Scheduling Engine (OR-Tools)
- **Algorithm**: CP-SAT (Constraint Programming)
- **Constraints**:
  - Task duration fixed
  - Dependencies enforced (prerequisites must complete first)
  - Working hours respected (configurable time blocks)
  - Deadlines met (when possible)
  - No overlaps in schedule
- **Optimization**: Maximize priority-weighted tasks completed
- **Output**: JSON with scheduled tasks, start/end timestamps

### 6. Real-Time Features (WebSocket)
- **Events**:
  - Schedule generation complete
  - Conflict detected
  - Task updated
- **Implementation**: FastAPI WebSocket + Redis Pub/Sub
- **Frontend**: Socket.IO client

## Data Flow Examples

### Task Creation with AI Classification
```
User Input → FastAPI POST /tasks/ → AI Classifier (with cache) → PostgreSQL
                                    ↓
                          Quadrant assignment + duration estimate
```

### Schedule Generation
```
User Request → Scheduler Engine → Load tasks + dependencies → CP-SAT solver
                                    ↓
                         Optimized schedule → Store → WebSocket notify
```

### Conflict Detection
```
Schedule update → Conflict detector → Overlap/resource check → Alert user
```

## Deployment Architecture

### Development (Local)
```yaml
docker-compose.yml:
  - postgres:15
  - redis:7-alpine
  - backend: FastAPI (reload mode)
  - frontend: Vite dev server
```

### Production
```yaml
docker-compose.prod.yml:
  - Nginx (reverse proxy + static files)
  - Gunicorn + Uvicorn (multiple workers)
  - PostgreSQL (persistent volume)
  - Redis (persistent volume)
  - Optional: Traefik for SSL termination
```

## Environment Variables

See `.env.example` for complete list. Key variables:
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `OPENAI_API_KEY` - OpenAI API key
- `SECRET_KEY` - JWT signing
- `WORK_HOURS_START/END` - Daily schedule constraints

## Performance Considerations

- **Caching**: AI classification results cached 24h in Redis
- **Database**: Indexes on user_id, due_date, created_at
- **Scheduling**: CP-SAT solves ~100 tasks in <5s (tested)
- **API**: Async operations for I/O-bound tasks
- **Frontend**: Lazy loading for large task lists

## Security

- JWT authentication (access + refresh tokens)
- Password hashing with bcrypt
- Rate limiting per user/IP
- CORS configured for frontend origin
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection headers

## Monitoring & Observability

- **Metrics**: API latency, scheduling duration, cache hit rate (Prometheus)
- **Logging**: Structured JSON logs with correlation IDs
- **Tracing**: Request correlation across microservices
- **Alerts**: Error rate >1%, scheduling >30s, Redis down
- **Dashboard**: Grafana with key metrics visualization

## Future Enhancements

- Multi-timezone support
- Recurring task patterns
- Calendar integration (Google Calendar, Outlook)
- Collaborative task sharing
- Mobile app (React Native)
- Advanced machine learning for duration prediction
