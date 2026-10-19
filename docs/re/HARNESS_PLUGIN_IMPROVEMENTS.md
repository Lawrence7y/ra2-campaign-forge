# harness-pilot 插件改良提案（基于 2026-10-03 实测）

> **背景**：本机 `harness-pilot` 插件源码位于打包的 `D:\DeepSeek harness\resources\app.asar` 内，
> `app.asar.unpacked` 只解出原生模块（koffi / libreoffice-kit），**无法在工作区内直接修改**。
> 因此本文以**可执行提案**形式交付：每条给出"现状行为 / 期望行为 / 验收 / 优先级 / 影响面"。
> **可立即落地的替代物**：`tools/harness_launch_cdp.ps1`（补上 P1 缺失的那一步）。
> **相关证据**：`docs/re/LESSONS_20261003_AGENTS_AND_HARNESS.md`。

---

## P1【阻断级】`harness_open(launch=true)` 无法拉起单实例 Electron 应用

**现状行为**（实测原文）：
```
cdp=error (CDP endpoint did not appear on 127.0.0.1:9344 within 20000ms …)
launched D:\Qoder CN\Qoder CN.exe --remote-debugging-port=9344 (pid 33292):
  the launched process was already gone — the app is most likely single-instance
  and only focused an existing window
window=skip (window: no window matching {"title":"/^Qoder CN$/i","process":"Qoder CN.exe"})
```
- 连续重试 3 次（含换 `cwd`）**全部同样失败**。
- 报错里的"most likely single-instance"是**正确的诊断**，但**没有给出补救动作**，操作者只能自己摸索。

**期望行为**：
1. 当检测到"启动后进程立即消失"时，**先枚举同名进程**；若发现已有实例，报错文本**必须**包含：
   - 已存在实例的 **pid 列表**与**窗口标题**（若有）；
   - 该目标需要的**调试端口号**；
   - 一条**可直接复制执行**的补救命令（kill + 带端口重启），形如：
     ```
     taskkill /F /IM "Qoder CN.exe" ; Start-Process "D:\Qoder CN\Qoder CN.exe" -ArgumentList "--remote-debugging-port=9344"
     ```
   - 以及"结束 Electron 应用后需等待数秒让 tray/helper 退出"的提示。
2. 可选（更佳）：新增 `harness_open(target=…, launch=true, kill_first=true)`，由插件**自己**完成
   "结束同名进程 → 等待 N 秒 → 带调试端口启动 → 轮询端点"这一整条流程。
   这样 `launch=true` 对单实例应用才名副其实。

**验收**：
- 在"应用已在运行"的前提下调用 `harness_open(launch=true)`，返回的报错中**必然**包含可直接执行的补救命令与端口号；
- 若实现了 `kill_first=true`，则同一调用能直接返回 `transport=cdp`（无需人工介入）。

**优先级**：阻断级（今天整条外部执行链卡在这里，靠人工两轮 `taskkill` + `Start-Process` 才打通）。

### P1 实测更新（2026-10-04）—— **诊断文案已修好，动作没修好**

**① 文案已改进** ✅：`harness_list(probe=true)` 现在会给出可执行的补救提示与端口号：
```
probe cdp: no — cdp: target 'qoder-cn-app' is already running without a matching
debugging endpoint (Qoder CN.exe, pid 5004, 7992, …);
remedy: harness_open target=qoder-cn-app kill_first=true (would use port 9344),
        or restart it yourself with --remote-debugging-port=9344
```

**② `kill_first=true` 动作不执行** ❌：连试三次，全部**静默退回 `transport=window`** 或直接报 `cdp=skip`：
```
harness_open(target="qoder-cn-app", kill_first=true)                → transport=window（未重启）
harness_open(target="qoder-cn-app", kill_first=true, launch=true,
             transport="cdp")                                       → Error: cdp=skip (… already running …)
```
**推测根因**：插件文档说 `kill_first`「**refuses if new pids appeared since the check**」。Electron 应用有 **10–17 个进程**持续增删 ⇒ **pid-drift 守卫每次都拒绝** ⇒ 该 remedy 对 Electron **结构性不可用**。
**建议**：pid-drift 守卫改为按**可执行文件路径归组**（同一镜像的多进程应用视为同一目标），而不是严格比对 pid 集合。

**③ 新发现：`probe: can launch` ≠ 真能启动** ❌：当应用窗口已关、但有后台/托盘进程占着单实例锁时：
- `probe cdp: OK — cdp: can launch … with a debugging port`（**乐观结论**）
- 实际 `harness_open(launch=true)` → `the launched process was already gone — the app is most likely single-instance … the launched process tree was terminated`

