/**
 * Stress Test - High load to find breaking point
 * Run: k6 run --vus 500 --duration 10m stress-test.js
 */

import { CONFIG } from "./config.js";
import { getAuthToken, generateSchedule, getScheduleHistory } from "./utils.js";

export const options = {
  thresholds: {
    http_req_duration: [
      { threshold: "p(99)<5000", abortOnFail: false }, // 99% under 5s
    ],
    http_req_failed: [{ threshold: "rate<0.05" }], // Up to 5% errors acceptable in stress
  },
  noDisconnect: true,
  maxRedirects: 3,
  timeout: "60s",
  // Use more aggressive ramp-up
};

export default async function () {
  // Use round-robin assignment of users
  const userIndex = (__VU - 1) % Math.min(CONFIG.TEST_USERS.length, 10);
  const testUser = CONFIG.TEST_USERS[userIndex];

  const token = await getAuthToken(testUser);
  if (!token) {
    return;
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  // Simulate heavy scheduling operations
  // Each user generates a schedule, which is the most resource-intensive operation
  const scheduleRes = await generateSchedule(headers);

  if (scheduleRes.status === 200) {
    // Immediately check history
    await getScheduleHistory(headers, 10);

    // Optional: also try to get the generated schedule
    try {
      const scheduleData = JSON.parse(scheduleRes.body);
      if (scheduleData.timeline_id) {
        await getSpecificSchedule(headers, scheduleData.timeline_id);
      }
    } catch (e) {
      // ignore parse errors
    }
  }

  // Shorter think time to increase load
  sleep(0.2 + Math.random() * 0.8);
}

async function getSpecificSchedule(headers, timelineId) {
  const url = `${CONFIG.API_URL}/scheduler/${timelineId}`;
  return await http.get(url, { headers });
}
