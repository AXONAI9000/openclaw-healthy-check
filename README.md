# OpenClaw Health Daemon (Standalone)

OpenClaw 假死、掉线、进程挂掉时，这个守护进程会先发现，再通过 Telegram 直接通知你。

## Repository Description

Standalone macOS watchdog for OpenClaw with strict health checks and Telegram alerts (single alert on failure, single alert on recovery).

## What It Does

- 每 30 秒执行一次三层检查:
- `openclaw health --json`
- `openclaw status --deep --json`
- 系统探针（DNS + TCP）
- 严格模式: 任一层连续 3 次失败即判定故障
- 通知降噪: 故障 1 条，恢复 1 条，不刷屏
- 通过 `launchd` 开机自启动

## Requirements

- macOS
- Python 3.9+
- OpenClaw CLI 已安装且可执行（建议在 `/opt/homebrew/bin/openclaw`）
- Telegram Bot Token + Telegram Chat ID

## Quick Start

1. 克隆仓库并进入目录
2. 创建配置文件

```bash
cp config.example.toml config.toml
```

3. 编辑 `config.toml`，填入:
- `telegram.bot_token`
- `telegram.chat_id`

4. 先跑一轮自检

```bash
PYTHONPATH=src python3 -m oc_healthd.main --config config.toml --once
```

5. 前台运行（调试）

```bash
PYTHONPATH=src python3 -m oc_healthd.main --config config.toml
```

## Run As LaunchAgent (Recommended)

1. 编辑 `deploy/com.openclaw.healthd.plist`，确认:
- `ProgramArguments` 中 `--config` 路径正确
- `WorkingDirectory` 正确
- `PYTHONPATH` 正确

2. 安装并启动

```bash
mkdir -p ~/Library/LaunchAgents
cp deploy/com.openclaw.healthd.plist ~/Library/LaunchAgents/
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.healthd.plist >/dev/null 2>&1 || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.openclaw.healthd.plist
launchctl kickstart -k gui/$(id -u)/com.openclaw.healthd
```

3. 查看状态和日志

```bash
launchctl print gui/$(id -u)/com.openclaw.healthd | head -n 40
./scripts/healthctl status
./scripts/healthctl logs 50
```

## Alert Rules

- `HEALTHY -> UNHEALTHY`: 首次故障时发 1 条 Telegram
- `UNHEALTHY -> HEALTHY`: 完全恢复时发 1 条 Telegram
- 非状态跃迁不发送通知

## Development

运行测试:

```bash
python3 -m unittest discover -s tests -v
```

## Security Notes

- 不要提交真实 `config.toml`（已在 `.gitignore`）
- 建议将 token 放在环境变量，并在泄露后立刻轮换
