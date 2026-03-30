"""
Prometheus Metrics Service

Lightweight metrics collection for observability.
Provides counters, gauges, and histograms in Prometheus format.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class Counter:
    """Prometheus-style counter metric."""

    name: str
    description: str
    _value: float = 0.0
    _label_values: dict[str, float] = None

    def __post_init__(self):
        if self._label_values is None:
            self._label_values = {}

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment counter by value."""
        if labels:
            label_key = self._labels_key(labels)
            self._label_values[label_key] = self._label_values.get(label_key, 0.0) + value
        else:
            self._value += value

    def _labels_key(self, labels: dict[str, str]) -> str:
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))

    def collect(self) -> list[str]:
        """Collect metric lines in Prometheus format."""
        lines = [f"# HELP {self.name} {self.description}"]
        lines.append(f"# TYPE {self.name} counter")

        if self._value > 0:
            lines.append(f"{self.name} {self._value}")

        for label_str, value in self._label_values.items():
            if value > 0:
                lines.append(f"{self.name}{{{label_str}}} {value}")

        return lines


@dataclass
class Gauge:
    """Prometheus-style gauge metric."""

    name: str
    description: str
    _value: float = 0.0
    _label_values: dict[str, float] = None

    def __post_init__(self):
        if self._label_values is None:
            self._label_values = {}

    def inc(self, value: float = 1.0, **labels: str) -> None:
        """Increment gauge by value."""
        if labels:
            label_key = self._labels_key(labels)
            self._label_values[label_key] = self._label_values.get(label_key, 0.0) + value
        else:
            self._value += value

    def dec(self, value: float = 1.0, **labels: str) -> None:
        """Decrement gauge by value."""
        if labels:
            label_key = self._labels_key(labels)
            self._label_values[label_key] = self._label_values.get(label_key, 0.0) - value
        else:
            self._value -= value

    def set(self, value: float, **labels: str) -> None:
        """Set gauge to value."""
        if labels:
            label_key = self._labels_key(labels)
            self._label_values[label_key] = value
        else:
            self._value = value

    def _labels_key(self, labels: dict[str, str]) -> str:
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))

    def collect(self) -> list[str]:
        """Collect metric lines in Prometheus format."""
        lines = [f"# HELP {self.name} {self.description}"]
        lines.append(f"# TYPE {self.name} gauge")

        lines.append(f"{self.name} {self._value}")

        for label_str, value in self._label_values.items():
            lines.append(f"{self.name}{{{label_str}}} {value}")

        return lines


@dataclass
class Histogram:
    """Prometheus-style histogram metric."""

    name: str
    description: str
    buckets: tuple[float, ...] = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    _count: float = 0.0
    _sum: float = 0.0
    _buckets: dict[float, float] = None
    _labeled_data: dict[str, dict[str, Any]] = None

    def __post_init__(self):
        if self._buckets is None:
            self._buckets = {b: 0.0 for b in self.buckets}
        if self._labeled_data is None:
            self._labeled_data = {}

    def observe(self, value: float, **labels: str) -> None:
        """Observe a value."""
        self._count += 1
        self._sum += value

        for bucket in self.buckets:
            if value <= bucket:
                self._buckets[bucket] = self._buckets.get(bucket, 0.0) + 1

        if labels:
            label_key = self._labels_key(labels)
            if label_key not in self._labeled_data:
                self._labeled_data[label_key] = {
                    "count": 0.0,
                    "sum": 0.0,
                    "buckets": {b: 0.0 for b in self.buckets},
                }
            data = self._labeled_data[label_key]
            data["count"] += 1
            data["sum"] += value
            for bucket in self.buckets:
                if value <= bucket:
                    data["buckets"][bucket] = data["buckets"].get(bucket, 0.0) + 1

    def _labels_key(self, labels: dict[str, str]) -> str:
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))

    def collect(self) -> list[str]:
        """Collect metric lines in Prometheus format."""
        lines = [f"# HELP {self.name} {self.description}"]
        lines.append(f"# TYPE {self.name} histogram")

        cumulative = 0.0
        for bucket in self.buckets:
            cumulative += self._buckets.get(bucket, 0.0)
            lines.append(f'{self.name}_bucket{{le="{bucket}"}} {cumulative}')
        lines.append(f'{self.name}_bucket{{le="+Inf"}} {self._count}')
        lines.append(f"{self.name}_sum {self._sum}")
        lines.append(f"{self.name}_count {self._count}")

        for label_key, data in self._labeled_data.items():
            cum = 0.0
            for bucket in self.buckets:
                cum += data["buckets"].get(bucket, 0.0)
                lines.append(f'{self.name}_bucket{{le="{bucket}",{label_key}}} {cum}')
            lines.append(f'{self.name}_bucket{{le="+Inf",{label_key}}} {data["count"]}')
            lines.append(f"{self.name}_sum{{{label_key}}} {data['sum']}")
            lines.append(f"{self.name}_count{{{label_key}}} {data['count']}")

        return lines


class MetricsRegistry:
    """Central registry for all metrics."""

    _instance: "MetricsRegistry | None" = None

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}

    @classmethod
    def get_instance(cls) -> "MetricsRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def counter(self, name: str, description: str, **labels: str) -> Counter:
        """Get or create a counter."""
        key = f"{name}:{self._labels_key(labels)}"
        if key not in self._counters:
            self._counters[key] = Counter(name, description)
        return self._counters[key]

    def gauge(self, name: str, description: str, **labels: str) -> Gauge:
        """Get or create a gauge."""
        key = f"{name}:{self._labels_key(labels)}"
        if key not in self._gauges:
            self._gauges[key] = Gauge(name, description)
        return self._gauges[key]

    def histogram(
        self, name: str, description: str, buckets: tuple[float, ...] | None = None, **labels: str
    ) -> Histogram:
        """Get or create a histogram."""
        key = f"{name}:{self._labels_key(labels)}"
        if key not in self._histograms:
            self._histograms[key] = Histogram(
                name, description, buckets=buckets if buckets is not None else ()
            )
        return self._histograms[key]

    def _labels_key(self, labels: dict[str, str]) -> str:
        return ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))

    def collect(self) -> str:
        """Collect all metrics in Prometheus format."""
        lines = ["# Prometheus metrics"]

        for counter in self._counters.values():
            lines.extend(counter.collect())

        for gauge in self._gauges.values():
            lines.extend(gauge.collect())

        for histogram in self._histograms.values():
            lines.extend(histogram.collect())

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


registry = MetricsRegistry.get_instance()

synaptic_requests_total = registry.counter(
    "synaptic_requests_total",
    "Total number of requests processed",
)

synaptic_request_duration_seconds = registry.histogram(
    "synaptic_request_duration_seconds",
    "Request duration in seconds",
)

synaptic_tool_executions_total = registry.counter(
    "synaptic_tool_executions_total",
    "Total number of tool executions",
)

synaptic_cle_corrections_total = registry.counter(
    "synaptic_cle_corrections_total",
    "Total number of CLE corrections applied",
)

synaptic_active_sessions = registry.gauge(
    "synaptic_active_sessions",
    "Number of active sessions",
)

synaptic_policy_violations_total = registry.counter(
    "synaptic_policy_violations_total",
    "Total number of policy violations",
)

synaptic_errors_total = registry.counter(
    "synaptic_errors_total",
    "Total number of errors",
)


class TimingContext:
    """Context manager for timing operations."""

    def __init__(self, histogram: Histogram, **labels: str):
        self.histogram = histogram
        self.labels = labels
        self.start_time: float | None = None

    def __enter__(self) -> "TimingContext":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.histogram.observe(duration, **self.labels)
        return False
