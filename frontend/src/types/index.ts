export type Quadrant = 'Q1' | 'Q2' | 'Q3' | 'Q4';

export type Priority = 'low' | 'medium' | 'high' | 'critical';

export type RelationshipType = 'depends_on' | 'blocks' | 'relates_to';

export interface Task {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  quadrant: Quadrant;
  priority: Priority;
  estimated_duration?: number; // in minutes
  due_date?: string; // ISO datetime
  completed: boolean;
  created_at: string;
  updated_at?: string;
}

export interface TaskChain {
  id: number;
  task_id: number;
  prerequisite_task_id: number;
  relationship_type: RelationshipType;
}

export interface TimelineTask {
  id: number;
  timeline_id: number;
  task_id: number;
  scheduled_start: string; // ISO datetime
  scheduled_end: string; // ISO datetime
  created_at: string;
  task?: Task;
}

export interface Timeline {
  id: number;
  user_id: number;
  name?: string;
  start_date: string; // ISO datetime
  end_date: string; // ISO datetime
  generated_at: string;
  schedule_data?: string; // JSON string
  tasks: TimelineTask[];
}

// Helper to get quadrant colors
export const quadrantColors: Record<Quadrant, { bg: string; border: string; text: string }> = {
  Q1: { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-800' },
  Q2: { bg: 'bg-green-100', border: 'border-green-500', text: 'text-green-800' },
  Q3: { bg: 'bg-yellow-100', border: 'border-yellow-500', text: 'text-yellow-800' },
  Q4: { bg: 'bg-gray-100', border: 'border-gray-500', text: 'text-gray-800' },
};

// Priority color mapping
export const priorityColors: Record<Priority, string> = {
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};
