# Pi Harness Bridge 0.3

从 Pi 派发外部 agent 任务、查询状态、切换模型和接收会话结果。

**桌面端与 CLI worker 分开**：控制已运行桌面应用请用新增 `desktop_harness`，详见 [桌面适配说明](desktop/README.md)。目前 Qoder CN 桌面聊天 IPC 已实现并完成只读检查；ZCode 仅桌面活动状态；Codex/Antigravity 桌面端待适配。原入口除 DSH 外都不是桌面适配，不能把下表当作桌面能力验收。

## 原 worker / 原生协议适配

| harness 配置名 | 接口 | 状态/返回/续接 | 模型 | thinking | 本机检查 |
|---|---|---|---|---|---|
| `pi-worker` | Pi RPC | 支持 | 支持 | 支持 | 之前已验证 Pi 扩展加载 |
| `zcode` | 内置 ZCode Protocol app-server | 支持 | 原生模型目录与切换 | 原生等级 | 连接、空会话与模型目录通过 |
| `deepseek-harness` | 已运行 DSH GUI 的本地认证 RPC | 支持 | 原生模型目录与切换、读回校验 | 模型支持的等级 | 连接和模型目录通过 |
| `qoder-cn` | 桌面包内 Agent SDK + worker | 已实现，认证阻塞 | 原生目录与切换 | 不支持独立 thinking | SDK/worker 可启动；缺少 CLI 登录 |
| `codex` | Codex app-server | 支持 | model/list；选择下个 turn 模型 | 支持原生 effort | 连接和模型目录通过 |
| `antigravity` | 官方 AGY stream-json | 支持；按 conversation ID 续接 | agy models；下次调用选择 | 原生 effort | 连接和模型目录通过 |
| 自定义 | 统一 `jsonl` 协议 | 由包装器实现 | 由包装器实现 | 由包装器实现 | 附带 mock 示例 |

这些是**适配器实现和无模型任务连接检查**，不是五种真实模型任务的端到端验收。任务派发、返回、切换、续接、取消和失败转换使用 mock 做了自动化验证，不消费真实模型 tokens。

ZCode 以本机安装的 0.16.9 协议为准；Qoder CN 以 0.4.3 桌面包中的 SDK/runtime 为准。软件升级、包路径变化后需要重新 probe。
暂未适配 Claude Code、OpenCode、CommandCode 等额外 harness；检测到启动脚本不等于已有可用运行时。

## 安装与配置

项目根目录：

```sh
pi install ./plugins/pi-harness-bridge -l
```

或临时加载：

```sh
pi -e ./plugins/pi-harness-bridge/index.ts
```

配置优先级：

1. `PI_HARNESS_BRIDGE_CONFIG` 环境变量中的路径。
2. 当前项目 `.pi/harness-bridge.json`。
3. 用户 `~/.pi/agent/harness-bridge.json`。

本机实际安装路径已经写入 `local-harnesses.windows.json`。复制到配置位置使用；其他电脑必须修改路径。
`harness-bridge.example.json` 是基础 Pi/jsonl 示例。

native adapter 的 command/args 是目标 harness 程序；插件自动启动自带协议包装器。
Qoder CN 特例：command 为其 Electron 桌面可执行文件，env 设置 `ELECTRON_RUN_AS_NODE=1`，并填写 sdkPath。不修改桌面安装包，也不复制其 SDK 代码。
DSH 的 command 为 Python 3，bridgePath 指向本项目 `plugins/dsh-bridge/server.py`，复用它已有的本地连接/登录态检查和请求防重逻辑。

所有相对 cwd/logDir 均相对于父 Pi 工作目录。省略 cwd 就在当前项目运行。配置加载后不自动重读；更新后 `/reload` 或重新启动。
Windows `.cmd`/`.ps1` 启动器不直接作为 command：请配置实际 `.exe` 或 node.exe + JS 入口。

