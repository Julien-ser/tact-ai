import React from 'react';
import { render, screen } from '@testing-library/react';
import QuadrantBoard from '../QuadrantBoard';
import { Task, Quadrant } from '../../types';

const mockTasks: Task[] = [
  {
    id: 1,
    user_id: 1,
    title: 'Urgent Important Task',
    quadrant: 'Q1',
    priority: 'critical',
    completed: false,
    created_at: '2026-03-12T10:00:00Z',
  },
  {
    id: 2,
    user_id: 1,
    title: 'Not Urgent Important Task',
    quadrant: 'Q2',
    priority: 'high',
    completed: false,
    created_at: '2026-03-12T10:00:00Z',
  },
  {
    id: 3,
    user_id: 1,
    title: 'Urgent Not Important Task',
    quadrant: 'Q3',
    priority: 'medium',
    completed: false,
    created_at: '2026-03-12T10:00:00Z',
  },
  {
    id: 4,
    user_id: 1,
    title: 'Not Urgent Not Important Task',
    quadrant: 'Q4',
    priority: 'low',
    completed: false,
    created_at: '2026-03-12T10:00:00Z',
  },
];

describe('QuadrantBoard', () => {
  const mockTaskMove = jest.fn();
  const mockToggleComplete = jest.fn();
  const mockEdit = jest.fn();
  const mockDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders all four quadrants', () => {
    render(
      <QuadrantBoard
        tasks={mockTasks}
        onTaskMove={mockTaskMove}
        onToggleComplete={mockToggleComplete}
        onEdit={mockEdit}
        onDelete={mockDelete}
      />
    );

    expect(screen.getByText(/Urgent & Important/)).toBeInTheDocument();
    expect(screen.getByText(/Not Urgent & Important/)).toBeInTheDocument();
    expect(screen.getByText(/Urgent & Not Important/)).toBeInTheDocument();
    expect(screen.getByText(/Not Urgent & Not Important/)).toBeInTheDocument();
  });

  it('displays tasks in correct quadrants', () => {
    render(
      <QuadrantBoard
        tasks={mockTasks}
        onTaskMove={mockTaskMove}
        onToggleComplete={mockToggleComplete}
        onEdit={mockEdit}
        onDelete={mockDelete}
      />
    );

    expect(screen.getByText('Urgent Important Task')).toBeInTheDocument();
    expect(screen.getByText('Not Urgent Important Task')).toBeInTheDocument();
    expect(screen.getByText('Urgent Not Important Task')).toBeInTheDocument();
    expect(screen.getByText('Not Urgent Not Important Task')).toBeInTheDocument();
  });

  it('shows task count per quadrant', () => {
    render(
      <QuadrantBoard
        tasks={mockTasks}
        onTaskMove={mockTaskMove}
        onToggleComplete={mockToggleComplete}
        onEdit={mockEdit}
        onDelete={mockDelete}
      />
    );

    // Each quadrant should show "1 task"
    const taskCounts = screen.getAllByText('1 task');
    expect(taskCounts).toHaveLength(4);
  });

  it('renders empty state when no tasks in quadrant', () => {
    const emptyQuadrantTasks = mockTasks.filter(t => t.quadrant !== 'Q1');
    render(
      <QuadrantBoard
        tasks={emptyQuadrantTasks}
        onTaskMove={mockTaskMove}
      />
    );

    expect(screen.getByText('No tasks in this quadrant')).toBeInTheDocument();
    expect(screen.getByText('Drag tasks here')).toBeInTheDocument();
  });
});
