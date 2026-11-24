# -*- coding: utf-8 -*-
"""Append §556: RE continuation line + dispatch routing (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7556"

head = subprocess.run(["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
                      cwd=REPO, capture_output=True).stdout.replace(b"\r\n", b"\n")
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.replace(b"\r\n", b"\n").startswith(head):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
if b"\r" in wt:
    print("REFUSE: worktree has bare CR bytes; inspect before appending")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = u"""
## §556 · 逆向线续开：挂起计数器的**脚本入口已绑到动作号**，且测量图根本没有这两个动作（2026-11-05）

> **本节的地位**：用户 2026-11-05 令「继续逆向任务」，并指定工作流模型路由
> （hy4free 优先 → gemini-3.8-flash → deepseek-v4.1-flash 交叉；gpt-6.1-sol(medium) 只做决策）。
> 本节登记**本轮领队自己跑的离线预检结论** + **新派发路由写死** + **两条工作流的题**。
> 明细：`lead/re_line_20261105/_leader/LEADER_PRECHECK_20261105.md`。

### 一、★ 闭掉 P01 遗留开放项②：`0x684060`/`0x53B460` 的调用点已绑到动作号

`P01/REPORT.md:150` 自陈「动作处理器区 0x6DF6FD/0x6E4080 的**动作号**未定谳」。
本轮用 `out/re_work/triggers/action_dispatch_table.tsv` 的派发块区间命中：

| call 点 | 落在的动作块 | kind | 动作名 |
|---|---|---|---|
| `0x6DF703` → call `0x684060`（挂起请求） | `0x6DF6FD..0x6DF717` | **0x6E = 110** | **PauseGame** |
| `0x6DFAC5` → call `0x53B460`（渐变启动器） | `0x6DFABF..0x6DFAD9` | **0x7F = 127** | **StartChronoScreenEffect** |

字节自证（`ra2tool.Engine.disasm` 实跑）：
`0x6DF6FD mov ecx,[esi+0x90]` → `0x6DF703 call 0x684060`；
`0x6DFABF mov ecx,[esi+0x90]` → `0x6DFAC5 call 0x53B460`。
与 `trigger_system_manifest.md:247/:264` 的 `PauseScenarioFor 0x6E4080` / `SetChronoScreenEffectState 0x6E2F90` 一致。

**第三个挂起入口不是脚本动作**：`0x657CA0` 所在函数头 = `0x6579E0`，
**全镜像唯一调用者 `0x653446`**，由全局计数 `0xB45B68`（23 处引用、3 个写点）的沿翻转驱动
（沿翻正 → call `0x684060` 时长=0；沿翻回 → call `0x684180`）。⇒ **引擎内部状态机，无脚本入口**。
（该对象身份本轮**未定谳**，列入 W1 的 Q1/Q2。）

### 二、★ 更重要：测量用地图 `U0400` 的 `[Actions]` 里**没有** 110 与 127

`ra2youli/[2]0LoadBench_U0400.yrm` 的 `[Actions]` 段解析结果：

```
n=3   kinds = [(2,1), (4,1), (9,1)]      # Lose / CreateTeam / FireSale
```

抽查的同族：`U0050 / U0200 / U0400` 均 `{2,4,9}`；`U0100 / U0800` **无 `[Actions]` 段**；
`ECH01/02/03.MAP` 只有 `{(1,11)}` / `{(1,11),(2,1)}` / `{(1,12)}`。

⇒ **在测量语料这一范围内，「帧钟停摆」不能用「地图脚本主动 PauseGame / ChronoScreen」解释。**
这是**阳性排除**（入口不存在，不是"未观察到"）。

**它不证明什么**（必须一起写）：不证明 32 个零推进窗「不是引擎停摆」——`0x6579E0` 那条内部路径仍在，
本轮**未查**其触发条件；不覆盖未解析的测量图（`l1*` 的 `0add791d`、`l3*` 的 `f3bb0a4e`、archive 各图
**本轮未逐张解析**，交 W1 做全量）。

### 三、★ 目标①出现一组**受控对照**（这是本轮最有价值的发现）

同图 `map_sha256=f3bb0a4e…`、同 harness 家族、`span_s=25` 的窗里：

| 趟 | units0 | `frame_ms_p50`（w0/w1/w2） | `fps_avg` |
|---|---:|---|---|
| `l3_1101v4d` | 1225 | **32.3 / 32.3 / 32.1** | 31.16 / 31.24 / 31.24 |
| `l3_1101v4e` | 1189 | **32.2 / 32.3 / 32.4** | 31.28 / 31.20 / 31.24 |
| `l3_1101v4c` | 1229 | **50.5 → 33.1 → 32.4** | 18.52 → 28.40 → 30.68 |
| `l3_1101v3b` | 1352 | 55.3 / 55.7 / 76.1 | 16.72 / 12.36 / 11.20 |
| `l3_1101v3a` | 1349 | **82.5 / 70.3 / 166.8** | 11.60 / 14.04 / 5.88 |
| `l3_20261031hb` | 1347 | **106.6 / 182.9 / 72.0** | 6.79 / 4.73 / 10.60 |
| `l3_20261021` | 1342 | 105.2 / 72.9 / 92.3 | 8.76 / 11.96 / 10.20 |

