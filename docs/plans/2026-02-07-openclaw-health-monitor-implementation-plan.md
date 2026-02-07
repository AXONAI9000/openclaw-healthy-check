# OpenClaw Health Monitor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone Python daemon for macOS that monitors OpenClaw health and pushes single-shot Telegram alerts on failure/recovery.

**Architecture:** A small `oc_healthd` package runs a 30-second loop, executes layered probes (`health`, `status`, `system`), updates consecutive-failure counters, transitions `HEALTHY/UNHEALTHY`, notifies Telegram, and persists JSON state/logs. `launchd` manages process lifecycle.

**Tech Stack:** Python 3.11+ stdlib (`tomllib`, `subprocess`, `urllib`, `socket`, `json`, `unittest`), launchd plist, TOML config.

---

### Task 1: Project Skeleton and Config Parsing

**Files:**
- Create: `src/oc_healthd/__init__.py`
- Create: `src/oc_healthd/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
def test_load_config_from_toml_and_env_override(self):
    cfg = load_config(path)
    self.assertEqual(cfg.monitor.interval_seconds, 30)
    self.assertEqual(cfg.telegram.bot_token, "env-token")
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError` / missing `load_config`.

**Step 3: Write minimal implementation**

```python
def load_config(path: str) -> AppConfig:
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_config.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_config.py src/oc_healthd/config.py src/oc_healthd/__init__.py
git commit -m "feat: add config loader for health daemon"
```

### Task 2: Probe Execution and Normalized Results

**Files:**
- Create: `src/oc_healthd/checks.py`
- Create: `tests/test_checks.py`

**Step 1: Write the failing test**

```python
def test_health_check_nonzero_exit_marks_failure(self):
    result = check_openclaw_health(...)
    self.assertFalse(result.ok)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_checks.py -v`
Expected: FAIL due to missing check functions.

**Step 3: Write minimal implementation**

```python
def check_openclaw_health(...):
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_checks.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_checks.py src/oc_healthd/checks.py
git commit -m "feat: implement layered health checks"
```

### Task 3: State Machine and Transition Logic

**Files:**
- Create: `src/oc_healthd/state_machine.py`
- Create: `src/oc_healthd/state_store.py`
- Create: `tests/test_state_machine.py`

**Step 1: Write the failing test**

```python
def test_transition_to_unhealthy_after_threshold(self):
    transition = machine.apply(results)
    self.assertEqual(transition, "entered_unhealthy")
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_state_machine.py -v`
Expected: FAIL due to missing state machine.

**Step 3: Write minimal implementation**

```python
class MonitorStateMachine:
    def apply(...):
        ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_state_machine.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_state_machine.py src/oc_healthd/state_machine.py src/oc_healthd/state_store.py
git commit -m "feat: add monitor state machine and persistence"
```

### Task 4: Telegram Notifier and Daemon Loop

**Files:**
- Create: `src/oc_healthd/notifier.py`
- Create: `src/oc_healthd/daemon.py`
- Create: `src/oc_healthd/main.py`
- Create: `tests/test_daemon.py`

**Step 1: Write the failing test**

```python
def test_daemon_sends_alert_once_then_recovery_once(self):
    daemon.run_cycle(...)
    self.assertEqual(len(sent_messages), 2)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_daemon.py -v`
Expected: FAIL due to missing daemon/notifier wiring.

**Step 3: Write minimal implementation**

```python
class HealthDaemon:
    def run_cycle(self):
        ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_daemon.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_daemon.py src/oc_healthd/notifier.py src/oc_healthd/daemon.py src/oc_healthd/main.py
git commit -m "feat: wire daemon loop and telegram notifications"
```

### Task 5: Packaging, launchd, and Smoke Validation

**Files:**
- Create: `config.example.toml`
- Create: `deploy/com.openclaw.healthd.plist`
- Create: `scripts/healthctl`
- Create: `README.md`

**Step 1: Write the failing test**

```python
def test_example_config_contains_required_keys(self):
    self.assertIn("interval_seconds", content)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_assets.py -v`
Expected: FAIL because files do not exist.

**Step 3: Write minimal implementation**

```text
Add concrete example config, launchd plist template, and ops commands.
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest -v`
Expected: PASS all tests.

**Step 5: Commit**

```bash
git add README.md config.example.toml deploy/com.openclaw.healthd.plist scripts/healthctl
git commit -m "chore: add deploy assets and usage docs"
```
