/**
 * Soak Test - Long-running test to detect memory leaks, degradation
 * Run: k6 run --vus 50 --duration 30m soak-test.js
 */

import { CONFIG } from "./config.js";
import {
  getAuthToken,
  getTasks,
  generateSchedule,
  getScheduleHistory,
} from "./utils.js";

export const options = {
  thresholds: {
    http_req_duration: [
      { threshold: "p(95)<2000", abortOnFail: false },
    ],
    http_req_failed: [{ threshold: "rate<0.01" }],
  },
  noDisconnect: true,
  maxRedirects: 3,
  timeout: "30s",
  // Setup and teardown for tracking
};

let iterationCount = 0;

export default async function () {
  const userIndex = (__VU - 1) % CONFIG.TEST_USERS.length;
  const testUser = CONFIG.TEST_USERS[userIndex];

  const token = await getAuthToken(testUser);
  if (!token) {
    return;
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  // Lightweight operations to maintain steady load without overwhelming
  // but still testing over long duration

  // 1. Get task list (common operation)
  const tasksRes = await getTasks(headers);
  if (tasksRes.status === 200) {
    const tasks = JSON.parse(tasksRes.body);
    // Track page load performance
    if (tasks.length > 0) {
      // Simulate viewing a task
      await getSingleTask(headers, tasks[0].id);
    }
  }

  // 2. Get schedule history (read-only, moderate load)
  await getScheduleHistory(headers, 10);

  // 3. Occasionally (every 10 iterations) generate a schedule
  iterationCount++;
  if (iterationCount % 10 === 0) {
    await generateSchedule(headers);
  }

  // Longer think time to simulate real user behavior
  sleep(2 + Math.random() * 3);
}

async function getSingleTask(headers, taskId) {
  const url = `${CONFIG.API_URL}/tasks/${taskId}`;
  return await http.get(url, { headers });
}
