#!/usr/bin/env python3
"""
Analyze k6 load test results.

Processes JSON output from k6 and generates a comprehensive performance report
with metrics, trends, and recommendations.
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import statistics


def load_results(filepath: str) -> Dict[str, Any]:
    """Load k6 JSON results."""
    with open(filepath, "r") as f:
        return json.load(f)


def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile from a list of values."""
    if not data:
        return 0.0
    data.sort()
    index = (percentile / 100) * (len(data) - 1)
    if index.is_integer():
        return data[int(index)]
    else:
        lower = data[int(index)]
        upper = data[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


def analyze_metrics(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze k6 metrics and generate statistics."""
    metrics = results.get("metrics", {})
    analysis = {}

    # HTTP Request metrics
    for metric_name in [
        "http_req_duration",
        "http_req_connecting",
        "http_req_waiting",
        "http_req_receiving",
    ]:
        if metric_name in metrics:
            data = metrics[metric_name]["values"]
            if data:
                analysis[metric_name] = {
                    "count": len(data),
                    "min": min(data),
                    "max": max(data),
                    "mean": statistics.mean(data),
                    "median": statistics.median(data),
                    "p95": calculate_percentile(data, 95),
                    "p99": calculate_percentile(data, 99),
                    "stddev": statistics.stdev(data) if len(data) > 1 else 0,
                }

    # Custom metrics
    for metric_name in ["errors", "response_time"]:
        if metric_name in metrics:
            data = metrics[metric_name]["values"]
            if data:
                analysis[metric_name] = {
                    "count": len(data),
                    "min": min(data),
                    "max": max(data),
                    "mean": statistics.mean(data),
                    "median": statistics.median(data),
                    "p95": calculate_percentile(data, 95),
                    "p99": calculate_percentile(data, 99),
                }

    # Error rate
    if "errors" in metrics and "http_req_duration" in metrics:
        error_count = len(metrics["errors"]["values"])
        total_requests = len(metrics["http_req_duration"]["values"])
        analysis["error_rate"] = (
            (error_count / total_requests * 100) if total_requests > 0 else 0
        )

    return analysis


def analyze_thresholds(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze threshold results."""
    thresholds = results.get("thresholds", {})
    threshold_results = []

    for name, data in thresholds.items():
        threshold_results.append(
            {
                "name": name,
                "status": data.get("status", "unknown"),
                "actual": data.get("actual", 0),
                "threshold": data.get("threshold", "N/A"),
                "ok": data.get("ok", False),
            }
        )

    return threshold_results


def analyze_check_rates(results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate pass/fail rates for checks."""
    checks = results.get("checks", {})
    check_rates = {}

    for check_name, data in checks.items():
        values = data.get("values", [])
        if values:
            passed = sum(1 for v in values if v)
            total = len(values)
            check_rates[check_name] = {
                "passed": passed,
                "failed": total - passed,
                "rate": (passed / total * 100) if total > 0 else 0,
            }

    return check_rates


def generate_report(
    analysis: Dict[str, Any],
    thresholds: List[Dict[str, Any]],
    check_rates: Dict[str, float],
    metadata: Dict[str, Any],
) -> str:
    """Generate a human-readable performance report."""
    report = []
    report.append("=" * 80)
    report.append("TACT-AI LOAD TEST PERFORMANCE REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(
        f"Test Duration: {metadata.get('state', {}).get('updatedAt', 'Unknown')}"
    )
    report.append("")

    # Summary
    report.append("SUMMARY")
    report.append("-" * 80)
    total_requests = analysis.get("http_req_duration", {}).get("count", 0)
    error_rate = analysis.get("error_rate", 0)
    report.append(f"Total Requests: {total_requests}")
    report.append(f"Overall Error Rate: {error_rate:.2f}%")

    if "response_time" in analysis:
        rt = analysis["response_time"]
        report.append(f"Response Time (mean): {rt['mean']:.2f}ms")
        report.append(f"Response Time (p95): {rt['p95']:.2f}ms")
        report.append(f"Response Time (p99): {rt['p99']:.2f}ms")
    report.append("")

    # Thresholds
    report.append("THRESHOLD RESULTS")
    report.append("-" * 80)
    for thresh in thresholds:
        status_icon = "✓" if thresh["ok"] else "✗"
        report.append(
            f"{status_icon} {thresh['name']}: {thresh['actual']} (threshold: {thresh['threshold']})"
        )
    report.append("")

    # Check Rates
    report.append("CHECK PASS RATES")
    report.append("-" * 80)
    for check_name, rates in check_rates.items():
        status_icon = "✓" if rates["rate"] >= 95 else "✗"
        report.append(
            f"{status_icon} {check_name}: {rates['rate']:.1f}% ({rates['passed']}/{rates['passed'] + rates['failed']})"
        )
    report.append("")

    # Detailed Metrics
    report.append("DETAILED METRICS")
    report.append("-" * 80)
    for metric_name, stats in analysis.items():
        if (
            metric_name not in ["error_rate"]
            and isinstance(stats, dict)
            and "mean" in stats
        ):
            report.append(f"\n{metric_name}:")
            report.append(f"  Count: {stats['count']}")
            report.append(f"  Min: {stats['min']:.2f}ms")
            report.append(f"  Max: {stats['max']:.2f}ms")
            report.append(f"  Mean: {stats['mean']:.2f}ms")
            report.append(f"  Median: {stats['median']:.2f}ms")
            report.append(f"  p95: {stats['p95']:.2f}ms")
            report.append(f"  p99: {stats['p99']:.2f}ms")
            if "stddev" in stats:
                report.append(f"  StdDev: {stats['stddev']:.2f}ms")

    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    return "\n".join(report)


def generate_recommendations(
    analysis: Dict[str, Any],
    thresholds: List[Dict[str, Any]],
    check_rates: Dict[str, float],
) -> List[str]:
    """Generate optimization recommendations based on results."""
    recommendations = []

    # Check error rate
    error_rate = analysis.get("error_rate", 0)
    if error_rate > 10:
        recommendations.append(
            "High error rate detected (>10%). Check database connections and server logs."
        )

    # Check response times
    if "http_req_duration" in analysis:
        p95 = analysis["http_req_duration"]["p95"]
        if p95 > 500:
            recommendations.append(
                "p95 response time exceeds 500ms threshold. Consider:"
            )
            recommendations.append("  - Increasing database connection pool size")
            recommendations.append("  - Adding or optimizing database indexes")
            recommendations.append("  - Implementing additional Redis caching")
            recommendations.append("  - Optimizing heavy scheduler operations")

    # Check specific endpoint issues
    scheduler_issues = False
    for check_name in check_rates:
        if "scheduler" in check_name and check_rates[check_name]["rate"] < 90:
            scheduler_issues = True
            break

    if scheduler_issues:
        recommendations.append("Scheduler endpoints showing issues. Consider:")
        recommendations.append("  - Increasing OR-Tools num_search_workers")
        recommendations.append(
            "  - Reducing solver time_limit_seconds for faster responses"
        )
        recommendations.append(
            "  - Implementing async schedule generation with background tasks"
        )
        recommendations.append("  - Caching schedule results for similar task sets")

    # Check thresholds
    failed_thresholds = [t for t in thresholds if not t["ok"]]
    if failed_thresholds:
        recommendations.append(
            f"{len(failed_thresholds)} threshold(s) failed. Review performance baselines."
        )

    if not recommendations:
        recommendations.append(
            "All metrics within acceptable thresholds. System performing well."
        )

    return recommendations


def main():
    parser = argparse.ArgumentParser(description="Analyze k6 load test results")
    parser.add_argument("input", help="Path to k6 JSON results file")
    parser.add_argument("-o", "--output", help="Output report file (default: stdout)")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    try:
        results = load_results(args.input)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in input file: {e}")
        sys.exit(1)

    # Analyze results
    analysis = analyze_metrics(results)
    thresholds = analyze_thresholds(results)
    check_rates = analyze_check_rates(results)
    metadata = results.get("meta", {})

    # Generate report
    report = generate_report(analysis, thresholds, check_rates, metadata)

    # Add recommendations
    recommendations = generate_recommendations(analysis, thresholds, check_rates)
    report += "\n\nRECOMMENDATIONS\n"
    report += "-" * 80 + "\n"
    for i, rec in enumerate(recommendations, 1):
        report += f"{i}. {rec}\n"

    # Output
    if args.output:
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report written to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
