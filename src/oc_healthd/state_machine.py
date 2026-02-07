from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional

from oc_healthd.checks import CheckResult


@dataclass
class MonitorStateMachine:
    threshold: int
    current_state: str = "HEALTHY"
    counters: Dict[str, int] = field(default_factory=dict)

    def apply(self, results: Iterable[CheckResult]) -> Optional[str]:
        layers_seen = set()
        for result in results:
            layers_seen.add(result.layer)
            if result.ok:
                self.counters[result.layer] = 0
            else:
                self.counters[result.layer] = self.counters.get(result.layer, 0) + 1

        for layer in layers_seen:
            self.counters.setdefault(layer, 0)

        now_unhealthy = any(count >= self.threshold for count in self.counters.values())
        if self.current_state == "HEALTHY" and now_unhealthy:
            self.current_state = "UNHEALTHY"
            return "entered_unhealthy"
        if self.current_state == "UNHEALTHY" and not now_unhealthy:
            self.current_state = "HEALTHY"
            return "recovered"
        return None

