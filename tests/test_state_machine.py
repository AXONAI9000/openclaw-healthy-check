import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from oc_healthd.checks import CheckResult  # noqa: E402
from oc_healthd.state_machine import MonitorStateMachine  # noqa: E402
from oc_healthd.state_store import StateStore  # noqa: E402


class StateMachineTests(unittest.TestCase):
    def test_transition_to_unhealthy_after_threshold(self) -> None:
        machine = MonitorStateMachine(threshold=3)
        failing = CheckResult(
            layer="openclaw_health",
            ok=False,
            reason="boom",
            code=1,
            latency_ms=1,
            raw_excerpt="",
        )

        self.assertIsNone(machine.apply([failing]))
        self.assertIsNone(machine.apply([failing]))
        self.assertEqual(machine.apply([failing]), "entered_unhealthy")
        self.assertEqual(machine.current_state, "UNHEALTHY")

    def test_transition_back_to_healthy_after_recovery(self) -> None:
        machine = MonitorStateMachine(threshold=3)
        failing = CheckResult("system_probe", False, "boom", 1, 1, "")
        healthy = CheckResult("system_probe", True, "ok", 0, 1, "")

        machine.apply([failing])
        machine.apply([failing])
        machine.apply([failing])
        self.assertEqual(machine.current_state, "UNHEALTHY")
        self.assertEqual(machine.apply([healthy]), "recovered")
        self.assertEqual(machine.current_state, "HEALTHY")

    def test_state_store_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "state.json"
            store = StateStore(str(state_path))
            store.save({"state": "UNHEALTHY", "counters": {"system_probe": 3}})
            loaded = store.load()
        self.assertEqual(loaded["state"], "UNHEALTHY")
        self.assertEqual(loaded["counters"]["system_probe"], 3)


if __name__ == "__main__":
    unittest.main()
