# OpenClaw 健康监控工具设计

- 日期: 2026-02-07
- 状态: 已确认设计
- 目标: 在 MacBook 上持续监控 OpenClaw 健康状态，并在异常/恢复时通过 Telegram 发送通知

## 1. 背景与目标

OpenClaw 部署在个人 MacBook 上，存在断电、断网、进程异常、CLI 异常等风险。需要一个本地常驻健康监控工具，实现以下目标:

1. 自动识别 OpenClaw 部署形态（Docker/本机进程）。
2. 每 30 秒执行一次健康探测。
3. 采用严格模式，任一监控层连续 3 次失败即判定故障。
4. 故障只告警 1 次，恢复只通知 1 次。
5. 通过 Telegram Bot 推送消息。
6. 支持开机自动启动（launchd）。

## 2. 官方健康标准对齐

根据 OpenClaw 文档:

1. `openclaw health --json` 是官方健康检查主命令，失败时会非零退出。
2. `openclaw status --deep` 适合作为深度诊断信息，不作为唯一主判据。
3. 监控应同时考虑 liveness/readiness 概念（连接可用 + 实际就绪）。

因此本设计将 `health --json` 作为主检查，`status --deep` 作为辅助诊断，系统探针作为第三层判定信号。

## 3. 总体架构

采用单守护进程架构: `oc-healthd`（Python）。

核心流水线:

1. `collect`: 采集各层探测结果。
2. `evaluate`: 更新各层失败计数，计算全局状态。
3. `transition`: 检测状态是否发生 `HEALTHY/UNHEALTHY` 跃迁。
4. `notify`: 触发 Telegram 告警或恢复消息。
5. `persist`: 记录日志与状态快照。

### 3.1 监控层定义

1. OpenClaw 健康层（主判据）
   - 执行 `openclaw health --json`
   - 成功条件: 退出码为 0 且 `ok=true`（若有该字段）
2. OpenClaw 运行态补充层（辅助）
   - 执行 `openclaw status --deep`
   - 主要用于告警消息附加诊断摘要
3. 系统层探针
   - 网络/DNS 连通性
   - 可选电源/系统事件探针（用于解释非服务自身故障）

### 3.2 严格模式判定

1. 每层维护独立 `consecutive_failures` 计数器。
2. 某层本轮失败则计数 +1，成功则归零。
3. 任一层计数达到 3，判定全局 `UNHEALTHY`。
4. 所有层恢复成功（计数清零）后回到 `HEALTHY`。

## 4. 状态机与通知策略

状态机:

1. `HEALTHY -> UNHEALTHY`: 发送 1 条故障通知。
2. `UNHEALTHY -> HEALTHY`: 发送 1 条恢复通知。
3. 其他情况不发送通知（防止重复刷屏）。

消息格式:

1. 标题: `[OpenClaw Alert] UNHEALTHY` 或 `[OpenClaw Alert] RECOVERED`
2. 主因: 首个触发阈值层的失败原因
3. 证据:
   - `health --json` 摘要
   - `status --deep` 摘要
   - 系统探针失败摘要
4. 时间戳: 本地时区绝对时间（例如 `2026-02-07 15:42:10 PST`）
5. 建议动作: 最多 2 条可执行建议

Telegram 发送失败不影响主循环，仅记录错误并重试待发送事件。

## 5. 配置与密钥管理

配置文件采用 TOML（`config.toml`），并允许环境变量覆盖敏感项。

示例配置字段:

1. `interval_seconds = 30`
2. `failure_threshold = 3`
3. `strict_mode = true`
4. `openclaw.health_cmd = "openclaw health --json"`
5. `openclaw.status_cmd = "openclaw status --deep"`
6. `telegram.bot_token`（支持 `TELEGRAM_BOT_TOKEN` 覆盖）
7. `telegram.chat_id`（支持 `TELEGRAM_CHAT_ID` 覆盖）

敏感值不写入日志，不进入普通错误堆栈。

## 6. 目录结构

```text
src/oc_healthd/main.py
src/oc_healthd/config.py
src/oc_healthd/state_store.py
src/oc_healthd/checks/openclaw_health.py
src/oc_healthd/checks/openclaw_status.py
src/oc_healthd/checks/system_net.py
src/oc_healthd/checks/system_power.py
src/oc_healthd/notifiers/telegram.py
deploy/com.openclaw.healthd.plist
config.example.toml
logs/healthd.jsonl
```

## 7. macOS 运行与自启动

通过 `launchd` 交付:

1. `RunAtLoad = true`，开机自动启动。
2. `KeepAlive = true`，异常退出自动拉起。
3. 日志重定向到固定文件路径，便于排障。

## 8. 日志与可观测性

采用 JSON Lines 输出，每条记录包含:

1. 时间戳
2. 各层探测结果（`ok/code/latency/reason`）
3. 状态机当前状态
4. 是否触发通知与通知结果

保留最近状态快照文件，重启后读取，避免“守护进程重启导致重复告警”。

## 9. 测试策略

1. 单元测试
   - 状态机跃迁
   - 连续失败计数逻辑
   - 配置解析与默认值
   - 告警消息渲染
2. 集成测试
   - mock CLI 成功/失败/超时/坏 JSON
   - mock Telegram 成功/失败
3. 本机冒烟测试
   - 断网场景
   - OpenClaw CLI 不可用场景
   - 恢复场景

## 10. 验收标准

1. 监控连续运行 24 小时无崩溃。
2. 任一层连续 3 次失败可稳定触发 1 条故障告警。
3. 恢复后 1 分钟内收到 1 条恢复通知。
4. 不出现重复风暴告警。
5. 重启守护进程后不会重复发送历史故障告警。

## 11. 实施里程碑

1. M1: 搭建项目骨架 + 配置加载 + 主循环
2. M2: 完成 OpenClaw 健康层与系统层探针
3. M3: 接入 Telegram 通知 + 状态持久化
4. M4: launchd 部署 + 冒烟测试 + 文档补齐

