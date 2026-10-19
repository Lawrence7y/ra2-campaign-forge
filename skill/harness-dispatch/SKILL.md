---
name: harness-dispatch
description: 把任务派发给本机外部 Agent Harness（Qoder CN / ZCode / Antigravity / 各家 CLI）与 DSH 内部子代理时使用。当用户要求"派任务给外部模型 / 多开 harness / 并行 subagent / 用 Qoder CN 或 ZCode 干活"，或 harness_dispatch / harness_open / subagent 调用失败（无可用传输、单实例、额度、登录、静默失败）时使用。内含各通道的真实前置条件、错误对照表与派卡自检清单。
---

# 外部 Harness 与内部子代理派工

把任务派给"别的模型"是本项目的常规动作，但**通道前置条件经常不满足**，且失败信息往往不够。本技能给出实测可用的判断与配方。

> 证据来源：2026-10-03 本机实测，详见 `docs/re/LESSONS_20261003_AGENTS_AND_HARNESS.md` 与 `docs/re/HARNESS_PLUGIN_IMPROVEMENTS.md`。

## 0. 先做这三步，再决定派给谁

1. **`harness_list(probe=true)`** —— 看每个目标到底哪条传输可用（`acp/headless/pty/cdp/window`）。
2. **判断"能不能派发"**：
   - `headless` / `acp` / `pty` 可用 ⇒ 直接 `harness_dispatch`；
   - **只有 `window` 可用 ⇒ 不能派发**（窗口通道不参与 dispatch），必须先拿到 `cdp`；
   - `cdp: no — already running without a matching debugging endpoint` ⇒ 走 §2。
3. **内部子代理**（`subagent`）：确认它**没有 shell**，只派只读分析/规格/审计/合成。

## 1. 通道能力速查（2026-10-03 实测）

| 通道 | 传输 | 能派发 | 前置条件 |
|---|---|---|---|
| **Qoder CN 桌面端** `qoder-cn-app` | cdp | ✅ | 必须带 `--remote-debugging-port=9344` 启动 |
| **Qoder CN IDE** `qoder-cn` | cdp | ✅ | 端口是 **9336**（**不是** 9344）；可执行文件 `D:\Qoder CN IDE\Qoder CN IDE.exe` |
| **ZCode 桌面端** `zcode` | cdp | ✅ | 必须带 `--remote-debugging-port=9333` 启动 |
| Antigravity `agy` | headless | ✅（额度内） | 个人额度会 429，按 `retry-after` 等待 |
| `zcode-cli` | headless | ⚠️ | **工作区级月额度**；换模型无效 |
| `qoderclicn` | headless | ⚠️ | 需 `qoderclicn login`（与 GUI 登录态**分离**） |
| 任意 GUI（无调试端口） | window | ❌ | 只能读屏/点按钮，不能投递 |
| DSH 内部 `subagent` | — | ✅ | **无 shell**；路由受白名单限制 |

## 2. 把 GUI harness 拉起到 CDP（最高频的坑）

**症状**：
- `harness_open(launch=true)` 报 `the launched process was already gone — the app is most likely single-instance`
- 或 `cdp=error (CDP endpoint did not appear on 127.0.0.1:9344 within 20000ms)`
- `harness_dispatch` 报 `no usable transport … cdp=skip`

**根因**：Electron 单实例应用；插件 `launch=true` 只是"再启动一次"，被已有实例顶掉，端口永不出现。

**配方**（用本仓库脚本，端口必须与插件一致）：
```powershell
pwsh -File tools/harness_launch_cdp.ps1 -App "Qoder CN" -Exe "D:\Qoder CN\Qoder CN.exe" -Port 9344
pwsh -File tools/harness_launch_cdp.ps1 -App "ZCode"    -Exe "D:\zai\ZCode\ZCode.exe"   -Port 9333
```
脚本做四件事：结束同名进程 → **等 5 秒**让 tray/helper 退出 → 带端口启动 → 轮询 `/json/version`。

若没有该脚本，手工等价：
```powershell
taskkill /F /IM "Qoder CN.exe"
Start-Sleep 5
Start-Process "D:\Qoder CN\Qoder CN.exe" -ArgumentList "--remote-debugging-port=9344"
```
然后 **`harness_open(target=…, launch=false)`**，screen 首行应显示 `transport=cdp cdp port 9344`。

**注意**：`taskkill` 之后 probe 可能仍短暂报"already running"——**给它几秒**再启动。

## 3. 投递任务的正确姿势

### 3.1 开新会话
- Qoder CN：`click="新的任务"`（**用短文本**；"新的任务 Ctrl+N" 这种复合节点匹配不到）
- ZCode：`click="新建任务"`

