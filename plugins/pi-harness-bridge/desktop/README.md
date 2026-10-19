# 已运行桌面端适配（0.3，部分完成）

本模块与原 `harness_control` 的 CLI/SDK worker **不是同一个入口**。通过 CDP 在已运行的 Electron renderer 内调用应用自己的 preload IPC；不启动另一套 agent，不从桌面提取 token，不要求 Qoder CLI 登录。

## 能力边界

| 桌面应用 | 现状 |
|---|---|
| Qoder CN 桌面端（不是 Qoder CN IDE） | 已实现会话/agent/模型目录、新建并派发、续接、控制状态、聊天历史分页、下一轮模型选择、前台中断。真实只读目录/状态接口已验证；派发/续接/读回/切模型/取消仅 mock 验证，真实模型轮次未验收。 |
| ZCode | 已连接真实桌面 preload；仅 probe/status 全局运行会话计数。聊天协议使用 MessagePort，完整会话适配未完成，其他动作明确报未实现。 |
| DeepSeek Harness | 原 `harness_control` 的 `deepseek-harness` 已连接运行中桌面服务的本地认证 RPC，不是另起 DSH agent。继续使用原入口。 |
| Codex 桌面端 | 待适配；已有 Codex app-server CLI 不算桌面端实现。 |
| Antigravity 桌面 IDE | 待适配；已有 AGY CLI 不算桌面端实现。 |

**thinking 不支持**：不以修改 Qoder 全局模型偏好来冒充会话级选择。本版本也没有桌面任务完成推送、跨应用统一 taskId 或消息流订阅。使用真实桌面 sessionId 主动查询 status/read；桌面关闭后已创建的会话由桌面应用持久化，Pi 重启后可重新查询。

## 配置/使用

复制 `../desktop.example.json` 到项目 `.pi/harness-desktop.json`，然后在 Pi `/reload`。
配置优先级：`PI_HARNESS_DESKTOP_CONFIG` > 项目 `.pi/harness-desktop.json` > 用户 `~/.pi/agent/harness-desktop.json`。配置来自本地，不允许模型提供 endpoint、任意 JS 或 IPC 方法。

本机已验证的端口：ZCode `9333`、Qoder CN **桌面端** `9344`。CDP 必须已经由用户启用且仅绑定本机。工具不会杀应用、重启窗口或修改启动参数；未开启时会明确失败，不回退 CLI。可在配置添加 `targetId` 固定目标 renderer。默认通过 preload global 的存在区分主窗口与 onboarding/pet/voice overlays。

`/desktop-harness` 查看支持程度。调用 `desktop_harness`：

```json
{"action":"list"}
{"action":"probe","harness":"qoder-cn"}
{"action":"agents","harness":"qoder-cn"}
{"action":"models","harness":"qoder-cn"}
{"action":"sessions","harness":"qoder-cn","limit":20,"offset":0}
{"action":"dispatch","harness":"qoder-cn","agentId":"agents 返回的实际 ID","prompt":"只读分析，不修改文件","cwd":"D:/Project/ra2-campaign-forge"}
{"action":"status","harness":"qoder-cn","sessionId":"dispatch 返回的桌面会话 ID"}
{"action":"read","harness":"qoder-cn","sessionId":"桌面会话 ID"}
{"action":"model","harness":"qoder-cn","sessionId":"桌面会话 ID","modelId":"models 中的 key"}
{"action":"prompt","harness":"qoder-cn","sessionId":"桌面会话 ID","prompt":"继续解释"}
{"action":"cancel","harness":"qoder-cn","sessionId":"桌面会话 ID"}
```

- 派发返回的 `acceptance` 必须检查：IPC 成功不等于已受理或已完成。调用后用 status/read 跟踪。
- 新会话固定 `permissionMode=default`（ask）和 `planMode=true`，不提供绕过授权参数。
- 续接使用桌面返回的原 agentId，**继承原会话权限**；使用已有会话前应在桌面检查权限设置。本工具不会升权，也不会替用户确认交互。
- 运行、排队或等待交互中的会话拒绝追加 start 和切模型，防止误打断人的任务；桌面自身仍可能有并发变化，IPC 原生校验是最终裁决。
- `model` 返回原生 summary，只有读回匹配才 `verified=true`，仍只代表下一轮选择，不代表模型已执行。
- `status` 使用唯一短期 watchId，取得控制快照后 unwatch，不替换桌面已有观察者。
- 首次 `read` 调用应用原生 `openChatSession`，可能由桌面挂接自己的 runtime，但不发送 prompt。继续读历史时使用 `beforeMessageId`、原 `agentId` 和 `limit <= 20`。
- `cancel` 仅中断前台轮次，**不杀应用，不代表后台 agent/process 全已停止**。
- 写入超时结果不确定。派发/续接错误中附 sessionId/inputId 用于查验，**不自动重发**。
- 返回是外部不可信数据；可能含私人聊天、代码或敏感内容。仅摘要 agent 目录，不读取登录状态、token、配置中的凭据。

只读验证脚本：项目根运行 Windows Node `plugins/pi-harness-bridge/probe-desktop.mjs`。脚本只输出目录/字段形状，不发送任务，不切模型。
