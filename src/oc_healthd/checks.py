from __future__ import annotations

import json
import shlex
import socket
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class CheckResult:
    layer: str
    ok: bool
    reason: str
    code: int
    latency_ms: int
    raw_excerpt: str


Runner = Callable[[str, int], subprocess.CompletedProcess]
Resolver = Callable[[str], str]
Connector = Callable[..., object]


def run_command(command: str, timeout_seconds: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        shlex.split(command),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def _excerpt(text: str, limit: int = 300) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[:limit]


def _ms(start: float) -> int:
    return int((time.monotonic() - start) * 1000)


def check_openclaw_health(
    command: str,
    timeout_seconds: int,
    runner: Runner = run_command,
) -> CheckResult:
    started = time.monotonic()
    try:
        completed = runner(command, timeout_seconds)
    except subprocess.TimeoutExpired:
        return CheckResult(
            layer="openclaw_health",
            ok=False,
            reason="health command timeout",
            code=124,
            latency_ms=_ms(started),
            raw_excerpt="",
        )
    except FileNotFoundError as error:
        return CheckResult(
            layer="openclaw_health",
            ok=False,
            reason=f"health command missing: {error}",
            code=127,
            latency_ms=_ms(started),
            raw_excerpt="",
        )
    except Exception as error:  # pragma: no cover - defensive path
        return CheckResult(
            layer="openclaw_health",
            ok=False,
            reason=f"health command error: {error}",
            code=1,
            latency_ms=_ms(started),
            raw_excerpt="",
        )

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if completed.returncode != 0:
        reason = _excerpt(stderr or stdout or "health command failed")
        return CheckResult(
            layer="openclaw_health",
            ok=False,
            reason=reason,
            code=completed.returncode,
            latency_ms=_ms(started),
            raw_excerpt=_excerpt(stdout or stderr),
        )

    parsed: Optional[dict] = None
    if stdout.strip():
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    if isinstance(parsed, dict) and parsed.get("ok") is False:
        return CheckResult(
            layer="openclaw_health",
            ok=False,
            reason="health payload ok=false",
            code=0,
            latency_ms=_ms(started),
            raw_excerpt=_excerpt(stdout),
        )

    return CheckResult(
        layer="openclaw_health",
        ok=True,
        reason="ok",
        code=completed.returncode,
        latency_ms=_ms(started),
        raw_excerpt=_excerpt(stdout),
    )


def check_openclaw_status(
    command: str,
    timeout_seconds: int,
    runner: Runner = run_command,
) -> CheckResult:
    started = time.monotonic()
    try:
        completed = runner(command, timeout_seconds)
    except subprocess.TimeoutExpired:
        return CheckResult(
            layer="openclaw_status",
            ok=False,
            reason="status command timeout",
            code=124,
            latency_ms=_ms(started),
            raw_excerpt="",
        )
    except FileNotFoundError as error:
        return CheckResult(
            layer="openclaw_status",
            ok=False,
            reason=f"status command missing: {error}",
            code=127,
            latency_ms=_ms(started),
            raw_excerpt="",
        )
    except Exception as error:  # pragma: no cover - defensive path
        return CheckResult(
            layer="openclaw_status",
            ok=False,
            reason=f"status command error: {error}",
            code=1,
            latency_ms=_ms(started),
            raw_excerpt="",
        )

    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    ok = completed.returncode == 0
    reason = "ok" if ok else _excerpt(stderr or stdout or "status command failed")

    return CheckResult(
        layer="openclaw_status",
        ok=ok,
        reason=reason,
        code=completed.returncode,
        latency_ms=_ms(started),
        raw_excerpt=_excerpt(stdout or stderr),
    )


def check_system_probe(
    dns_host: str,
    tcp_host: str,
    tcp_port: int,
    timeout_seconds: int,
    resolver: Resolver = socket.gethostbyname,
    connector: Connector = socket.create_connection,
) -> CheckResult:
    started = time.monotonic()
    try:
        resolver(dns_host)
    except Exception as error:
        return CheckResult(
            layer="system_probe",
            ok=False,
            reason=f"dns probe failed: {error}",
            code=1,
            latency_ms=_ms(started),
            raw_excerpt="",
        )

    try:
        conn = connector((tcp_host, tcp_port), timeout_seconds)
        close_fn = getattr(conn, "close", None)
        if callable(close_fn):
            close_fn()
    except Exception as error:
        return CheckResult(
            layer="system_probe",
            ok=False,
            reason=f"tcp probe failed: {error}",
            code=1,
            latency_ms=_ms(started),
            raw_excerpt="",
        )

    return CheckResult(
        layer="system_probe",
        ok=True,
        reason="ok",
        code=0,
        latency_ms=_ms(started),
        raw_excerpt=f"dns={dns_host} tcp={tcp_host}:{tcp_port}",
    )

