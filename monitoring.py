"""
Monitoring and Metrics System for Agent Orchestration

Provides real-time monitoring, metrics collection, and analysis.

Installation:
    pip install prometheus-client

Usage:
    from monitoring import MetricsCollector, Dashboard

    collector = MetricsCollector()
    collector.record_routing_decision("ui-implementer")
    collector.display_dashboard()
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from collections import defaultdict, deque


class MetricsCollector:
    """
    Collects and stores metrics for monitoring
    """

    def __init__(self, history_size: int = 1000):
        """
        Initialize metrics collector

        Args:
            history_size: Maximum number of events to keep in history
        """
        # Counters
        self.counters = defaultdict(int)

        # Timing data
        self.timings = defaultdict(list)

        # Event history (circular buffer)
        self.history_size = history_size
        self.event_history: deque = deque(maxlen=history_size)

        # Error tracking
        self.errors = defaultdict(list)

        # Start time
        self.start_time = datetime.now()

    def record_routing_decision(
        self,
        agent: str,
        request_type: str,
        duration_ms: Optional[float] = None,
    ):
        """
        Record routing decision

        Args:
            agent: Agent selected
            request_type: Type of request
            duration_ms: Time taken for decision (ms)
        """
        self.counters['total_routing_decisions'] += 1
        self.counters[f'routed_to_{agent}'] += 1
        self.counters[f'request_type_{request_type}'] += 1

        if duration_ms is not None:
            self.timings['routing_decision'].append(duration_ms)

        self.event_history.append({
            'timestamp': datetime.now().isoformat(),
            'event_type': 'routing_decision',
            'agent': agent,
            'request_type': request_type,
            'duration_ms': duration_ms,
        })

    def record_prerequisite_check(
        self,
        agent: str,
        passed: bool,
        missing_files: Optional[List[str]] = None,
    ):
        """
        Record prerequisite check result

        Args:
            agent: Agent being checked
            passed: Whether check passed
            missing_files: List of missing files (if failed)
        """
        self.counters['total_prerequisite_checks'] += 1

        if passed:
            self.counters['prerequisite_checks_passed'] += 1
        else:
            self.counters['prerequisite_checks_failed'] += 1
            self.counters[f'blocked_{agent}'] += 1

        self.event_history.append({
            'timestamp': datetime.now().isoformat(),
            'event_type': 'prerequisite_check',
            'agent': agent,
            'passed': passed,
            'missing_files': missing_files or [],
        })

    def record_completion_verification(
        self,
        agent: str,
        passed: bool,
        missing_deliverables: Optional[List[str]] = None,
    ):
        """
        Record completion verification result

        Args:
            agent: Agent being verified
            passed: Whether verification passed
            missing_deliverables: List of missing deliverables (if failed)
        """
        self.counters['total_completion_verifications'] += 1

        if passed:
            self.counters['completion_verifications_passed'] += 1
            self.counters[f'successful_{agent}'] += 1
        else:
            self.counters['completion_verifications_failed'] += 1

        self.event_history.append({
            'timestamp': datetime.now().isoformat(),
            'event_type': 'completion_verification',
            'agent': agent,
            'passed': passed,
            'missing_deliverables': missing_deliverables or [],
        })

    def record_file_operation(
        self,
        agent: str,
        operation: str,
        file_path: str,
        allowed: bool,
        error: Optional[str] = None,
    ):
        """
        Record file operation check

        Args:
            agent: Agent performing operation
            operation: "create" or "modify"
            file_path: Path to file
            allowed: Whether operation was allowed
            error: Error message if forbidden
        """
        self.counters['total_file_operations'] += 1

        if allowed:
            self.counters['file_operations_allowed'] += 1
        else:
            self.counters['file_operations_blocked'] += 1
            self.counters['conflict_preventions'] += 1

        self.event_history.append({
            'timestamp': datetime.now().isoformat(),
            'event_type': 'file_operation',
            'agent': agent,
            'operation': operation,
            'file_path': file_path,
            'allowed': allowed,
            'error': error,
        })

    def record_error(
        self,
        error_type: str,
        error_message: str,
        context: Optional[Dict] = None,
    ):
        """
        Record error

        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        self.counters['total_errors'] += 1
        self.counters[f'error_{error_type}'] += 1

        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
        }

        self.errors[error_type].append(error_entry)

        self.event_history.append({
            'timestamp': datetime.now().isoformat(),
            'event_type': 'error',
            'error_type': error_type,
            'error_message': error_message,
        })

    def get_summary(self) -> Dict:
        """
        Get summary of metrics

        Returns:
            Dictionary with metric summary
        """
        uptime = datetime.now() - self.start_time

        return {
            'uptime_seconds': uptime.total_seconds(),
            'counters': dict(self.counters),
            'timings': {
                key: {
                    'count': len(values),
                    'avg_ms': sum(values) / len(values) if values else 0,
                    'min_ms': min(values) if values else 0,
                    'max_ms': max(values) if values else 0,
                }
                for key, values in self.timings.items()
            },
            'recent_events': list(self.event_history)[-10:],
        }

    def get_success_rate(self) -> float:
        """
        Calculate overall success rate

        Returns:
            Success rate (0.0 to 1.0)
        """
        total = self.counters['total_routing_decisions']
        if total == 0:
            return 1.0

        blocked = (
            self.counters['prerequisite_checks_failed'] +
            self.counters['completion_verifications_failed'] +
            self.counters['file_operations_blocked']
        )

        return 1.0 - (blocked / total)

    def export_metrics(self, output_file: Path):
        """
        Export metrics to JSON file

        Args:
            output_file: Path to output file
        """
        data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_summary(),
            'errors': {k: v[-100:] for k, v in self.errors.items()},  # Last 100 errors
            'history': list(self.event_history),
        }

        output_file.write_text(json.dumps(data, indent=2))


