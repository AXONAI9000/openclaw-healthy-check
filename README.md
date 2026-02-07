# OpenClaw Health Daemon (Standalone)

Standalone monitor for OpenClaw on macOS. It checks OpenClaw and system health every 30 seconds, uses a 3-failure threshold, and sends Telegram alerts once on failure and once on recovery.

## Features

- Independent process managed by `launchd`
- Layered checks:
  - `openclaw health --json`
  - `openclaw status --deep`
  - system DNS + TCP probe
- Strict mode: any layer reaches threshold => `UNHEALTHY`
- Anti-spam notifications: one failure alert, one recovery alert

## Quick Start

1. Create config from example:

```bash
cp config.example.toml config.toml
```

2. Set Telegram secrets (recommended):

```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

3. Run one cycle:

```bash
PYTHONPATH=src python3 -m oc_healthd.main --config config.toml --once
```

4. Run daemon in foreground:

```bash
PYTHONPATH=src python3 -m oc_healthd.main --config config.toml
```

## launchd

1. Copy and adjust `deploy/com.openclaw.healthd.plist` paths/secrets.
2. Install agent:

```bash
mkdir -p ~/Library/LaunchAgents
cp deploy/com.openclaw.healthd.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.openclaw.healthd.plist
```

3. Check runtime status:

```bash
./scripts/healthctl status
./scripts/healthctl logs 50
```

## Tests

```bash
python3 -m unittest -v
```

