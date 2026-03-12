#!/usr/bin/env python3
"""Benchmark script for the AI scheduling engine.

This script measures the performance of the TaskScheduler with varying
numbers of tasks, dependencies, and constraints.
"""

import argparse
import json
import random
import time
from datetime import datetime, timedelta, time as dt_time
from typing import List, Dict, Any

from backend.scheduler.engine import TaskScheduler


def generate_random_tasks(
    num_tasks: int, avg_dependencies: float = 0.2
) -> List[Dict[str, Any]]:
    """Generate random tasks for benchmarking.

    Args:
        num_tasks: Number of tasks to generate
        avg_dependencies: Average number of dependencies per task (0-1)

    Returns:
        List of task dictionaries
    """
    tasks = []
    priorities = ["low", "medium", "high", "critical"]

    for i in range(1, num_tasks + 1):
        duration = random.randint(15, 180)  # 15 minutes to 3 hours

        # Randomly assign due date within next 7 days
        due_date = None
        if random.random() < 0.3:  # 30% have due dates
            due_date = datetime.now() + timedelta(days=random.randint(1, 7))

        # Generate dependencies
        dependencies = []
        if i > 1 and random.random() < avg_dependencies:
            # Each task has avg_dependencies chance to depend on earlier tasks
            num_deps = random.randint(1, min(3, i - 1))
            possible_deps = list(range(1, i))
            dependencies = random.sample(possible_deps, num_deps)

        tasks.append(
            {
                "id": i,
                "duration": duration,
                "priority": random.choice(priorities),
                "title": f"Task {i}",
                "description": f"Auto-generated benchmark task {i}",
                "due_date": due_date,
                "dependencies": dependencies,
            }
        )

    return tasks


def generate_working_hours(
    start_date: datetime, num_days: int = 7, work_hours_per_day: int = 8
) -> List[Dict[str, Any]]:
    """Generate standard working hours schedule aligned with start_date.

    Args:
        start_date: The start date of the planning horizon
        num_days: Number of days in the schedule
        work_hours_per_day: Hours of work per day

    Returns:
        List of time block dictionaries
    """
    # Work from 9 AM to 12 PM and 1 PM to 5 PM with 1 hour lunch break
    time_blocks = []
    start_weekday = start_date.weekday()  # 0=Monday, 6=Sunday

    for day_offset in range(num_days):
        day_of_week = (start_weekday + day_offset) % 7
        # Morning block 9:00-12:00
        time_blocks.append(
            {
                "day_of_week": day_of_week,
                "start_time": dt_time(9, 0),
                "end_time": dt_time(12, 0),
            }
        )
        # Afternoon block 13:00-17:00
        time_blocks.append(
            {
                "day_of_week": day_of_week,
                "start_time": dt_time(13, 0),
                "end_time": dt_time(17, 0),
            }
        )

    return time_blocks


def run_benchmark(
    num_tasks: int,
    num_days: int,
    time_limit: float,
    warmup: bool = True,
) -> Dict[str, Any]:
    """Run a single benchmark with given parameters.

    Args:
        num_tasks: Number of tasks to schedule
        num_days: Planning horizon in days
        time_limit: Solver time limit in seconds
        warmup: Whether to run a warmup solve first (to avoid first-call overhead)

    Returns:
        Dictionary with benchmark results
    """
    start_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    tasks = generate_random_tasks(num_tasks)
    time_blocks = generate_working_hours(start_date=start_date, num_days=num_days)

    # Warmup
    if warmup and num_tasks > 10:
        small_tasks = tasks[:10]
        warmup_scheduler = TaskScheduler(
            tasks_data=small_tasks,
            time_blocks=time_blocks,
            start_date=start_date,
            horizon_days=num_days,
        )
        warmup_scheduler.solve(time_limit_seconds=min(1.0, time_limit / 10))

    # Actual benchmark
    scheduler = TaskScheduler(
        tasks_data=tasks,
        time_blocks=time_blocks,
        start_date=start_date,
        horizon_days=num_days,
    )

    start_time = time.time()
    solution = scheduler.solve(time_limit_seconds=time_limit)
    elapsed = time.time() - start_time

    total_duration = sum(task["duration"] for task in tasks)
    scheduled_tasks = len(solution)

    # Calculate available minutes
    total_available_minutes = (
        sum(
            (block["end_time"].hour * 60 + block["end_time"].minute)
            - (block["start_time"].hour * 60 + block["start_time"].minute)
            for block in time_blocks
        )
        * num_days
    )

    conflicts = scheduler.get_conflicts()
    json_schedule = scheduler.get_schedule_json()

    return {
        "num_tasks": num_tasks,
        "num_days": num_days,
        "time_limit_seconds": time_limit,
        "total_task_duration_minutes": total_duration,
        "total_available_minutes": total_available_minutes,
        "scheduled_tasks": scheduled_tasks,
        "tasks_percentage": (scheduled_tasks / num_tasks) * 100 if num_tasks > 0 else 0,
        "solve_time_seconds": elapsed,
        "status": "success",
        "num_conflicts": len(conflicts),
        "schedule_length": len(json_schedule),
        "objective_value": scheduler.solution[list(scheduler.solution.keys())[0]][
            "objective_value"
        ]
        if scheduler.solution
        else None,
    }