class Dashboard:
    """
    Real-time dashboard for monitoring
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize dashboard

        Args:
            collector: MetricsCollector instance
        """
        self.collector = collector

    def display(self):
        """
        Display current dashboard (console output)
        """
        summary = self.collector.get_summary()

        print("\n" + "=" * 80)
        print("AGENT ORCHESTRATION SYSTEM - MONITORING DASHBOARD")
        print("=" * 80)

        # Uptime
        uptime = timedelta(seconds=int(summary['uptime_seconds']))
        print(f"\n📊 Uptime: {uptime}")

        # Main metrics
        counters = summary['counters']
        print("\n🎯 ROUTING DECISIONS:")
        print(f"  Total: {counters.get('total_routing_decisions', 0)}")
        print(f"  → ui-implementer: {counters.get('routed_to_ui-implementer', 0)}")
        print(f"  → feature-logic-implementer: {counters.get('routed_to_feature-logic-implementer', 0)}")

        # Request types
        print("\n📝 REQUEST TYPES:")
        for key, value in counters.items():
            if key.startswith('request_type_'):
                req_type = key.replace('request_type_', '')
                print(f"  {req_type}: {value}")

        # Prerequisite checks
        print("\n✅ PREREQUISITE CHECKS:")
        total_checks = counters.get('total_prerequisite_checks', 0)
        passed_checks = counters.get('prerequisite_checks_passed', 0)
        failed_checks = counters.get('prerequisite_checks_failed', 0)
        print(f"  Total: {total_checks}")
        print(f"  Passed: {passed_checks}")
        print(f"  Failed: {failed_checks}")

        # Completion verifications
        print("\n🎉 COMPLETION VERIFICATIONS:")
        total_verifications = counters.get('total_completion_verifications', 0)
        passed_verifications = counters.get('completion_verifications_passed', 0)
        failed_verifications = counters.get('completion_verifications_failed', 0)
        print(f"  Total: {total_verifications}")
        print(f"  Passed: {passed_verifications}")
        print(f"  Failed: {failed_verifications}")

        # File operations
        print("\n📁 FILE OPERATIONS:")
        total_ops = counters.get('total_file_operations', 0)
        allowed_ops = counters.get('file_operations_allowed', 0)
        blocked_ops = counters.get('file_operations_blocked', 0)
        print(f"  Total: {total_ops}")
        print(f"  Allowed: {allowed_ops}")
        print(f"  Blocked: {blocked_ops}")
        print(f"  Conflicts Prevented: {counters.get('conflict_preventions', 0)}")

        # Success rate
        success_rate = self.collector.get_success_rate()
        print(f"\n📈 SUCCESS RATE: {success_rate:.1%}")

        # Errors
        total_errors = counters.get('total_errors', 0)
        if total_errors > 0:
            print(f"\n❌ ERRORS: {total_errors}")
            for key, value in counters.items():
                if key.startswith('error_'):
                    error_type = key.replace('error_', '')
                    print(f"  {error_type}: {value}")

        # Recent events
        print("\n📋 RECENT EVENTS:")
        for event in summary['recent_events'][-5:]:
            timestamp = event['timestamp'].split('T')[1][:8]
            event_type = event['event_type']
            print(f"  [{timestamp}] {event_type}")

        print("\n" + "=" * 80 + "\n")

    def generate_report(self, output_file: Optional[Path] = None) -> str:
        """
        Generate detailed report

        Args:
            output_file: Optional file to write report to

        Returns:
            Report as string
        """
        summary = self.collector.get_summary()

        report_lines = [
            "=" * 80,
            "AGENT ORCHESTRATION SYSTEM - DETAILED REPORT",
            "=" * 80,
            "",
            f"Generated: {datetime.now().isoformat()}",
            f"Uptime: {timedelta(seconds=int(summary['uptime_seconds']))}",
            "",
        ]

        # Counters
        report_lines.append("METRICS:")
        for key, value in sorted(summary['counters'].items()):
            report_lines.append(f"  {key}: {value}")

        # Timings
        if summary['timings']:
            report_lines.append("")
            report_lines.append("TIMINGS:")
            for key, timing in summary['timings'].items():
                report_lines.append(f"  {key}:")
                report_lines.append(f"    Count: {timing['count']}")
                report_lines.append(f"    Average: {timing['avg_ms']:.2f} ms")
                report_lines.append(f"    Min: {timing['min_ms']:.2f} ms")
                report_lines.append(f"    Max: {timing['max_ms']:.2f} ms")

        # Success rate
        success_rate = self.collector.get_success_rate()
        report_lines.append("")
        report_lines.append(f"SUCCESS RATE: {success_rate:.1%}")

        report_lines.append("")
        report_lines.append("=" * 80)

        report = "\n".join(report_lines)

        if output_file:
            output_file.write_text(report)

        return report


