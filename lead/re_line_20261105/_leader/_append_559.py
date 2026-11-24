# -*- coding: utf-8 -*-
"""Append §559: Q1-vs-Q3 conflict adjudicated + Q3b full census (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7559"

head = subprocess.run(["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
                      cwd=REPO, capture_output=True).stdout
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.replace(b"\r\n", b"\n").startswith(head.replace(b"\r\n", b"\n")):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
if b"\r" in wt:
    print("REFUSE: bare CR in worktree")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = u"""
## §559 · 裁决 W1 内部冲突（Q1 vs Q3）：**Q3 对、Q1 错**；且 265 张图**零张**含 110/127/117（2026-11-05）

> **本节的地位**：W1（`dwfrun-3eee0767`，`magpie/work/cn:hy4free$high`）的子代理在 phase-1 内部
> 对同一事实给出**互相矛盾**的结论（Q1 说 INTRO 会把影片播放器压进队列使 `Count` 非 0，
> Q3 说 `0x5BF260` 不写 `Count`）。我亲自反汇编裁决。
> 同时 Q3b 的**全量普查**已落盘，把 §556 的「抽查 8 张」升级为「265 张全查」。

### 一、★ 裁决：`0x5BF260` **不写** `0xB45B68`（Q3 对，Q1 错；我上一轮的表述也错）

我实跑 `ra2tool.Engine.disasm(0x5BF260, 0x50)`（原始输出 `lead/re_line_20261105/_leader/_v_intro_probe2.py`）：

```
005BF260 85c9             test ecx,ecx
005BF264 3b0da0f3ab00     cmp  ecx,[0xABF3A0]        ; 影片 id 边界
005BF275 8a1d78e3a800     mov  bl,[0xA8E378]
005BF284 a194f3ab00       mov  eax,[0xABF394]        ; Movies 数组
005BF289 c60578e3a80000   mov  byte [0xA8E378],0
005BF293 8b0c88           mov  ecx,[eax+ecx*4]       ; 取 MovieInfo*
005BF296 e8a5faffff       call 0x5BED40              ; ← 唯一调用
005BF29B 881d78e3a800     mov  [0xA8E378],bl
005BF2A2 c20c00           ret  0xC
```

**全函数只有一处 call（`0x5BED40`）**，**没有** `0xB45B68` / `0xB45B5C` / `0x5BF390` / `0x5BF2B0` /
`0x684060` 的任何访存。⇒ **`0x5BF260` 走的是全屏 Bink 播放链，不进侧栏影片队列，不碰挂起计数器。**

`0x5BF2B0` 是**另一个函数**（`mov eax,[0xA8B238]` game mode 门 → `call 0x5C07D0` …），
才是那个「`inc [0xB45B68]` @`0x5BF341`」的全屏影片**注册器**；
而它**全镜像 0 个静态 `E8` xref**（Q3 与我早前都复现过）。

### 二、我对 §557 的连带订正

§557 第三节我写：

> 「即使一张图的 `[Actions]` 段里一个 110/117/127 都没有（如 `U0400`），
> 引擎自身的 INTRO / 简报 / 过场 / 结算影片流程仍可能让 `0xB45B68 > 0`，进而让 `+0x62C` 非 0。」

**这句作废。** 我当时只看到 `0x53933E call 0x5BF260` + 串 `INTRO` 就下了结论，
**没有进 `0x5BF260` 函数体核实它写不写 Count**。这正是我上一轮刚写下的教训
（「引用一个文件时必须读它紧邻的注释」）的**同类变体**：**看到一个 call 不等于知道它做了什么**。

**订正后的正确表述**：
- `+0x62C` 的**已证来源** = 4 类，其中脚本可达 3 类（110 / 127 / **117**）、引擎内部**未证**；
- 「无任何脚本动作时自发非零」**在静态证据下没有已证实的来源**，
  唯一残余是 `0x5BF2B0`（0 静态 xref、可达性未验）；
- ⇒ §556 第三节那个「测量图无 110/127 ⇒ 不能用脚本解释停摆」的排除，
  **在「110/127/117」三者的范围内成立**，但**仍不能外推成「引擎挂起路径不可达」**
  （残余 `0x5BF2B0` 未验）。

### 三、★★ Q3b 全量普查结果（把「抽查 8 张」升级为「265 张全查」）

`lead/re_line_20261105/W1_HOLD_SURFACE/sections/_q3b_probe_out.txt`（子代理实跑，探针 `_q3b_probe.py`）：

