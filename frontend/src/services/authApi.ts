/**
 * API Service for Authentication
 * 
 * Handles all API calls to the /auth endpoints.
 */

import { User, Token, UserCreate, UserLogin } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * API client for authentication
 */
export const authApi = {
  /**
   * Register a new user
   */
  async register(userData: UserCreate): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to register: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Login user and get access token
   */
  async login(credentials: UserLogin): Promise<Token> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: credentials.email,
        password: credentials.password,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `Failed to login: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get current user profile (optional endpoint if needed)
   */
  async getCurrentUser(): Promise<User> {
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch current user');
    }

    return response.json();
  },
};

export default authApi;
