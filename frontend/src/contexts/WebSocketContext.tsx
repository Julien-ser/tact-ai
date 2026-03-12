import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';

export type WebSocketEventType =
  | 'connected'
  | 'task_created'
  | 'task_updated'
  | 'task_deleted'
  | 'conflict_alert'
  | 'schedule_updated'
  | 'pong';

export interface WebSocketMessage<T = any> {
  event: WebSocketEventType;
  data: T;
}

export interface Notification {
  id: string;
  type: WebSocketEventType;
  message: string;
  data?: any;
  timestamp: Date;
}

interface WebSocketContextType {
  isConnected: boolean;
  notifications: Notification[];
  clearNotification: (id: string) => void;
  clearAllNotifications: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const { user, token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Generate unique notification ID
  const generateId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Add notification
  const addNotification = useCallback((event: string, data: any) => {
    const message: Notification = {
      id: generateId(),
      type: event as WebSocketEventType,
      message: getNotificationMessage(event, data),
      data,
      timestamp: new Date(),
    };

    setNotifications((prev) => [message, ...prev].slice(0, 50)); // Keep last 50 notifications
  }, []);

  // Get human-readable message for event type
  const getNotificationMessage = (event: string, data: any): string => {
    switch (event) {
      case 'connected':
        return 'Connected to real-time updates';
      case 'task_created':
        return `New task created: ${data.title || 'Untitled'}`;
      case 'task_updated':
        return `Task updated: ${data.title || data.id}`;
      case 'task_deleted':
        return `Task ${data.task_id} deleted`;
      case 'conflict_alert':
        return `Schedule conflict detected: ${data.conflicts?.length || 0} issues`;
      case 'schedule_updated':
        return 'Schedule has been updated';
      default:
        return `Event: ${event}`;
    }
  };

  // Clear a specific notification
  const clearNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  // Clear all notifications
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // WebSocket connection effect
  useEffect(() => {
    if (!user || !token) {
      setIsConnected(false);
      return;
    }

    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${API_BASE_URL.replace(/^https?:\/\//, '')}/ws?token=${token}`;

    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 2000;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
          reconnectAttempts = 0;
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            console.log('WebSocket message received:', message);
            addNotification(message.event, message.data);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          setIsConnected(false);
          ws = null;

          // Attempt to reconnect if not by user logout
          if (user && token && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`Reconnecting in ${reconnectDelay}ms (attempt ${reconnectAttempts})`);
            reconnectTimer = setTimeout(connect, reconnectDelay);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

      } catch (error) {
        console.error('Failed to create WebSocket:', error);
      }
    };

    connect();

    // Cleanup
    return () => {
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [user, token, addNotification]);

  const value: WebSocketContextType = {
    isConnected,
    notifications,
    clearNotification,
    clearAllNotifications,
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};
