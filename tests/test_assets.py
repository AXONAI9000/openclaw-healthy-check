import unittest
from pathlib import Path


class AssetTests(unittest.TestCase):
    def test_example_config_contains_required_keys(self) -> None:
        content = Path("config.example.toml").read_text(encoding="utf-8")
        self.assertIn("interval_seconds", content)
        self.assertIn("failure_threshold", content)
        self.assertIn("health_cmd", content)
        self.assertIn("bot_token", content)

    def test_launchd_template_exists(self) -> None:
        content = Path("deploy/com.openclaw.healthd.plist").read_text(encoding="utf-8")
        self.assertIn("com.openclaw.healthd", content)
        self.assertIn("KeepAlive", content)
        self.assertIn("RunAtLoad", content)


if __name__ == "__main__":
    unittest.main()