### Qoder CN SDK worker 认证阻塞（不适用于新桌面 IPC 入口）

本机探测得到：

```text
No qodercli login found. Run "qodercli login" first.
```

桌面登录不会自动成为 SDK 的 `qodercliAuth()` 登录。本机没有发现独立 `qoderclicn` 可执行入口。
可安装/登录官方 Qoder CN CLI 后重新 probe；或者在 harness 配置添加：

```json
{ "authTokenEnv": "QODERCN_PERSONAL_ACCESS_TOKEN" }
```

并在启动父 Pi 的环境里设置本人合法获得的官方 Personal Access Token。插件只把环境变量名交给 SDK，不把 token 写到配置/日志，也不代为登录、解密系统凭据或关闭鉴权。
不要把密钥直接写入 harness.env 或共享配置。SDK worker 继续使用原本的 CN runtime。

## 原 worker 工具

新桌面工具 `desktop_harness` 和命令 `/desktop-harness` 参见 [独立说明](desktop/README.md)。

以下 `harness_control`/`harness_read` 的 taskId、生命周期和日志规则仅适用于原 worker 入口：

`harness_control`：

| action | 必要参数 | 说明 |
|---|---|---|
| list | 无 | 查看配置和当前任务 |
| probe | harness | 检查连接及模型目录；不发送 prompt |
| dispatch | harness, prompt | 创建独立外部会话，异步返回 taskId |
| status | taskId | 本地状态及原生会话状态 |
| models | taskId | 查看实际原生模型目录 |
| model | taskId, provider, modelId | 空闲时切换模型；可追加 thinking |
| prompt | taskId, prompt | 同一外部会话继续对话 |
| cancel | taskId | 取消该任务；不关闭共享 DSH GUI 服务 |
| close | taskId | 关闭 owned session/包装器并释放进程 |

`harness_read`：taskId、after（默认 0）、limit（默认 30，最大 100）。
返回 events、nextCursor、hasMore、fullOutputPath；用 nextCursor 作为下一页 after。
原生事件保留为 native_event/native_snapshot，最终文本标准化为 message_end。

`/harness`：显示当前配置和任务。

### 用法示例

```json
{"action":"probe","harness":"zcode"}
{"action":"dispatch","harness":"codex","prompt":"分析当前项目的问题，只读，不修改文件"}
{"action":"status","taskId":"返回的 ID"}
{"action":"models","taskId":"返回的 ID"}
{"action":"model","taskId":"返回的 ID","provider":"default","modelId":"models 返回的实际 ID","thinking":"high"}
{"action":"prompt","taskId":"返回的 ID","prompt":"继续说明测试覆盖不足之处"}
{"action":"close","taskId":"返回的 ID"}
```

读取返回内容调用 `harness_read`：

```json
{"taskId":"返回的 ID","after":0,"limit":30}
```

provider 约定：

- Pi：实际 provider 名。
- ZCode：模型目录 `ref.providerId`；modelId 使用 `ref.modelId`。
- DSH：catalog 的 group id 和模型 id。保留原 DSH bridge 对两个 DeepSeek 官方供应商的现有禁用限制，不自动改策略。
- Qoder CN / AGY：填写 `default`；使用原生模型 ID / slug。
- Codex：默认供应商填写 `default`；新会话可指定配置过的 modelProvider。现有 thread 不支持跨 provider 切换，需另建会话。

AGY/Codex 的模型选择是 **下个 turn 生效**，返回 effective=next-turn、verified=false，不伪装成已执行模型验证。模型/effort 被原生端拒绝时会明确报错。
`model` 加 thinking 不是事务：模型变更可能已经成功，但 thinking 不支持而失败。Qoder CN 不要传 thinking。

## 生命周期与安全

