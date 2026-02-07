from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Protocol

from oc_healthd.checks import CheckResult
from oc_healthd.state_machine import MonitorStateMachine
from oc_healthd.state_store import StateStore


class Notifier(Protocol):
    def send(self, message: str) -> bool:
        ...


class Restarter(Protocol):
    def restart(self) -> tuple[bool, str]:
        ...


CheckRunner = Callable[[], CheckResult]


class HealthDaemon:
    def __init__(
        self,
        threshold: int,
        checks: Iterable[CheckRunner],
        notifier: Notifier,
        state_store: StateStore,
        log_file: str,
        restarter: Optional[Restarter] = None,
    ) -> None:
        self.notifier = notifier
        self.restarter = restarter
        self.state_store = state_store
        self.log_file = Path(log_file)
        self.checks = list(checks)
        persisted = self.state_store.load()
        self.machine = MonitorStateMachine(
            threshold=threshold,
            current_state=str(persisted.get("state", "HEALTHY")),
            counters={
                str(key): int(value)
                for key, value in dict(persisted.get("counters", {})).items()
            },
        )

    def run_cycle(self) -> str:
        results: List[CheckResult] = [check() for check in self.checks]
        transition = self.machine.apply(results)
        notified = False
        restart_attempted = False
        restart_ok = False
        message = ""

        if transition == "entered_unhealthy":
            restart_attempted, restart_ok, restart_note = self._maybe_restart(results)
            message = self._build_unhealthy_message(results)
            if restart_attempted:
                status = "ok" if restart_ok else "failed"
                message = f"{message}\nAuto-restart: {status} ({restart_note})"
            notified = self.notifier.send(message)
        elif transition == "recovered":
            message = self._build_recovered_message(results)
            notified = self.notifier.send(message)

        self.state_store.save(
            {
                "state": self.machine.current_state,
                "counters": self.machine.counters,
            }
        )
        self._append_log(
            results=results,
            transition=transition or "steady",
            notified=notified,
            message=message,
            restart_attempted=restart_attempted,
            restart_ok=restart_ok,
        )
        return transition or "steady"

    def _maybe_restart(self, results: List[CheckResult]) -> tuple[bool, bool, str]:
        if self.restarter is None:
            return False, False, "restarter disabled"
        if not self._has_openclaw_failure(results):
            return False, False, "no openclaw failure"
        ok, note = self.restarter.restart()
        return True, ok, note

    @staticmethod
    def _has_openclaw_failure(results: List[CheckResult]) -> bool:
        for result in results:
            if result.layer in {"openclaw_health", "openclaw_status"} and not result.ok:
                return True
        return False

    def _build_unhealthy_message(self, results: List[CheckResult]) -> str:
        failing = [item for item in results if not item.ok]
        primary = failing[0] if failing else results[0]
        return (
            "[OpenClaw Alert] UNHEALTHY\n"
            f"Time: {self._now()}\n"
            f"Reason: {primary.layer} - {primary.reason}\n"
            f"Code: {primary.code}"
        )

    def _build_recovered_message(self, results: List[CheckResult]) -> str:
        summary = ", ".join(f"{item.layer}=ok" for item in results)
        return (
            "[OpenClaw Alert] RECOVERED\n"
            f"Time: {self._now()}\n"
            f"Checks: {summary}"
        )

    def _append_log(
        self,
        results: List[CheckResult],
        transition: str,
        notified: bool,
        message: str,
        restart_attempted: bool,
        restart_ok: bool,
    ) -> None:
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": self._now(),
            "state": self.machine.current_state,
            "transition": transition,
            "notified": notified,
            "restart_attempted": restart_attempted,
            "restart_ok": restart_ok,
            "message_preview": message[:180],
            "counters": self.machine.counters,
            "results": [asdict(result) for result in results],
        }
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
