import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from oc_healthd.checks import CheckResult  # noqa: E402
from oc_healthd.daemon import HealthDaemon  # noqa: E402
from oc_healthd.state_store import StateStore  # noqa: E402


class MemoryNotifier:
    def __init__(self) -> None:
        self.messages = []

    def send(self, message: str) -> bool:
        self.messages.append(message)
        return True


class MemoryRestarter:
    def __init__(self) -> None:
        self.calls = 0

    def restart(self) -> tuple[bool, str]:
        self.calls += 1
        return True, "restart ok"


class DaemonTests(unittest.TestCase):
    def test_daemon_sends_alert_once_then_recovery_once(self) -> None:
        failing = CheckResult("openclaw_health", False, "down", 1, 1, "")
        healthy = CheckResult("openclaw_health", True, "ok", 0, 1, "")
        # 3 failures trigger alert, recovery triggers recovered message.
        timeline = [failing, failing, failing, failing, healthy, healthy]
        cursor = {"idx": 0}

        def check() -> CheckResult:
            idx = cursor["idx"]
            if idx >= len(timeline):
                return healthy
            cursor["idx"] = idx + 1
            return timeline[idx]

        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(str(Path(tmpdir) / "state.json"))
            notifier = MemoryNotifier()
            restarter = MemoryRestarter()
            daemon = HealthDaemon(
                threshold=3,
                checks=[check],
                notifier=notifier,
                restarter=restarter,
                state_store=state_store,
                log_file=str(Path(tmpdir) / "healthd.jsonl"),
            )
            for _ in range(6):
                daemon.run_cycle()

        self.assertEqual(len(notifier.messages), 2)
        self.assertIn("UNHEALTHY", notifier.messages[0])
        self.assertIn("RECOVERED", notifier.messages[1])
        self.assertEqual(restarter.calls, 1)

    def test_daemon_does_not_restart_when_only_system_probe_fails(self) -> None:
        failing = CheckResult("system_probe", False, "dns down", 1, 1, "")
        healthy = CheckResult("system_probe", True, "ok", 0, 1, "")
        timeline = [failing, failing, failing, healthy]
        cursor = {"idx": 0}

        def check() -> CheckResult:
            idx = cursor["idx"]
            if idx >= len(timeline):
                return healthy
            cursor["idx"] = idx + 1
            return timeline[idx]

        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(str(Path(tmpdir) / "state.json"))
            notifier = MemoryNotifier()
            restarter = MemoryRestarter()
            daemon = HealthDaemon(
                threshold=3,
                checks=[check],
                notifier=notifier,
                restarter=restarter,
                state_store=state_store,
                log_file=str(Path(tmpdir) / "healthd.jsonl"),
            )
            for _ in range(4):
                daemon.run_cycle()

        self.assertEqual(restarter.calls, 0)


if __name__ == "__main__":
    unittest.main()
