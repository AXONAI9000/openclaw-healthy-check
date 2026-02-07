import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from oc_healthd.restart import CommandRestarter  # noqa: E402


class RestartTests(unittest.TestCase):
    def test_restart_returns_success_on_zero_exit(self) -> None:
        calls = []

        def runner(command: str, timeout: int) -> SimpleNamespace:
            calls.append((command, timeout))
            return SimpleNamespace(returncode=0, stdout="done", stderr="")

        restarter = CommandRestarter(
            command="openclaw gateway restart",
            timeout_seconds=8,
            runner=runner,
        )
        ok, note = restarter.restart()

        self.assertTrue(ok)
        self.assertIn("done", note)
        self.assertEqual(calls, [("openclaw gateway restart", 8)])


if __name__ == "__main__":
    unittest.main()