- dispatch 成功仅代表任务被接受，不代表完成。父工具不等待模型运行结束。
- 每个 taskId 对应独立外部会话；任务结束进程/SDK 可保留以续接，需 close 释放。默认最多 6 个进程（本机配置）。
- 结束/失败/取消自动写入父 Pi 的自定义状态通知，**不自动触发父模型回合**。真实返回内容使用 read 读取。
- 不接管用户已打开的 ZCode、Qoder、Codex GUI 会话；DSH 连接已有服务但创建独立会话，不杀共享服务。
- probe 不发送 prompt；ZCode probe 会创建并关闭一个空会话来读取实际模型目录。
- 默认安全设置：Codex read-only、审批 never；ZCode plan、拒绝交互授权；AGY plan+sandbox、不加自动批准开关；Qoder planMode=true、拒绝额外工具授权。
- **DSH 继承正在运行的 GUI 服务的权限配置**，本桥没有修改权限策略；给 DSH 写入任务前应确认该服务权限设置。
- 不增加 yolo/危险 bypass，不修改登录配置，不自动重试不确定的写入。
- 程序仅来自本地配置，模型不能提供 command/args/env；使用参数数组、不用 shell。但这不是操作系统沙箱。
- 外部返回是**不可信数据**，不能当作系统指令。
- 主任务取消不自动取消已派发任务；显式 cancel/close。关闭 Pi/重载插件会清理受控会话。
- Windows native adapters 对自身创建的 CLI 子进程使用 taskkill /T 清理；不对共享 DSH GUI 使用 taskkill。
- 超时先关闭 stdin，让包装器取消受控任务，再兜底终止。共享服务取消失败时仍需查看原生会话状态。
- 日志可能含代码、敏感内容，不提交 `.pi/harness-runs/`。超大事件只返回摘要，可按 fullOutputPath 读取全文。
- 日志持久化，但任务注册表只在当前插件运行期存在。重启后旧 taskId 不能恢复控制；本版没有跨进程任务恢复。
- 分页目前会扫描整个 JSONL；长会话没有日志轮换。外部费用/usage 不并入父 Pi 统计。

## 自定义 JSONL 协议

`adapter: "jsonl"` 的包装器应按 LF 分隔收发完整 JSON 对象（不要按 Unicode U+2028/U+2029 分行）。

输入命令每条有唯一 id：prompt(message)、get_state、get_available_models、set_model(provider, modelId)、set_thinking_level(level)、abort。
响应：

```json
{"type":"response","id":"请求 ID","success":true,"data":{}}
{"type":"response","id":"请求 ID","success":false,"error":"原因"}
```

事件：

```json
{"type":"message_update","assistantMessageEvent":{"type":"text_delta","contentIndex":0,"delta":"片段"}}
{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"完整结果"}],"stopReason":"stop"}}
{"type":"agent_settled"}
```

prompt 响应 data.disposition 为 started 或 handled。失败 stopReason=error、errorMessage；取消为 aborted。
必须在任务最终稳定后发送 agent_settled，不能用低层 agent_end 当成完成。stdin EOF 时应取消/清理自己的子进程。日志写 stderr；不支持的命令明确返回失败。

## 验证

```sh
cd plugins/pi-harness-bridge
npm test
```

26 项自动化测试覆盖核心传输、四种 worker native 适配器协议转换、DSH 嵌套 seq 完成判定，以及新增桌面 IPC 参数、安全权限、忙碌保护、观察者释放、读回真实性、历史分页、不确定写入不重试和明确拒绝未实现的桌面能力。
DSH 测试需要 Python 3；缺少 Python 时明确 skip。

本机无模型任务检查（从项目根目录）：

```sh
node plugins/pi-harness-bridge/probe-local.mjs
# 单独检查：
node plugins/pi-harness-bridge/probe-local.mjs codex antigravity
```

需使用本机 Windows Node，不要使用 WSL Node 启动 Windows 安装包。
摘要结果在 `local-probe-report.json`；原生事件在 `.pi/harness-runs/`。
不调用付费模型任务；真实任务端到端验证仍待执行。