class AlertSystem:
    """
    Alert system for monitoring critical events
    """

    def __init__(self, collector: MetricsCollector):
        """
        Initialize alert system

        Args:
            collector: MetricsCollector instance
        """
        self.collector = collector
        self.alerts: List[Dict] = []

        # Alert thresholds
        self.thresholds = {
            'error_rate': 0.1,  # 10% error rate
            'block_rate': 0.2,  # 20% block rate
            'success_rate': 0.8,  # 80% success rate
        }

    def check_alerts(self) -> List[Dict]:
        """
        Check for alert conditions

        Returns:
            List of active alerts
        """
        active_alerts = []

        summary = self.collector.get_summary()
        counters = summary['counters']

        # Check error rate
        total = counters.get('total_routing_decisions', 0)
        if total > 0:
            errors = counters.get('total_errors', 0)
            error_rate = errors / total

            if error_rate > self.thresholds['error_rate']:
                active_alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'warning',
                    'message': f"Error rate is {error_rate:.1%} (threshold: {self.thresholds['error_rate']:.1%})",
                    'value': error_rate,
                })

        # Check block rate
        if total > 0:
            blocked = (
                counters.get('prerequisite_checks_failed', 0) +
                counters.get('file_operations_blocked', 0)
            )
            block_rate = blocked / total

            if block_rate > self.thresholds['block_rate']:
                active_alerts.append({
                    'type': 'high_block_rate',
                    'severity': 'warning',
                    'message': f"Block rate is {block_rate:.1%} (threshold: {self.thresholds['block_rate']:.1%})",
                    'value': block_rate,
                })

        # Check success rate
        success_rate = self.collector.get_success_rate()
        if success_rate < self.thresholds['success_rate']:
            active_alerts.append({
                'type': 'low_success_rate',
                'severity': 'critical',
                'message': f"Success rate is {success_rate:.1%} (threshold: {self.thresholds['success_rate']:.1%})",
                'value': success_rate,
            })

        self.alerts = active_alerts
        return active_alerts

    def display_alerts(self):
        """
        Display active alerts
        """
        alerts = self.check_alerts()

        if not alerts:
            print("✅ No active alerts")
            return

        print(f"\n⚠️  ACTIVE ALERTS ({len(alerts)}):")
        for alert in alerts:
            severity_icon = "🔴" if alert['severity'] == 'critical' else "⚠️"
            print(f"{severity_icon} [{alert['severity'].upper()}] {alert['message']}")


if __name__ == "__main__":
    # Example usage
    collector = MetricsCollector()

    # Simulate some events
    collector.record_routing_decision("ui-implementer", "full_feature", 12.5)
    collector.record_prerequisite_check("ui-implementer", True)
    collector.record_completion_verification("ui-implementer", True)

    collector.record_routing_decision("feature-logic-implementer", "backend_only", 8.3)
    collector.record_prerequisite_check("feature-logic-implementer", False, ["types.ts", "api.ts"])

    collector.record_file_operation(
        "feature-logic-implementer",
        "create",
        "app/feature/api.ts",
        False,
        "FORBIDDEN: Cannot create api.ts"
    )

    # Display dashboard
    dashboard = Dashboard(collector)
    dashboard.display()

    # Check alerts
    alert_system = AlertSystem(collector)
    alert_system.display_alerts()

    # Export metrics
    collector.export_metrics(Path("metrics.json"))
    print("✅ Metrics exported to metrics.json")

    # Generate report
    report = dashboard.generate_report(Path("report.txt"))
    print("✅ Report generated to report.txt")
