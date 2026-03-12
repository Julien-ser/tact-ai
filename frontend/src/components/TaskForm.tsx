import React, { useState } from 'react';
import { TaskCreate, Priority, Quadrant } from '../types';
import taskApi from '../services/taskApi';

interface TaskFormProps {
  onTaskCreated?: (task: any) => void;
  onCancel?: () => void;
}

const TaskForm: React.FC<TaskFormProps> = ({ onTaskCreated, onCancel }) => {
  const [mode, setMode] = useState<'natural' | 'manual'>('natural');
  const [naturalInput, setNaturalInput] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Priority>(Priority.MEDIUM);
  const [estimatedDuration, setEstimatedDuration] = useState(60);
  const [dueDate, setDueDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      let taskData: TaskCreate;

      if (mode === 'natural') {
        // Parse natural language input
        // For now, use the input as title and ask AI to classify
        // Future: could use NLP to extract title, description, etc.
        taskData = {
          title: naturalInput.trim() || 'Untitled Task',
          description: undefined,
          priority: priority,
          estimated_duration: estimatedDuration,
          due_date: dueDate ? new Date(dueDate) : undefined,
          // quadrant will be determined by AI backend
        };
      } else {
        // Manual mode
        if (!title.trim()) {
          throw new Error('Title is required');
        }
        taskData = {
          title: title.trim(),
          description: description.trim() || undefined,
          priority: priority,
          estimated_duration: estimatedDuration,
          due_date: dueDate ? new Date(dueDate) : undefined,
          // quadrant will be determined by AI backend
        };
      }

      const createdTask = await taskApi.create(taskData);
      onTaskCreated?.(createdTask);

      // Reset form
      setNaturalInput('');
      setTitle('');
      setDescription('');
      setPriority(Priority.MEDIUM);
      setEstimatedDuration(60);
      setDueDate('');
    } catch (err: any) {
      setError(err.message || 'Failed to create task');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Add New Task</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setMode('natural')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === 'natural'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Natural Language
          </button>
          <button
            type="button"
            onClick={() => setMode('manual')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              mode === 'manual'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Manual Input
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {mode === 'natural' ? (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Describe your task in plain English
            </label>
            <textarea
              value={naturalInput}
              onChange={(e) => setNaturalInput(e.target.value)}
              placeholder="e.g., I need to prepare a presentation for the client meeting next week, it should take about 2 hours..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
              required
            />
            <p className="mt-2 text-sm text-gray-500">
              The AI will classify your task into the appropriate Eisenhower quadrant.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Task Title *
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter task title"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add a description (optional)"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priority
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value as Priority)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={Priority.LOW}>Low</option>
                  <option value={Priority.MEDIUM}>Medium</option>
                  <option value={Priority.HIGH}>High</option>
                  <option value={Priority.CRITICAL}>Critical</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duration (minutes)
                </label>
                <input
                  type="number"
                  value={estimatedDuration}
                  onChange={(e) => setEstimatedDuration(Number(e.target.value))}
                  min={15}
                  max={480}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Due Date
                </label>
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isSubmitting ? 'Creating...' : 'Create Task'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TaskForm;
