import React, { useState, useEffect } from 'react';
import TaskCard from '../components/TaskCard';
import TaskForm from '../components/TaskForm';
import { Task, Quadrant, Priority } from '../types';
import taskApi from '../services/taskApi';

const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [filter, setFilter] = useState<{
    quadrant?: Quadrant;
    completed?: boolean;
    priority?: Priority;
  }>({});

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await taskApi.getAll(
        filter.completed,
        filter.priority
      );
      setTasks(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTask = (newTask: Task) => {
    setTasks((prev) => [newTask, ...prev]);
  };

  const handleUpdateTask = async (taskId: number, updates: Partial<Task>) => {
    try {
      const updatedTask = await taskApi.update(taskId, updates);
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? updatedTask : t))
      );
      setEditingTask(null);
    } catch (err: any) {
      alert(`Failed to update task: ${err.message}`);
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }
    
    try {
      await taskApi.delete(taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
    } catch (err: any) {
      alert(`Failed to delete task: ${err.message}`);
    }
  };

  const handleToggleComplete = async (taskId: number) => {
    const task = tasks.find((t) => t.id === taskId);
    if (!task) return;

    try {
      await taskApi.update(taskId, { completed: !task.completed });
      setTasks((prev) =>
        prev.map((t) =>
          t.id === taskId ? { ...t, completed: !t.completed } : t
        )
      );
    } catch (err: any) {
      alert(`Failed to update task: ${err.message}`);
    }
  };

  const handleEditTask = (task: Task) => {
    setEditingTask(task);
  };

  const filteredTasks = tasks.filter((task) => {
    if (filter.quadrant && task.quadrant !== filter.quadrant) {
      return false;
    }
    return true;
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Task Management
        </h1>
        <p className="text-gray-600">
          Create and manage your tasks. Use natural language or manual input.
          AI will automatically classify tasks into Eisenhower quadrants.
        </p>
      </div>

      <div className="mb-6">
        <TaskForm onTaskCreated={handleCreateTask} />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-6">
        <select
          value={filter.quadrant || ''}
          onChange={(e) =>
            setFilter((prev) => ({
              ...prev,
              quadrant: (e.target.value as Quadrant) || undefined,
            }))
          }
          className="px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          <option value="">All Quadrants</option>
          <option value="Q1">Q1: Urgent & Important</option>
          <option value="Q2">Q2: Not Urgent & Important</option>
          <option value="Q3">Q3: Urgent & Not Important</option>
          <option value="Q4">Q4: Not Urgent & Not Important</option>
        </select>

        <select
          value={filter.completed === undefined ? '' : filter.completed.toString()}
          onChange={(e) =>
            setFilter((prev) => ({
              ...prev,
              completed:
                e.target.value === '' ? undefined : e.target.value === 'true',
            }))
          }
          className="px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          <option value="">All Status</option>
          <option value="false">Active</option>
          <option value="true">Completed</option>
        </select>

        <button
          onClick={() => setFilter({})}
          className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
        >
          Clear Filters
        </button>
      </div>

      {/* Task List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading tasks...</p>
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-md p-6 text-center">
          <p className="text-red-700">{error}</p>
          <button
            onClick={fetchTasks}
            className="mt-3 px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
          >
            Retry
          </button>
        </div>
      ) : filteredTasks.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-600">
            {tasks.length === 0
              ? 'No tasks yet. Create your first task above!'
              : 'No tasks match the current filters.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredTasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onToggleComplete={handleToggleComplete}
              onEdit={handleEditTask}
              onDelete={handleDeleteTask}
            />
          ))}
        </div>
      )}

      {/* Edit Modal */}
      {editingTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Edit Task</h2>
              <button
                onClick={() => setEditingTask(null)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                &times;
              </button>
            </div>
            <TaskForm
              onTaskCreated={(task) => {
                setEditingTask(null);
                fetchTasks();
              }}
              onCancel={() => setEditingTask(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default TasksPage;
