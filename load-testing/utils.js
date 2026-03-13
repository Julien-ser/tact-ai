/**
 * Utility functions for k6 load tests
 */

import { CONFIG } from "./config.js";

/**
 * Get authentication token for a test user
 */
export async function getAuthToken(user) {
  const url = `${CONFIG.API_URL}/auth/token`;
  const payload = {
    username: user.email,
    password: user.password,
  };

  const res = await http.post(url, JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
  });

  if (res.status === 200) {
    const data = JSON.parse(res.body);
    return data.access_token;
  } else {
    console.error(`Failed to authenticate ${user.email}: ${res.status}`);
    return null;
  }
}

/**
 * Get or create test tasks for a user
 */
export async function getOrCreateTestTasks(headers) {
  // First, try to get existing tasks
  const getRes = await http.get(`${CONFIG.API_URL}/tasks/?limit=100`, { headers });
  if (getRes.status === 200) {
    const tasks = JSON.parse(getRes.body);
    if (tasks.length > 0) {
      return tasks;
    }
  }

  // If no tasks exist, create some
  const createdTasks = [];
  for (let i = 0; i < 5; i++) {
    const taskData = CONFIG.SAMPLE_TASKS[i % CONFIG.SAMPLE_TASKS.length];
    const createRes = await createTask(headers, {
      ...taskData,
      title: `${taskData.title} - ${Math.random().toString(36).substr(2, 9)}`,
    });
    if (createRes.status === 201) {
      createdTasks.push(JSON.parse(createRes.body));
    }
  }

  return createdTasks;
}

/**
 * Create a test task
 */
export function createTestTask(overrides = {}) {
  const baseTask = CONFIG.SAMPLE_TASKS[Math.floor(Math.random() * CONFIG.SAMPLE_TASKS.length)];
  return {
    title: `${baseTask.title} - ${Date.now()}`,
    description: baseTask.description,
    priority: baseTask.priority,
    estimated_duration: baseTask.estimated_duration,
    quadrant: ["Q1", "Q2", "Q3", "Q4"][Math.floor(Math.random() * 4)],
    ...overrides,
  };
}

/**
 * Perform common task operations
 */
export async function performTaskWorkflow(headers) {
  // Create a task
  const task = createTestTask();
  const createRes = await createTask(headers, task);
  if (createRes.status !== 201) {
    return;
  }

  const createdTask = JSON.parse(createRes.body);

  // Get task list
  await getTasks(headers);

  // Update the task
  await updateTask(headers, createdTask.id, { completed: true });

  // Get single task
  await getTask(headers, createdTask.id);

  // Delete the task
  await deleteTask(headers, createdTask.id);
}

export async function createTask(headers, taskData) {
  const url = `${CONFIG.API_URL}/tasks/`;
  const res = await http.post(url, JSON.stringify(taskData), { headers });
  return res;
}

export async function getTasks(headers, params = "") {
  const url = `${CONFIG.API_URL}/tasks/?limit=20${params}`;
  return await http.get(url, { headers });
}

export async function getTask(headers, taskId) {
  const url = `${CONFIG.API_URL}/tasks/${taskId}`;
  return await http.get(url, { headers });
}

export async function updateTask(headers, taskId, updates) {
  const url = `${CONFIG.API_URL}/tasks/${taskId}`;
  const res = await http.put(url, JSON.stringify(updates), { headers });
  return res;
}

export async function deleteTask(headers, taskId) {
  const url = `${CONFIG.API_URL}/tasks/${taskId}`;
  return await http.del(url, { headers });
}

export async function generateSchedule(headers) {
  const url = `${CONFIG.API_URL}/scheduler/generate`;
  return await http.post(url, {}, { headers });
}

export async function getScheduleHistory(headers, limit = 10) {
  const url = `${CONFIG.API_URL}/scheduler/history?limit=${limit}`;
  return await http.get(url, { headers });
}

export async function getSchedule(headers, timelineId) {
  const url = `${CONFIG.API_URL}/scheduler/${timelineId}`;
  return await http.get(url, { headers });
}
