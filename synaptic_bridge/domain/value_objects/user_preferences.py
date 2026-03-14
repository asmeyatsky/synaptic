"""
User Preferences Value Object

Immutable value object representing user settings and preferences.
Following skill2026.md Rule 3 - Immutable Domain Models.
"""

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class UserPreferences:
    sampling_rate_hz: float = 250.0
    enabled_channels: FrozenSet[str] = frozenset()
    classification_threshold: float = 0.7
    auto_connect_devices: bool = True
    notifications_enabled: bool = True
    signal_quality_alerts: bool = True
    data_retention_days: int = 30

    def with_sampling_rate(self, rate: float) -> "UserPreferences":
        if rate <= 0:
            raise ValueError("Sampling rate must be positive")
        return UserPreferences(
            sampling_rate_hz=rate,
            enabled_channels=self.enabled_channels,
            classification_threshold=self.classification_threshold,
            auto_connect_devices=self.auto_connect_devices,
            notifications_enabled=self.notifications_enabled,
            signal_quality_alerts=self.signal_quality_alerts,
            data_retention_days=self.data_retention_days,
        )

    def with_threshold(self, threshold: float) -> "UserPreferences":
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return UserPreferences(
            sampling_rate_hz=self.sampling_rate_hz,
            enabled_channels=self.enabled_channels,
            classification_threshold=threshold,
            auto_connect_devices=self.auto_connect_devices,
            notifications_enabled=self.notifications_enabled,
            signal_quality_alerts=self.signal_quality_alerts,
            data_retention_days=self.data_retention_days,
        )
