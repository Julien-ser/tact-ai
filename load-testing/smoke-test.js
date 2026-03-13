/**
 * Smoke Test - Light load test to verify basic functionality
 * Run: k6 run --vus 10 --duration 30s smoke-test.js
 */

import { CONFIG } from "./config.js";
import { getAuthToken, createTestTask, getOrCreateTestTasks } from "./utils.js";

export const options = {
  thresholds: {
    http_req_duration: ["p(95)<2000"], // 95% of requests < 2s
    http_req_failed: ["rate<0.01"], // Error rate < 1%
  },
};

const API_URL = CONFIG.API_URL;

export default async function () {
  // Use a different test user for each VU
  const userIndex = (__VU - 1) % CONFIG.TEST_USERS.length;
  const testUser = CONFIG.TEST_USERS[userIndex];

  // Authenticate
  const token = await getAuthToken(testUser);
  if (!token) {
    return;
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  // Test 1: Get task list
  await getTasks(headers);

  // Test 2: Create a new task
  const task = createTestTask();
  await createTask(headers, task);

  // Test 3: Get task list again
  await getTasks(headers);

  // Test 4: Generate a schedule
  await generateSchedule(headers);

  // Test 5: Get schedule history
  await getScheduleHistory(headers);
}

async function getTasks(headers) {
  const url = `${API_URL}/tasks/?limit=20`;
  const res = await http.get(url, { headers });
  check(res, { "Get tasks - status 200": (r) => r.status === 200 });
  return res;
}

async function createTask(headers, taskData) {
  const url = `${API_URL}/tasks/`;
  const res = await http.post(url, JSON.stringify(taskData), { headers });
  check(res, { "Create task - status 201": (r) => r.status === 201 });
  return res;
}

async function generateSchedule(headers) {
  const url = `${API_URL}/scheduler/generate`;
  const res = await http.post(url, {}, { headers });
  check(res, { "Generate schedule - status 200": (r) => r.status === 200 });
  return res;
}

async function getScheduleHistory(headers) {
  const url = `${API_URL}/scheduler/history?limit=10`;
  const res = await http.get(url, { headers });
  check(res, { "Get schedule history - status 200": (r) => r.status === 200 });
  return res;
}
