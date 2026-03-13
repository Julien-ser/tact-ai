# Load Testing Optimization Report

## Summary

This document outlines the load testing framework and performance optimizations implemented for Tact-AI. Due to infrastructure constraints, the actual load test execution requires a properly configured environment with Docker/docker-compose.

## Enhancements Completed

### 1. Fixed Authentication in k6 Load Tests

**File**: `load-tests/load-test.js`

- **Problem**: Previous load test used hardcoded placeholder tokens, not representing real authentication flow
- **Solution**: Modified load test to perform actual JWT login for each virtual user
- **Impact**: More realistic load simulation including authentication endpoint load
- **Details**: 
  - VUs now authenticate with credentials from `USER_CREDENTIALS` env var
  - Tokens are obtained from `/auth/login` and used for subsequent requests
  - Better represents true production traffic patterns

### 2. Created Results Analysis Script

**File**: `load-tests/analyze-results.py`

- **Purpose**: Comprehensive analysis of k6 JSON output
- **Features**:
  - Calculates percentiles (p50, p95, p99) for all metrics
  - Analyzes threshold compliance
  - Computes check pass rates
  - Generates human-readable report with recommendations
- **Usage**: `python load-tests/analyze-results.py results.json [-o report.txt]`

### 3. Added Database Indexes

**Migration**: `backend/alembic/versions/20260312_000004_add_tasks_created_index.py`

- **Index**: `ix_tasks_user_created` on `tasks(user_id, created_at DESC)`
- **Purpose**: Optimize task list pagination with `ORDER BY created_at DESC`
- **Impact**: Faster paginated task queries, especially with large task counts per user
- **Query Pattern**: `WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?`

**Note**: The following indexes were already present:
- `ix_tasks_user_completed` (user_id, completed)
- `ix_tasks_user_priority` (user_id, priority)
- `ix_tasks_user_quadrant` (user_id, quadrant)
- `ix_tasks_user_due_date` (user_id, due_date)
- `ix_task_chains_task_relationship` (task_id, relationship_type)
- `ix_timelines_user_generated` (user_id, generated_at DESC)
- `ix_time_blocks_user_day` (user_id, day_of_week)

### 4. Redis Caching (Already Implemented)

**File**: `backend/ai/classifier.py`

- Eisenhower quadrant classifier caches results in Redis with 24-hour TTL
- Cache key: SHA256 of task title + description
- Cache hits bypass expensive GPT-4 API calls
- Keyword-based fallback also cached if confidence > 0.5

### 5. Database Connection Pooling (Already Configured)

**File**: `backend/database/__init__.py`

- `pool_size=20` (increased from default 5)
- `max_overflow=30` for connection spikes
- `pool_recycle=3600` to prevent stale connections
- `pool_pre_ping=True` for connection health checks
- Supports 100+ concurrent users

## Load Testing Procedure

### Prerequisites

1. **Docker & Docker Compose** installed and running
2. **k6** installed (https://k6.io/docs/getting-started/installation/)
3. **Python 3.9+** with dependencies from `requirements.txt`

### Step-by-Step Execution

```bash
# 1. Start services
docker-compose up -d postgres redis

# 2. Apply database migrations
cd backend
alembic upgrade head

# 3. Create test data (200 users × 50 tasks = 10,000 tasks)
python ../load-tests/setup-test-data.py

# 4. Start the backend server
# In production, use: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Verify backend health
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# 6. Run load test
cd ../load-tests
k6 run --out json=results.json load-test.js

# 7. Analyze results
python analyze-results.py results.json -o performance-report.txt
```

### Test Scenarios

The load test simulates three user types:

| Type | Percentage | Workflow |
|------|------------|----------|
| Task CRUD | 33% | List, create, update tasks |
| Scheduler | 33% | Generate schedule, view history |
| Mixed | 33% | CRUD + Scheduler |

**Total Duration**: ~7.5 minutes
**Target**: 100 concurrent virtual users

### Performance Baselines

| Endpoint | Target p95 | Target p99 |
|----------|------------|------------|
| GET /tasks/ | <150ms | <300ms |
| POST /tasks/ | <300ms | <600ms |
| POST /scheduler/generate | <8000ms | <15000ms |
| GET /scheduler/history | <100ms | <200ms |

**Error Rate**: <10%
**Thresholds**: Configured in load-test.js (line 24-27)

## Expected Results

With the implemented optimizations, the system should handle 100+ concurrent users with:

- **Task operations**: <200ms p95 response time
- **Scheduler generation**: <8s p95 for users with up to 50 tasks
- **Error rate**: <5% under normal conditions
- **Redis cache hit rate**: >80% for task classification (if classifier is used frequently)

## Troubleshooting

### Connection Errors
- Verify PostgreSQL is running: `docker-compose logs postgres`
- Check DATABASE_URL in `.env` matches docker-compose configuration

### High Authentication Errors
- Ensure test users were created: `python setup-test-data.py`
- Check that passwords match (`testpassword123` by default)

### Slow Scheduler Performance
- Scheduler is CPU-intensive; performance depends on task count and dependencies
- Consider increasing OR-Tools workers in `scheduler.py` (line 150)
- For large task sets (>100 tasks), consider async background processing

### Database Connection Pool Exhaustion
- Current pool_size=20, max_overflow=30 supports 50+ active DB connections
- If connections are exhausted, increase pool_size in `database/__init__.py`
- Monitor with: `SELECT count(*) FROM pg_stat_activity;`

## Optimization Summary

| Optimization | Status | Impact |
|--------------|--------|--------|
| Task pagination index | ✅ Added | Faster list queries with ordering |
| Task chains composite index | ✅ Already present | Faster dependency lookups |
| Timeline queries index | ✅ Already present | Fast schedule history retrieval |
| Redis caching (classifier) | ✅ Implemented | 24h cache reduces GPT-4 calls |
| Connection pooling | ✅ Configured | Supports 50+ concurrent DB connections |
| Load test authentication | ✅ Fixed | Realistic load simulation |

## Next Steps (for execution)

When Docker environment is available:

1. Run the load test to establish baseline metrics
2. If thresholds are not met:
   - Increase database connection pool
   - Add additional Redis caching for frequently accessed data
   - Optimize scheduler solver parameters (time_limit, workers)
   - Consider query result caching for read-heavy endpoints
3. Re-run tests and compare results
4. Document actual performance metrics

## Files Modified/Created

- `load-tests/load-test.js` - Fixed authentication
- `load-tests/analyze-results.py` - New analysis script
- `backend/alembic/versions/20260312_000004_add_tasks_created_index.py` - New index migration
- `docs/load-testing-optimization.md` - This documentation

---

**Note**: This report assumes standard hardware (4+ CPUs, 8GB+ RAM). Adjust expectations for lower-spec environments.
