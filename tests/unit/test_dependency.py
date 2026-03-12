"""Tests for task chain dependency resolver."""

import pytest
from datetime import datetime, timedelta
from backend.scheduler.dependency import (
    TaskNode,
    DependencyResolver,
    resolve_task_chain,
)


class TestTaskNode:
    """Test the TaskNode class."""

    def test_creation(self):
        """Test basic TaskNode creation."""
        node = TaskNode(task_id=1, duration=60)
        assert node.task_id == 1
        assert node.duration == 60
        assert node.dependencies == []
        assert node.earliest_start is None
        assert node.earliest_finish is None

    def test_creation_with_due_date(self):
        """Test TaskNode creation with due date."""
        due = datetime(2026, 1, 15, 17, 0)
        node = TaskNode(task_id=1, duration=60, due_date=due)
        assert node.due_date == due

    def test_creation_with_all_params(self):
        """Test TaskNode with all parameters."""
        due = datetime(2026, 1, 15, 17, 0)
        node = TaskNode(task_id=42, duration=120, due_date=due)
        assert node.task_id == 42
        assert node.duration == 120
        assert node.due_date == due


class TestDependencyResolver:
    """Test the DependencyResolver class."""

    def setup_method(self):
        """Set up a fresh resolver for each test."""
        self.resolver = DependencyResolver()

    def test_add_task(self):
        """Test adding a single task."""
        self.resolver.add_task(task_id=1, duration=60)
        assert 1 in self.resolver.tasks
        assert self.resolver.tasks[1].duration == 60
        assert len(self.resolver.tasks) == 1

    def test_add_multiple_tasks(self):
        """Test adding multiple tasks."""
        self.resolver.add_task(task_id=1, duration=60)
        self.resolver.add_task(task_id=2, duration=30)
        self.resolver.add_task(task_id=3, duration=45)
        assert len(self.resolver.tasks) == 3
        assert all(tid in self.resolver.tasks for tid in [1, 2, 3])

    def test_add_task_duplicate_raises(self):
        """Test that adding duplicate task raises error."""
        self.resolver.add_task(task_id=1, duration=60)
        with pytest.raises(ValueError, match="Task with ID 1 already exists"):
            self.resolver.add_task(task_id=1, duration=30)

    def test_add_dependency(self):
        """Test adding a dependency between tasks."""
        self.resolver.add_task(task_id=1, duration=60)
        self.resolver.add_task(task_id=2, duration=30)
        self.resolver.add_dependency(task_id=2, prerequisite_id=1)

        task2 = self.resolver.tasks[2]
        assert 1 in task2.dependencies
        assert 2 in self.resolver.adjacency_list[1]
        assert self.resolver.in_degree[2] == 1
        assert self.resolver.in_degree[1] == 0

    def test_add_dependency_updates_in_degree_multiple(self):
        """Test that in_degree is correctly updated for multiple dependencies."""
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_task(3, 45)

        self.resolver.add_dependency(2, 1)
        assert self.resolver.in_degree[2] == 1

        self.resolver.add_dependency(3, 1)
        assert self.resolver.in_degree[3] == 1

    def test_add_dependency_missing_task_raises(self):
        """Test that adding dependency with missing task raises error."""
        self.resolver.add_task(task_id=1, duration=60)
        with pytest.raises(KeyError, match="Prerequisite task 2 not found"):
            self.resolver.add_dependency(task_id=1, prerequisite_id=2)

        with pytest.raises(KeyError, match="Task 99 not found"):
            self.resolver.add_dependency(task_id=99, prerequisite_id=1)

    def test_add_dependency_self_raises(self):
        """Test that a task cannot depend on itself."""
        self.resolver.add_task(task_id=1, duration=60)
        with pytest.raises(ValueError, match="Task cannot depend on itself"):
            self.resolver.add_dependency(task_id=1, prerequisite_id=1)

    def test_topological_sort_simple_chain(self):
        """Test topological sort with simple linear chain: A -> B -> C."""
        self.resolver.add_task(task_id=1, duration=60)  # A
        self.resolver.add_task(task_id=2, duration=30)  # B
        self.resolver.add_task(task_id=3, duration=45)  # C
        self.resolver.add_dependency(task_id=2, prerequisite_id=1)  # B depends on A
        self.resolver.add_dependency(task_id=3, prerequisite_id=2)  # C depends on B

        order = self.resolver.topological_sort()
        assert order == [1, 2, 3]

    def test_topological_sort_fork_join(self):
        """Test topological sort with fork-join pattern."""
        #    A (1)
        #  /   \
        # B(2)  C(3)
        #  \   /
        #    D(4)
        self.resolver.add_task(1, duration=60)
        self.resolver.add_task(2, duration=30)
        self.resolver.add_task(3, duration=45)
        self.resolver.add_task(4, duration=90)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(3, 1)
        self.resolver.add_dependency(4, 2)
        self.resolver.add_dependency(4, 3)

        order = self.resolver.topological_sort()
        # A must come first, D must come last, B and C can be in any order after A
        assert order[0] == 1
        assert order[-1] == 4
        assert set(order[1:3]) == {2, 3}

    def test_topological_sort_multiple_independent(self):
        """Test topological sort with multiple independent chains."""
        # Chain 1: A(1) -> B(2)
        # Chain 2: C(3) -> D(4)
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_task(3, 45)
        self.resolver.add_task(4, 90)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(4, 3)

        order = self.resolver.topological_sort()
        # Should contain all tasks
        assert set(order) == {1, 2, 3, 4}
        # Ordering constraints: 1<2, 3<4
        assert order.index(1) < order.index(2)
        assert order.index(3) < order.index(4)

    def test_topological_sort_diamond_dependency(self):
        """Test topological sort with diamond dependency pattern."""
        #    A
        #  /   \
        # B     C
        #   \   /
        #     D
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_task(3, 30)
        self.resolver.add_task(4, 60)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(3, 1)
        self.resolver.add_dependency(4, 2)
        self.resolver.add_dependency(4, 3)

        order = self.resolver.topological_sort()
        assert order[0] == 1
        assert order[-1] == 4
        assert set(order[1:3]) == {2, 3}

    def test_topological_sort_empty(self):
        """Test topological sort with no tasks."""
        order = self.resolver.topological_sort()
        assert order == []

    def test_topological_sort_single_task(self):
        """Test topological sort with single task."""
        self.resolver.add_task(1, 60)
        order = self.resolver.topological_sort()
        assert order == [1]

    def test_topological_sort_cycle_detection(self):
        """Test that topological sort raises error on cycle."""
        # A -> B -> C -> A
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_task(3, 45)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(3, 2)
        self.resolver.add_dependency(1, 3)

        with pytest.raises(ValueError, match="Cyclic dependency"):
            self.resolver.topological_sort()

    def test_detect_cycles_none(self):
        """Test cycle detection returns None when no cycle."""
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_dependency(2, 1)

        cycle = self.resolver.detect_cycles()
        assert cycle is None

    def test_detect_cycles_simple_two_node(self):
        """Test cycle detection on two-node cycle."""
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(1, 2)

        cycle = self.resolver.detect_cycles()
        assert cycle is not None
        assert set(cycle) == {1, 2}

    def test_detect_cycles_longer_cycle(self):
        """Test cycle detection on longer cycle."""
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_task(3, 45)
        self.resolver.add_task(4, 90)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(3, 2)
        self.resolver.add_dependency(4, 3)
        self.resolver.add_dependency(1, 4)

        cycle = self.resolver.detect_cycles()
        assert cycle is not None
        assert len(cycle) == 4
        assert set(cycle) == {1, 2, 3, 4}

    def test_detect_cycles_multiple_cycles_returns_one(self):
        """Test that detect_cycles returns at least one cycle when multiple exist."""
        # Create two separate cycles: 1->2->1 and 3->4->3
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_task(3, 45)
        self.resolver.add_task(4, 90)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(1, 2)
        self.resolver.add_dependency(4, 3)
        self.resolver.add_dependency(3, 4)

        cycle = self.resolver.detect_cycles()
        assert cycle is not None
        assert len(cycle) >= 2

    def test_compute_earliest_times_simple_chain(self):
        """Test earliest time calculation for simple chain."""
        start = datetime(2026, 1, 1, 8, 0)
        self.resolver.add_task(1, duration=60)
        self.resolver.add_task(2, duration=30)
        self.resolver.add_task(3, duration=45)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(3, 2)

        times = self.resolver.compute_earliest_times(start)

        assert times[1] == (start, start + timedelta(hours=1))
        assert times[2] == (
            start + timedelta(hours=1),
            start + timedelta(hours=1, minutes=30),
        )
        assert times[3] == (
            start + timedelta(hours=1, minutes=30),
            start + timedelta(hours=2, minutes=15),
        )

    def test_compute_earliest_times_fork_join(self):
        """Test earliest time calculation with fork-join pattern."""
        start = datetime(2026, 1, 1, 8, 0)
        # A(60) -> B(30) -> D(90)
        #   \         /
        #    -> C(45)-
        self.resolver.add_task(1, duration=60)
        self.resolver.add_task(2, duration=30)
        self.resolver.add_task(3, duration=45)
        self.resolver.add_task(4, duration=90)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(3, 1)
        self.resolver.add_dependency(4, 2)
        self.resolver.add_dependency(4, 3)

        times = self.resolver.compute_earliest_times(start)

        # A starts at 8:00, finishes 9:00
        assert times[1] == (start, start + timedelta(hours=1))

        # B and C can start after A finishes
        after_a = start + timedelta(hours=1)
        assert times[2][0] == after_a
        assert times[3][0] == after_a

        # D starts after max(B finish, C finish)
        b_finish = after_a + timedelta(minutes=30)
        c_finish = after_a + timedelta(minutes=45)
        d_start = max(b_finish, c_finish)
        assert times[4][0] == d_start
        assert times[4][1] == d_start + timedelta(minutes=90)

    def test_compute_earliest_times_multiple_sources(self):
        """Test earliest times with tasks having multiple prerequisites."""
        start = datetime(2026, 1, 1, 8, 0)
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_task(3, 45)
        self.resolver.add_task(4, 90)

        # Task 4 depends on both 2 and 3
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(3, 1)
        self.resolver.add_dependency(4, 2)
        self.resolver.add_dependency(4, 3)

        times = self.resolver.compute_earliest_times(start)
        task2_start, task2_finish = times[2]
        task3_start, task3_finish = times[3]
        task4_start, task4_finish = times[4]

        # Task 4 should start after both 2 and 3 finish
        assert task4_start >= task2_finish
        assert task4_start >= task3_finish

    def test_compute_earliest_times_cycle_raises(self):
        """Test that computing earliest times fails on cycle."""
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_dependency(2, 1)
        self.resolver.add_dependency(1, 2)

        with pytest.raises(ValueError, match="Cannot compute times"):
            self.resolver.compute_earliest_times(datetime.now())

    def test_calculate_slack_with_due_date(self):
        """Test slack calculation when due date is provided."""
        start = datetime(2026, 1, 1, 8, 0)
        self.resolver.add_task(1, duration=60, due_date=datetime(2026, 1, 1, 10, 0))
        self.resolver.compute_earliest_times(start)

        slack = self.resolver.calculate_slack(1)
        assert slack is not None
        # Task finishes at 9:00, due at 10:00, slack = 1 hour
        assert slack == timedelta(hours=1)

    def test_calculate_slack_no_due_date(self):
        """Test slack calculation when no due date."""
        start = datetime(2026, 1, 1, 8, 0)
        self.resolver.add_task(1, duration=60)
        self.resolver.compute_earliest_times(start)

        slack = self.resolver.calculate_slack(1)
        assert slack is None

    def test_calculate_slack_tight_deadline(self):
        """Test slack calculation when deadline is tight."""
        start = datetime(2026, 1, 1, 8, 0)
        self.resolver.add_task(1, duration=60, due_date=datetime(2026, 1, 1, 8, 30))
        self.resolver.compute_earliest_times(start)

        slack = self.resolver.calculate_slack(1)
        assert slack is not None
        # Task finishes at 9:00, due at 8:30 -> negative slack = 0
        assert slack == timedelta(0)

    def test_calculate_slack_before_times_computed_raises(self):
        """Test that calculate_slack fails if times not computed."""
        self.resolver.add_task(1, duration=60, due_date=datetime.now())
        with pytest.raises(AttributeError):
            self.resolver.calculate_slack(1)

    def test_resolve_full_info(self):
        """Test resolve method returns complete information."""
        start = datetime(2026, 1, 1, 8, 0)
        self.resolver.add_task(1, duration=60, due_date=datetime(2026, 1, 1, 10, 0))
        self.resolver.add_task(2, duration=30, due_date=datetime(2026, 1, 1, 11, 0))
        self.resolver.add_dependency(2, 1)

        result = self.resolver.resolve(start)

        assert 1 in result and 2 in result

        # Check task 1 info
        assert result[1]["task_id"] == 1
        assert result[1]["duration"] == 60
        assert result[1]["dependencies"] == []
        assert result[1]["earliest_start"] == start
        assert result[1]["earliest_finish"] == start + timedelta(hours=1)
        assert result[1]["due_date"] == datetime(2026, 1, 1, 10, 0)
        assert result[1]["slack_time"] == timedelta(hours=1)

        # Check task 2 info
        assert result[2]["task_id"] == 2
        assert result[2]["duration"] == 30
        assert result[2]["dependencies"] == [1]
        assert result[2]["earliest_start"] == start + timedelta(hours=1)
        assert result[2]["earliest_finish"] == start + timedelta(hours=1, minutes=30)
        assert result[2]["due_date"] == datetime(2026, 1, 1, 11, 0)
        assert result[2]["slack_time"] == timedelta(
            hours=1, minutes=30
        )  # Slack = due 11:00 - finish 9:30 = 1.5 hours

    def test_resolve_empty(self):
        """Test resolve with no tasks."""
        result = self.resolver.resolve(datetime.now())
        assert result == {}

    def test_resolve_cycle_detected(self):
        """Test that resolve raises error on cycle."""
        self.resolver.add_task(1, 60)
        self.resolver.add_task(2, 30)
        self.resolver.add_dependency(1, 2)
        self.resolver.add_dependency(2, 1)

        with pytest.raises(ValueError, match="Cyclic dependency"):
            self.resolver.resolve(datetime.now())


