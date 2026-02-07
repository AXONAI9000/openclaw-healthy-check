from __future__ import annotations

import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - runtime fallback for Python < 3.11
    tomllib = None  # type: ignore[assignment]


@dataclass(frozen=True)
class MonitorConfig:
    interval_seconds: int = 30
    failure_threshold: int = 3
    timeout_seconds: int = 10


@dataclass(frozen=True)
class OpenClawConfig:
    health_cmd: str = "openclaw health --json"
    status_cmd: str = "openclaw status --deep"


@dataclass(frozen=True)
class SystemConfig:
    dns_host: str = "api.telegram.org"
    tcp_host: str = "1.1.1.1"
    tcp_port: int = 53


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str = ""
    chat_id: str = ""


@dataclass(frozen=True)
class PathsConfig:
    log_file: str = "logs/healthd.jsonl"
    state_file: str = "logs/state.json"


@dataclass(frozen=True)
class AppConfig:
    monitor: MonitorConfig
    openclaw: OpenClawConfig
    system: SystemConfig
    telegram: TelegramConfig
    paths: PathsConfig


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _load_raw_data(path: str) -> Dict[str, Any]:
    content_text = Path(path).read_text(encoding="utf-8")
    if tomllib is not None:
        return tomllib.loads(content_text)

    parser = configparser.ConfigParser()
    parser.read_string(content_text)
    data: Dict[str, Any] = {}
    for section in parser.sections():
        section_data: Dict[str, Any] = {}
        for key, raw_value in parser.items(section):
            section_data[key] = _strip_quotes(raw_value)
        data[section] = section_data
    return data


def load_config(path: str) -> AppConfig:
    data = _load_raw_data(path)

    monitor = _as_dict(data.get("monitor"))
    openclaw = _as_dict(data.get("openclaw"))
    system = _as_dict(data.get("system"))
    telegram = _as_dict(data.get("telegram"))
    paths = _as_dict(data.get("paths"))

    monitor_cfg = MonitorConfig(
        interval_seconds=int(monitor.get("interval_seconds", 30)),
        failure_threshold=int(monitor.get("failure_threshold", 3)),
        timeout_seconds=int(monitor.get("timeout_seconds", 10)),
    )
    openclaw_cfg = OpenClawConfig(
        health_cmd=str(openclaw.get("health_cmd", "openclaw health --json")),
        status_cmd=str(openclaw.get("status_cmd", "openclaw status --deep")),
    )
    system_cfg = SystemConfig(
        dns_host=str(system.get("dns_host", "api.telegram.org")),
        tcp_host=str(system.get("tcp_host", "1.1.1.1")),
        tcp_port=int(system.get("tcp_port", 53)),
    )
    telegram_cfg = TelegramConfig(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN", str(telegram.get("bot_token", ""))),
        chat_id=os.getenv("TELEGRAM_CHAT_ID", str(telegram.get("chat_id", ""))),
    )
    paths_cfg = PathsConfig(
        log_file=str(paths.get("log_file", "logs/healthd.jsonl")),
        state_file=str(paths.get("state_file", "logs/state.json")),
    )

    return AppConfig(
        monitor=monitor_cfg,
        openclaw=openclaw_cfg,
        system=system_cfg,
        telegram=telegram_cfg,
        paths=paths_cfg,
    )
