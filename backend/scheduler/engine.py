"""AI Scheduling Engine using OR-Tools CP-SAT.

This module provides a constraint programming solver for scheduling tasks
respecting dependencies, working hours, priorities, and deadlines.
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta, time
from collections import defaultdict
import itertools

from ortools.sat.python import cp_model

from .dependency import TaskNode


# Priority mapping to numeric weights (higher number = higher priority)
PRIORITY_WEIGHTS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


class SchedulingError(Exception):
    """Base exception for scheduling errors."""

    pass


class InfeasibleScheduleError(SchedulingError):
    """Raised when no feasible schedule exists."""

    pass


class TaskScheduler:
    """CP-SAT based task scheduler."""

    def __init__(
        self,
        tasks_data: List[Dict[str, Any]],
        time_blocks: List[Dict[str, Any]],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        horizon_days: Optional[int] = None,
    ):
        """Initialize the scheduler.

        Args:
            tasks_data: List of task dictionaries with keys:
                - id: int (task identifier)
                - duration: int (minutes)
                - priority: str ("low", "medium", "high", "critical")
                - due_date: Optional[datetime] (deadline for task)
                - dependencies: List[int] (prerequisite task ids)
            time_blocks: List of time block dictionaries with keys:
                - day_of_week: int (0=Monday, 6=Sunday)
                - start_time: datetime.time (start of available time)
                - end_time: datetime.time (end of available time)
            start_date: The start date/time for the planning horizon
            end_date: Optional end date for planning horizon
            horizon_days: Optional number of days from start_date (used if end_date not provided)

        Raises:
            ValueError: If inputs are invalid
        """
        self.tasks_data = tasks_data
        self.time_blocks = time_blocks
        self.start_date = start_date

        # Calculate planning horizon in minutes
        if end_date:
            self.end_date = end_date
            self.horizon_minutes = int((end_date - start_date).total_seconds() // 60)
        elif horizon_days:
            self.end_date = start_date + timedelta(days=horizon_days)
            self.horizon_minutes = horizon_days * 24 * 60
        else:
            # Default to 7 days if neither provided
            self.end_date = start_date + timedelta(days=7)
            self.horizon_minutes = 7 * 24 * 60

        if self.horizon_minutes <= 0:
            raise ValueError("Planning horizon must be positive")

        # Build dependency graph for validation
        self._build_dependency_graph()

        # Check for cycles early
        cycle = self.resolver.detect_cycles()
        if cycle:
            raise InfeasibleScheduleError(f"Cyclic dependency detected: {cycle}")

        # Pre-compute available time slots in minutes from start_date
        self.available_slots = self._compute_available_slots()

        # Initialize CP-SAT model
        self.model = cp_model.CpModel()
        self.task_vars: Dict[int, Any] = {}  # task_id -> start variable
        self.task_intervals: Dict[int, Any] = {}  # task_id -> interval variable
        self.solution: Optional[Dict[int, Dict[str, Any]]] = None

    def _build_dependency_graph(self) -> None:
        """Build dependency resolver from tasks_data."""
        self.resolver = TaskNode(self.start_date)  # Actually need to use proper class

        # Use the existing DependencyResolver pattern
        from backend.scheduler.dependency import DependencyResolver

        self.resolver = DependencyResolver()

        for task in self.tasks_data:
            self.resolver.add_task(
                task_id=task["id"],
                duration=task["duration"],
                due_date=task.get("due_date"),
            )

        for task in self.tasks_data:
            task_id = task["id"]
            for dep_id in task.get("dependencies", []):
                self.resolver.add_dependency(task_id, dep_id)

    def _compute_available_slots(self) -> List[Tuple[int, int]]:
        """Compute available time slots within the planning horizon.

        Returns:
            List of (start_minute, end_minute) tuples representing available slots
        """
        slots = []
        current_day = 0
        total_days = (self.horizon_minutes + 1439) // 1440  # ceil division

        for day_offset in range(total_days):
            day_date = self.start_date + timedelta(days=day_offset)
            day_of_week = day_date.weekday()  # 0=Monday, 6=Sunday

            # Find time blocks for this day of week
            day_blocks = [
                tb for tb in self.time_blocks if tb["day_of_week"] == day_of_week
            ]

            for block in day_blocks:
                # Convert time objects to minutes since midnight
                start_minutes = (
                    block["start_time"].hour * 60 + block["start_time"].minute
                )
                end_minutes = block["end_time"].hour * 60 + block["end_time"].minute

                # Convert to absolute minutes from planning horizon start
                absolute_start = day_offset * 1440 + start_minutes
                absolute_end = day_offset * 1440 + end_minutes

                # Clamp to horizon bounds
                if absolute_start < self.horizon_minutes:
                    absolute_end = min(absolute_end, self.horizon_minutes)
                    if absolute_end > absolute_start:
                        slots.append((absolute_start, absolute_end))

        # Merge overlapping slots (can happen if multiple blocks overlap)
        if not slots:
            return []

        slots.sort()
        merged = [slots[0]]
        for current in slots[1:]:
            last = merged[-1]
            if current[0] <= last[1]:  # overlap
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)

        return merged

    def _create_variables(self) -> None:
        """Create CP-SAT variables for each task."""
        for task in self.tasks_data:
            task_id = task["id"]
            duration = task["duration"]

            # Start time variable (in minutes from horizon start)
            start_var = self.model.NewIntVar(
                0, self.horizon_minutes - duration, f"start_{task_id}"
            )
            self.task_vars[task_id] = start_var

            # Interval variable for no-overlap constraint
            interval_var = self.model.NewIntervalVar(
                start_var, duration, start_var + duration, f"interval_{task_id}"
            )
            self.task_intervals[task_id] = interval_var

    def _add_dependency_constraints(self) -> None:
        """Add constraints for task dependencies."""
        for task in self.tasks_data:
            task_id = task["id"]
            for dep_id in task.get("dependencies", []):
                if dep_id not in self.task_vars:
                    raise ValueError(f"Dependency task {dep_id} not found")
                # task_id cannot start until dep_id finishes
                self.model.Add(
                    self.task_vars[task_id]
                    >= self.task_vars[dep_id]
                    + self.tasks_data[self._get_task_index(dep_id)]["duration"]
                )

    def _get_task_index(self, task_id: int) -> int:
        """Get index of task in tasks_data by id."""
        for i, task in enumerate(self.tasks_data):
            if task["id"] == task_id:
                return i
        raise ValueError(f"Task {task_id} not found")

    def _add_working_hours_constraints(self) -> None:
        """Add constraints that tasks must be scheduled within available working hours."""
        if not self.available_slots:
            raise InfeasibleScheduleError(
                "No available working hours in the planning horizon"
            )

        # For each task, create a boolean variable for each available slot indicating
        # whether the task is scheduled in that slot
        task_in_slot = {}
        for task_id in self.task_vars:
            task_duration = self.tasks_data[self._get_task_index(task_id)]["duration"]
            task_in_slot[task_id] = []
            for slot_idx, (slot_start, slot_end) in enumerate(self.available_slots):
                slot_duration = slot_end - slot_start
                # Task can only fit in this slot if duration <= slot duration
                if task_duration <= slot_duration:
                    # Create boolean: is task in this slot?
                    in_slot = self.model.NewBoolVar(
                        f"task_{task_id}_in_slot_{slot_idx}"
                    )
                    task_in_slot[task_id].append(
                        (in_slot, slot_idx, slot_start, slot_end)
                    )

                    # Link task start to slot: if in_slot is true, start must be within [slot_start, slot_end - duration]
                    self.model.Add(self.task_vars[task_id] >= slot_start).OnlyEnforceIf(
                        in_slot
                    )
                    self.model.Add(
                        self.task_vars[task_id] <= slot_end - task_duration
                    ).OnlyEnforceIf(in_slot)

                    # Alternative: if in_slot is false, task start is not in this slot
                    self.model.Add(self.task_vars[task_id] < slot_start).OnlyEnforceIf(
                        in_slot.Not()
                    )
                    self.model.Add(
                        self.task_vars[task_id] > slot_end - task_duration
                    ).OnlyEnforceIf(in_slot.Not())
                else:
                    # Task cannot fit in this slot at all
                    in_slot = self.model.NewBoolVar(
                        f"task_{task_id}_in_slot_{slot_idx}_impossible"
                    )
                    self.model.Add(in_slot == 0)  # Force to false
                    task_in_slot[task_id].append(
                        (in_slot, slot_idx, slot_start, slot_end)
                    )

            # Each task must be assigned to exactly one slot (since it must be scheduled exactly once)
            bool_vars = [item[0] for item in task_in_slot[task_id]]
            if bool_vars:
                self.model.AddExactlyOne(bool_vars)
            else:
                # No slot can accommodate this task
                raise InfeasibleScheduleError(
                    f"Task {task_id} duration {task_duration}min doesn't fit in any available slot"
                )

        # Add no-overlap constraint within each slot
        # For each slot, collect tasks assigned to that slot and ensure their intervals don't overlap
        for slot_idx, (slot_start, slot_end) in enumerate(self.available_slots):
            slot_tasks = []
            for task_id in self.task_vars:
                for in_slot, s_idx, _, _ in task_in_slot[task_id]:
                    if s_idx == slot_idx:
                        slot_tasks.append((in_slot, self.task_intervals[task_id]))

            if len(slot_tasks) > 1:
                # For tasks that could be in this slot, add no-overlap condition
                # But only if both are assigned to this slot
                intervals = [interval for _, interval in slot_tasks]
                if intervals:
                    self.model.AddNoOverlap(intervals)

    def _add_due_date_constraints(self) -> None:
        """Add soft constraints for due dates using objective."""
        # We'll handle due dates in the objective function, not as hard constraints
        pass

    def _create_objective(self) -> None:
        """Create objective function to minimize weighted completion time and tardiness."""
        # Priority weights: higher priority = smaller weight (to schedule earlier)
        priority_weights = {
            "low": 4,
            "medium": 3,
            "high": 2,
            "critical": 1,
        }

        weighted_completion_terms = []
        tardiness_terms = []

        for task in self.tasks_data:
            task_id = task["id"]
            duration = task["duration"]
            priority = task.get("priority", "medium")
            due_date = task.get("due_date")

            # Completion time variable
            completion = self.model.NewIntVar(
                0, self.horizon_minutes, f"completion_{task_id}"
            )
            self.model.Add(completion == self.task_vars[task_id] + duration)

            # Weighted completion time (lower weight = higher priority)
            weight = priority_weights.get(priority, 3)
            weighted_completion = self.model.NewIntVar(
                0, self.horizon_minutes * weight, f"weighted_comp_{task_id}"
            )
            self.model.AddMultiplicationEquality(
                weighted_completion, [completion, weight]
            )
            weighted_completion_terms.append(weighted_completion)

            # Tardiness (if due_date is set)
            if due_date:
                # Convert due_date to minutes from horizon start
                due_minutes = int((due_date - self.start_date).total_seconds() // 60)
                if due_minutes < 0:
                    # Due date is before horizon start - treat as already late
                    due_minutes = 0

                # Tardiness = max(0, completion - due_date)
                tardiness = self.model.NewIntVar(
                    0, self.horizon_minutes, f"tardiness_{task_id}"
                )
                self.model.Add(tardiness >= completion - due_minutes)
                tardiness_terms.append(tardiness)

        # Objective: minimize sum of weighted completion times + sum of tardiness
        objective = sum(weighted_completion_terms) + sum(tardiness_terms)
        self.model.Minimize(objective)

    def solve(
        self,
        time_limit_seconds: float = 30.0,
        num_search_workers: int = 4,
    ) -> Dict[int, Dict[str, Any]]:
        """Solve the scheduling problem.

        Args:
            time_limit_seconds: Maximum solving time in seconds
            num_search_workers: Number of parallel search workers

        Returns:
            Dictionary mapping task_id to schedule info:
                - task_id: int
                - start: datetime
                - end: datetime
                - duration: int (minutes)
                - priority: str
                - due_date: Optional[datetime]
                - dependencies: List[int]

        Raises:
            InfeasibleScheduleError: If no feasible schedule exists
            SchedulingError: If solving fails for other reasons
        """
        # Create variables and constraints
        self._create_variables()
        self._add_dependency_constraints()
        self._add_working_hours_constraints()
        self._add_due_date_constraints()
        self._create_objective()

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit_seconds
        solver.parameters.num_search_workers = num_search_workers
        solver.parameters.log_search_progress = False  # Set to True for debugging

        status = solver.Solve(self.model)

        if status == cp_model.INFEASIBLE or status == cp_model.MODEL_INVALID:
            raise InfeasibleScheduleError("No feasible schedule found")
        elif status in (cp_model.UNKNOWN, cp_model.ERROR):
            raise SchedulingError(
                f"Solver failed with status: {solver.StatusName(status)}"
            )

        # Extract solution
        self.solution = {}
        for task in self.tasks_data:
            task_id = task["id"]
            start_minutes = solver.Value(self.task_vars[task_id])
            duration = task["duration"]

            start_dt = self.start_date + timedelta(minutes=start_minutes)
            end_dt = start_dt + timedelta(minutes=duration)

            self.solution[task_id] = {
                "task_id": task_id,
                "title": task.get("title", ""),
                "description": task.get("description", ""),
                "start": start_dt,
                "end": end_dt,
                "duration": duration,
                "priority": task.get("priority", "medium"),
                "due_date": task.get("due_date"),
                "dependencies": task.get("dependencies", []),
                "objective_value": solver.ObjectiveValue(),
            }

        return self.solution

    def get_schedule_json(self) -> List[Dict[str, Any]]:
        """Get schedule in JSON-serializable format.

        Returns:
            List of schedule entries sorted by start time
        """
        if self.solution is None:
            raise SchedulingError("No solution available. Call solve() first.")

        schedule_list = []
        for task_id, info in self.solution.items():
            schedule_list.append(
                {
                    "task_id": info["task_id"],
                    "title": info["title"],
                    "description": info["description"],
                    "start": info["start"].isoformat(),
                    "end": info["end"].isoformat(),
                    "duration": info["duration"],
                    "priority": info["priority"],
                    "due_date": info["due_date"].isoformat()
                    if info["due_date"]
                    else None,
                    "dependencies": info["dependencies"],
                }
            )

        # Sort by start time
        schedule_list.sort(key=lambda x: x["start"])
        return schedule_list

    def get_conflicts(self) -> List[Dict[str, Any]]:
        """Get list of conflicts in the schedule (post-solve analysis).

        Currently returns tasks that missed their due dates.

        Returns:
            List of conflict dictionaries
        """
        if self.solution is None:
            return []

        conflicts = []
        for task_id, info in self.solution.items():
            due_date = info.get("due_date")
            if due_date and info["end"] > due_date:
                conflicts.append(
                    {
                        "task_id": task_id,
                        "title": info["title"],
                        "type": "missed_deadline",
                        "description": f"Task ends at {info['end']} but due at {due_date}",
                        "end": info["end"],
                        "due_date": due_date,
                    }
                )

        return conflicts


def schedule_tasks(
    tasks_data: List[Dict[str, Any]],
    time_blocks: List[Dict[str, Any]],
    start_date: datetime,
    end_date: Optional[datetime] = None,
    horizon_days: Optional[int] = None,
    **solver_kwargs,
) -> Dict[int, Dict[str, Any]]:
    """Convenience function to schedule tasks in one call.

    Args:
        tasks_data: List of task dictionaries
        time_blocks: List of time block dictionaries
        start_date: Planning horizon start
        end_date: Optional planning horizon end
        horizon_days: Optional number of days (used if end_date not provided)
        **solver_kwargs: Additional arguments passed to solve()

    Returns:
        Dictionary mapping task_id to schedule info

    Example:
        >>> tasks = [
        ...     {"id": 1, "duration": 60, "priority": "high", "due_date": datetime(2026, 1, 2, 17, 0)},
        ...     {"id": 2, "duration": 30, "priority": "medium", "dependencies": [1]},
        ... ]
        >>> time_blocks = [
        ...     {"day_of_week": 0, "start_time": time(9, 0), "end_time": time(17, 0)},  # Monday
        ...     {"day_of_week": 1, "start_time": time(9, 0), "end_time": time(17, 0)},  # Tuesday
        ... ]
        >>> schedule = schedule_tasks(tasks, time_blocks, datetime(2026, 1, 1, 8, 0), horizon_days=2)
    """
    scheduler = TaskScheduler(
        tasks_data=tasks_data,
        time_blocks=time_blocks,
        start_date=start_date,
        end_date=end_date,
        horizon_days=horizon_days,
    )
    return scheduler.solve(**solver_kwargs)
