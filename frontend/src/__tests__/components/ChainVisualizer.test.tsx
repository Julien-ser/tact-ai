import React from 'react';
import { render, screen } from '@testing-library/react';
import ChainVisualizer from '../ChainVisualizer';
import { Task, TaskChain } from '../../types';

const mockTasks: Task[] = [
  {
    id: 1,
    user_id: 1,
    title: 'Task A',
    quadrant: 'Q1',
    priority: 'high',
    completed: false,
    created_at: '2026-03-12T10:00:00Z',
  },
  {
    id: 2,
    user_id: 1,
    title: 'Task B',
    quadrant: 'Q2',
    priority: 'medium',
    completed: false,
    created_at: '2026-03-12T10:00:00Z',
  },
];

const mockTaskChains: TaskChain[] = [
  {
    id: 1,
    task_id: 2,
    prerequisite_task_id: 1,
    relationship_type: 'depends_on',
  },
];

describe('ChainVisualizer', () => {
  it('renders empty message when no tasks or chains', () => {
    render(<ChainVisualizer tasks={[]} taskChains={[]} />);
    expect(screen.getByText('No task chains to visualize')).toBeInTheDocument();
  });

  it('renders empty message when tasks exist but no chains', () => {
    render(<ChainVisualizer tasks={mockTasks} taskChains={[]} />);
    expect(screen.getByText('No task chains to visualize')).toBeInTheDocument();
  });

  it('renders empty message when chains exist but no tasks', () => {
    render(<ChainVisualizer tasks={[]} taskChains={mockTaskChains} />);
    expect(screen.getByText('No task chains to visualize')).toBeInTheDocument();
  });

  it('renders SVG when tasks and chains provided', () => {
    const { container } = render(<ChainVisualizer tasks={mockTasks} taskChains={mockTaskChains} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('applies custom dimensions', () => {
    const { container } = render(<ChainVisualizer tasks={mockTasks} taskChains={mockTaskChains} width={1000} height={800} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '1000');
    expect(svg).toHaveAttribute('height', '800');
  });

  it('filters out task chains with missing tasks', () => {
    const invalidChain: TaskChain = {
      id: 2,
      task_id: 999,
      prerequisite_task_id: 1,
      relationship_type: 'depends_on',
    };
    const { container } = render(<ChainVisualizer tasks={mockTasks} taskChains={[invalidChain, ...mockTaskChains]} />);
    // Should still render SVG because at least one valid chain exists
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});
