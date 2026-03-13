/**
 * tact-ai Load Testing Configuration
 */

export const CONFIG = {
  // API endpoint - change this to your backend URL
  API_URL: "http://localhost:8000",

  // Test users for authentication
  TEST_USERS: [
    { email: "testuser1@example.com", password: "testpass123" },
    { email: "testuser2@example.com", password: "testpass123" },
    { email: "testuser3@example.com", password: "testpass123" },
  ],

  // Test data templates
  SAMPLE_TASKS: [
    { title: "Complete project proposal", description: "Write and submit the Q2 project proposal", priority: "high", estimated_duration: 120 },
    { title: "Review team pull requests", description: "Review pending PRs from the backend team", priority: "medium", estimated_duration: 60 },
    { title: "Weekly team meeting", description: "Standup and planning for the week", priority: "high", estimated_duration: 45 },
    { title: "Update documentation", description: "Update API docs with new endpoints", priority: "low", estimated_duration: 90 },
    { title: "Fix critical bug", description: "Address user login issue reported by support", priority: "critical", estimated_duration: 60 },
    { title: "Code review for feature X", description: "Review and approve feature branch", priority: "medium", estimated_duration: 45 },
    { title: "Client presentation prep", description: "Prepare slides for Friday's client demo", priority: "high", estimated_duration: 180 },
    { title: "Team lunch", description: "Monthly team building lunch", priority: "low", estimated_duration: 90 },
  ],

  // Timing thresholds (in milliseconds)
  THRESHOLDS: {
    login: 2000,
    list_tasks: 1000,
    create_task: 1500,
    generate_schedule: 30000,
  },
};