> ⚠️ **开完新会话，先确认权限模式，再投卡。**
> Qoder CN / ZCode 的 composer 底部有一个 `完全访问` 控件，**权限是按会话生效的**，部分对话会停在"权限不完整"状态。
> **插件点不动它**：`click="完全访问"` 会返回 `ok:true`（点击命中），但**屏幕无任何变化**——不可自动化。
> ⇒ **每次开新会话后，请人工确认该会话显示为 `完全访问`，然后再投递任务卡。**
> 若某张卡出现"工具被拦 / 反复要批准 / 写域内写入失败"，**先怀疑权限模式**，而不是卡面或执行者。

### 3.2 **先单独 click 确认，再发文本**
```
harness_send(session_id, click="<任务短名>", wait_ms=3000)     # 先确认 ok:true
harness_send(session_id, text="<卡面>", submit=true)           # 再投递
```
**理由**：`click` 失败时文本**仍会被插入并提交**，会污染当前打开的会话（实测误投递过一次）。

### 3.3 卡面首行写成**互不相同的短名**
侧边栏用首行作标题；同前缀长标题既难 `click`，也无法区分。

### 3.4 卡面必备八项
1. 工作目录 + 目标镜像/指纹
2. **唯一写域** + "其他一律只读"
3. 任务身份（执行者/审计者/规格撰写者，明确**不做什么**）
4. 必做步骤（逐条、可勾选）
5. **退出码独立采集写法**：`cmd > out 2>&1; rc=$?; printf '%d' "$rc" > out.exitcode`
6. **负控要求**：先证明能击穿修前版本
7. **证据强度边界**（例如"Count/帧号只能验循环规模前提，不得外推到耗时"）
8. "不得伪造输出；失败如实记录"

### 3.5 实例独占
真机/游戏实例**同一时间只允许一个任务**操作；派卡时写明"本卡执行期间不得有其它任务操作该实例"。

## 4. 错误对照表

| 错误 | 含义 | 处置 |
|---|---|---|
| `no usable transport for target` | 只有 window 可用 | 按 §2 拿 cdp |
| `already running without a matching debugging endpoint` | 应用在跑但没调试端口 | kill + 带端口重启 |
| `the launched process was already gone` | 单实例顶掉 | 同上；并等几秒 |
| `refusing to type: … is not in the foreground` | 窗口不在前台 | 先点该窗口内的 Button 抢焦点 |
| `no UIA element matched "<X>"` | X 是 Text 节点 | 改用 Button/Hyperlink 文本；或先单独 click |
| `GoUsageLimitError … limitName: monthly` | 通道级月额度 | **换模型无效**；换通道或等 `retry-after` |
| `RESOURCE_EXHAUSTED (429)` | 个人额度 | 按 `retry-after` 等（滚动恢复） |
| `Not logged in · Please run /login` | CLI 未登录 | 人工登录（GUI 登录态不通用） |
| `child LLM route "…" is not allowed for this Session` | 子代理路由被白名单拒 | 换已实测可用的模型 |

## 5. 内部子代理（`subagent`）纪律

- **无 shell**：所有"跑命令/算哈希/跑回归"的任务**不要**派给它们；派了必然 `0xC0000142`。
- **静默失败率约 20%**：卡面强制"开工先写 `_STARTED.md`"；派工后 5–10 分钟查一次；不存在就**换模型重派**。
- **可靠度（本会话样本）**：`step/step-5-preview` 5/5、`opencode-go/deepseek-v4.1-flash` 5/5、`step/step-3.7-flash` 3/4、`xiaomi/mimo-v2.6-flash` 2/5。
- **对抗审计优先 `deepseek-v4.1-flash`**（今天三次抓到实质缺陷，包括审到 Lead 自己台账）。
- **无状态查询**：`list_agents` 不列子代理，`send_message` 对子代理 id 报 `not found` ⇒ 只能靠产物存在性判断。

## 6. 跨通道验证纪律

1. **执行与审计跨通道**：Qoder CN 写 → ZCode 审；反之亦然。
2. **审计要审到"修订者"与"Lead 台账"**：只审第一版会漏掉"修订引入的阻断级回归"（今天实例：claims 文件不存在导致门禁恒 FAIL）。
3. **同一模块单写者**；重派前确认旧任务已终态，避免并发覆盖。
4. **进程 completed ≠ 项目 ACCEPTED**：验收必须实读文件、复算退出码与关键结论。

## 7. 派工前自检（复制使用）

- [ ] `harness_list(probe=true)` 已确认目标**有可用传输**（GUI 必须 cdp）
- [ ] GUI 目标已用 `tools/harness_launch_cdp.ps1` 拉起到正确端口
- [ ] 已 `harness_open(launch=false)` 并确认 `transport=cdp`
- [ ] 已用**短标题**开新会话，并**先单独 click 确认 ok:true**
- [ ] **新会话的权限已人工确认为 `完全访问`**（插件点不动，必须人工；确认后再投卡）
- [ ] 卡面含"唯一写域 + 其他只读"
- [ ] 卡面含**独立退出码采集**写法
- [ ] 卡面含**负控**与**证据强度边界**
- [ ] 需要独占实例时已声明，并确认无其它在飞任务冲突
- [ ] 内部子代理任务**不含**任何需要 shell 的步骤
