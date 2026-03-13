# tact-ai Load Testing

This directory contains load testing scripts using k6 to simulate real-world usage patterns.

## Prerequisites

1. Install k6: https://k6.io/docs/getting-started/installation/
2. Ensure the backend is running and accessible
3. Set environment variables or edit config.js with your test settings

## Test Scenarios

### 1. Smoke Test (light load)
```bash
k6 run --vus 10 --duration 30s smoke-test.js
```

### 2. Load Test (moderate load)
```bash
k6 run --vus 100 --duration 5m load-test.js
```

### 3. Stress Test (high load)
```bash
k6 run --vus 500 --duration 10m stress-test.js
```

### 4. Soak Test (long duration)
```bash
k6 run --vus 50 --duration 30m soak-test.js
```

## Metrics Collected

- Response times (p50, p95, p99)
- Request rate
- Error rates
- HTTP status codes
- Custom metrics for scheduler performance

## Test Data

The scripts use pre-defined test users. Create these users in your test environment:

- `testuser1@example.com` / `testpass123`
- `testuser2@example.com` / `testpass123`
- `testuser3@example.com` / `testpass123`

## Interpreting Results

After running tests, check:
1. **Error rate**: Should be < 1%
2. **p95 response time**: Should be < 2 seconds for most endpoints
3. **Throughput**: Should scale linearly with VUs

Results can be exported as JSON:
```bash
k6 run --out json=results.json load-test.js
```

Use the HTML reporter for visual analysis:
```bash
k6 report --html report.html results.json
```
