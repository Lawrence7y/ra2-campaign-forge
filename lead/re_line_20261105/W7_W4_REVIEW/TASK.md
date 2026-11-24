# W7 任务书 · W4 七份产出的**独立复核**（接手被中断的 phase 4）

> **为什么要重开这一题**：W4（`dwfrun-c976a0e3`，`magpie/work/cn:hy4free$high`）
> 在 **2026-11-05 22:00:45** 以 `stop_reason = interrupted` 停止（宿主进程退出，非模型报错）。
> 它 phase 1–3 的**七份正文全部已落盘**，但 **phase 4「对四份产出做独立复核」的回件一份都没有落盘**
> （目录 `W4_FIELD_SPEC/reviews/` 不存在）。
> ⇒ 按纪律：**不 `ResumeWorkflowRun` 同一模型死等**，改为**独立重开复核题**。
>
> **本任务只做复核，不重写那七份正文。零真机。**

## 0. 被核对象（七份，SHA256 已固化——你必须自己重算验证）

| # | 文件 | 字节数 | 我算出的 SHA256 |
|---|---|---|---|
| 1 | `sections/card_0087E8E0.md` | 44,403 | `e3afe2abb9bcac4be6f7e9666a836c6dff3499e4be9796ab568c6347bd1534b8` |
| 2 | `sections/card_00A8EC34.md` | 31,647 | `6cde19c881ab09f6f7b1246fe75dbc41d7538d0dbba59c9b528db9b35d821b46` |
| 3 | `sections/card_00B0CE88.md` | 32,262 | `c16cf1f3a3e5c254f8c232534a738ca24ced23803051f0fdb1e6145fc33ea578` |
| 4 | `sections/card_00A8ED50.md` | 37,864 | `a5926b6398879f880c7fe0c1726fec4a29306c9670bfcc67dad67aca36f3325e` |
| 5 | `sections/Q2_ALPHA.md` | 31,712 | `27055e6b94f892c6a53facc07adf908688c151eca82cfe56da8133cee8507663` |
| 6 | `sections/Q3_FRAME_EDGE_SPEC.md` | 38,799 | `0d3e13875855ea4b5d36f22e6f622916ac15b479944767fe4d067aaee5639c5d` |
| 7 | `sections/Q4_REDLINE.md` | 23,037 | `2189d17a115249e20d9f31465d7ec38535b10c10904db5c32212a5ecc886c329` |

★ **每份复核回件开头必须有**（缺则整份作废，见锚点 §三 铁律 9）：
```
被核对象 = <文件名>
被核对象 SHA256 = <你自己实算的 64 位>，字节数 = <你自己实算的>
复核时刻 = <你实际读取的时刻>
```
**若你算出的 SHA256 与上表不同 ⇒ 标 `OBJECT_CHANGED`，以你算出的为准并说明差异。**

## 1. 先读（按序）

1. `lead/re_line_20261105/W4_FIELD_SPEC/TASK.md` —— 原始任务书（Q1–Q4 的要求）
2. `lead/re_line_20261105/D19_RULING/RULING_D19.md` —— D-19 定谳（四 VA 的受限语义）
3. `lead/re_line_20261105/D21_RULING/RULING_D21.md` + `EXECUTION_D21.md` —— **D-21 裁 A 之后每沿 5 读**
4. `lead/re_line_20261105/V6_V3_REVIEW/V6_V3_REVIEW.md` —— 已验证的 5 读实现（判 CONFIRMED）
5. `lead/re_line_20261105/D20_B_VISIBILITY_GAP.md` —— 「可见单位数不存在现成计数 VA」

## 2. 七项复核（逐项给判定）

### A 组 · 四张字段规格卡（核 `card_*.md`）

**A1 · `card_0087E8E0.md`（代际尝试代理）**
- 它主张「**推翻 W3 的『每次寻路恰一次自增』**」——核这条是否真有字节依据支撑
  （它引用 `0x42CC80 可再推进最多 4 次`、`0x42D170` 18 个调用者、单例立即数 28 处）。
- 「回绕跳 0 且那次 **+2**」「构造初值 `-1` ⇒ **首次调用即走回绕**」——核这两条。
- 符号名判「未定名」的依据（pefile `RSDS`/`NB10`/`.pdb` 全 0）是否属实。

**A2 · `card_00A8EC34.md`（索敌入口累计）**
- 「直接写点**穷尽 = 恰 1 处**（`0x6F8E09`）」是否真的穷尽（它自己 §3.3 也说不宣称穷尽——核这两处是否矛盾）。
- ★ 它 §6.2 披露 `ra2render.dll` 的 **9 字节 Inline Hook** 会节流到 1/8——核这条的源码行号是否对得上。
- 符号名「未定名」依据。

**A3 · `card_00B0CE88.md`（脏矩形 Count）**
- 「**不是** `TacticalClass::DirtyAreas`」「`0x6D3DF5 test` 抄录错、真实为 `jne`、`test` 在 `0x6D3DFF`」——核这两处订正。
- 「`DrawIfVisible 0x5F4B10` 函数体内**零处** `call 0x6D2790`」——核。

