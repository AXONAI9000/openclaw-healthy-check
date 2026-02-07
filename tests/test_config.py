import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from oc_healthd.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_from_toml_and_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    [monitor]
                    interval_seconds = 30
                    failure_threshold = 3
                    timeout_seconds = 10

                    [openclaw]
                    health_cmd = "openclaw health --json"
                    status_cmd = "openclaw status --deep"

                    [system]
                    dns_host = "api.telegram.org"

                    [telegram]
                    bot_token = "file-token"
                    chat_id = "12345"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            os.environ["TELEGRAM_BOT_TOKEN"] = "env-token"
            os.environ["TELEGRAM_CHAT_ID"] = "env-chat"
            try:
                config = load_config(str(config_path))
            finally:
                os.environ.pop("TELEGRAM_BOT_TOKEN", None)
                os.environ.pop("TELEGRAM_CHAT_ID", None)

        self.assertEqual(config.monitor.interval_seconds, 30)
        self.assertEqual(config.monitor.failure_threshold, 3)
        self.assertEqual(config.telegram.bot_token, "env-token")
        self.assertEqual(config.telegram.chat_id, "env-chat")


if __name__ == "__main__":
    unittest.main()
