import React from 'react';
import { render, screen } from '@testing-library/react';
import TaskCard from '../TaskCard';
import { Task } from '../../types';

const mockTask: Task = {
  id: 1,
  user_id: 1,
  title: 'Test Task',
  description: 'This is a test task',
  quadrant: 'Q2',
  priority: 'high',
  estimated_duration: 120,
  due_date: '2026-03-15T10:00:00Z',
  completed: false,
  created_at: '2026-03-12T10:00:00Z',
};

describe('TaskCard', () => {
  it('renders task title', () => {
    render(<TaskCard task={mockTask} />);
    expect(screen.getByText('Test Task')).toBeInTheDocument();
  });

  it('displays priority badge', () => {
    render(<TaskCard task={mockTask} />);
    expect(screen.getByText('HIGH')).toBeInTheDocument();
  });

  it('shows task description', () => {
    render(<TaskCard task={mockTask} />);
    expect(screen.getByText('This is a test task')).toBeInTheDocument();
  });

  it('displays duration when provided', () => {
    render(<TaskCard task={mockTask} />);
    expect(screen.getByText(/2h/)).toBeInTheDocument();
  });

  it('renders edit and delete buttons when callbacks provided', () => {
    const onEdit = jest.fn();
    const onDelete = jest.fn();
    render(<TaskCard task={mockTask} onEdit={onEdit} onDelete={onDelete} />);
    
    expect(screen.getByLabelText('Edit task')).toBeInTheDocument();
    expect(screen.getByLabelText('Delete task')).toBeInTheDocument();
  });

  it('calls onToggleComplete when button clicked', () => {
    const onToggleComplete = jest.fn();
    render(<TaskCard task={mockTask} onToggleComplete={onToggleComplete} />);
    
    const button = screen.getByText('Mark Complete');
    button.click();
    expect(onToggleComplete).toHaveBeenCalledWith(1);
  });

  it('shows completed styling when task is completed', () => {
    const completedTask = { ...mockTask, completed: true };
    render(<TaskCard task={completedTask} />);
    
    const title = screen.getByText('Test Task');
    expect(title.className).toContain('line-through');
  });
});
