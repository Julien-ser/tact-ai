import React from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragStartEvent,
 PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  DragOverlay,
} from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import { Task, Quadrant, quadrantColors } from '../types';
import TaskCard from './TaskCard';

interface QuadrantBoardProps {
  tasks: Task[];
  onTaskMove: (taskId: number, newQuadrant: Quadrant) => void;
  onToggleComplete?: (taskId: number) => void;
  onEdit?: (task: Task) => void;
  onDelete?: (taskId: number) => void;
}

const QuadrantBoard: React.FC<QuadrantBoardProps> = ({
  tasks,
  onTaskMove,
  onToggleComplete,
  onEdit,
  onDelete,
}) => {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const quadrants: Quadrant[] = ['Q1', 'Q2', 'Q3', 'Q4'];

  const getTasksForQuadrant = (quadrant: Quadrant) => {
    return tasks.filter(task => task.quadrant === quadrant);
  };

  const findQuadrantByTaskId = (taskId: number): Quadrant | null => {
    const task = tasks.find(t => t.id === taskId);
    return task ? task.quadrant : null;
  };

  const handleDragStart = (event: DragStartEvent) => {
    // Can be used to track drag state if needed
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as number;
    const overId = over.id as string;

    // Check if over is a quadrant container (e.g., "quadrant-Q1")
    if (overId.startsWith('quadrant-')) {
      const newQuadrant = overId.replace('quadrant-', '') as Quadrant;
      const currentQuadrant = findQuadrantByTaskId(activeId);

      if (currentQuadrant !== newQuadrant) {
        onTaskMove(activeId, newQuadrant);
      }
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    // Final validation if needed
  };

  const getQuadrantTitle = (quadrant: Quadrant): string => {
    switch (quadrant) {
      case 'Q1':
        return 'Urgent & Important';
      case 'Q2':
        return 'Not Urgent & Important';
      case 'Q3':
        return 'Urgent & Not Important';
      case 'Q4':
        return 'Not Urgent & Not Important';
    }
  };

  const getQuadrantDescription = (quadrant: Quadrant): string => {
    switch (quadrant) {
      case 'Q1':
        return 'Crisis, deadlines, emergencies';
      case 'Q2':
        return 'Planning, improvement, relationship building';
      case 'Q3':
        return 'Interruptions, some meetings, distractions';
      case 'Q4':
        return 'Trivia, time wasters, busywork';
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4">
        {quadrants.map(quadrant => {
          const quadrantTasks = getTasksForQuadrant(quadrant);
          const colors = quadrantColors[quadrant];

          return (
            <div
              key={quadrant}
              id={`quadrant-${quadrant}`}
              className={` rounded-xl border-2 border-dashed p-4 min-h-[400px] transition-colors ${colors.bg} ${colors.border}`}
            >
              <div className="mb-4">
                <h2 className={`text-lg font-bold ${colors.text}`}>
                  {quadrant}: {getQuadrantTitle(quadrant)}
                </h2>
                <p className="text-xs text-gray-600 mt-1">{getQuadrantDescription(quadrant)}</p>
                <span className="text-xs font-medium text-gray-500 mt-2 block">
                  {quadrantTasks.length} task{quadrantTasks.length !== 1 ? 's' : ''}
                </span>
              </div>

              <SortableContext
                items={quadrantTasks.map(t => t.id)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-2">
                  {quadrantTasks.map(task => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      draggable={true}
                      onToggleComplete={onToggleComplete}
                      onEdit={onEdit}
                      onDelete={onDelete}
                    />
                  ))}
                  {quadrantTasks.length === 0 && (
                    <div className={`text-center py-8 border-2 border-dashed rounded-lg ${colors.border} ${colors.bg} opacity-50`}>
                      <p className="text-sm text-gray-500">No tasks in this quadrant</p>
                      <p className="text-xs text-gray-400">Drag tasks here</p>
                    </div>
                  )}
                </div>
              </SortableContext>
            </div>
          );
        })}
      </div>
    </DndContext>
  );
};

export default QuadrantBoard;
