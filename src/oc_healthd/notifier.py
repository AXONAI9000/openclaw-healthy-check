from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, timeout_seconds: int = 10) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout_seconds = timeout_seconds

    def send(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            return False

        endpoint = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }
        body = urllib.parse.urlencode(payload).encode("utf-8")
        request = urllib.request.Request(endpoint, data=body, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
            parsed = json.loads(raw)
            return bool(parsed.get("ok"))
        except (urllib.error.URLError, ValueError, OSError):
            return False

