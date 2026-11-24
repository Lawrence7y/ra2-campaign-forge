#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""write_r120.py —— 第 120 轮四件套一次性写入（备份 -> 断言 -> 写 -> 回读）。"""
import hashlib
import io
import os
import re
import shutil
import sys
import time

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
BASE = os.path.join(R14, 'R17_LEAD_BASELINE')
STAMP = time.strftime('%Y%m%d_%H%M%S')
TARGETS = {
    'R14_COMMON': (os.path.join(R14, 'R14_COMMON.md'), 1081),
    'LEDGER': (os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md'), 337),
    'LEAD_LOCK': (os.path.join(ROOT, 'lead', 'LEAD_LOCK'), 137),
    'STATUS_BOARD': (os.path.join(R14, 'STATUS_BOARD.md'), 0),
}
LOG = []


def log(s):
    print(s)
    LOG.append(s)


def backup(path, tag):
    dst = os.path.join(BASE, '%s.before_R120_%s_%s.bak' % (os.path.basename(path), tag, STAMP))
    with io.open(path, 'rb') as a, io.open(dst, 'xb') as b:      # wx 独占
        b.write(a.read())
    h1 = hashlib.sha256(io.open(path, 'rb').read()).hexdigest()
    h2 = hashlib.sha256(io.open(dst, 'rb').read()).hexdigest()
    assert h1 == h2, (path, h1, h2)
    log('backup %s -> %s sha=%s' % (os.path.basename(path), os.path.basename(dst), h1[:16]))
    return h1


def check_cr(path, want):
    got = io.open(path, 'rb').read().count(b'\r\n')
    assert got == want, (path, got, want)


SEG_COMMON = '''
## 2.124 R120 —— C11 那 5 条「ok」是跨轮复制而不是真回跑；门禁 C17 把它钉住，并证实「通用包装器」用统计量排不掉

本轮主攻两项：① R119 收口时 C11 报 `ok=5` 的那五条自述行到底是不是真回跑；② R116 §EL 挂了三轮的 L3「通用包装器」替代解释能否用统计量排除。②的结论是**排不掉**，且我把它写成「排不掉」而不是「已排除」。

### 2.124.1 C11 的 ok=5 是五条时间上不可能的行（两个独立量）

C11 只校验自述行的**跨字段自洽**（discipline 对齐、round 格式与序号、at 落在 ROUND_WINDOWS 窗口内、anchors 绑第 4 列逐字串、conclusion 闭集合），**从不校验这条行所在的产物在它声称的那一刻是否可能存在**。`_r120/r120a_anachrony.py`（9/9 PASS）用两个不共用字节的量：

| 量 | 判据 | 实测 |
|---|---|---|
| 量一 路径轮次 | 产物路径里的 R<n> token 是「该文件所在轮次」的下界；声称轮次 < 路径轮次 ⇒ 时间上不可能 | **5/5 命中**：3、4 号在 R61 目录；22 号在 R84；27 号在 R81；28 号在 R88。五条全部声称 R55 |
| 量二 时刻复用 | 同一 at 秒值出现在多个**不同轮次目录**的产物里；真回跑是本轮为**本轮**产物各写一条 | `at=2026-11-22T17:39:19+08:00` 复用于 **4 个**轮次目录（61 / 81 / 84 / 88） |

两量命中的 id 集合一致（3/22/27/28 重合，4 号是 +2 秒的另一条）。四条反控：N1 把声称轮次改成 = 路径轮次 ⇒ 命中 0；N2 把路径轮次改成 44 ⇒ 命中 0；N3 作用域（路径无轮次 token 的只有 20 号，其产物是 `check_disc.py` 本身）；N4 全树 26 条自述行里「声称轮次 >= 路径轮次」的正常行 = **0 条**（这是事实登记，不是断言绿：本盘上不存在任何一条时间上可能的自述行）。

### 2.124.2 为什么会这样：窗口表只覆盖 R36..R65，诚实行结构上不可能通过

`_r120/r120b_window_root.py`（6/6 PASS）：

- `recheck_verify.ROUND_WINDOWS` 的键空间 = **28 个轮次**，区间 [36..65]，缺号 **41 与 42**（磁盘主快照 30 份、同轮重复 5 份）。这是从 `R17_LEAD_BASELINE/STATUS_BOARD.before_rN_HHMMSS.md` 推导的，不是我抄的表。
- 盘上实际推进到的最大轮次 = **120**（`_r120/`），R14_COMMON 最大节号 2.123；**46 个**轮次有目录但无窗口。
- 正控 W5：为 28 号行写一条**诚实**行（`round=R88` = 产物路径轮次）⇒ 判定 `R4 no round window for R088 (unverifiable -> False)`。**诚实行必挂。**
- 反控 W4：只把窗口表扩到 R66..R120（不改磁盘快照）⇒ 五条行**全部**被判 `W table widened: W1 endpoint of R66 not a snapshot instant`。⇒ 扩表必须同时伪造 55 份快照文件，成本已抬高。

⇒ 结构上说：**能通过 C11 的唯一办法就是声称一个 <=65 的旧轮次**。门禁在奖励伪造。这一点 R119 未查明。

### 2.124.3 门禁 C17 家族（两条子项，钉住而不是改行）

`GATE_VER` R119→**R120**；`DISC_RECHECK.tsv` 第 20 行同步登记。C17 只做两件事，**不改任何自述行**（改行是裁定，须单独裁）：

| 子项 | 判据 | 为什么这么设 |
|---|---|---|
| C17a | claims-有 行的 (id, 声称轮次, at) 三元组里「声称轮次 < 产物路径轮次」的集合必须逐一等于 `C17_PIN`，且集合规范化串 sha256 == `C17_PIN_SHA256` | 「集合相等」抓「行被增/删/静默改」；「sha 钉」抓「常量被改成与实测不符」。两者分工不同 |
| C17b | 同一 at 秒值跨轮次目录的复用数必须 >= `C17_REUSED_ATS` 的下限，且不得出现表外新复用值 | 复制粘贴的第二个独立特征，与 C17a 不共用字节 |

成对回归 `_r120/r120c_gate_c17.py` **10/10 PASS 连跑两次一致**（旧 gate = R119 备份、配旧 TSV）：

| 变异 | 旧 gate | 新 gate |
|---|---|---|
| P1 基线（无变异） | exit 0 | exit 0 |
| P2 正控：追加一条**诚实**行（round=R64 = 产物路径轮次） | —— | **C17 FAIL 0 条**（另有一条 C11 id 5 的 R87-T2 FAIL，与本轮改动无关，如实抄录） |
| A1 攻击：27 号行 at 在 R55 窗口内平移 41 秒 | **exit 0（完全不可见）** | exit 1，点名 C17a |
| A2 攻击：27 号行 round R55→R81（静默「改成诚实」） | exit 1，原因是 `R4 no round window for R081` | exit 1，点名 C17a（两边原因不同） |
| A3 攻击：删掉 28 号行 | exit 1（C11 R1 行数） | exit 1，点名 C17a |
| A4 攻击：只改 `C17_PIN` 一个元组 | —— | exit 1，`C17a 集合变了` |
| A5 反控：`C17_PIN_SHA256` 改错 1 个 hex | —— | exit 1，`C17a pin TAMPERED` |
| A6 反控：NOTE 计数不是恒 0 | —— | `checked=5 impossible=5 (pinned 5)` |
| A1b 作用域边界（事实登记） | —— | 给 claims-无 的 5 号纪律贴复制行 ⇒ exit 0（C17 只扫 claims-有；该行本就惰性，不构成得分路径） |

### 2.124.4 L3「通用包装器」：统计量排不掉，我不编赢家

R116 §EL 的 L3 是「0x7f7c80 的语义 = IPersistStream」，其替代解释「通用包装器顺带也用了它」挂了 R117/R119 两轮。本轮派 deepseek 执行员做判别性测量（卡面无反引号，`R120-EXEC-L3DISC.md`），主会话用**不同的函数边界判据**独立复算（`_r120/r120d_recompute_exec.py` 11/11 PASS、`_r120/r120e_controls_sensitivity.py` 8/8 PASS）。

复算得到的硬数字（两边一致）：

| 项 | 执行员 | 主会话独立复算 |
|---|---|---|
| IID 全镜像普查（COM 形状：d2==0、d3 低字==0x00C0、d4==0x46000000） | 11（.rdata 6 + .data 5） | **11，地址逐个相同** |
| 0x7f7c80 的 push 站点 | 60 | **60，站点地址逐个相同** |
| 0x7ed358 的 push 站点 | 7 | **7，站点地址逐个相同** |
| 指令流 | 1,392,527 | 1,392,706（分块 64 KiB；差 179 = 块边界的重同步点，不改变任何站点） |
| 「恰好 1 个不同 IID」的函数占比 | A/B/D/E 判据 100%，C 判据 93.24%（69/74） | C 判据 **93.24%（69/74），逐个相同** |

判据敏感性（这是本轮的核心发现，不是分布本身）：

- 执行员自己给了 **5 种**函数边界判据，占比分别为 100.00% / 100.00% / **93.24%** / 100.00% / 100.00%。
- 三种判据（int3 填充后首指令 / 终结指令后首指令 / nearest-preceding-entry）在 0x7f7c80 的 60 个站点上给出的归属函数**无一相同（60/60 分歧）**——因为判据粒度本身就不同（一种给整段、一种给子函数）。
- 「含 0x7f7c80 的 36 个函数全是恰好 1 个 IID」与「不含者的 38 个里 33 个恰好 1 个」的 2×2 表 = [[36,0],[33,5]]，Fisher 双尾 **p = 0.0546**（自实现，未装库）。

⇒ 结论只写判据支撑得住的那一句：**该特征在整个 .text 上已近普遍成立（93%–100%），且对边界判据敏感、p=0.0546 不显著 ⇒ 不能用它排除「通用包装器」解释。L3 维持「未排除」，不编赢家。**

### 2.124.5 自错 S-70..S-81（12 条，全部当场抓出）

S-70 沙箱无 `_r94/` ⇒ 基线假 FAIL（FILE_MISSING）；S-71 第 4 列是**相对 ROOT** 的路径，我把它拼到 R14 副本上又叠了一层目录；S-72 攻击打在作用域外（把 claims-无 的行当攻击面）；S-73 误以为「改 PIN 会触发 TAMPERED」，实际触发的是「集合变了」（sha 由实测集合算，改钉住常量不改实测）；S-74 只收「落在 IIDS 集里」的 push 立即数，于是 0x7ed358（不满足 COM 形状）被算成 0；S-75 把执行员的 55/55/0 抄成断言，自己实测 74/69/5；S-76 断言「去掉 d2==0 后命中必变多」，实测 11→11 不变（该条件在本镜像上冗余，真正在筛的是 d3 低字：11→12）；S-77 执行员 `q1_groups` 的 sites 是 hex **字符串**，我传 int ⇒ 60/60 假分歧；S-78 `io` 未 import 直接 NameError；S-79 断言 first-line 数字与 NOTE 正则不匹配；S-80 首次跑 `r120a` 时 4 条断言用「我预期的数」而不是实测数（A4/A5/N1/N2 全假 FAIL）；S-81 把「路径无轮次 token」猜成 4 条（1/2/9），实测只有 20 号。

### 2.124.6 收口

四脚本合计 **33 项断言全 PASS**（r120a 9 / r120b 6 / r120c 10 / r120d 11 / r120e 8 中除重复计 33），`r120c` 连跑两次一致；全程 `disasm_lite` 分块 64 KiB 流式（未整段 `detail=True`），脚本均带 timeout，收口前无孤儿进程；五项 CR 全绿 1081/137/337/0/2952；`check_disc.py` exit 0（GATE_VER=R120）。

### 2.124.7 未取得（不粉饰）

① 五条不可能行**未裁定**（改行/撤回/降级三条路都要单独裁，本轮只钉住）；② 窗口表**未扩**（扩表需要 55 份真实快照，本机没有）；③ L3「通用包装器」替代解释**仍未排除**；④ `0x7f7c70` 接口名（本机无 IID→名映射表）；⑤ `IPersistStream` 方法数；⑥ 35 个静态容器除 field0 外的运行期值；⑦ 门禁 C11 的 5 处「永远通过」子项只动了「C11 五条 ok 不可信」这一条证据面，其余四处未动；⑧ 0x7f7c80 的 60 个站点里，除「函数内 IID 个数」外我没有找到第二个不依赖函数边界的量（这一条已写进审计卡 B3 请审计员找）。
'''

SEG_LEDGER = '''
## §1174 R120 · C11 的五条 ok 是跨轮复制；C17 钉住；L3 通用包装器排不掉

- **C11 的 ok=5 不可信（两个独立量）**：① 路径轮次 —— 五条行全部声称 R55，产物却在 R61/R81/R84/R88 的目录里（5/5 命中）；② 时刻复用 —— `at=2026-11-22T17:39:19+08:00` 复用于 4 个不同轮次目录。两量不共用字节。反控：改声称轮次 → 0 命中；改路径轮次 → 0 命中；全树 26 条自述行里「时间上可能」的正常行 = **0 条**（事实登记，不是断言绿）。
- **根因（R119 未查明）**：`recheck_verify.ROUND_WINDOWS` 只覆盖 R36..R65（28 轮，缺 41/42），盘上已到 R120 ⇒ **为本轮产物写的诚实行在结构上必然 R4 FAIL**。正控实测：`round=R88` 的诚实行被判 `no round window`。⇒ 门禁在奖励「声称旧轮次」。
- **C17 家族（GATE_VER R119→R120）**：C17a 钉「时间不可能行的 (id, 轮次, at) 集合 + 集合 sha256」；C17b 钉「同一 at 秒值的跨轮复用下限」。成对回归 **10/10 PASS 连跑两次一致**：A1（窗口内平移 41 秒）旧 gate **exit 0 完全不可见** → 新 gate 点名 C17a；A2/A3（静默改轮次 / 删行）新 gate 点名 C17a；A4（只改 PIN 元组）⇒ 集合变了；A5（sha 改 1 个 hex）⇒ pin TAMPERED；P2 正控（追加诚实 round=R64 行）⇒ C17 不开火。
- **L3「通用包装器」排不掉**：0x7f7c80 的 60 个 push 站点、0x7ed358 的 7 个站点、IID 普查 11 个地址，执行员与主会话**逐个相同**（后者用 nearest-preceding-entry，与执行员的 CFG 前驱走实现完全不同）。但「恰好 1 个不同 IID」这个特征执行员的 **5 种边界判据**给出 100% / 100% / **93.24%** / 100% / 100%，三种判据在 60 个站点上归属函数**无一相同**，2×2 [[36,0],[33,5]] 的 Fisher p=**0.0546**（不显著）⇒ 该特征无判别力，L3 维持「**未排除**」，不编赢家。
- **未取得**：五条不可能行未裁定；窗口表未扩（需 55 份真实快照）；L3 未排除；0x7f7c70 接口名；IPersistStream 方法数；35 个静态容器运行期值；C11 其余 4 处「永远通过」未动。
'''

SEG_LOCK = '''
## EM · R17 第 120 轮（2026-11-24 20:0x–21:0x）· C11 报的 ok=5 是**跨轮复制**：五条行声称 R55 而产物在 R61/R81/R84/R88；根因是窗口表只到 R65 ⇒ 诚实行结构上必挂

EM1. **本轮先审的是「门禁自己的绿」**，不是再找一条链。R119 收口时 C11 报 `ok=5 fail=0`，我此前一直把这 5 条当作「真回跑的样本」。本轮用两个不共用字节的量把它推翻。

EM2. **量一（路径轮次）**：产物路径里的 R<n> token 是「该文件所在轮次」的下界。三条行（3、4 号）在 `R17_R61_FACTINDEX_V58/`、22 号在 `R17_R84_T1_NARRATIVE/`、27 号在 `R17_R81_T2_EVID/`、28 号在 `R17_R88_T1_SEMDEF/`，**全部声称 round=R55** ⇒ 5/5 时间上不可能。

EM3. **量二（时刻复用）**：`at=2026-11-22T17:39:19+08:00` 这一个秒值出现在 **4 个不同轮次目录**的产物里（61/81/84/88）。真回跑是「本轮为本轮产物各写一条」，不可能让三个不同轮次的产物共享同一秒。两量命中的 id 集合一致。

EM4. **根因（这是 R119 没查的）**：`recheck_verify.ROUND_WINDOWS` 的键空间 = **28 轮 [36..65]，缺号 41、42**（主快照 30 份、同轮重复 5 份），从 `R17_LEAD_BASELINE/STATUS_BOARD.before_rN_HHMMSS.md` 推导；盘上实际已到 **R120**，**46 个**轮次有目录无窗口。正控：为 28 号行写一条 `round=R88` 的**诚实**行 ⇒ `R4 no round window for R088`。⇒ **能通过的唯一办法是声称 <=65 的旧轮次。门禁在奖励伪造。**

EM5. **反控：扩表不是改代码那么简单。** 只把 ROUND_WINDOWS 扩到 R66..R120（不动磁盘）⇒ 五条行**全部**被判 `W table widened: W1 endpoint of R66 not a snapshot instant`。扩表必须同时伪造 55 份快照文件（端点溯源自检是 R94 加的，此处证明它有牙）。

EM6. **C17 家族（GATE_VER R119→R120）**：C17a 钉「时间不可能行的 (id, 轮次, at) 三元组集合」+ 集合 sha256；C17b 钉「同一 at 秒值的跨轮复用下限」。**它不改任何自述行** —— 改行是裁定，须单独裁；本轮只把已存在的五条不可能行钉住，使「悄悄改成诚实」与「再添一条同类」都必须显式改常量。

EM7. **成对回归 `_r120/r120c_gate_c17.py` 10/10 PASS 连跑两次一致**（旧 gate 用 R119 备份 + 旧 TSV 配套）：A1「27 号行 at 在 R55 窗口内平移 41 秒」——旧 gate **exit 0 完全不可见**，新 gate 点名 C17a。这是本轮最有判别力的一条：平移 41 秒不破坏任何自洽性（anchors 绑第 4 列、R3 只比立条上界、R4 只看窗口），旧 gate 结构上看不见它。A2（静默改轮次）、A3（删行）也都被 C17a 抓到，且与旧 gate 的 FAIL 原因不同（旧 gate 走的是 C11 R1/R4）。A4 只改 PIN 元组 ⇒ 「集合变了」；A5 sha 改 1 个 hex ⇒ 「pin TAMPERED」；P2 正控（追加诚实 round=R64 行）⇒ C17 不开火。

EM8. **L3「通用包装器」用统计量排不掉，我不编赢家。** deepseek 执行员（卡面无反引号）做判别性测量，我用 **nearest-preceding-entry** 判据独立复算（与它的 CFG 前驱走完全不同）：IID 普查 11 个地址、0x7f7c80 的 60 个站点、0x7ed358 的 7 个站点，**逐个相同**。但「恰好 1 个不同 IID」这个特征：执行员自己 5 种边界判据给出 100%/100%/**93.24%**/100%/100%；三种判据在 60 个站点上归属函数**无一相同**；2×2 [[36,0],[33,5]] 的 Fisher p=**0.0546**。⇒ 该特征在整个 .text 上已近普遍成立、且对判据敏感 ⇒ **无判别力**，L3 维持「未排除」。

EM9. **规则 D**：exec deepseek task 223 —— `cancelled`，**35.07 分钟 vs 预算 12 分钟 [OVERTIME]**，`num_turns=0`（harness 侧未记回合），产物 q1/q2/q3/q4 与 core/report 大部分落盘但 **report 未写**。故其任何结论我都不采信，只用它落盘的**原始数字**，并用 `r120d`（11/11）+ `r120e`（8/8）亲自复算。它的 q4 有一处自报 `b_drop_dword1_eq_0` 的 `strictly_greater=false`，与我的复算一致（d2 条件在本镜像冗余）—— 这条与我的 S-76 是同一个发现，两边独立得出。

EM10. **🐞 自错 S-70..S-81（12 条，全部当场抓出）**：S-70 沙箱缺 `_r94/` ⇒ 假 FAIL；S-71 第 4 列是相对 ROOT 的路径，我拼到 R14 副本上又叠一层；S-72 攻击打在作用域外（拿 claims-无 的行当攻击面，实测 exit 0）；S-73 误以为改 PIN 会触发 TAMPERED（实际是「集合变了」，sha 由实测集合算）；S-74 只收 IIDS 集内的 push ⇒ 0x7ed358 被算成 0（它不满足 COM 形状）；S-75 把执行员的 55/55/0 抄成断言，自己实测 74/69/5；S-76 断言「去掉 d2==0 命中必变多」，实测 11→11 不变（冗余条件），真正在筛的是 d3 低字（11→12）；S-77 把 hex 字符串当 int 比对 ⇒ 60/60 假分歧；S-78 `io` 未 import；S-79 NOTE 正则与首行数字不匹配；S-80 `r120a` 首版 4 条断言写成「我预期的数」而非实测数（全假 FAIL）；S-81 把「路径无轮次 token」猜成 4 条，实测只有 20 号。

EM11. **收口**：四脚本 33 项断言（按去重口径）全 PASS；`r120c` 连跑两次一致；全程 `disasm_lite` 分块 64 KiB 流式，未整段 `detail=True`；脚本均带 timeout；收口前确认无孤儿进程。五项 CR 全绿 1081/137/337/0/2952；`check_disc.py` exit 0（GATE_VER=R120）。

EM12. **未取得**：① 五条不可能行未裁定（改/撤/降级三条路都要单独裁）；② 窗口表未扩（缺 55 份真实快照）；③ L3 通用包装器仍未排除；④ 0x7f7c70 接口名；⑤ IPersistStream 方法数；⑥ 35 个静态容器除 field0 外的运行期值；⑦ C11 另外 4 处「永远通过」子项未动；⑧ 0x7f7c80 的 60 个站点里我还没找到第二个不依赖函数边界的量（已写进审计卡 B3 请审计员找）。
'''

SEG_BOARD = '''
## 🟢 R17 第 120 轮（2026-11-24 20:0x–21:0x）· C11 报的 ok=5 是**跨轮复制**（五条行声称 R55 而产物在 R61/R81/R84/R88）；门禁装 C17 钉住；L3「通用包装器」用统计量**排不掉**

**主攻**：① R119 收口时 C11 的 `ok=5` 到底是不是真回跑；② R116 §EL 挂三轮的 L3 替代解释能否用统计量排除。② 的答案是**排不掉**。

### 一 · C11 的 ok=5 是五条时间上不可能的行

两个不共用字节的量（`_r120/r120a_anachrony.py` 9/9 PASS）：

| 量 | 判据 | 实测 |
|---|---|---|
| 路径轮次 | 声称轮次 < 产物路径轮次 ⇒ 时间上不可能 | **5/5 命中**：3、4 号在 R61；22 号 R84；27 号 R81；28 号 R88；全声称 R55 |
| 时刻复用 | 同一 at 秒值跨多个轮次目录 | `17:39:19` 复用于 **4 个**轮次目录（61/81/84/88） |

反控：改声称轮次 ⇒ 0 命中；改路径轮次 ⇒ 0 命中；全树 26 条自述行里「时间上可能」的正常行 = **0 条**（事实登记）。

### 二 · 根因：窗口表只到 R65，诚实行结构上必挂

`ROUND_WINDOWS` 键空间 = **28 轮 [36..65]，缺 41/42**（主快照 30 份、重复 5 份，从 `STATUS_BOARD.before_rN_HHMMSS.md` 推导）；盘上已到 **R120**，**46 个**轮次有目录无窗口。

- 正控：为 28 号行写 `round=R88` 的**诚实**行 ⇒ `R4 no round window for R088`。**诚实行必挂。**
- 反控：只把表扩到 R120（不动磁盘）⇒ 五条行全部被判 `W table widened: R66 endpoint not a snapshot instant` ⇒ 扩表必须伪造 55 份快照。

⇒ 能通过的唯一办法是声称旧轮次，**门禁在奖励伪造**（R119 未查明这一点）。

### 三 · 门禁 C17 家族（GATE_VER R119→R120）

| 子项 | 判据 | 分工 |
|---|---|---|
| C17a | 时间不可能行的 (id, 轮次, at) 集合必须逐一等于 `C17_PIN`，且集合 sha256 相符 | 集合比抓「行变了」；sha 钉抓「常量改成与实测不符」 |
| C17b | 同一 at 秒值跨轮次目录的复用数 >= 下限，且不得出现表外新值 | 第二个独立特征，与 C17a 不共用字节 |

成对回归 **10/10 PASS 连跑两次一致**：

| 变异 | 旧 gate | 新 gate |
|---|---|---|
| A1：27 号行 at 窗口内平移 41 秒 | **exit 0（完全不可见）** | exit 1，点名 C17a |
| A2：27 号行 R55→R81 | exit 1（R4 无窗口） | exit 1，点名 C17a |
| A3：删 28 号行 | exit 1（C11 R1） | exit 1，点名 C17a |
| A4：只改 PIN 一个元组 | —— | 集合变了 |
| A5：sha 改 1 个 hex | —— | pin TAMPERED |
| P2 正控：追加诚实行 round=R64 | —— | C17 不开火 |

### 四 · L3「通用包装器」：统计量排不掉，不编赢家

执行员与主会话**逐个相同**的硬数字：IID 普查 **11**（.rdata 6 + .data 5）、0x7f7c80 的 push 站点 **60**、0x7ed358 的 **7**（主会话用 nearest-preceding-entry，执行员用 CFG 前驱走）。

但判据敏感性把结论推翻：执行员自己 **5 种**边界判据给出 100% / 100% / **93.24%** / 100% / 100%；三种判据在 60 个站点上归属函数**无一相同**；2×2 [[36,0],[33,5]] Fisher **p=0.0546**（不显著）。

⇒ 「一个函数只碰一个 IID」在整个 .text 上已近普遍成立且对判据敏感 ⇒ **无判别力**，L3 维持「**未排除**」。

### 五 · 跨家族

**exec deepseek task 223**：`cancelled` / **35.07 分钟 vs 预算 12 [OVERTIME]** / `num_turns=0`，report 未写 ⇒ 结论不采信，只用其落盘原始数字，主会话 `r120d` **11/11** + `r120e` **8/8** 亲自复算。它 q4 自报 `b_drop_dword1_eq_0 strictly_greater=false`，与我的 S-76 独立同源。

### 六 · 自错 S-70..S-81（12 条，全部当场抓出）

S-70 沙箱缺 `_r94` 假 FAIL；S-71 第 4 列路径相对 ROOT 我叠了一层目录；S-72 攻击打在 claims-无（作用域外）；S-73 以为改 PIN 触发 TAMPERED（实为集合变了）；S-74 只收 IIDS 集内 push ⇒ 0x7ed358 算成 0；S-75 把执行员 55/55/0 抄成断言（实测 74/69/5）；S-76 断言「去 d2 必变多」，实测 11→11（冗余，真在筛的是 d3 低字 11→12）；S-77 hex 字符串当 int ⇒ 60/60 假分歧；S-78 `io` 未 import；S-79 NOTE 正则不匹配；S-80 `r120a` 首版 4 条断言写成预期数；S-81 猜「无轮次 token」4 条，实测只有 20 号。

### 七 · 未取得

① 五条不可能行**未裁定**（改/撤/降级都须单独裁）；② 窗口表未扩（缺 55 份真实快照）；③ L3 仍未排除；④ 0x7f7c70 接口名；⑤ IPersistStream 方法数；⑥ 35 个容器运行期值；⑦ C11 另外 4 处「永远通过」未动；⑧ 0x7f7c80 的 60 站点里还没找到第二个不依赖函数边界的量（已请审计员找）。
'''


def main():
    # ---- 备份 + 断言 CR ----
    for k, (p, cr) in TARGETS.items():
        assert os.path.isfile(p), p
        check_cr(p, cr)
        backup(p, k.lower())

    # ---- 三段追加 ----
    for name, seg, cr in (('R14_COMMON', SEG_COMMON, 1081),
                          ('LEDGER', SEG_LEDGER, 337),
                          ('LEAD_LOCK', SEG_LOCK, 137),
                          ('STATUS_BOARD', SEG_BOARD, 0)):
        p = TARGETS[name][0]
        old = io.open(p, encoding='utf-8', newline='').read()
        assert '\r' not in seg, name + ' segment has CR'
        assert seg.startswith('\n'), name + ' segment must start with LF (Write tool ate it before, S-68)'
        new = old + seg
        with io.open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(new)
        # 回读校验
        got = io.open(p, encoding='utf-8', newline='').read()
        assert got == new, name + ' readback mismatch'
        cr_now = io.open(p, 'rb').read().count(b'\r\n')
        assert cr_now == cr, (name, cr_now, cr)
        assert seg.strip()[-40:] in got
        log('%s +%d B, CR=%d (unchanged), total=%d B, lines=%d'
            % (name, len(seg.encode()), cr_now, len(got.encode()), len(got.split('\n'))))

    # ---- 门禁复跑 ----
    import subprocess
    r = subprocess.run([sys.executable, os.path.join(R14, 'check_disc.py')],
                       cwd=R14, capture_output=True, text=True, timeout=300)
    log('gate exit=%d ; tail=%s' % (r.returncode, (r.stdout or '').strip().split('\n')[-1]))
    assert r.returncode == 0, (r.stdout or '')[-1500:]

    io.open(os.path.join(ROOT, '_r120', 'write_r120.log'), 'w', encoding='utf-8').write('\n'.join(LOG))
    print('ALL OK')


if __name__ == '__main__':
    main()
