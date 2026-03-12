"""Tests for conflict detection module."""

import pytest
from datetime import datetime, timedelta, time
from backend.scheduler.conflicts import ConflictDetector, detect_schedule_conflicts


class TestConflictDetector:
    """Test the ConflictDetector class."""

    def setup_method(self):
        """Set up common test data."""
        self.start_date = datetime(2026, 1, 1, 8, 0)
        self.time_blocks = [
            {
                "day_of_week": 2,  # Wednesday
                "start_time": time(9, 0),
                "end_time": time(17, 0),
            },
            {
                "day_of_week": 3,  # Thursday
                "start_time": time(9, 0),
                "end_time": time(17, 0),
            },
        ]

    def test_no_conflicts_ideal_schedule(self):
        """Test with a perfect schedule - no conflicts."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),  # Wed 9:00
                "end": datetime(2026, 1, 1, 10, 0),  # Wed 10:00
                "duration": 60,
                "due_date": None,
            },
            {
                "task_id": 2,
                "title": "Task 2",
                "start": datetime(2026, 1, 1, 10, 30),  # Wed 10:30
                "end": datetime(2026, 1, 1, 11, 30),  # Wed 11:30
                "duration": 60,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 0

    def test_detect_overlapping_tasks(self):
        """Test detection of overlapping tasks."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),  # Wed 9:00
                "end": datetime(2026, 1, 1, 10, 30),  # Wed 10:30 (60 min + 30 buffer)
                "duration": 90,
                "due_date": None,
            },
            {
                "task_id": 2,
                "title": "Task 2",
                "start": datetime(
                    2026, 1, 1, 10, 0
                ),  # Wed 10:00 - overlaps with Task 1
                "end": datetime(2026, 1, 1, 11, 0),  # Wed 11:00
                "duration": 60,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "overlap"
        assert "1" in conflicts[0]["conflicting_tasks"]
        assert "2" in conflicts[0]["conflicting_tasks"]
        assert "Task 1" in conflicts[0]["description"]
        assert "Task 2" in conflicts[0]["description"]

    def test_detect_multiple_overlaps(self):
        """Test detection of multiple overlapping pairs."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),
                "end": datetime(2026, 1, 1, 10, 0),
                "duration": 60,
                "due_date": None,
            },
            {
                "task_id": 2,
                "title": "Task 2",
                "start": datetime(2026, 1, 1, 9, 30),  # Overlaps with Task 1 and Task 3
                "end": datetime(2026, 1, 1, 10, 30),
                "duration": 60,
                "due_date": None,
            },
            {
                "task_id": 3,
                "title": "Task 3",
                "start": datetime(2026, 1, 1, 10, 15),  # Overlaps with Task 2
                "end": datetime(2026, 1, 1, 11, 0),
                "duration": 45,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        # Should detect: (1,2), (1,3), (2,3) - but note not all pairs may overlap
        # Task 1: 9:00-10:00, Task 2: 9:30-10:30, Task 3: 10:15-11:00
        # Overlaps: 1&2 (yes), 1&3 (9:00<11:00 and 10:15<10:00? false), 2&3 (yes)
        # Actually: 1&3: start1(9:00) < end3(11:00) true AND start3(10:15) < end1(10:00) false -> no overlap
        # So should be 2 overlaps: (1,2) and (2,3)
        assert len(conflicts) == 2
        assert all(c["conflict_type"] == "overlap" for c in conflicts)

    def test_detect_missed_deadlines(self):
        """Test detection of missed deadlines."""
        due_date = datetime(2026, 1, 1, 10, 0)  # 10 AM
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),
                "end": datetime(2026, 1, 1, 10, 30),  # 30 minutes late
                "duration": 90,
                "due_date": due_date,
            },
            {
                "task_id": 2,
                "title": "Task 2",
                "start": datetime(2026, 1, 1, 11, 0),
                "end": datetime(2026, 1, 1, 12, 0),
                "duration": 60,
                "due_date": datetime(2026, 1, 1, 12, 30),  # On time
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "missed_deadline"
        assert conflicts[0]["task_id"] == "1"
        assert "delay" in conflicts[0]["description"].lower()

    def test_detect_resource_overload_outside_hours(self):
        """Test detection of tasks scheduled outside working hours."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(
                    2026, 1, 1, 8, 0
                ),  # Thursday 8:00 AM (before 9:00 start)
                "end": datetime(2026, 1, 1, 9, 30),  # 8:00-9:30
                "duration": 90,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "resource_overload"
        assert conflicts[0]["task_id"] == "1"
        assert "outside of working hours" in conflicts[0]["description"]

    def test_detect_resource_overload_no_hours_for_day(self):
        """Test detection when no time blocks are defined for the task day."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(
                    2026, 1, 6, 10, 0
                ),  # Monday (day 0) but we only have Wed/Thu
                "end": datetime(2026, 1, 6, 11, 0),
                "duration": 60,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "resource_overload"
        assert "no working hours defined" in conflicts[0]["description"]

    def test_detect_resource_overload_spans_blocks(self):
        """Test detection of tasks that span across non-contiguous working hours."""
        # Time blocks: 9-12 and 13-17 (with lunch break)
        time_blocks_with_lunch = [
            {
                "day_of_week": 2,
                "start_time": time(9, 0),
                "end_time": time(12, 0),
            },
            {
                "day_of_week": 2,
                "start_time": time(13, 0),
                "end_time": time(17, 0),
            },
        ]

        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 11, 0),  # Wed 11:00
                "end": datetime(2026, 1, 1, 13, 30),  # Wed 13:30 - spans lunch break
                "duration": 150,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, time_blocks_with_lunch)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "resource_overload"

    def test_multiple_conflict_types(self):
        """Test a schedule with multiple types of conflicts."""
        due_date = datetime(2026, 1, 1, 10, 0)
        scheduled_tasks = [
            # Overlap pair
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),
                "end": datetime(2026, 1, 1, 10, 0),
                "duration": 60,
                "due_date": None,
            },
            {
                "task_id": 2,
                "title": "Task 2",
                "start": datetime(2026, 1, 1, 9, 30),
                "end": datetime(2026, 1, 1, 10, 30),
                "duration": 60,
                "due_date": None,
            },
            # Missed deadline
            {
                "task_id": 3,
                "title": "Task 3",
                "start": datetime(2026, 1, 1, 10, 0),
                "end": datetime(2026, 1, 1, 11, 0),
                "duration": 60,
                "due_date": due_date,  # Due at 10:00, ends at 11:00
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 3  # Two overlaps, one missed deadline
        conflict_types = [c["conflict_type"] for c in conflicts]
        assert "overlap" in conflict_types
        assert "missed_deadline" in conflict_types

    def test_detect_all_conflicts_convenience_function(self):
        """Test the convenience function detect_schedule_conflicts."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),
                "end": datetime(2026, 1, 1, 10, 0),
                "duration": 60,
                "due_date": None,
            },
            {
                "task_id": 2,
                "title": "Task 2",
                "start": datetime(2026, 1, 1, 9, 30),
                "end": datetime(2026, 1, 1, 10, 30),
                "duration": 60,
                "due_date": None,
            },
        ]

        conflicts = detect_schedule_conflicts(scheduled_tasks, self.time_blocks)

        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "overlap"

    def test_conflicts_sorted_by_severity(self):
        """Test that conflicts are sorted by severity."""
        scheduled_tasks = [
            # Resource overload (least severe)
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 2, 8, 0),  # Outside hours
                "end": datetime(2026, 1, 2, 9, 0),
                "duration": 60,
                "due_date": None,
            },
            # Missed deadline
            {
                "task_id": 2,
                "title": "Task 2",
                "start": datetime(2026, 1, 1, 9, 0),
                "end": datetime(2026, 1, 1, 11, 0),
                "duration": 120,
                "due_date": datetime(2026, 1, 1, 10, 0),
            },
            # Overlap (most severe)
            {
                "task_id": 3,
                "title": "Task 3",
                "start": datetime(2026, 1, 1, 9, 30),
                "end": datetime(2026, 1, 1, 10, 30),
                "duration": 60,
                "due_date": None,
            },
            {
                "task_id": 4,
                "title": "Task 4",
                "start": datetime(2026, 1, 1, 10, 0),
                "end": datetime(2026, 1, 1, 11, 0),
                "duration": 60,
                "due_date": None,
            },
        ]

        conflicts = detect_schedule_conflicts(scheduled_tasks, self.time_blocks)

        # Should have 5 conflicts: 3 overlaps, 1 missed deadline, 1 resource overload
        assert len(conflicts) == 5
        # Check ordering: overlaps first, then missed_deadline, then resource_overload
        conflict_types = [c["conflict_type"] for c in conflicts]
        assert conflict_types == [
            "overlap",
            "overlap",
            "overlap",
            "missed_deadline",
            "resource_overload",
        ]

    def test_empty_schedule(self):
        """Test conflict detection with no tasks."""
        scheduled_tasks = []

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 0

    def test_conflict_suggested_resolution_present(self):
        """Test that all conflict types have suggested resolutions."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),
                "end": datetime(2026, 1, 1, 10, 0),
                "duration": 60,
                "due_date": datetime(2026, 1, 1, 9, 30),  # Missed
            },
        ]

        conflicts = detect_schedule_conflicts(scheduled_tasks, self.time_blocks)

        assert len(conflicts) == 1
        assert conflicts[0]["suggested_resolution"] is not None
        assert len(conflicts[0]["suggested_resolution"]) > 0

    def test_task_exactly_at_block_boundary(self):
        """Test task that exactly fits within a time block."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),  # Exactly at block start
                "end": datetime(
                    2026, 1, 1, 10, 0
                ),  # Exactly at block end would still be fine
                "duration": 60,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 0

    def test_due_date_exactly_at_end(self):
        """Test task that ends exactly at due date (not late)."""
        due_date = datetime(2026, 1, 1, 10, 0)
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),
                "end": datetime(2026, 1, 1, 10, 0),  # Exactly at due date
                "duration": 60,
                "due_date": due_date,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 0

    def test_task_on_day_with_hours_outside_block(self):
        """Test task scheduled on a day with hours but task partially outside."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 8, 0),  # Wednesday 8:00 AM (before 9:00)
                "end": datetime(2026, 1, 1, 9, 30),
                "duration": 90,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 1
        assert conflicts[0]["conflict_type"] == "resource_overload"

    def test_overlap_with_same_task_different_id(self):
        """Test that same task ID doesn't cause false positive with itself."""
        scheduled_tasks = [
            {
                "task_id": 1,
                "title": "Task 1",
                "start": datetime(2026, 1, 1, 9, 0),
                "end": datetime(2026, 1, 1, 10, 0),
                "duration": 60,
                "due_date": None,
            },
        ]

        detector = ConflictDetector(scheduled_tasks, self.time_blocks)
        conflicts = detector.detect_all_conflicts()

        assert len(conflicts) == 0
