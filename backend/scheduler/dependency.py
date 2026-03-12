"""Task chain dependency resolver using topological sorting.

This module provides functionality to resolve task dependencies using
topological sort, detect cycles in task chains, and compute earliest
start times for tasks based on their dependencies and durations.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated


class TaskNode:
    """Represents a task in the dependency graph."""

    def __init__(
        self, task_id: int, duration: int, due_date: Optional[datetime] = None
    ):
        """Initialize a task node.

        Args:
            task_id: Unique identifier for the task
            duration: Duration in minutes
            due_date: Optional due date for deadline calculations
        """
        self.task_id = task_id
        self.duration = duration
        self.due_date = due_date
        self.dependencies: List[int] = []
        self.earliest_start: Optional[datetime] = None
        self.earliest_finish: Optional[datetime] = None

    def __repr__(self) -> str:
        return f"TaskNode(id={self.task_id}, duration={self.duration})"


class DependencyResolver:
    """Resolves task dependencies using topological sorting."""

    def __init__(self) -> None:
        """Initialize the dependency resolver."""
        self.tasks: Dict[int, TaskNode] = {}
        self.adjacency_list: Dict[int, List[int]] = defaultdict(list)
        self.in_degree: Dict[int, int] = defaultdict(int)

    def add_task(
        self, task_id: int, duration: int, due_date: Optional[datetime] = None
    ) -> None:
        """Add a task to the resolver.

        Args:
            task_id: Unique identifier for the task
            duration: Duration in minutes
            due_date: Optional due date for deadline calculations

        Raises:
            ValueError: If task with same ID already exists
        """
        if task_id in self.tasks:
            raise ValueError(f"Task with ID {task_id} already exists")
        self.tasks[task_id] = TaskNode(task_id, duration, due_date)

    def add_dependency(self, task_id: int, prerequisite_id: int) -> None:
        """Add a dependency: task_id depends on prerequisite_id.

        Args:
            task_id: The dependent task
            prerequisite_id: The prerequisite task that must be completed first

        Raises:
            KeyError: If either task does not exist
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")
        if prerequisite_id not in self.tasks:
            raise KeyError(f"Prerequisite task {prerequisite_id} not found")

        if prerequisite_id == task_id:
            raise ValueError("Task cannot depend on itself")

        self.tasks[task_id].dependencies.append(prerequisite_id)
        self.adjacency_list[prerequisite_id].append(task_id)
        self.in_degree[task_id] += 1

    def topological_sort(self) -> List[int]:
        """Perform topological sort using Kahn's algorithm.

        Returns:
            List of task IDs in topological order

        Raises:
            ValueError: If a cycle is detected
        """
        # Create a copy of in_degree to avoid modifying the original
        in_degree_copy = {tid: self.in_degree[tid] for tid in self.tasks}
        zero_in_degree = deque([tid for tid in self.tasks if in_degree_copy[tid] == 0])
        sorted_order = []

        while zero_in_degree:
            node_id = zero_in_degree.popleft()
            sorted_order.append(node_id)

            for neighbor in self.adjacency_list[node_id]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    zero_in_degree.append(neighbor)

        if len(sorted_order) != len(self.tasks):
            remaining = set(self.tasks.keys()) - set(sorted_order)
            raise ValueError(f"Cyclic dependency detected among tasks: {remaining}")

        return sorted_order

    def detect_cycles(self) -> Optional[List[int]]:
        """Detect cycles in the dependency graph using DFS.

        Returns:
            List representing a cycle if found, None otherwise
        """
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node_id: int) -> Optional[List[int]]:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for neighbor in self.adjacency_list[node_id]:
                if neighbor not in visited:
                    cycle = dfs(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found a cycle, extract it from the path
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:]

            path.pop()
            rec_stack.remove(node_id)
            return None

        for task_id in self.tasks:
            if task_id not in visited:
                cycle = dfs(task_id)
                if cycle:
                    return cycle

        return None

    def compute_earliest_times(
        self, start_date: datetime
    ) -> Dict[int, Tuple[datetime, datetime]]:
        """Compute earliest start and finish times for all tasks.

        Args:
            start_date: The start date/time for the schedule

        Returns:
            Dict mapping task_id to (earliest_start, earliest_finish)

        Raises:
            ValueError: If a cycle is detected
        """
        try:
            sorted_tasks = self.topological_sort()
        except ValueError as e:
            raise ValueError(f"Cannot compute times: {str(e)}")

        result = {}
        for task_id in sorted_tasks:
            task = self.tasks[task_id]

            # Calculate earliest start based on dependencies
            if not task.dependencies:
                task.earliest_start = start_date
            else:
                # Validate all dependencies have computed finish times
                finish_times = []
                for dep_id in task.dependencies:
                    dep_finish = self.tasks[dep_id].earliest_finish
                    if dep_finish is None:
                        raise ValueError(
                            f"Task {task_id} has dependency {dep_id} with undefined finish time"
                        )
                    finish_times.append(dep_finish)
                latest_finish = max(finish_times)
                task.earliest_start = latest_finish

            # Calculate earliest finish
            task.earliest_finish = task.earliest_start + timedelta(
                minutes=task.duration
            )

            result[task_id] = (task.earliest_start, task.earliest_finish)

        return result

    def calculate_slack(self, task_id: int) -> Optional[timedelta]:
        """Calculate slack time for a task.

        Slack time is the difference between earliest finish and due date.
        Positive slack means the task can be delayed by that amount.

        Args:
            task_id: The task to calculate slack for

        Returns:
            Slack time as timedelta, or None if no due date

        Raises:
            AttributeError: If earliest times have not been computed
        """
        task = self.tasks[task_id]
        if task.due_date:
            if task.earliest_finish is None:
                raise AttributeError("Earliest finish time not computed")
            slack = task.due_date - task.earliest_finish
            return max(slack, timedelta(0))
        return None

    def resolve(self, start_date: datetime) -> Dict[int, Dict[str, object]]:
        """Resolve task chains and return detailed scheduling information.

        Args:
            start_date: The start date/time for the schedule

        Returns:
            Dict mapping task_id to scheduling info containing:
            - task_id: int
            - duration: int (minutes)
            - dependencies: List[int]
            - earliest_start: datetime
            - earliest_finish: datetime
            - due_date: Optional[datetime]
            - slack_time: Optional[timedelta]

        Raises:
            ValueError: If a cycle is detected
        """
        cycle = self.detect_cycles()
        if cycle:
            raise ValueError(f"Cyclic dependency detected: {cycle}")

        if not self.tasks:
            return {}

        earliest_times = self.compute_earliest_times(start_date)

        result = {}
        for task_id, (start, finish) in earliest_times.items():
            task = self.tasks[task_id]
            result[task_id] = {
                "task_id": task_id,
                "duration": task.duration,
                "dependencies": task.dependencies.copy(),
                "earliest_start": start,
                "earliest_finish": finish,
                "due_date": task.due_date,
                "slack_time": self.calculate_slack(task_id),
            }

        return result


