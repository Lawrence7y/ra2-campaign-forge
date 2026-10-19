# @dsh-external/lark-notify

DeepSeek Harness（DSH）→ 飞书的通知 hook：**每一轮对话结束**、以及**需要用户回答 / 批准**时，
用固定收件人的 bot 身份，经本机 `lark-cli` 发一条飞书状态通知。

配套的 Pi 版本在 `../pi-feishu-notify`，本插件沿用同一套安全模型。

## 为什么是插件而不是 hooks 配置

DSH（0.1.7-rc）**没有** Claude Code 那种 settings 里的 `hooks` 段。`dsh-session` 虽然预留了
`hook/invoked` / `hook/result` 两个事件类型，但没有任何 hook 引擎实现它们。
DSH 的等价机制是 Cordis 插件 + `ctx.on(event)`，所以本 hook 就是一个普通插件。

## 挂载方式

插件源码在本仓库，通过 junction 链进 profile：

```
C:\Users\Administrator\.dsh\profiles\desktop\node_modules\@dsh-external\lark-notify
    → D:\Project\ra2-campaign-forge\plugins\lark-notify
```

profile 的 `package.json` 里记录 `link:` 依赖，`cordis.patch.yml` 里 insert 挂载：

```yaml
- insert:
    - id: lark-notify
      name: '@dsh-external/lark-notify'
```

`cordis.patch.yml` 是 DSH 用 Cordis HMR 监听的文件，**改完即时生效，不需要重启 App**。
想让所有 profile / 所有会话都生效，把上面这段 insert 搬到机器级补丁
`~/.dsh/cordis.patch.yml`。

## 三个触发点

| 触发点 | 事件 | 说明 |
|---|---|---|
| 每轮对话结束 | `session/event` → `turn/end` | 只认根会话（`header.origin !== 'subagent'` 且无 `parentSession`），子代理不会刷屏 |
| 需要用户批准 | `approval/request`（waterfall） | 通知后原样 `return next()` 放行 |
| 需要用户回答 | `tools/pre-execute` 命中 `ask_user_question` | 从 `exec.arguments.questions[0]` 取问题摘要 |

`turn/end` 之后还会等 `settleDelayMs`（默认 1500ms）；若期间同一会话又 `turn/start`
（目标自动续跑、被 steer 等），就取消这次通知——避免一轮任务被拆成多条消息。

另外注册了一个模型工具 **`feishu_notify_waiting`**，覆盖「用普通文本追问」的场景：
模型在追问用户之前调用一次，即可让用户不在电脑前也收到飞书提醒。

## 配置

配置文件：`~/.dsh/plugins/lark-notify/config.json`（首次加载自动生成，热改 5 秒内生效）。
可用环境变量 `DSH_LARK_NOTIFY_CONFIG` 指向别处。字段见 `config.example.json`。

| 字段 | 默认 | 说明 |
|---|---|---|
| `enabled` | `true` | 总开关；关闭后所有通知直接跳过 |
| `command` | `""` | lark-cli 可执行文件；留空则自动探测本机已知安装位 |
| `expectedAppId` | `cli_YOUR_APP_ID` | 期望的飞书应用；不匹配就拒绝发送 |
| `recipient` | `{type:'user', id:'ou_1953…'}` | 固定收件人：`user`(open_id) 或 `chat`(chat_id) |
| `approvedRecipient` | `user:ou_1953…` | 必须与 `recipient` 完全一致，否则拒绝发送（防止收件人被静默改掉） |
| `includeQuestions` | `true` | ask 通知是否带上问题摘要（截断 200 字并脱敏） |
| `includeCompletionSummary` | `false` | 是否带上最后一轮回复正文 |
| `settleDelayMs` | `1500` | turn/end 后的静默观察窗口 |
| `timeoutMs` | `30000` | 单次 CLI 超时；超时**不重试**（结果不确定时重试会重复发送） |
| `identityCacheMs` | `600000` | `auth status` 身份校验结果的缓存时长（0 = 每次发送都校验） |
| `onlyProjects` | `[]` | 只对这些项目名（会话工作目录的目录名）发通知；空数组 = 所有项目 |
| `notifyTurnEnd` / `notifyApprovals` / `notifyUserQuestions` | `true` | 分项开关 |

> 注意：插件对**该宿主进程里所有根会话**生效，不限于当前工作区。若只想收某个项目的通知，
> 用 `onlyProjects`（例如 `["ra2-campaign-forge"]`）。

## 安全设计

- **收件人锁定**：`approvedRecipient` 必须与 `recipient` 一致，改收件人必须同步改这个确认字段。
- **只用 bot 身份**：发送固定 `--as bot`；`auth status` 校验失败时直接放弃，**绝不回退到你的个人账号**。
- **幂等**：每次通知带 `--idempotency-key`（同 key 一小时内只发一次），并对同 key 去重。
- **不重试**：超时或返回非 JSON 时只记「结果不确定」，不自动重发。
- **串行排队**：同时最多 20 条待发，避免刷屏。
- **正文脱敏**：`Bearer`/`sk-*`/`appSecret`/`accessToken`/`password` 形态的文本一律抹掉。
- **本地台账只记元数据**：`~/.dsh/plugins/lark-notify/notifications.jsonl` 只写时间、幂等键、
  类型、状态、`message_id`；不落消息正文、不落 CLI 输出、不落凭据。
- **旁路**：通知的任何失败只写日志，绝不影响 agent 主流程。

## 排障

```bash
# 看投递台账（最新几条）
Get-Content "$env:USERPROFILE\.dsh\plugins\lark-notify\notifications.jsonl" -Tail 5

# 看插件是否被宿主加载过（每次 apply 会写心跳）
Get-Content "$env:USERPROFILE\.dsh\plugins\lark-notify\loaded.json"

# 独立冒烟测试（真实发送一条；加 --dry-run 则只预演）
node smoke.mjs
node smoke.mjs --dry-run
```

常见情况：

- **收不到通知**：先确认 `config.json` 的 `enabled` 是 `true`，再跑 `node smoke.mjs` 验证 CLI 链路。
- **`飞书通知已关闭`**：`enabled: false`，或配置非法（`expectedAppId`/`recipient`/`approvedRecipient` 校验不过）。
- **改了插件源码没生效**：`cordis.patch.yml` 的 HMR 只监听配置文件，不监听本插件源码目录；
  改源码后需要重启 App，或在 `cordis.patch.yml` 里删掉再重新加回 insert 强制重载。
