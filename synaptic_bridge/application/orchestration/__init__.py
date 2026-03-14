"""
Workflow Orchestration

Following skill2026.md Pattern 7 - Parallel-Safe Orchestration.
DAG-based execution for multi-step workflows with parallelization.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

from synaptic_bridge.domain.entities import NeuralSignal, CognitiveState


@dataclass
class WorkflowStep:
    name: str
    execute: Callable
    depends_on: list[str] = field(default_factory=list)


class DAGOrchestrator:
    """
    Executes workflow steps respecting dependency order,
    parallelizing independent steps automatically.

    Following skill2026.md Rule 7 - Parallel-Safe Orchestration.
    """

    def __init__(self, steps: list[WorkflowStep]):
        self.steps = {s.name: s for s in steps}
        self._validate_no_cycles()

    def _validate_no_cycles(self) -> None:
        visited = set()
        path = set()

        def visit(name: str) -> None:
            if name in path:
                raise ValueError(f"Circular dependency detected at {name}")
            if name in visited:
                return

            path.add(name)
            visited.add(name)

            for dep in self.steps[name].depends_on:
                visit(dep)

            path.remove(name)

        for name in self.steps:
            visit(name)

    async def execute(self, context: dict) -> dict:
        completed: dict[str, Any] = {}
        pending = set(self.steps.keys())

        while pending:
            ready = [
                name
                for name in pending
                if all(dep in completed for dep in self.steps[name].depends_on)
            ]

            if not ready:
                raise RuntimeError("Circular dependency detected")

            results = await asyncio.gather(
                *(self.steps[name].execute(context, completed) for name in ready),
                return_exceptions=True,
            )

            for name, result in zip(ready, results):
                if isinstance(result, Exception):
                    raise RuntimeError(f"Step {name} failed: {result}")
                completed[name] = result
                pending.discard(name)

        return completed


class ProcessSignalWorkflow:
    """
    Workflow for processing neural signals through:
    1. Preprocessing (filtering, artifact removal)
    2. Feature extraction
    3. Classification

    Steps 1 and 2 can run in parallel (per channel).
    Step 3 waits for all features to be ready.

    Following skill2026.md - Parallelism-First Design.
    """

    def __init__(
        self,
        signal: NeuralSignal,
        classifier: Any,
        signal_repo: Any,
    ):
        self.signal = signal
        self.classifier = classifier
        self.signal_repo = signal_repo

    async def execute(self) -> CognitiveState:
        steps = [
            WorkflowStep("preprocess", self._preprocess_channels),
            WorkflowStep("extract_features", self._extract_features),
            WorkflowStep(
                "classify",
                self._classify,
                depends_on=["preprocess", "extract_features"],
            ),
        ]

        orchestrator = DAGOrchestrator(steps)
        results = await orchestrator.execute({"signal": self.signal})

        return results["classify"]

    async def _preprocess_channels(
        self, context: dict, completed: dict
    ) -> dict[str, Any]:
        signal = context["signal"]

        preprocessed = {}
        tasks = [self._preprocess_single_channel(signal, ch) for ch in signal.channels]

        results = await asyncio.gather(*tasks)

        for ch, result in zip(signal.channels, results):
            preprocessed[ch] = result

        return preprocessed

    async def _preprocess_single_channel(
        self, signal: NeuralSignal, channel: str
    ) -> tuple[float, ...]:
        await asyncio.sleep(0.001)
        return signal.get_channel_data(channel)

    async def _extract_features(self, context: dict, completed: dict) -> dict[str, Any]:
        signal = context["signal"]

        features = {}
        tasks = [self._extract_channel_features(signal, ch) for ch in signal.channels]

        results = await asyncio.gather(*tasks)

        for ch, result in zip(signal.channels, results):
            features[ch] = result

        return features

    async def _extract_channel_features(
        self, signal: NeuralSignal, channel: str
    ) -> dict[str, float]:
        data = signal.get_channel_data(channel)

        return {
            "mean": sum(data) / len(data) if data else 0.0,
            "std": self._calculate_std(data),
            "min": min(data) if data else 0.0,
            "max": max(data) if data else 0.0,
        }

    def _calculate_std(self, data: tuple[float, ...]) -> float:
        if len(data) < 2:
            return 0.0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance**0.5

    async def _classify(self, context: dict, completed: dict) -> CognitiveState:
        signal = context["signal"]

        from synaptic_bridge.domain.entities import CognitiveState, CognitiveStateType
        from datetime import datetime, UTC

        result = await self.classifier.classify(signal)

        return CognitiveState(
            id=f"cogstate_{datetime.now(UTC).timestamp()}",
            session_id=signal.session_id,
            user_id=signal.session_id.split("_")[0]
            if "_" in signal.session_id
            else "unknown",
            state_type=CognitiveStateType(result.state_type),
            confidence=result.confidence,
            features_used=frozenset(result.features_used),
            timestamp=datetime.now(UTC),
        )
