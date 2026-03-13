/**
 * Load Test - Moderate load (100 concurrent users)
 * Run: k6 run --vus 100 --duration 5m load-test.js
 */

import { CONFIG } from "./config.js";
import {
  getAuthToken,
  performTaskWorkflow,
  generateSchedule,
  getScheduleHistory,
} from "./utils.js";

export const options = {
  thresholds: {
    http_req_duration: [
      { threshold: "p(95)<2000", abortOnFail: true, delayAbortEval: "10s" },
    ],
    http_req_failed: [{ threshold: "rate<0.02", abortOnFail: true }], // 2% error rate
  },
  noDisconnect: true, // Keep connections alive
  maxRedirects: 3,
  timeout: "30s",
};

const API_URL = CONFIG.API_URL;

// Each VU simulates a real user session
export default async function () {
  const userIndex = (__VU - 1) % CONFIG.TEST_USERS.length;
  const testUser = CONFIG.TEST_USERS[userIndex];

  // Authenticate (cache token in this context)
  const tokenKey = `token_${userIndex}`;
  let token = __ENV.token;

  if (!token) {
    token = await getAuthToken(testUser);
    if (!token) {
      return;
    }
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  // Simulate realistic user workflow with some randomness
  const scenario = Math.random();

  if (scenario < 0.4) {
    // 40%: Task management workflow
    await performTaskWorkflow(headers);
  } else if (scenario < 0.7) {
    // 30%: Schedule generation
    await generateSchedule(headers);
    await getScheduleHistory(headers, 5);
  } else {
    // 30%: Browse and view
    await getScheduleHistory(headers, 20);
    const tasksRes = await getTasksPaged(headers, 1, 20);
    if (tasksRes.status === 200) {
      const tasks = JSON.parse(tasksRes.body);
      if (tasks.length > 0) {
        await getSingleTask(headers, tasks[0].id);
      }
    }
  }

  // Add small delay to simulate think time
  sleep(0.5 + Math.random() * 1.5);
}

async function getTasksPaged(headers, page, limit = 20) {
  const offset = (page - 1) * limit;
  const url = `${CONFIG.API_URL}/tasks/?limit=${limit}&offset=${offset}`;
  return await http.get(url, { headers });
}

async function getSingleTask(headers, taskId) {
  const url = `${CONFIG.API_URL}/tasks/${taskId}`;
  return await http.get(url, { headers });
}