```
MAP_ROOT = ra2youli      EXTS = ['.map', '.mmx', '.yrm']
n_files = 265            by_ext = {'.map': 3, '.mmx': 38, '.yrm': 224}
files_with_[Actions] = 154        files_without = 111
n_records = 1261        n_actions = 5309        malformed_records = 0
distinct_action_kinds = 34
FILES_WITH_110 = 0 []
FILES_WITH_127 = 0 []
```

我另跑一次解析核对（逐行 `has110`/`has127` 列）：**264 行全为 `N`**，
且**没有任何文件含 kind 117**（`grep '\b117:'` 命中 0）。

**全局 kind 直方图**（照录）：`{99:4421, 119:81, 14:62, 54:177, 53:145, ...}` ——
kind 99 占 83%，是绝对主体；110/127/117 **一条都没有**。

⇒ **`ra2youli` 下全部 265 张图（含全部测量用图）中，没有任何一张使用 PauseGame(110)、
StartChronoScreenEffect(127) 或 PlayIngameMovieAndPause(117)。**

**这让 §556 的排除从「抽查」升级为「全量」，且结论更强**：
在这套测量语料里，`+0x62C` 的**三条脚本入口全部不存在**。

### 四、由此得到一条可用的**正面**结论（目标①）

把三条串起来：
1. `+0x62C != 0` 的已证来源只有 4 类，其中 3 类脚本可达（110/127/117）；
2. 测量语料 265 张图**零张**含 110/127/117；
3. `0x6579E0`（117 的下游）只由「影片队列 `Count>0` ∧ 当前项 `pause=1`」驱动，
   而队列的唯一局内注册器 `0x5BF390` 的 4 个 call 点**全部**是动作 100/117 的内联或从属体。

⇒ **在测量语料的静态度量下，`Scenario+0x62C` 应当恒为 0**
（唯一缺口是 `0x5BF2B0` 的可达性未验，它是全屏影片注册器、0 静态 xref）。

**这条的意义**：它把「32 个零推进窗不是挂起造成的」从「推测」推进到「有静态完备性支撑的排除」——
**但仍然不是运行期证据**。要真正排除，必须读到窗内 `+0x62C` 的实际值，
而**现有语料没有该通道**（与 A12 的两条红线同一边界）。

### 五、W1 状态处置

W1 的 phase-1 四个子问题**三份正文 + Q3b 探针/输出/表格全部已落盘**，
但 `GetWorkflowRun` 显示 `last_progress=51m35s ago`、两个子代理仍 `executing` **且 token 冻结**，
即**卡在 phase-1 未收尾**（复核 phase 2 尚未启动）。

**本轮处置**：**不停止**（已落盘的成果已可独立使用；停止会丢失其内部复核机会），
按 running 零干预纪律继续等；但**下轮若仍零进度**，则按换道处理：
用 `AmendWorkflow` 把脚本改为「只做复核+汇总」（phase-1 已完成的四份节文件作为输入，走缓存），
模型换到 `magpie/antigravity/gemini-3.8-flash$high` 或 `new-provider/cn:deepseek-v4.1-flash$max`。

### 六、诚实账

1. **我亲验**：`0x5BF260` 全函数反汇编（上表逐条）、`0x5BF2B0` 头部、`0x5BED40` 头部；
   Q3b 输出文件的 `FILES_WITH_110 = 0` / `FILES_WITH_127 = 0` / `n_files = 265` 三个数，
   以及逐行 `has110/has127` 全 N、无 kind 117。
2. **我未验**：`0x5BF2B0` 的运行时可达性（穷尽间接调用闭包未做）；
   `0x5BED40` 下游虚调是否间接写 `+0x62C`（Q3 标未验，我未另查）。
3. **我未验**：Q1 其余结论（`0xB45B68` 的类级定名）——我只裁了它那条与 Q3 冲突的断言。
4. **我未验**：W1 内部复核（phase 2）尚未跑，本节的三份正文**都还是未复核初稿**；
   我复核的是**其中的关键字节断言**，不是全部推论。
5. 本轮**零真机**、**零母本改动**、**未 commit**。
6. ★ **本轮第二次同类错误**：上一轮是「引用了文件没读紧邻注释」，这一轮是
   「看到 call 就当知道它做了什么」。两次都是**把间接线索当直接证据**。
   下一轮起：**凡「A 调用 B ⇒ A 具有 B 的性质」形式的推理，必须进 B 的函数体核实。**
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