**④ 新发现：20 s 超时后插件会终止自己启动的进程树**：Electron 冷启动可能 >20 s，此时调试端口尚未出现，插件**先把树杀掉**，于是"再来一次"永远失败。
**建议**：把 CDP 等待超时做成可配置（或对 Electron 目标放宽到 60 s），并在超时**之后**再决定是否终止，而不是边等边杀。

**综合结论**：P1 现在是**半修复**状态 —— 报错信息足以让人工介入，但**自动路径仍然不可用**。

---

## P2【高】`harness_dispatch` 的传输阶梯**不含窗口通道**，且报错信息量不足

**现状行为**：
```
harness_dispatch(target="qoder-cn-app") →
  no usable transport for target "qoder-cn-app":
  cdp=skip (target is already running without a matching debugging endpoint)
```
- 传输阶梯为 `acp → headless → pty → cdp`；**window 通道只在 `harness_open`/`harness_send` 生效**。
- 操作者若只看 `harness_list(probe=true)` 会看到 `probe window: OK`，**误以为可以派发**。

**期望行为**：
1. `harness_dispatch` 的失败信息里**显式说明**"窗口通道不参与 dispatch，本目标需要 cdp 或 headless"；
2. `harness_list(probe=true)` 对 GUI 目标**增列一行**：`dispatchable: yes/no`（并给出原因），避免 `window: OK` 造成的误解；
3. 或者在 `harness_list` 里直接打印该目标的 **CDP 端口号**（Qoder CN `9344`、ZCode `9333`），省去操作者试错。

**验收**：对"已运行但无调试端口"的 GUI 目标调用 `harness_dispatch`，报错中明确出现"window 不参与 dispatch"与"需要的端口号"。

**优先级**：高（今天为此浪费了多轮探测）。

---

## P3【高】`harness_send` 在 `click` 失败后**仍然插入并提交文本**

**现状行为**（实测）：
```
click("【任务卡 PERF-TARGET01 …】") -> {"ok":false,"reason":"no visible element matched …"}
input=heuristic-lower-half -> <DIV> …; inserted with Input.insertText; submitted by clicking sendSelector [aria-label="发送消息"]
```
- `click` 失败后，**文本照样落进当前打开的那个会话**，造成**误投递**（今天一条核实卡落进了另一张卡的会话）。

**期望行为**：
- 当调用方**显式**提供了 `click` 且该 click 返回 `ok:false` 时，**默认中止本次发送**（不插入、不提交），并返回明确错误；
- 若调用方确实希望"click 失败也照发"，需显式传 `allow_click_failure=true`。

**验收**：`click` 不命中时，`harness_send` 返回非成功状态且**不产生任何输入**；对目标会话做前后快照可证明未投递。

**优先级**：高（误投递会污染他人任务的上下文，今天需要额外的"调度更正"消息去补救）。

---

## P4【中】同名任务在 sidebar 无法区分，长标题 `click` 不命中

**现状行为**：
- 侧边栏用**任务首行**作标题；连续两张同前缀的卡会出现两个几乎相同的条目；
- 长标题被渲染成 Text 节点，`click` 报 `no visible element matched`（今天因此误投递，见 P3）。

**期望行为**：
1. `harness_open` 返回的 screen 文本中，把每个任务**编号**（或给出稳定的 `data-*` 标识）供 `click` 引用；
2. 或在 `click` 匹配失败时，**把候选元素清单里最接近的 N 个**（含其可见文本）回传给调用方，便于改选。

**验收**：对两个同前缀任务，能通过插件提供的稳定标识区分并分别定位。

**优先级**：中（可通过"给每张卡写不同短标题"规避）。

---

## P5【中】任务回执不含**实际模型身份**

**现状行为**：`harness_task_list` 输出形如 `target=agy model=gemini-3.8-flash-high`，其中 `model` 是**请求值**；
`harness_dispatch` 的返回里模型身份往往缺失（今天多个包只能记"未回传模型名"）。

**期望行为**：回执中区分 `model_requested` 与 `model_reported`（由执行端自述）；缺失时显式写 `model_reported: null`。

**验收**：任一外部任务的回执都能明确回答"实际用的是哪个模型、还是未知"。

**优先级**：中（影响"模型身份核验"这一项目纪律的可执行性）。

---

## P6【中】额度/登录类错误缺少**通道级**降级建议

**现状行为**：`zcode-cli` 返回
```
GoUsageLimitError: Go usage limit exceeded
retry-after: 267972, limitName: monthly, url: https://opencode.ai/zen/go/v1/chat/completions
```
- 该额度是**工作区级月额度**；在同一路由上换模型**无效**（实测 `qwen3.8-flash`、`deepseek-v4.1-flash` 均 429）。

