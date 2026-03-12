"""Conflict detection for task schedules.

This module provides functionality to detect various conflicts in a generated schedule:
- Overlapping tasks (time conflicts)
- Resource over-allocation (tasks outside working hours)
- Missed deadlines (tasks completing after due date)
"""

from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import itertools


class ConflictDetector:
    """Detects conflicts in a task schedule."""

    def __init__(
        self,
        scheduled_tasks: List[Dict[str, Any]],
        time_blocks: List[Dict[str, Any]],
    ):
        """Initialize the conflict detector.

        Args:
            scheduled_tasks: List of scheduled task dictionaries with keys:
                - task_id: int
                - title: str
                - start: datetime
                - end: datetime
                - due_date: Optional[datetime]
            time_blocks: List of time block dictionaries with keys:
                - day_of_week: int (0=Monday, 6=Sunday)
                - start_time: datetime.time
                - end_time: datetime.time
        """
        self.scheduled_tasks = scheduled_tasks
        self.time_blocks = time_blocks

    def detect_all_conflicts(self) -> List[Dict[str, Any]]:
        """Detect all types of conflicts in the schedule.

        Returns:
            List of conflict dictionaries, each containing:
                - task_id: str
                - conflict_type: str ("overlap", "resource_overload", "missed_deadline")
                - description: str
                - conflicting_tasks: List[str] (task IDs involved)
                - suggested_resolution: Optional[str]
        """
        conflicts = []
        conflicts.extend(self._detect_overlaps())
        conflicts.extend(self._detect_resource_overload())
        conflicts.extend(self._detect_missed_deadlines())
        return conflicts

    def _detect_overlaps(self) -> List[Dict[str, Any]]:
        """Detect overlapping tasks.

        Returns:
            List of overlap conflict dictionaries.
        """
        conflicts = []
        n = len(self.scheduled_tasks)

        # Check all pairs of tasks for overlap
        for i in range(n):
            for j in range(i + 1, n):
                task1 = self.scheduled_tasks[i]
                task2 = self.scheduled_tasks[j]

                start1, end1 = task1["start"], task1["end"]
                start2, end2 = task2["start"], task2["end"]

                # Check if intervals overlap: (start1 < end2) and (start2 < end1)
                if start1 < end2 and start2 < end1:
                    conflicts.append(
                        {
                            "task_id": str(task1["task_id"]),
                            "conflict_type": "overlap",
                            "description": f"Task '{task1['title']}' overlaps with '{task2['title']}'",
                            "conflicting_tasks": [
                                str(task1["task_id"]),
                                str(task2["task_id"]),
                            ],
                            "suggested_resolution": "Reschedule one of the tasks to a different time slot or adjust durations.",
                        }
                    )

        return conflicts

    def _detect_resource_overload(self) -> List[Dict[str, Any]]:
        """Detect tasks scheduled outside working hours.

        Returns:
            List of resource overload conflict dictionaries.
        """
        conflicts = []

        if not self.time_blocks:
            # If no time blocks defined, can't determine over-allocation
            return conflicts

        for task in self.scheduled_tasks:
            task_start = task["start"]
            task_end = task["end"]
            task_day_of_week = task_start.weekday()  # 0=Monday, 6=Sunday
            task_title = task["title"]
            task_id = str(task["task_id"])

            # Get time blocks for this day
            day_blocks = [
                tb for tb in self.time_blocks if tb["day_of_week"] == task_day_of_week
            ]

            if not day_blocks:
                conflicts.append(
                    {
                        "task_id": task_id,
                        "conflict_type": "resource_overload",
                        "description": f"Task '{task_title}' is scheduled on a day with no working hours defined",
                        "conflicting_tasks": [task_id],
                        "suggested_resolution": "Add working hours for this day or reschedule the task.",
                    }
                )
                continue

            # Check if task fits entirely within at least one time block
            fits_in_any_block = False
            for block in day_blocks:
                block_start_dt = datetime.combine(
                    task_start.date(), block["start_time"]
                )
                block_end_dt = datetime.combine(task_start.date(), block["end_time"])

                if task_start >= block_start_dt and task_end <= block_end_dt:
                    fits_in_any_block = True
                    break

            if not fits_in_any_block:
                # Determine if it's outside hours or spans multiple blocks
                conflicts.append(
                    {
                        "task_id": task_id,
                        "conflict_type": "resource_overload",
                        "description": f"Task '{task_title}' is scheduled outside of working hours",
                        "conflicting_tasks": [task_id],
                        "suggested_resolution": "Reschedule the task to fit within defined working hours or adjust working hours.",
                    }
                )

        return conflicts

    def _detect_missed_deadlines(self) -> List[Dict[str, Any]]:
        """Detect tasks that miss their deadlines.

        Returns:
            List of missed deadline conflict dictionaries.
        """
        conflicts = []

        for task in self.scheduled_tasks:
            due_date = task.get("due_date")
            if due_date:
                task_end = task["end"]
                task_title = task["title"]
                task_id = str(task["task_id"])

                if task_end > due_date:
                    # Calculate how late it is
                    delay = task_end - due_date
                    delay_minutes = int(delay.total_seconds() // 60)

                    conflicts.append(
                        {
                            "task_id": task_id,
                            "conflict_type": "missed_deadline",
                            "description": f"Task '{task_title}' ends at {task_end} but due at {due_date} (delay: {delay_minutes} minutes)",
                            "conflicting_tasks": [task_id],
                            "suggested_resolution": "Prioritize this task earlier in the schedule, reduce its duration, or extend the deadline.",
                        }
                    )

        return conflicts


def detect_schedule_conflicts(
    scheduled_tasks: List[Dict[str, Any]],
    time_blocks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Convenience function to detect conflicts in a schedule.

    Args:
        scheduled_tasks: List of scheduled task dictionaries (from TaskScheduler solution)
        time_blocks: List of time block dictionaries (used for resource over-allocation check)

    Returns:
        List of conflict dictionaries sorted by severity/type.
    """
    detector = ConflictDetector(
        scheduled_tasks=scheduled_tasks, time_blocks=time_blocks
    )
    conflicts = detector.detect_all_conflicts()

    # Sort conflicts: overlaps first (most severe), then missed_deadline, then resource_overload
    severity_order = {"overlap": 0, "missed_deadline": 1, "resource_overload": 2}
    conflicts.sort(key=lambda x: severity_order.get(x["conflict_type"], 3))

    return conflicts