class TestResolveTaskChain:
    """Test the convenience function resolve_task_chain."""

    def test_simple_chain(self):
        """Test resolving a simple linear chain."""
        start = datetime(2026, 1, 1, 8, 0)
        tasks = [
            {"id": 1, "duration": 60},
            {"id": 2, "duration": 30, "dependencies": [1]},
            {"id": 3, "duration": 45, "dependencies": [2]},
        ]

        result = resolve_task_chain(tasks, start)

        assert len(result) == 3
        assert result[1]["earliest_start"] == start
        assert result[3]["earliest_finish"] == start + timedelta(hours=2, minutes=15)

    def test_complex_dag(self):
        """Test resolving a complex DAG."""
        start = datetime(2026, 1, 1, 8, 0)
        tasks = [
            {"id": 1, "duration": 60},
            {"id": 2, "duration": 30, "dependencies": [1]},
            {"id": 3, "duration": 45, "dependencies": [1]},
            {"id": 4, "duration": 90, "dependencies": [2, 3]},
            {"id": 5, "duration": 60, "dependencies": [4]},
        ]

        result = resolve_task_chain(tasks, start)
        assert len(result) == 5

        # Check 5 starts after 4 finishes
        task4_finish = result[4]["earliest_finish"]
        assert result[5]["earliest_start"] == task4_finish

    def test_multiple_independent_chains(self):
        """Test resolving multiple independent chains."""
        start = datetime(2026, 1, 1, 8, 0)
        tasks = [
            {"id": 1, "duration": 60},
            {"id": 2, "duration": 30, "dependencies": [1]},
            {"id": 3, "duration": 45},
            {"id": 4, "duration": 90, "dependencies": [3]},
        ]

        result = resolve_task_chain(tasks, start)
        assert len(result) == 4

        # Chain 1: 1->2
        assert result[2]["earliest_start"] == start + timedelta(hours=1)
        # Chain 2: 3->4
        assert result[4]["earliest_start"] == start + timedelta(minutes=45)

    def test_single_task(self):
        """Test resolving a single task."""
        start = datetime(2026, 1, 1, 8, 0)
        tasks = [{"id": 1, "duration": 60}]
        result = resolve_task_chain(tasks, start)
        assert result[1]["earliest_start"] == start
        assert result[1]["earliest_finish"] == start + timedelta(hours=1)

    def test_empty_tasks_list(self):
        """Test resolving empty task list."""
        result = resolve_task_chain([], datetime.now())
        assert result == {}

    def test_cycle_detection(self):
        """Test that cycle is detected in convenience function."""
        start = datetime(2026, 1, 1, 8, 0)
        tasks = [
            {"id": 1, "duration": 60, "dependencies": [2]},
            {"id": 2, "duration": 30, "dependencies": [1]},
        ]

        with pytest.raises(ValueError, match="Cyclic dependency"):
            resolve_task_chain(tasks, start)

    def test_missing_task_in_dependency(self):
        """Test that missing task in dependency raises error."""
        start = datetime(2026, 1, 1, 8, 0)
        tasks = [{"id": 1, "duration": 60, "dependencies": [2]}]

        with pytest.raises(KeyError, match="not found"):
            resolve_task_chain(tasks, start)

    def test_duplicate_task_ids(self):
        """Test that duplicate task IDs raise error."""
        start = datetime(2026, 1, 1, 8, 0)
        tasks = [{"id": 1, "duration": 60}, {"id": 1, "duration": 30}]

        with pytest.raises(ValueError, match="already exists"):
            resolve_task_chain(tasks, start)

    def test_tasks_with_due_dates(self):
        """Test resolution with due dates."""
        start = datetime(2026, 1, 1, 8, 0)
        tasks = [
            {"id": 1, "duration": 60, "due_date": datetime(2026, 1, 1, 10, 0)},
            {
                "id": 2,
                "duration": 30,
                "dependencies": [1],
                "due_date": datetime(2026, 1, 1, 11, 0),
            },
        ]

        result = resolve_task_chain(tasks, start)
        assert result[1]["due_date"] == datetime(2026, 1, 1, 10, 0)
        assert result[2]["due_date"] == datetime(2026, 1, 1, 11, 0)
        # Slack time calculations
        assert result[1]["slack_time"] == timedelta(hours=1)  # finishes 9:00, due 10:00
        assert result[2]["slack_time"] is None or result[2]["slack_time"] > timedelta(
            0
        )  # finishes 9:30, due 11:00 has 1.5hrs
