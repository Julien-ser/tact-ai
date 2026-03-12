/**
 * API Service for Task Management
 * 
 * Handles all API calls to the /tasks endpoints.
 */

import { Task, TaskCreate, TaskUpdate } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * API client for tasks
 */
export const taskApi = {
  /**
   * Fetch all tasks (with optional filters)
   */
  async getAll(completed?: boolean, priority?: string): Promise<Task[]> {
    const params = new URLSearchParams();
    if (completed !== undefined) params.append('completed', String(completed));
    if (priority) params.append('priority', priority);
    
    const response = await fetch(
      `${API_BASE_URL}/tasks/?${params.toString()}`,
      {
        credentials: 'include',
      }
    );
    
    if (!response.ok) {
      throw new Error(`Failed to fetch tasks: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Fetch a single task by ID
   */
  async getById(taskId: number): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
      credentials: 'include',
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Task not found');
      }
      throw new Error(`Failed to fetch task: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Create a new task with AI-powered classification
   */
  async create(taskData: TaskCreate): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/tasks/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(taskData),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to create task: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Update an existing task
   */
  async update(taskId: number, taskData: TaskUpdate): Promise<Task> {
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(taskData),
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to update task: ${response.statusText}`);
    }
    
    return response.json();
  },

  /**
   * Delete a task
   */
  async delete(taskId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
      method: 'DELETE',
      credentials: 'include',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to delete task: ${response.statusText}`);
    }
  },
};

export default taskApi;
