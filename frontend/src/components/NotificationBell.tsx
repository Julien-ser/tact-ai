import React, { useState } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

const NotificationBell: React.FC = () => {
  const { notifications, clearNotification, clearAllNotifications, isConnected } = useWebSocket();
  const [isOpen, setIsOpen] = useState(false);

  const getEventIcon = (event: string) => {
    switch (event) {
      case 'task_created':
        return '➕';
      case 'task_updated':
        return '✏️';
      case 'task_deleted':
        return '🗑️';
      case 'conflict_alert':
        return '⚠️';
      case 'schedule_updated':
        return '📅';
      case 'connected':
        return '✅';
      case 'pong':
        return '🏓';
      default:
        return '📢';
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors"
        aria-label="Notifications"
      >
        <svg
          className="h-6 w-6"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {notifications.length > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/4 -translate-y-1/4 bg-red-600 rounded-full">
            {notifications.length}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg overflow-hidden z-50">
          <div className="flex items-center justify-between px-4 py-3 bg-gray-100 border-b">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            {notifications.length > 0 && (
              <button
                onClick={clearAllNotifications}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Clear all
              </button>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-sm text-gray-500">
                No notifications
              </div>
            ) : (
              <div>
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className="px-4 py-3 border-b hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        <span className="text-lg">{getEventIcon(notification.type)}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-gray-900 break-words">
                            {notification.message}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {formatTimestamp(notification.timestamp)}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => clearNotification(notification.id)}
                        className="ml-2 text-gray-400 hover:text-gray-600"
                        aria-label="Clear notification"
                      >
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500 flex items-center justify-between">
            <span>Connection: {isConnected ? '✅ Connected' : '❌ Disconnected'}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
