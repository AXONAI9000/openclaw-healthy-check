import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from oc_healthd.checks import (  # noqa: E402
    check_openclaw_health,
    check_openclaw_status,
    check_system_probe,
)


class CheckTests(unittest.TestCase):
    def test_health_check_nonzero_exit_marks_failure(self) -> None:
        def runner(_command: str, _timeout: int) -> SimpleNamespace:
            return SimpleNamespace(returncode=2, stdout="", stderr="gateway down")

        result = check_openclaw_health("openclaw health --json", 5, runner)
        self.assertFalse(result.ok)
        self.assertEqual(result.code, 2)
        self.assertIn("gateway down", result.reason)

    def test_health_check_ok_false_marks_failure(self) -> None:
        def runner(_command: str, _timeout: int) -> SimpleNamespace:
            return SimpleNamespace(returncode=0, stdout='{"ok": false}', stderr="")

        result = check_openclaw_health("openclaw health --json", 5, runner)
        self.assertFalse(result.ok)
        self.assertIn("ok=false", result.reason)

    def test_status_check_parses_stdout(self) -> None:
        def runner(_command: str, _timeout: int) -> SimpleNamespace:
            return SimpleNamespace(returncode=0, stdout="status good", stderr="")

        result = check_openclaw_status("openclaw status --deep", 5, runner)
        self.assertTrue(result.ok)
        self.assertEqual(result.raw_excerpt, "status good")

    def test_system_probe_dns_failure_marks_failure(self) -> None:
        def resolver(_host: str) -> str:
            raise OSError("no dns")

        result = check_system_probe(
            dns_host="api.telegram.org",
            tcp_host="1.1.1.1",
            tcp_port=53,
            timeout_seconds=3,
            resolver=resolver,
            connector=lambda *_args, **_kwargs: None,
        )
        self.assertFalse(result.ok)
        self.assertIn("dns", result.reason.lower())


if __name__ == "__main__":
    unittest.main()
