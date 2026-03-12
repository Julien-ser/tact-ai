import React from 'react';
import { render, screen } from '@testing-library/react';
import TimelineView from '../TimelineView';
import { Timeline, Task } from '../../types';

const mockTask: Task = {
  id: 1,
  user_id: 1,
  title: 'Test Task',
  quadrant: 'Q2',
  priority: 'high',
  estimated_duration: 60,
  completed: false,
  created_at: '2026-03-12T10:00:00Z',
};

const mockTimeline: Timeline = {
  id: 1,
  user_id: 1,
  name: 'Test Schedule',
  start_date: '2026-03-12T09:00:00Z',
  end_date: '2026-03-12T17:00:00Z',
  generated_at: '2026-03-12T08:00:00Z',
  tasks: [
    {
      id: 1,
      timeline_id: 1,
      task_id: 1,
      scheduled_start: '2026-03-12T09:00:00Z',
      scheduled_end: '2026-03-12T10:00:00Z',
      task: mockTask,
    },
  ],
};

describe('TimelineView', () => {
  it('renders timeline title', () => {
    render(<TimelineView timeline={mockTimeline} />);
    expect(screen.getByText(/Test Schedule/)).toBeInTheDocument();
  });

  it('displays date range', () => {
    render(<TimelineView timeline={mockTimeline} />);
    expect(screen.getByText(/3/)).toBeInTheDocument(); // Contains date
  });

  it('renders SVG element', () => {
    const { container } = render(<TimelineView timeline={mockTimeline} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('shows empty message when no tasks', () => {
    const emptyTimeline = { ...mockTimeline, tasks: [] };
    render(<TimelineView timeline={emptyTimeline} />);
    expect(screen.getByText('No timeline data available')).toBeInTheDocument();
  });

  it('applies custom dimensions', () => {
    const { container } = render(<TimelineView timeline={mockTimeline} width={1000} height={800} />);
    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', '1000');
    expect(svg).toHaveAttribute('height', '800');
  });
});