**A4 · `card_00A8ED50.md`（Bullet Count）**
- `+0x98` 是**对象内 1 字节、无固定全局 VA**——核（`0x55B954/5A/5C`）。
- ★ **二道门 `+0x90`**（`0x4666F7 mov al,[ebp+0x90]` / `0x4666FF je 0x467fee` 早退）——核。
- 「Count ≥ 实际完成更新数」这个结论是否由上述字节支撑。

### B 组 · 三份分析（核 `Q2/Q3/Q4`）

**B1 · `Q2_ALPHA.md`（alpha 可解性）**
- 结论「**不可解**」的论证链是否成立：是否真的只有 `alpha_i ≥ 0` 这个平凡界；
  「对两个**差分**字段连平凡界都保不住（重置/进程重启可使 `Δy ≤ 0`）——核这条反例。
- 它批评 W3 `:177` 把 `alpha_i` 当**已知常数**放进矩阵、「Rank=4 是前提不是结论」——核这个批评是否公允。
- 「四个 `y_i` 中两个是窗口差分、两个是瞬时水位」的量纲分层——核它是否与该文件自述一致。

**B2 · `Q3_FRAME_EDGE_SPEC.md`（帧沿规格）**
- ★ **它采「每沿新增 5 读、20 B」，`S0` 复用既有轮询读数**——这与 **D-21 裁 A 一致**，
  也与 V6 已确认的实现一致。核它是否真的写对了（不是碰巧）。
- 「四地址跨度 `0x28E5A8` B（约 2.7 MB）」——核这个数（不是要求你反汇编，是核对它自己的算术）。
- 「全部是**名义操作数**，不是耗时/CPU/扰动实测」——核它有没有在别处违反这个自我约束（例如偷偷给百分比）。
- `λ` 七档（5.9952 / 6.0 / 19.8112 / 30.2016 / 30.8426 / 31.25 / 500）与对应 B/s、调用/s——核算术。

**B3 · `Q4_REDLINE.md`（三红线重评）**
- **C2 = 不能 / C1 = 部分能 / C4 = 不能** —— 逐条核判据是否够。
- 特别核 C1 的「部分能」：它说「只能说发生了会推进代际的**入口/重试尝试**，不能说真展开很多节点」——
  这与 `card_0087E8E0.md` 的字节事实是否一致（两文件之间**不得自相矛盾**）。

### C 组 · 跨文件一致性（这一组最重要）

**C1 · 七份文件之间有没有互相矛盾？**
逐对检查至少这几对：
- `card_0087E8E0.md` ↔ `Q4_REDLINE.md`（C1 判定）
- `card_00B0CE88.md` ↔ `Q4_REDLINE.md`（C2 判定）
- `card_00A8EC34.md` ↔ `Q4_REDLINE.md`（C4 判定）
- `card_00A8ED50.md` ↔ `Q2_ALPHA.md`（Bullet 的量纲归类）
- `Q3_FRAME_EDGE_SPEC.md` ↔ `Q2_ALPHA.md`（5 读口径与 alpha 不可解是否相容）

**C2 · 这七份里有没有把「未验」写成「已验」的？**
逐个文件搜「未验 / 未核实 / 未独立复验」等标记，核对它们是否**真的**列在诚实账里，
以及正文有没有出现与诚实账相反的强断言。

## 3. 交付物

写到 `lead/re_line_20261105/W7_W4_REVIEW/`：
- `W7_W4_REVIEW.md` —— 正文（七节：0 总判 / 1 SHA256 绑定 / 2 A 组四卡判定 / 3 B 组三分析判定 / 4 C 组跨文件一致性 / 5 必须改项 / 6 诚实账）
- `parts/` 下每项一份（A1–A4、B1–B3、C 组一份）
- `reviews/` 下每项一道独立复核
- `_w7_probe.py` + `_w7_probe_out.txt` —— 你实跑的只读探针（可用 `ra2tool.Engine` 反汇编核字节）

**判定规则**：任一项会让结论错误 ⇒ 该项 **REFUTED**；部分对 ⇒ **PARTIAL**；
全部对 ⇒ **CONFIRMED**。**★ 缺 SHA256 绑定段的回件不得判 CONFIRMED。**

## 4. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，**不读活进程内存**。
- **零采样注入代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
- **只读**：`ra2youli\`、`out\re_work\...`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
  `W1_*`…`W5_*` 既有件、`V6_*`、`D*_RULING\`、`A1_*`、`A2_*`、`A3_*`、`_leader\*`、
  **以及本任务要核的 `W4_FIELD_SPEC/sections/*` 七份正文**
  —— **一律不得修改**。**唯一写域 = `W7_W4_REVIEW/`**。
- Python 一律 `python -I -X utf8`，绝对路径。
- **不 commit、不 push**。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；**拿不到就写「未验」，不许补造**。
- ★ **不要把「查不到」当成「不存在」**（A3 曾两次犯此错）。
- 读 `gamemd.exe` 用：`sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104')` 后 `from ra2tool import Engine`。
