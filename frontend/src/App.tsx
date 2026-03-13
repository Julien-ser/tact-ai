import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import TasksPage from './pages/TasksPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import NotificationBell from './components/NotificationBell';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

const Navigation: React.FC = () => {
  const { user, logout } = useAuth();
  
  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/tasks" className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Tact AI</h1>
            </Link>
          </div>
          
          {user && (
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                {user.username || user.email}
              </span>
              <NotificationBell />
              <button
                onClick={logout}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

const AppContent: React.FC = () => {
  const { user } = useAuth();
  
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {user && <Navigation />}
        <Routes>
          <Route
            path="/login"
            element={user ? <Navigate to="/tasks" replace /> : <LoginPage />}
          />
          <Route
            path="/register"
            element={user ? <Navigate to="/tasks" replace /> : <RegisterPage />}
          />
          <Route
            path="/tasks"
            element={
              <ProtectedRoute>
                <TasksPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={<Navigate to="/tasks" replace />}
          />
          <Route
            path="*"
            element={<Navigate to="/tasks" replace />}
          />
        </Routes>
      </div>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <AppContent />
      </WebSocketProvider>
    </AuthProvider>
  );
};

export default App;