def run_scaling_benchmark(
    task_counts: List[int],
    num_days: int = 7,
    time_limit: float = 30.0,
) -> List[Dict[str, Any]]:
    """Run benchmarks across different task counts.

    Args:
        task_counts: List of task counts to test
        num_days: Planning horizon in days
        time_limit: Time limit per solve in seconds

    Returns:
        List of result dictionaries
    """
    results = []

    for num_tasks in task_counts:
        print(f"\n{'=' * 60}")
        print(f"Running benchmark: {num_tasks} tasks, {num_days} days")
        print(f"{'=' * 60}")

        try:
            result = run_benchmark(num_tasks, num_days, time_limit)
            results.append(result)

            print(
                f"✓ Successfully scheduled {result['scheduled_tasks']}/{result['num_tasks']} tasks"
            )
            print(f"  Solve time: {result['solve_time_seconds']:.3f}s")
            print(f"  Conflicts: {result['num_conflicts']}")

        except Exception as e:
            print(f"✗ Failed: {type(e).__name__}: {e}")
            results.append(
                {
                    "num_tasks": num_tasks,
                    "num_days": num_days,
                    "time_limit_seconds": time_limit,
                    "status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

    return results


def main():
    parser = argparse.ArgumentParser(description="Benchmark the AI scheduling engine")
    parser.add_argument(
        "--tasks",
        type=int,
        nargs="+",
        default=[5, 10, 20, 50, 100],
        help="Task counts to benchmark (e.g., --tasks 10 20 50 100)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Planning horizon in days (default: 7)",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=30.0,
        help="Solver time limit in seconds (default: 30)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results.json",
        help="Output JSON file for results (default: benchmark_results.json)",
    )

    args = parser.parse_args()

    print("AI Scheduling Engine Benchmark")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  Task counts: {args.tasks}")
    print(f"  Planning horizon: {args.days} days")
    print(f"  Time limit per solve: {args.time_limit}s")
    print(f"  Output file: {args.output}")
    print("=" * 60)

    results = run_scaling_benchmark(
        task_counts=args.tasks,
        num_days=args.days,
        time_limit=args.time_limit,
    )

    # Save results to JSON
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]

    print(f"\nSuccessful: {len(successful)}")
    for r in successful:
        print(f"  {r['num_tasks']:4d} tasks: {r['solve_time_seconds']:.3f}s")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for r in failed:
            print(f"  {r['num_tasks']:4d} tasks: {r['error_type']}: {r['error']}")

    # Calculate scaling factor if we have at least 2 successful runs
    if len(successful) >= 2:
        r1, r2 = successful[0], successful[1]
        if r1["num_tasks"] > 0 and r2["num_tasks"] > 0:
            time_delta = r2["solve_time_seconds"] - r1["solve_time_seconds"]
            task_delta = r2["num_tasks"] - r1["num_tasks"]
            if task_delta > 0:
                scaling = time_delta / task_delta
                print(f"\nApproximate scaling: +{scaling:.4f}s per additional task")

    print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()