⇒ **单位数只差 ~10%，帧时差 2–5.7 倍。** 这批窗 `logic_frames` 全为正（118–767）、
`max_stall_s` ≤ 0.75s ⇒ **是连续慢泵，不是冻结**，与 §545/§550 的计分屏线**无关**。

**第一层筛查（我实跑，已被否定的方向）**：

| 量 | 慢组 | 快组（v4d/v4e） | 判定 |
|---|---|---|---|
| `g_items` | 256,152,480（v3a/hb 恒定） | **369,700,440**（更大） | 方向反 ⇒ 非成本源 |
| `ws_kb` | 136,312–136,778 | **137,850–137,935**（更高） | 方向反 |
| `pf_kb` | 122,588–123,368 | **123,444–123,674**（更高） | 方向反 |

**★ 唯一完美分离的量：`counters[].shape.b_valid`**

```
87 个 25s 窗中，b_valid 全 false 的 24 窗（跨 8 趟）：frame_ms_p50 中位 = 73.9   （范围 32.2–182.9）
            b_valid 全 true  的 61 窗（跨 21 趟）：frame_ms_p50 中位 = 32.2   （范围 31.6–105.2）
```

**这不是"慢与快"的渐变，是两群。** `b_valid` 的引擎语义**本轮未定谳**，已列为 W2 的 Q1 第一优先。

### 四、新派发路由（用户 2026-11-05 令，写死；本节起取代 §553 的回退链）

```
推进首选 : magpie/work/cn:hy4free$high
推进备选1: magpie/antigravity/gemini-3.8-flash$high
推进备选2: new-provider/cn:deepseek-v4.1-flash$max      （ListModels 标 disabled 则跳过）
仅决策   : magpie/codex/gpt-6.1-sol$medium                （只在需要裁决时才派）
```

**并发纪律（用户令「不要启动过多导致卡顿」「同一模型不要并发过多」）**：
1. **同时在飞的推进工作流 ≤ 2**；且**不同模型**（同一模型同一时刻只跑 1 件）。
2. 严格按优先级取通道：hy4free 空闲就用 hy4free；它忙/报错才降 gemini，再降 deepseek。
3. **报错即换下一路**，不等退避、不重试同一模型。
4. 决策工作流（gpt-6.1-sol）不受上面 2 条限制，但**不得与推进流水并发超过 1 个**。
5. 三路全不可用 → 停下列给用户，不自行换被禁模型。
6. 唯一例外：已确认「启动不了」的通道（如 ListModels 标记 disabled）直接跳过，不占位。

**与 §551 的关系**：§551 的「禁止派发 `new-provider-2/*`（MUZE）」**继续有效**；
`account:bigmodel-start-plan/GLM-5.3-Flash` 在 **23:00–09:00** 才可用，是**夜间首选**，
白天不派（§551 的教训）。

### 五、本轮派出的两条工作流

| run | 模型 | 题 | 交付 |
|---|---|---|---|
| 待回收 | `magpie/work/cn:hy4free$high` | **W1 挂起计数器来源完备性普查** | `lead/re_line_20261105/W1_HOLD_SURFACE/` |
| 待回收 | `magpie/antigravity/gemini-3.8-flash$high` | **W2 同图同兵力 5.7 倍帧时差归因** | `lead/re_line_20261105/W2_FRAMETIME_ATTRIB/` |

任务书已落盘（各自目录 `TASK.md`），**铁律统一写入任务书**：
零真机 / 不写采样代码 / 只读母本 / 唯一写域=各自目录 / `python -I -X utf8` / 不 commit。

### 六、诚实账

1. **我亲验**：§1 的四条区间命中与两段反汇编、`0x6579E0` 唯一调用者、`0xB45B68` 引用数、
   §2 的 U0400 等 8 张图 `[Actions]`、§3 的全部数字（含 87/24 的分组计数）、引擎 coverage/SHA
   （`99.9984% / 1,394,120 insns / resync=66`，SHA `73201cc0…f67476`）。
2. **我未验**：`0x6E4080`/`0x6E2F90` 与动作 110/127 的**字节级父子关系**——只采信 manifest 记载 + 地址相邻。
3. **我未验**：其余 40 张测量图的 `[Actions]`（只抽查 8 张）⇒ §2 的排除**只对已解析图成立**。
4. **我未验**：`b_valid` 的引擎语义与来源（交给 W2）。
5. 本轮**零真机**、**零母本改动**、**未 commit**。
6. **不改任何已裁结论**：D-16 / D-15 / D-13 处置不变；三目标句态不变
   （① 机制未闭合、② RC-4 不收口、③ 保持态）。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
