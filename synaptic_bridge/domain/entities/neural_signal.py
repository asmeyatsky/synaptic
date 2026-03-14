"""
Neural Signal Entity

Represents raw neural signal data acquired from BCI hardware.
Immutable domain model following skill2026.md Rule 3.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, UTC
from typing import FrozenSet

from ..events import DomainEvent, SignalAcquiredEvent


@dataclass(frozen=True)
class NeuralSignal:
    id: str
    session_id: str
    channels: FrozenSet[str]
    samples: tuple[tuple[float, ...], ...]
    sampling_rate_hz: float
    timestamp: datetime
    domain_events: tuple[DomainEvent, ...] = field(default=())

    def add_channel(
        self, channel_name: str, new_samples: tuple[float, ...]
    ) -> "NeuralSignal":
        if channel_name in self.channels:
            raise ValueError(f"Channel {channel_name} already exists")

        new_channels = self.channels | {channel_name}
        new_samples_combined = self.samples + (new_samples,)

        return replace(
            self,
            channels=new_channels,
            samples=new_samples_combined,
            domain_events=self.domain_events
            + (
                SignalAcquiredEvent(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(UTC),
                    session_id=self.session_id,
                    channel_count=len(new_channels),
                ),
            ),
        )

    def get_channel_data(self, channel_name: str) -> tuple[float, ...]:
        if channel_name not in self.channels:
            raise ValueError(f"Channel {channel_name} not found")

        channel_index = list(self.channels).index(channel_name)
        return tuple(
            sample[channel_index]
            for sample in self.samples
            if len(sample) > channel_index
        )

    def filter_frequency_band(self, low_hz: float, high_hz: float) -> "NeuralSignal":
        return replace(
            self,
            domain_events=self.domain_events
            + (
                SignalAcquiredEvent(
                    aggregate_id=self.id,
                    occurred_at=datetime.now(UTC),
                    session_id=self.session_id,
                    channel_count=len(self.channels),
                    note=f"Filtered {low_hz}-{high_hz} Hz",
                ),
            ),
        )
