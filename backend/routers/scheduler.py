"""
Scheduler Router

Provides endpoints for generating optimized schedules and viewing schedule history.
Integrates with WebSocket for real-time updates and conflict notifications.
"""

import logging
from typing import List, Optional
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from backend.database import get_db
from backend.models.user import User as UserModel
from backend.models.task import Task as TaskModel
from backend.models.time_block import TimeBlock as TimeBlockModel
from backend.models.timeline import Timeline as TimelineModel
from backend.models.timeline_task import TimelineTask as TimelineTaskModel
from backend.models.task_chain import TaskChain as TaskChainModel
from backend.scheduler.engine import TaskScheduler, schedule_tasks
from backend.scheduler.conflicts import detect_schedule_conflicts
from backend.auth.utils import get_current_user
from backend.websocket.router import (
    broadcast_schedule_updated,
    broadcast_conflict_alert,
    get_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.post("/generate")
async def generate_schedule(
    start_date: Optional[datetime] = Query(
        None, description="Schedule start date (defaults to now)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Schedule end date (defaults to start_date + 7 days)"
    ),
    name: Optional[str] = Query(None, description="Optional name for this schedule"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate an optimized schedule for the user's tasks.

    This endpoint:
    1. Fetches all incomplete tasks for the user
    2. Gets user's time blocks (working hours)
    3. Uses OR-Tools CP-SAT to generate optimal schedule
    4. Detects and reports any conflicts
    5. Stores the schedule as a Timeline
    6. Broadcasts real-time updates via WebSocket

    Args:
        start_date: Optional start date for planning horizon (defaults to current time)
        end_date: Optional end date (defaults to start_date + 7 days)
        name: Optional name for the generated schedule
        current_user: Authenticated user
        db: Database session

    Returns:
        Dictionary with generated schedule, conflicts, and timeline metadata
    """
    user_id = current_user.id

    # Set default start_date to now if not provided
    if start_date is None:
        start_date = datetime.now()

    # Set default end_date to 7 days from start if not provided
    if end_date is None:
        from datetime import timedelta

        end_date = start_date + timedelta(days=7)

    logger.info(
        f"Generating schedule for user {user_id} from {start_date} to {end_date}"
    )

    # 1. Fetch user's incomplete tasks
    tasks_query = (
        select(TaskModel)
        .where(TaskModel.user_id == user_id)
        .where(TaskModel.completed == False)
    )
    tasks = db.execute(tasks_query).scalars().all()

    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No incomplete tasks to schedule",
        )

    # 1a. Fetch task dependencies from task_chains table
    task_ids = [task.id for task in tasks]
    chains_query = select(TaskChainModel).where(
        TaskChainModel.task_id.in_(task_ids),
        TaskChainModel.relationship_type == "depends_on",
    )
    chains = db.execute(chains_query).scalars().all()

    # Build dependency dict: task_id -> list of prerequisite_task_ids
    dependencies = {}
    for chain in chains:
        if chain.task_id not in dependencies:
            dependencies[chain.task_id] = []
        dependencies[chain.task_id].append(chain.prerequisite_task_id)

    # Prepare tasks data for scheduler
    tasks_data = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description or "",
            "duration": task.estimated_duration or 60,  # default 60 minutes
            "priority": task.priority or "medium",
            "due_date": task.due_date,
            "dependencies": dependencies.get(task.id, []),
        }
        tasks_data.append(task_dict)

    # 2. Fetch user's time blocks
    time_blocks_query = select(TimeBlockModel).where(TimeBlockModel.user_id == user_id)
    time_blocks_db = db.execute(time_blocks_query).scalars().all()

    time_blocks = []
    for tb in time_blocks_db:
        time_blocks.append(
            {
                "day_of_week": tb.day_of_week,
                "start_time": tb.start_time,
                "end_time": tb.end_time,
            }
        )

    # 3. Generate schedule using TaskScheduler
    try:
        scheduler = TaskScheduler(
            tasks_data=tasks_data,
            time_blocks=time_blocks,
            start_date=start_date,
            end_date=end_date,
        )
        solution = scheduler.solve(time_limit_seconds=30.0, num_search_workers=4)
    except Exception as e:
        logger.error(f"Scheduling failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scheduling failed: {str(e)}",
        )

    # 4. Get conflicts
    conflicts = scheduler.get_conflicts()

    # 5. Convert solution to JSON-serializable format
    schedule_json = scheduler.get_schedule_json()

    # 6. Create Timeline record
    timeline = TimelineModel(
        user_id=user_id,
        name=name or f"Schedule {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        start_date=start_date,
        end_date=end_date,
        schedule_data=str(schedule_json),  # Store as JSON string
    )
    db.add(timeline)
    db.commit()
    db.refresh(timeline)

    # 7. Create TimelineTask entries linking tasks to timeline
    for entry in schedule_json:
        task_id = entry["task_id"]
        # Parse start and end datetimes
        start_dt = datetime.fromisoformat(entry["start"])
        end_dt = datetime.fromisoformat(entry["end"])

        timeline_task = TimelineTaskModel(
            timeline_id=timeline.id,
            task_id=task_id,
            scheduled_start=start_dt,
            scheduled_end=end_dt,
        )
        db.add(timeline_task)

    db.commit()

    logger.info(
        f"Schedule generated for user {user_id}: {len(solution)} tasks, {len(conflicts)} conflicts, timeline_id={timeline.id}"
    )

    # 8. Broadcast real-time updates
    manager = get_manager()

    # Broadcast schedule update (full schedule)
    schedule_data = {
        "timeline_id": timeline.id,
        "name": timeline.name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "generated_at": timeline.generated_at.isoformat(),
        "tasks": schedule_json,
        "task_count": len(schedule_json),
    }
    try:
        await broadcast_schedule_updated(manager, schedule_data, user_id)
    except Exception as e:
        logger.error(f"Failed to broadcast schedule update: {e}")

    # Broadcast conflict alerts if any
    if conflicts:
        conflicts_data = {
            "timeline_id": timeline.id,
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
        }
        try:
            await broadcast_conflict_alert(manager, conflicts_data, user_id)
        except Exception as e:
            logger.error(f"Failed to broadcast conflict alert: {e}")

    # 9. Return response
    return {
        "timeline_id": timeline.id,
        "name": timeline.name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "generated_at": timeline.generated_at.isoformat()
        if timeline.generated_at
        else None,
        "tasks": schedule_json,
        "conflicts": conflicts,
        "stats": {
            "total_tasks": len(tasks_data),
            "scheduled_tasks": len(solution),
            "conflict_count": len(conflicts),
        },
    }


@router.get("/history")
async def get_schedule_history(
    limit: int = Query(10, ge=1, le=100, description="Number of schedules to return"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's schedule generation history.

    Args:
        limit: Maximum number of schedules to return (1-100, default 10)
        current_user: Authenticated user
        db: Database session

    Returns:
        List of timeline records sorted by generation date (newest first)
    """
    user_id = current_user.id

    query = (
        select(TimelineModel)
        .where(TimelineModel.user_id == user_id)
        .order_by(TimelineModel.generated_at.desc())
        .limit(limit)
    )

    timelines = db.execute(query).scalars().all()

    result = []
    for tl in timelines:
        result.append(
            {
                "id": tl.id,
                "name": tl.name,
                "start_date": tl.start_date.isoformat(),
                "end_date": tl.end_date.isoformat(),
                "generated_at": tl.generated_at.isoformat()
                if tl.generated_at
                else None,
                "task_count": len(tl.tasks) if tl.tasks else 0,
            }
        )

    return result


@router.get("/{timeline_id}")
async def get_schedule(
    timeline_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific schedule (timeline) with all task details.

    Args:
        timeline_id: ID of the timeline to retrieve
        current_user: Authenticated user
        db: Database session

    Returns:
        Timeline with full task schedule
    """
    user_id = current_user.id

    # Fetch timeline with eager loading of tasks and their associated tasks
    timeline = db.execute(
        select(TimelineModel)
        .options(selectinload(TimelineModel.tasks).selectinload(TimelineTaskModel.task))
        .where(TimelineModel.id == timeline_id, TimelineModel.user_id == user_id)
    ).scalar_one_or_none()

    if not timeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Timeline not found"
        )

    # Parse schedule_data JSON
    import json

    try:
        schedule_data = (
            json.loads(timeline.schedule_data) if timeline.schedule_data else []
        )
    except json.JSONDecodeError:
        schedule_data = []

    return {
        "id": timeline.id,
        "name": timeline.name,
        "start_date": timeline.start_date.isoformat(),
        "end_date": timeline.end_date.isoformat(),
        "generated_at": timeline.generated_at.isoformat()
        if timeline.generated_at
        else None,
        "tasks": schedule_data,
        "tasks_detailed": [
            {
                "timeline_task_id": tt.id,
                "task_id": tt.task_id,
                "task_title": tt.task.title if tt.task else None,
                "scheduled_start": tt.scheduled_start.isoformat(),
                "scheduled_end": tt.scheduled_end.isoformat(),
                "duration_minutes": int(
                    (tt.scheduled_end - tt.scheduled_start).total_seconds() // 60
                ),
            }
            for tt in timeline.tasks
        ],
    }
