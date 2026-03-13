# Load Testing for Tact-AI

This directory contains load testing scripts using [k6](https://k6.io/).

## Prerequisites

1. Install k6: https://k6.io/docs/getting-started/installation/
2. Ensure the Tact-AI backend is running (default: http://localhost:8000)
3. Set up test data (see Setup below)

## Quick Start

```bash
# Run the main load test (100 concurrent users)
k6 run load-test.js

# Run with custom target
BASE_URL=http://your-server.com k6 run load-test.js

# Run in distributed mode (cloud)
k6 cloud load-test.js
```

## Test Scenarios

The load test simulates three types of users:

1. **Auth Users (20%)**: Login and profile access
2. **Task Users (60%)**: CRUD operations on tasks (list, create, update)
3. **Scheduler Users (20%)**: Heavy schedule generation operations

### Staging Plan

- 0-30s: Ramp up to 20 users
- 30s-1.5m: Ramp up to 50 users
- 1.5m-3.5m: Ramp up to 100 users (target load)
- 3.5m-6.5m: Maintain 100 concurrent users
- 6.5m-7.5m: Ramp down to 0

**Total duration**: ~7.5 minutes

## Metrics Collected

- **Request rate**: Requests per second
- **Error rate**: Failed requests (rate < 10% threshold)
- **Response time**: p95 < 500ms threshold
- **HTTP metrics**: By route, status, method

## Interpreting Results

### Success Criteria

✅ **Error rate** < 10% (threshold: rate<0.1)
✅ **95th percentile response time** < 500ms
✅ **No memory leaks** (monitor k6 process)
✅ **Database connections** stable (check pg_stat_activity)

### Common Issues & Fixes

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| High auth errors | Missing test users | Run setup script first |
| Slow scheduler | Insufficient workers | Increase OR-Tools workers |
| DB connection pool exhaustion | Pool size too small | Increase pool_size to 20 |
| High latency | Missing indexes | Run Alembic migration |

## Setup

### 1. Create Test Users

```bash
# Run the setup script to create 200 test users with tasks
python setup-test-data.py
```

This will:
- Create 200 users via register endpoint
- Create 50 tasks per user (10,000 tasks total)
- Establish task dependencies for some users

### 2. Verify Backend Health

```bash
curl http://localhost:8000/health
# Should return {"status": "healthy"}
```

### 3. Ensure Database Migrations Applied

```bash
cd backend
alembic upgrade head
```

### 4. Start Services

```bash
docker-compose up -d postgres redis
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Advanced Configuration

### Custom Test Duration

```bash
k6 run --vus 100 --duration 10m load-test.js
```

### Threshold Customization

Edit the `options.thresholds` in load-test.js:

```javascript
thresholds: {
  errors: ['rate<0.05'],  // 5% error rate
  response_time: ['p(99)<1000'],  // 99th percentile < 1s
}
```

### Environment Variables

- `BASE_URL`: Backend URL (default: http://localhost:8000)
- `K6_WEB_DASHBOARD_PORT`: k6 web dashboard port

## Performance Baselines

Expected performance on decent hardware (4+ CPU, 8GB RAM):

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| GET /tasks/ | 50ms | 150ms | 300ms |
| POST /tasks/ | 100ms | 300ms | 600ms |
| POST /scheduler/generate | 2000ms | 8000ms | 15000ms |
| GET /scheduler/history | 30ms | 100ms | 200ms |

**Note**: Scheduler generation is intentionally CPU-intensive (OR-Tools CP-SAT) and can take several seconds for complex task sets.

## Monitoring During Test

### Backend Metrics

```bash
# PostgreSQL connections
docker exec tact-ai-postgres-1 psql -U tactai -c "SELECT count(*) FROM pg_stat_activity;"

# Slow queries (>100ms)
docker exec tact-ai-postgres-1 psql -U tactai -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Redis stats
docker exec tact-ai-redis-1 redis-cli info stats
```

### System Resources

```bash
# CPU/Memory
docker stats

# k6 process
top -p $(pgrep -f k6)
```

## CI/CD Integration

Add to GitHub Actions:

```yaml
- name: Load Test
  run: |
    docker-compose up -d postgres redis
    cd backend && alembic upgrade head
    cd .. && k6 run --out json=results.json load-tests/load-test.js
    python load-tests/analyze-results.py results.json
```

## Troubleshooting

### "Connection refused" errors
- Verify backend is running: `curl $BASE_URL/health`
- Check CORS settings for WebSocket tests

### High error rates
- Check database connectivity
- Verify Redis is running
- Ensure test users exist (run setup script)

### Out of memory
- Reduce VU count: `k6 run --vus 50 load-test.js`
- Increase system RAM or swap

## Results Analysis

After test completion, k6 outputs summary statistics. For detailed analysis:

```bash
# Convert to JSON and analyze with Python
k6 run --out json=results.json load-test.js
python load-tests/analyze-results.py results.json
```

See `analyze-results.py` for sample analysis script.

## Next Steps

After baseline testing:
1. Profile scheduler performance with varied task counts
2. Tune database connection pool size
3. Add caching layer optimizations
4. Implement query result caching for frequent queries
5. Consider read replicas for read-heavy workloads
