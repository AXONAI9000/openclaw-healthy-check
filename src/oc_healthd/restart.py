from __future__ import annotations

import shlex
import subprocess
from typing import Callable, Tuple


Runner = Callable[[str, int], subprocess.CompletedProcess]


def run_command(command: str, timeout_seconds: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        shlex.split(command),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def _excerpt(text: str, limit: int = 220) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[:limit]


class CommandRestarter:
    def __init__(
        self,
        command: str,
        timeout_seconds: int,
        runner: Runner = run_command,
    ) -> None:
        self.command = command
        self.timeout_seconds = timeout_seconds
        self.runner = runner

    def restart(self) -> Tuple[bool, str]:
        try:
            completed = self.runner(self.command, self.timeout_seconds)
        except subprocess.TimeoutExpired:
            return False, "restart timeout"
        except FileNotFoundError as error:
            return False, f"restart command missing: {error}"
        except Exception as error:  # pragma: no cover - defensive path
            return False, f"restart error: {error}"

        output = _excerpt(completed.stdout or completed.stderr or "")
        if completed.returncode == 0:
            return True, output or "restart ok"
        return False, output or f"restart exit={completed.returncode}"

