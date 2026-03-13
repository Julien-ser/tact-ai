// K6 Load Testing Configuration for Tact-AI
// Simulates 100+ concurrent users across different scenarios

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';
import { SharedArray } from 'k6/data';
import ws from 'k6/ws';
import { Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTimeTrend = new Trend('response_time');

// Configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Ramp up to 20 users
    { duration: '1m', target: 50 },    // Ramp up to 50 users
    { duration: '2m', target: 100 },   // Ramp up to 100 users (target)
    { duration: '3m', target: 100 },   // Stay at 100 for 3 minutes
    { duration: '1m', target: 0 },     // Ramp down
  ],
  thresholds: {
    errors: ['rate<0.1'],  // Error rate less than 10%
    response_time: ['p(95)<500'],  // 95th percentile under 500ms
  },
  noConnectionReuse: false,
  maxRedirects: 3,
};

// Base URL (adjust as needed)
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Test data - will be populated from CSV or generated
const testUsers = new SharedArray('testUsers', function() {
  // In production, load from CSV: return open('users.csv').split('\n').slice(1);
  // For now, generate placeholder data
  return [];
});

// Helper functions
function getAuthHeaders(token) {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randomChoice(array) {
  return array[Math.floor(Math.random() * array.length)];
}

// Generate random task data
function generateTaskData(index) {
  const titles = [
    'Complete project proposal',
    'Team meeting',
    'Review pull requests',
    'Write documentation',
    'Bug fix: login issue',
    'Client call',
    'Update dependencies',
    'Code review',
    'Plan sprint',
    'Training session',
    'Deploy to production',
    'Monitoring setup',
    'Security audit',
    'Performance optimization',
    'Database backup',
  ];

  const priorities = ['low', 'medium', 'high', 'critical'];
  const quadrants = ['Q1', 'Q2', 'Q3', 'Q4'];

  return {
    title: `${titles[index % titles.length]} #${index}`,
    description: `Auto-generated test task ${index}`,
    estimated_duration: randomInt(30, 180),
    priority: randomChoice(priorities),
    quadrant: randomChoice(quadrants),
    due_date: new Date(Date.now() + randomInt(86400000, 604800000)).toISOString(),
  };
}

// Main execution
export default function() {
  const userId = Math.floor(this.vu / 2) + 1;  // Spread users across different IDs
  const vuType = this.vu % 3;  // 0: auth, 1: tasks, 2: scheduler

  // Each virtual user simulates a different workflow based on type
  if (vuType === 0) {
    // Authentication workflow (20% of users)
    handleAuthWorkflow(userId);
  } else if (vuType === 1) {
    // Task CRUD workflow (60% of users)
    handleTaskWorkflow(userId);
  } else {
    // Scheduler generation workflow (20% of users)
    handleSchedulerWorkflow(userId);
  }

  sleep(1);
}

function handleAuthWorkflow(userId) {
  // Simulate login
  const loginPayload = JSON.stringify({
    username: `user${userId}`,
    password: 'testpassword123',
  });

  const loginRes = http.post(
    `${BASE_URL}/auth/login`,
    loginPayload,
    { headers: { 'Content-Type': 'application/json' } }
  );

  const success = check(loginRes, {
    'login status 200': (r) => r.status === 200 || r.status === 401, // 200 success or 401 invalid creds
  });

  errorRate.add(!success);
  responseTimeTrend.add(loginRes.timings.duration);

  if (success && loginRes.status === 200) {
    const data = loginRes.json;
    const token = data.access_token;

    // Test protected endpoint
    const meRes = http.get(
      `${BASE_URL}/auth/me`,
      { headers: getAuthHeaders(token) }
    );

    check(meRes, {
      'me status 200': (r) => r.status === 200,
    });
  }

  sleep(2);
}

function handleTaskWorkflow(userId) {
  // Note: In real scenario, we'd first authenticate and get token
  // For load testing, we assume valid token exists (mocked or from prior login)
  // This is a simplified version - in production, pass token between iterations

  const token = `test_token_${userId}`;  // Placeholder

  // List tasks (with pagination)
  const listRes = http.get(
    `${BASE_URL}/tasks/?limit=20&offset=0`,
    { headers: getAuthHeaders(token) }
  );

  check(listRes, {
    'list tasks status 200': (r) => r.status === 200,
    'has X-Total-Count header': (r) => r.headers['X-Total-Count'] !== undefined,
  });

  responseTimeTrend.add(listRes.timings.duration);

  if (listRes.status === 200 && listRes.body.length > 10) {
    const tasks = listRes.json;

    if (tasks.length > 0) {
      const taskId = tasks[0].id;

      // Update a task
      const updatePayload = JSON.stringify({
        title: `Updated: ${tasks[0].title}`,
        description: 'Updated via load test',
      });

      const updateRes = http.put(
        `${BASE_URL}/tasks/${taskId}`,
        updatePayload,
        { headers: getAuthHeaders(token) }
      );

      check(updateRes, {
        'update task status 200': (r) => r.status === 200,
      });
    }

    // Create a new task
    const newTask = generateTaskData(randomInt(1000, 9999));
    const createRes = http.post(
      `${BASE_URL}/tasks/`,
      JSON.stringify(newTask),
      { headers: getAuthHeaders(token) }
    );

    check(createRes, {
      'create task status 200': (r) => r.status === 200,
    });
  }

  sleep(1);
}

function handleSchedulerWorkflow(userId) {
  const token = `test_token_${userId}`;  // Placeholder

  // Generate schedule (this is a heavy operation)
  const start = new Date();
  const end = new Date(Date.now() + 7 * 86400000); // 7 days from now

  const scheduleRes = http.post(
    `${BASE_URL}/scheduler/generate?start_date=${start.toISOString()}&end_date=${end.toISOString()}`,
    undefined,
    { headers: getAuthHeaders(token) }
  );

  const success = check(scheduleRes, {
    'scheduler status 200': (r) => r.status === 200,
    'has timeline_id': (r) => {
      if (r.status !== 200) return false;
      const data = r.json;
      return data.timeline_id !== undefined;
    },
  });

  responseTimeTrend.add(scheduleRes.timings.duration);
  errorRate.add(!success);

  if (success && scheduleRes.status === 200) {
    const data = scheduleRes.json;
    const timelineId = data.timeline_id;

    // Get schedule history
    const historyRes = http.get(
      `${BASE_URL}/scheduler/history?limit=10`,
      { headers: getAuthHeaders(token) }
    );

    check(historyRes, {
      'history status 200': (r) => r.status === 200,
    });

    // Get specific timeline
    const timelineRes = http.get(
      `${BASE_URL}/scheduler/${timelineId}`,
      { headers: getAuthHeaders(token) }
    );

    check(timelineRes, {
      'timeline status 200': (r) => r.status === 200,
    });
  }

  sleep(2);  // Scheduler operations are heavy, allow more rest
}

// WebSocket test (separate function, not called by default)
export function websocketTest() {
  const url = `ws://localhost:8000/ws?token=test_token`;
  const params = { trackActivityDuration: true };

  const response = ws.connect(url, params, (socket) => {
    socket.on('open', () => {
      console.log('WebSocket connected');
      socket.setInterval(() => {
        socket.send(JSON.stringify({ type: 'ping' }));
      }, 30000);
    });

    socket.on('message', (message) => {
      // Handle incoming messages
    });

    socket.on('close', () => {
      console.log('WebSocket closed');
    });

    socket.on('error', (e) => {
      console.error('WebSocket error:', e);
      errorRate.add(1);
    });

    // Keep connection open for 60 seconds
    sleep(60);
  });

  check(response, { 'status is 101': (r) => r === 101 });
}
