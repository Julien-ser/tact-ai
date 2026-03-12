import React from 'react';
import { Task, quadrantColors, priorityColors } from '../types';

interface TaskCardProps {
  task: Task;
  onToggleComplete?: (taskId: number) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (taskId: number) => void;
  draggable?: boolean;
}

const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onToggleComplete,
  onEdit,
  onDelete,
  draggable = false,
}) => {
  const quadrantStyle = quadrantColors[task.quadrant];
  const priorityLabel = task.priority.charAt(0).toUpperCase() + task.priority.slice(1);

  const formatDuration = (minutes?: number) => {
    if (!minutes) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div
      className={`rounded-lg border-l-4 p-4 mb-3 bg-white shadow-sm hover:shadow-md transition-shadow ${quadrantStyle.border} ${quadrantStyle.bg}`}
      draggable={draggable}
    >
      <div className="flex justify-between items-start mb-2">
        <h4 className={`font-semibold text-sm flex-1 ${task.completed ? 'line-through text-gray-400' : 'text-gray-800'}`}>
          {task.title}
        </h4>
        <div className="flex gap-1 ml-2">
          {onEdit && (
            <button
              onClick={() => onEdit(task)}
              className="text-gray-400 hover:text-blue-600 p-1"
              aria-label="Edit task"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(task.id)}
              className="text-gray-400 hover:text-red-600 p-1"
              aria-label="Delete task"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {task.description && (
        <p className="text-xs text-gray-600 mb-3 line-clamp-2">{task.description}</p>
      )}

      <div className="flex flex-wrap gap-2 items-center text-xs">
        <span className={`px-2 py-1 rounded-full ${priorityColors[task.priority]}`}>
          {priorityLabel}
        </span>

        {task.estimated_duration && (
          <span className="text-gray-500 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {formatDuration(task.estimated_duration)}
          </span>
        )}

        {task.due_date && (
          <span className={`flex items-center gap-1 ${task.completed ? 'text-gray-400' : 'text-gray-600'}`}>
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {formatDate(task.due_date)}
          </span>
        )}
      </div>

      {onToggleComplete && (
        <div className="mt-3 pt-2 border-t border-gray-200">
          <button
            onClick={() => onToggleComplete(task.id)}
            className={`text-xs font-medium ${task.completed ? 'text-green-600 hover:text-green-700' : 'text-blue-600 hover:text-blue-700'}`}
          >
            {task.completed ? 'Mark Incomplete' : 'Mark Complete'}
          </button>
        </div>
      )}
    </div>
  );
};

export default TaskCard;
