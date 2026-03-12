"""
Tasks CRUD Router

Provides REST endpoints for task management with AI-powered classification.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models.task import Task as TaskModel
from backend.models.user import User as UserModel
from backend.ai.classifier import EisenhowerQuadrantClassifier
from shared.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    Quadrant,
    Priority,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Placeholder: In production, this would come from JWT auth
def get_current_user_id() -> int:
    """Temporary function to get user ID. Will be replaced with JWT auth."""
    return 1  # Default user for development


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db),
):
    """
    List tasks with optional filters.

    Args:
        completed: Filter by completion status
        priority: Filter by priority level
        db: Database session

    Returns:
        List of tasks belonging to the current user
    """
    user_id = get_current_user_id()

    query = select(TaskModel).where(TaskModel.user_id == user_id)

    if completed is not None:
        query = query.where(TaskModel.completed == completed)
    if priority is not None:
        query = query.where(TaskModel.priority == priority.value)

    tasks = db.execute(query.order_by(TaskModel.created_at.desc())).scalars().all()

    return tasks


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new task with AI-powered quadrant classification.

    If quadrant is not provided, the EisenhowerQuadrantClassifier will classify it.

    Args:
        task_data: Task creation data (title, description, priority, etc.)
        db: Database session

    Returns:
        Created task with AI-assigned quadrant
    """
    user_id = get_current_user_id()

    # Determine quadrant using AI classifier if not provided
    quadrant_value = task_data.quadrant
    if not quadrant_value:
        classifier = EisenhowerQuadrantClassifier()
        classification = await classifier.classify(
            task_title=task_data.title,
            task_description=task_data.description,
        )
        quadrant_value = Quadrant(classification.quadrant.upper())

    # Create task
    db_task = TaskModel(
        user_id=user_id,
        title=task_data.title,
        description=task_data.description,
        quadrant=quadrant_value.value,
        priority=task_data.priority.value,
        estimated_duration=task_data.estimated_duration,
        due_date=task_data.due_date,
        completed=False,
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific task by ID.

    Args:
        task_id: Task ID
        db: Database session

    Returns:
        Task details
    """
    user_id = get_current_user_id()

    task = db.execute(
        select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user_id)
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a task.

    Args:
        task_id: Task ID to update
        task_update: Fields to update
        db: Database session

    Returns:
        Updated task
    """
    user_id = get_current_user_id()

    task = db.execute(
        select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user_id)
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    # Update provided fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Handle enum conversions
        if field == "priority" and value:
            setattr(task, field, value.value)
        elif field == "quadrant" and value:
            setattr(task, field, value.value)
        else:
            setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a task.

    Args:
        task_id: Task ID to delete
        db: Database session
    """
    user_id = get_current_user_id()

    task = db.execute(
        select(TaskModel).where(TaskModel.id == task_id, TaskModel.user_id == user_id)
    ).scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    db.delete(task)
    db.commit()

    return None
