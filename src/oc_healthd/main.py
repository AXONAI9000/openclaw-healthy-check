from __future__ import annotations

import argparse
import time
from typing import Callable, List

from oc_healthd.checks import (
    CheckResult,
    check_openclaw_health,
    check_openclaw_status,
    check_system_probe,
)
from oc_healthd.config import AppConfig, load_config
from oc_healthd.daemon import HealthDaemon
from oc_healthd.notifier import TelegramNotifier
from oc_healthd.restart import CommandRestarter
from oc_healthd.state_store import StateStore


def build_checks(config: AppConfig) -> List[Callable[[], CheckResult]]:
    return [
        lambda: check_openclaw_health(
            config.openclaw.health_cmd,
            config.monitor.timeout_seconds,
        ),
        lambda: check_openclaw_status(
            config.openclaw.status_cmd,
            config.monitor.timeout_seconds,
        ),
        lambda: check_system_probe(
            dns_host=config.system.dns_host,
            tcp_host=config.system.tcp_host,
            tcp_port=config.system.tcp_port,
            timeout_seconds=config.monitor.timeout_seconds,
        ),
    ]


def run(config_path: str, once: bool = False) -> int:
    config = load_config(config_path)
    notifier = TelegramNotifier(
        bot_token=config.telegram.bot_token,
        chat_id=config.telegram.chat_id,
        timeout_seconds=config.monitor.timeout_seconds,
    )
    restarter = CommandRestarter(
        command=config.openclaw.restart_cmd,
        timeout_seconds=config.monitor.timeout_seconds,
    )
    daemon = HealthDaemon(
        threshold=config.monitor.failure_threshold,
        checks=build_checks(config),
        notifier=notifier,
        restarter=restarter,
        state_store=StateStore(config.paths.state_file),
        log_file=config.paths.log_file,
    )
    if once:
        daemon.run_cycle()
        return 0

    try:
        while True:
            daemon.run_cycle()
            time.sleep(config.monitor.interval_seconds)
    except KeyboardInterrupt:
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw standalone health monitor")
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to config file (default: config.toml)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run exactly one cycle and exit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(config_path=args.config, once=bool(args.once))


if __name__ == "__main__":
    raise SystemExit(main())
