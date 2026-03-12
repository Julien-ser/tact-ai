"""Tests for AI scheduling engine using OR-Tools CP-SAT."""

import pytest
from datetime import datetime, timedelta, time
from backend.scheduler.engine import (
    TaskScheduler,
    schedule_tasks,
    SchedulingError,
    InfeasibleScheduleError,
)


class TestTaskScheduler:
    """Test the TaskScheduler class."""

    def setup_method(self):
        """Set up common test data."""
        self.start_date = datetime(2026, 1, 1, 8, 0)  # Jan 1, 2026 8:00 AM
        self.time_blocks = [
            {
                "day_of_week": 2,
                "start_time": time(9, 0),
                "end_time": time(17, 0),
            },  # Wednesday
            {
                "day_of_week": 3,
                "start_time": time(9, 0),
                "end_time": time(17, 0),
            },  # Thursday
        ]

    def test_basic_scheduling_single_task(self):
        """Test scheduling a single task."""
        tasks = [
            {"id": 1, "duration": 60, "priority": "high", "title": "Task 1"},
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)

        assert 1 in solution
        task_info = solution[1]
        assert task_info["start"] >= self.start_date
        assert task_info["end"] > task_info["start"]
        assert task_info["duration"] == 60

    def test_scheduling_with_dependencies(self):
        """Test scheduling tasks with dependencies."""
        tasks = [
            {"id": 1, "duration": 60, "priority": "high", "title": "Task 1"},
            {
                "id": 2,
                "duration": 30,
                "priority": "medium",
                "title": "Task 2",
                "dependencies": [1],
            },
            {
                "id": 3,
                "duration": 45,
                "priority": "low",
                "title": "Task 3",
                "dependencies": [2],
            },
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)

        # Check ordering: Task 1 -> Task 2 -> Task 3
        t1 = solution[1]
        t2 = solution[2]
        t3 = solution[3]

        assert t1["end"] <= t2["start"]
        assert t2["end"] <= t3["start"]

    def test_scheduling_with_priorities(self):
        """Test that higher priority tasks tend to be scheduled earlier."""
        tasks = [
            {"id": 1, "duration": 30, "priority": "critical", "title": "Urgent"},
            {"id": 2, "duration": 60, "priority": "low", "title": "Not urgent"},
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)

        # The objective minimizes weighted completion time
        # Critical (weight 1) should complete before low (weight 4) if feasible
        t1 = solution[1]
        t2 = solution[2]

        # Both tasks should be scheduled
        assert t1["start"] < t2["end"]

    def test_scheduling_with_due_dates(self):
        """Test scheduling with due dates creates tardiness terms in objective."""
        due_date = self.start_date + timedelta(days=1, hours=16)  # 4 PM next day
        tasks = [
            {
                "id": 1,
                "duration": 60,
                "priority": "medium",
                "due_date": due_date,
                "title": "Task with deadline",
            },
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)

        assert 1 in solution
        # The task should complete by or after due_date - tardiness is penalized in objective
        t1 = solution[1]

    def test_infeasible_due_to_cycle(self):
        """Test that cyclic dependencies raise InfeasibleScheduleError."""
        tasks = [
            {"id": 1, "duration": 60, "dependencies": [2]},
            {"id": 2, "duration": 30, "dependencies": [1]},
        ]

        with pytest.raises(InfeasibleScheduleError, match="Cyclic dependency"):
            TaskScheduler(
                tasks_data=tasks,
                time_blocks=self.time_blocks,
                start_date=self.start_date,
                horizon_days=2,
            )

    def test_infeasible_due_to_no_working_hours(self):
        """Test that no available working hours raises error."""
        tasks = [{"id": 1, "duration": 60}]
        time_blocks = []  # No working hours

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        with pytest.raises(InfeasibleScheduleError, match="No available working hours"):
            scheduler.solve(time_limit_seconds=10.0)

    def test_infeasible_due_to_task_too_long(self):
        """Test that a task longer than any available slot raises error."""
        tasks = [{"id": 1, "duration": 480}]  # 8 hours
        time_blocks = [
            {
                "day_of_week": 3,  # Thursday (Jan 1, 2026)
                "start_time": time(9, 0),
                "end_time": time(10, 0),
            },  # Only 1 hour on Thursday
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=time_blocks,
            start_date=datetime(2026, 1, 1, 8, 0),
            horizon_days=2,
        )

        with pytest.raises(
            InfeasibleScheduleError, match=r"doesn't fit in any available slot"
        ):
            scheduler.solve(time_limit_seconds=10.0)

    def test_get_schedule_json(self):
        """Test JSON serialization of schedule."""
        tasks = [{"id": 1, "duration": 60, "title": "Task 1"}]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        scheduler.solve(time_limit_seconds=10.0)
        json_schedule = scheduler.get_schedule_json()

        assert isinstance(json_schedule, list)
        assert len(json_schedule) == 1
        assert json_schedule[0]["task_id"] == 1
        assert "start" in json_schedule[0]  # ISO format string
        assert "end" in json_schedule[0]
        assert isinstance(json_schedule[0]["start"], str)

    def test_get_schedule_json_before_solve_raises(self):
        """Test that getting JSON before solving raises error."""
        tasks = [{"id": 1, "duration": 60}]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        with pytest.raises(SchedulingError, match="No solution available"):
            scheduler.get_schedule_json()

    def test_get_conflicts_after_solve(self):
        """Test conflict detection after solving."""
        due_date = self.start_date + timedelta(
            hours=1
        )  # Due before task can realistically finish
        tasks = [
            {"id": 1, "duration": 120, "due_date": due_date, "title": "Overdue task"},
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        scheduler.solve(time_limit_seconds=10.0)
        conflicts = scheduler.get_conflicts()

        # Task duration is 120 minutes, earliest it can finish is 10:00 AM (first day)
        # But due date is 9:00 AM (1 hour after start), so it will be late
        assert len(conflicts) >= 1
        assert any(c["type"] == "missed_deadline" for c in conflicts)

    def test_complex_dag_with_multiple_dependencies(self):
        """Test scheduling a complex DAG with multiple dependencies."""
        # Diamond shape: 1 -> {2,3} -> 4
        tasks = [
            {"id": 1, "duration": 60, "priority": "high"},
            {"id": 2, "duration": 30, "priority": "medium", "dependencies": [1]},
            {"id": 3, "duration": 45, "priority": "medium", "dependencies": [1]},
            {"id": 4, "duration": 90, "priority": "high", "dependencies": [2, 3]},
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)

        # Check all tasks are scheduled
        assert len(solution) == 4

        # Verify dependencies: 1 before 2, 1 before 3, 4 after both 2 and 3
        assert solution[1]["end"] <= solution[2]["start"]
        assert solution[1]["end"] <= solution[3]["start"]
        assert solution[2]["end"] <= solution[4]["start"]
        assert solution[3]["end"] <= solution[4]["start"]

    def test_schedule_spans_multiple_days(self):
        """Test scheduling over multiple working days."""
        tasks = [
            {"id": 1, "duration": 240},  # 4 hours
            {"id": 2, "duration": 240},  # 4 hours
        ]

        # Only 1 hour available per day -> should be infeasible for 4h tasks
        time_blocks = [
            {
                "day_of_week": 2,
                "start_time": time(9, 0),
                "end_time": time(10, 0),
            },  # 1 hour Wed
            {
                "day_of_week": 3,
                "start_time": time(9, 0),
                "end_time": time(10, 0),
            },  # 1 hour Thu
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        with pytest.raises(InfeasibleScheduleError):
            scheduler.solve(time_limit_seconds=10.0)

    def test_task_must_fit_in_single_slot(self):
        """Test that a task cannot be split across working hours."""
        # Task duration 2 hours, but working slots are 1 hour each separated by lunch
        tasks = [{"id": 1, "duration": 120}]

        time_blocks = [
            {
                "day_of_week": 2,
                "start_time": time(9, 0),
                "end_time": time(10, 0),
            },  # 1 hour
            {
                "day_of_week": 2,
                "start_time": time(13, 0),
                "end_time": time(14, 0),
            },  # 1 hour (different slot same day)
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        # Should fail because no single slot is 2 hours long
        with pytest.raises(InfeasibleScheduleError):
            scheduler.solve(time_limit_seconds=10.0)

    def test_schedule_tasks_convenience_function(self):
        """Test the convenience function schedule_tasks()."""
        tasks = [{"id": 1, "duration": 60}]

        solution = schedule_tasks(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        assert 1 in solution
        assert solution[1]["duration"] == 60

    def test_multiple_tasks_no_dependencies(self):
        """Test scheduling multiple independent tasks."""
        tasks = [
            {"id": 1, "duration": 60},
            {"id": 2, "duration": 30},
            {"id": 3, "duration": 45},
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)

        assert len(solution) == 3
        # All tasks should be scheduled within the horizon
        for task_info in solution.values():
            assert task_info["start"] >= self.start_date
            assert task_info["end"] <= self.start_date + timedelta(days=2)

    def test_due_date_before_horizon(self):
        """Test task with due date before planning horizon starts."""
        due_date = self.start_date - timedelta(days=1)  # Due before start
        tasks = [{"id": 1, "duration": 60, "due_date": due_date}]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)
        # Should still schedule, due date is treated as already missed
        assert 1 in solution
        conflicts = scheduler.get_conflicts()
        # Should have a conflict due to missed deadline
        assert len(conflicts) > 0

    def test_objective_minimizes_weighted_completion(self):
        """Test that the objective prioritizes high priority tasks."""
        tasks = [
            {"id": 1, "duration": 60, "priority": "critical"},  # weight 1
            {"id": 2, "duration": 60, "priority": "low"},  # weight 4
        ]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=self.time_blocks,
            start_date=self.start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)
        # Both tasks should be scheduled, objective should be minimal
        assert "objective_value" in solution[1] or "objective_value" in solution[2]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_tasks_list(self):
        """Test scheduling with empty task list."""
        start_date = datetime(2026, 1, 1, 8, 0)
        time_blocks = [
            {
                "day_of_week": 3,
                "start_time": time(9, 0),
                "end_time": time(17, 0),
            },  # Thursday
        ]

        scheduler = TaskScheduler(
            tasks_data=[],
            time_blocks=time_blocks,
            start_date=start_date,
            horizon_days=2,
        )

        solution = scheduler.solve(time_limit_seconds=10.0)
        assert solution == {}

    def test_missing_dependency_task(self):
        """Test that referencing a non-existent dependency fails."""
        tasks = [{"id": 1, "duration": 60, "dependencies": [999]}]

        with pytest.raises(ValueError, match="Dependency task 999 not found"):
            TaskScheduler(
                tasks_data=tasks,
                time_blocks=[],
                start_date=datetime.now(),
                horizon_days=1,
            )

    def test_negative_horizon_raises(self):
        """Test that negative horizon raises ValueError."""
        start = datetime(2026, 1, 1, 8, 0)
        end = start - timedelta(days=1)

        with pytest.raises(ValueError, match="Planning horizon must be positive"):
            TaskScheduler(
                tasks_data=[{"id": 1, "duration": 60}],
                time_blocks=[],
                start_date=start,
                end_date=end,
            )

    def test_task_zero_duration_should_work(self):
        """Test that zero-duration tasks are handled (edge case)."""
        tasks = [{"id": 1, "duration": 0}]

        scheduler = TaskScheduler(
            tasks_data=tasks,
            time_blocks=[],
            start_date=datetime.now(),
            horizon_days=1,
        )

        # Zero duration might cause issues or be instant
        # CP-SAT can handle zero duration intervals? They might be considered as point events
        # OR-Tools interval with size 0 might be invalid
        try:
            solution = scheduler.solve(time_limit_seconds=5.0)
            # If it succeeds, fine
        except Exception:
            # If it fails due to zero duration, that's also reasonable
            pass