def resolve_task_chain(
    tasks_data: List[Dict], start_date: datetime
) -> Dict[int, Dict[str, object]]:
    """Convenience function to resolve a task chain in one call.

    Args:
        tasks_data: List of dicts with keys:
            - 'id': int (task ID)
            - 'duration': int (minutes)
            - 'due_date': Optional[datetime]
            - 'dependencies': List[int] (prerequisite task IDs)
        start_date: The start date/time for the schedule

    Returns:
        Dict mapping task_id to scheduling info

    Example:
        >>> tasks = [
        ...     {'id': 1, 'duration': 60, 'dependencies': []},
        ...     {'id': 2, 'duration': 30, 'dependencies': [1]},
        ...     {'id': 3, 'duration': 45, 'dependencies': [1]},
        ...     {'id': 4, 'duration': 90, 'dependencies': [2, 3]}
        ... ]
        >>> result = resolve_task_chain(tasks, datetime(2026, 1, 1, 8, 0))
    """
    resolver = DependencyResolver()

    # Add all tasks first
    for task in tasks_data:
        resolver.add_task(
            task_id=task["id"], duration=task["duration"], due_date=task.get("due_date")
        )

    # Add all dependencies
    for task in tasks_data:
        task_id = task["id"]
        for dep_id in task.get("dependencies", []):
            resolver.add_dependency(task_id, dep_id)

    return resolver.resolve(start_date)