**期望行为**：识别到 `GoUsageLimitError` / `RESOURCE_EXHAUSTED` / `Not logged in` 三类时，在错误文本中给出：
- 该额度是"通道级"还是"模型级"（能否靠换模型绕过）；
- 预计恢复时间（若有 `retry-after`）；
- **同产品内的替代通道**（例如 ZCode 的 GUI cdp 通道）。

**验收**：遇到上述三类错误时，操作者无需查文档即可知道"能不能换模型、要不要等、换哪条通道"。

**优先级**：中。

---

## P7【中】内部子代理（`subagent`）**无状态查询**

**现状行为**：
- `list_agents` 只列"队友"（本会话仅 `lead`）；
- 对子代理 id 调 `send_message` → `active teammate "…" not found`；
- 子代理静默失败时**无任何提示**，只能靠产物缺席事后发现（今天 4/20 静默失败）。

**期望行为**（属 DSH 核心，非 harness-pilot）：
1. 提供"列出本会话全部子代理及其状态（running / settled / failed）"的查询；
2. 子代理**开工/结束**都产生事件；
3. 或最低限度：子代理在 N 分钟无输出时发一次心跳告警。

**验收**：任一子代理静默失败能在其启动后 10 分钟内被识别，而不是靠人工轮询产物目录。

**优先级**：中（可用"卡面强制写 `_STARTED.md`"临时规避，见 `docs/re/LESSONS_20261003_AGENTS_AND_HARNESS.md` §1.5）。

---

## P8【低】`harness_list` 的 probe 输出过长，关键结论被淹没

**现状行为**：`probe=true` 时每个目标打印多条探测行；GUI 目标同时给出 `cdp` 与 `window` 两行，
**关键判断（能不能派发、走哪条传输）需要人工合成**。

**期望行为**：为每个目标加一行汇总，例如：
```
qoder-cn-app  → dispatchable=NO  (need cdp :9344; window-only)  window=OK cdp=NO
zcode         → dispatchable=YES (cdp :9333)
```
**验收**：`harness_list(probe=true)` 的每个目标都有单行"可派发性 + 所需传输 + 端口"结论。

**优先级**：低（体验问题）。

---

## P9【高】插件**读不到也设不了** GUI 会话的权限模式

**现状行为**（2026-10-03 实测）：
- Qoder CN / ZCode 的 composer 底部有一个 `完全访问` 控件，**权限按会话生效**，部分对话会停在"权限不完整"状态；
- `harness_send(session_id=…, click="完全访问")` 返回 `{"ok":true,"text":"完全访问","rect":[373,837,48,16]}` —— **点击命中**；
- 但点击后**等待 6 秒屏幕无任何变化**：无下拉菜单、无模式切换、可访问性树里没有新元素。
- ⇒ 插件**既不报告当前权限模式，也无法设置它**。

**危害**：权限不完整时，平台层会额外收紧约束（工具被拦、逐次要求批准、写域内写入失败），**表现为"卡面有问题"或"执行者不听话"**，排查方向被带偏。

**期望行为**（任一即可，按实现成本排序）：
1. `harness_open` / screen 输出中**暴露一个只读的权限指示**（例如 `permission: full | limited | unknown`）；
2. 若确实无法通过可访问性树读取，则在 `harness_open` 返回里**明确写** `permission mode: unknown — verify manually before dispatching`，而不是静默不提；
3. 更佳：提供显式的**权限设置**能力（即使需要驱动底层菜单）。

**验收**：任一 GUI 会话打开后，调用方**不需要靠猜测**就能知道权限模式；或在权限不完整时收到**明确告警**。

**优先级**：高（今天直接造成"部分对话权限不完整"，且失败表现具有强误导性）。

---

## 附：本次已落地的替代物

| 提案 | 替代物 | 位置 |
|---|---|---|
| P1 | 一键结束 + 带端口重启 + 轮询 CDP 的脚本 | `tools/harness_launch_cdp.ps1` |
| P1/P2/P6 | 操作手册（含端口表、错误对照表、派卡自检清单） | `docs/re/LESSONS_20261003_AGENTS_AND_HARNESS.md` |
| P1/P3/P4 | 可复用技能卡（含"先单独 click 确认再发文本"的纪律） | `skill/harness-dispatch/SKILL.md` |
| P7 | 卡面强制 `_STARTED.md` + 换模型重派 | `docs/re/LESSONS_20261003_AGENTS_AND_HARNESS.md` §1.5 |
