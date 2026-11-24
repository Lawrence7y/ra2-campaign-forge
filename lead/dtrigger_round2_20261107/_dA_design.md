# 新判据族设计（禁止调参）· 离线核算说明

唯一写域：`lead/dtrigger_round2_20261107/`，本件为 `_dA_` 前缀新文件之一。
零真机（不启动 gamemd.exe / ra2loader / YURI.exe，不 taskkill，不读活进程内存）；零采样代码
（无 hook / MiniDump / SuspendThread / StackWalk / 探针注入，无 ctypes / OpenProcess /
ReadProcessMemory / WriteProcessMemory / VirtualAllocEx / CreateRemoteThread / SetWindowsHookEx /
TerminateProcess 及其动态解析）；只读语料与既有件；不 commit、不 push；
Python 全部 `python -I -X utf8` + 绝对路径；指纹用 Python `hashlib`（本机无 sha256sum / wc）。

**引用路径约定**：无目录前缀的 `*.md` / `*_out.txt` / `*.json` / `*.py` 均指
`D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/<文件名>`；
`CRITERIA_COMPARE.md` / `_cost_quota_data.json` / `CRITERIA_METRICS.json` 等带目录前缀的指
`lead/dtrigger_compare_20261107/<文件名>`；`STALL_EVENT_DEFINITION.md` 指
`lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md`；`RULING_D30.md` 指
`lead/d30_ruling_20261106/RULING_D30.md`；`S_OBSERVABILITY.md` 指
`lead/dstart_observable_20261107/S_OBSERVABILITY.md`。

---

## 1 本轮题目与边界

题给「新判据族设计（禁止调参）」：设计**不同于既有 C1–C5** 的新「在线因果」判据族；
明确禁止仅调整 k 值、P95/P99 倍数、滑窗 N、或加 40ms CAP —— 这些是
`CRITERIA_COMPARE.md:112-147` 的 26 档已覆盖的调参。可用信息只限语料已有的 `(t,f)` 前缀
（帧间隔序列形状、连续短间隔模式、相邻游程关系等），必须在线因果：只读 `t[runStart..i]`
与 `i` 之前的已完成历史，不读 `endTick` / `durationMs` / `isRealMatch` / 最终 `d≥100ms`；
事后标签只允许用于触发后计费。要求三维离线比较：① `:177` 及时性（S_hat 锚是下界，
须说明 e 修正）；② 区分度（误触发先到先得抢占配额后的真实捕获）；③ 配额 `N=1/3/5`。
若判定 `(t,f)` 前缀信息上界使三者不可兼得，必须给出可判定的形式化证据
（例如前缀不可分辨的计数上界），不许只写断言。

**本件结论（先给，证据见 §3–§5）**：三者不可兼得，且给出四条**可判定**的形式化计数上/下界；
其中三条（配额硬上界、存活集基准率、e 硬上界）对**任意** `(t,f)` 前缀谓词无条件成立，
一条（命中集 LB1）限定于本题给定的「形状/序数/相邻游程」特征类。`_dA_out.txt:191-257` 是全部实跑数字。

---

## 2 判据族定义：D1–D5（11 档，全部非调参）

### 2.1 共同字母表与「已完成历史」（结构性定义，非阈值调参）

`t` 的存储精度为 1e-6 s；相邻采样间隔 `g = t[x]−t[x−1]`（ms）落入 5 个**序数桶**
（`_dA_run.py:249-251`）：

| 字母 | 含义 | 区间 (ms) |
|---|---|---|
| S | 极短（密集拍/同帧多次读取） | `g < 0.05` |
| M | 中等 | `0.05 ≤ g < 0.5` |
| L | 长 | `0.5 ≤ g < 2` |
| X | 很长 | `2 ≤ g < 5` |
| G | 掉拍级 | `g ≥ 5` |

`_independent_recheck_findings_out.txt:9-11` 已实跑：`间隔<0.05ms` 占 127861/747437
= 17.107%，`>10ms` 有 1667 条（`CRITERIA_COMPARE.md:102-104` 转引）。故该字母表在语料上非退化。
已完成历史只取 `runStart` 之前：前一帧周期 `D = hist[he−1]`（`hist` = 帧沿到帧沿的帧周期，
与 `CRITERIA_COMPARE.md:99-101` 同口径）、前一游程最短/最长间隔、前一游程长度桶。
**冷启动不足**（`startTick=0` 的 64 条游程）不触发，不猜测。

### 2.2 逐族规则（`_dA_run.py:255-358`）

| id | 族 | 规则（在线因果，每游程最多 1 次触发） | 需要的历史 | 与 C1–C5 的结构差异 |
|---|---|---|---|---|
| `D1-word-MMM` | D1 形状字 | 间隔字首次包含 `MMM` 且已≥3 项 | `t[runStart..i]` 相邻间隔 | 有限自动机匹配字母序列，非计数/分位/时长 |
| `D1-word-LLL` | D1 形状字 | 同上，字 `LLL` | 同上 | 同上 |
| `D1-word-G` | D1 形状字 | 任一 `G` 且已≥3 项间隔（掉拍肘点） | 同上 | 同上 |
| `D2-run-S4` | D2 短间隔游程 | 连续 4 个 `S` 字母 | 同上 | 连续短间隔的**游程长度**，非帧号不变拍数 k |
| `D2-run-M6` | D2 短间隔游程 | 连续 6 个 `M` 字母 | 同上 | 同上（本语料零触发，见 §4） |
| `D3-min>prev` | D3 相邻游程 | 当前前缀最短间隔 > 前一已完成游程最短间隔（≥3 拍） | 前一游程最短间隔 | 用**相邻游程关系**，C1–C5 全无 |
| `D3-flip` | D3 相邻游程 | 当前首间隔序数跳到 L/X/G 且与前游程首字不同 | 前一游程首间隔 | 同上 |
| `D4-rising` | D4 肘形 | 连续 3 项相邻间隔严格递增（局部减速） | `t[runStart..i]` 间隔序数 | 序数单调性，非任何阈值 |
| `D4-burst` | D4 肘形 | 相邻间隔由短(<0.5ms)突变到长(≥2ms) | 同上 | 短→长肘点，非绝对 elapsed |
| `D5-phase` | D5 相位序数 | `elapsed` 跨过前一帧周期 `D` 的**整数商**边界且间隔字变化 | 前一帧周期 `D` | 用 `D` 作相位标尺的整数跳变，非 `elapsed/D > 倍率`（C3） |
| `D5-ordinal` | D5 相位序数 | 当前前缀 L/X/G 序数计数超过前一游程同计数 | 前一游程形状 | 序数计数比较，非分位/倍率 |

**禁止项自检**（`_dA_out.txt:31-32`）：扫描 id/定义中的 `P95` / `P99` / `CAP` / `percentile`
命中 `[]`（空=通过）。D1–D5 共 11 档；`CAL-*` 4 档只是校准基线（C1-k10 / C1-k25 /
C4-t40 / C5-k10t30），不并入新判据结论。
`_dA_out.txt:260-272` 逐档核对：与 `C1-k10` 共同触发的游程中，触发拍不同的比例
96.14%–100%（`D2-run-M6` 零触发，单列 DEGENERATE）；即**不是换名调参**。

### 2.3 在线因果性的代码级保证

`build_trig`（`_dA_run.py:430-445`）对每个游程调用 `fn(r)` 求触发采样点 `idx`，
`fn` 只读 `r["T"][i..idx]`、`r["hist"][:he]`、`r["D"]` / `r["prev_min"]` / `r["prev_len"]`
（全部 `≤ i−1` 的已完成历史）。`r["dfin"]` / `r["is_real"]` / `r["e"]` 只在
`build_trig` **拿到 idx 之后**才写入 trig 元组用于事后计费与 :177 核算，从未传入 `fn`。
`durationMs` / `endTick` / 最终 `d≥100ms` 在触发路径中完全不出现；
`dfin<100` 只用于 `falseTriggers` 计费（`_dA_run.py:466`），与
`CRITERIA_COMPARE.md:195-198` 的口径 B 一致。

---

## 3 :177 及时性与 e 修正

- 语料只有 `(t,f)`；观测锚 `S_hat = t[runStart]`，物理起点
  `S ∈ (t[runStart−1], t[runStart]]`，`S_hat−S ∈ [0, e]`，
  `e = t[runStart]−t[runStart−1]`（题给 `CRITERIA_COMPARE.md:93-98`；
  `S_OBSERVABILITY.md:48-62`）。
- 本轮实跑逐游程 `e`（`_dA_out.txt:27`）：有效 `n=28317`（首拍游程 64 条 `e 未验`），
  `min=0.008 / med=2.511 / P99=4.145 / max=488.616 ms`，与
  `_dtrigger_probe_out.txt:245-250` 完全一致。
- **因此所有 `waitAfterS_hat` / `latP50` 都是下界**：真实等待
  `= waitAfterS_hat + (S_hat−S) ≥ waitAfterS_hat`。本件的严格合规口径为
  `waitAfterS_hat + e ≤ 50ms`（逐游程，不是 `CRITERIA_COMPARE.md:222-223` 只加中位常数 2.511ms
  的近似），分母固定 1681（含漏检、含 `e 未验` 按不合规计 0）。
- 逐档 `in50_strict` 见 `_dA_out.txt:49-65` 的 `in50s` 列与 `:67-188` 明细。
  最好的是 `D4-burst` = **1569/1681 = 93.3373%**（`:160`），`D4-rising` = 1555/1681（`:149`），
  `D3-min>prev` = 1521/1681（`:127`）；而区分度较好的 `D5-phase` 只有 18/1681（`:171`）、
  `D1-word-MMM` = 0/1681（`:72`）。
- **e 硬上界**（`_dA_out.txt:252-253`）：真实事件中 `e>50ms` 有 56 条、
  `startTick=0` 的 `e 未验` 有 4 条，合计 60/1681 无法给出 :177 严格合规证明；故
  `in50_strict ≤ 1621/1681 = 96.4307%` 是**任何 `(t,f)` 前缀判据的上确界**。
  `e` 的最大值 488.616ms 是采样掉拍，不证明线程被卡（`RULING_D30.md:78`）。

---

## 4 三维离线比较（实跑数字，全部来自 `_dA_run.py`）

主表 `_dA_out.txt:49-65`；逐档 6 格配额明细 `:67-188`。语料 `n=104` 文件 /
`1125992` 采样点 / `hz=[500]` / 64 推进窗 / 28381 游程 / 1681 真实事件（`:21-25`），
与 `CRITERIA_COMPARE.md:39-41` 一致。校准：`_dA_out.txt:35-40` 独立重算 4 档既有判据，
triggers / realHits / W1W3W5 / T1T3T5 逐格与 `_cost_quota_data.json` 全等，`PASS=4 FAIL=0`。

| id | ① in50_strict /1681 | ② falseRate | ② W5 captured | ③ W1/W3/W5 | ③ T1/T3/T5 | Qfalse@W5 |
|---|---:|---:|---:|---|---|---:|
| `D1-word-MMM` | 0 | 0.000% | 7 | 4/7/7 | 2/6/7 | 1 |
| `D1-word-LLL` | 0 | 0.000% | 0 | 0/0/0 | 0/0/0 | 1 |
| `D1-word-G` | 170 | 26.880% | 37 | 10/25/37 | 4/12/22 | 68 |
| `D2-run-S4` | 151 | 18.852% | 30 | 7/18/30 | 4/12/20 | 17 |
| `D2-run-M6` | 0 | N/A（零触发） | 0 | 0/0/0 | 0/0/0 | 0 |
| `D3-min>prev` | 1521 | 93.189% | 46 | 8/26/46 | 5/14/20 | 273 |
| `D3-flip` | 302 | 93.905% | 49 | 10/30/49 | 6/13/19 | 260 |
| `D4-rising` | 1555 | 93.879% | 40 | 4/23/40 | 3/13/20 | 280 |
| `D4-burst` | 1569 | 93.990% | 41 | 4/23/41 | 3/13/21 | 279 |
| `D5-phase` | 18 | 80.738% | **66** | 13/40/66 | 5/16/27 | 235 |
| `D5-ordinal` | 38 | 85.195% | 64 | 8/35/64 | 5/16/27 | 251 |

读数：
- **及时性占优者区分度差**：`D4-burst` in50_strict=1569/1681，但 falseRate=93.990%、
  W5 捕获仅 41/1681（误触发吃掉 279 个 W5 配额槽）。
- **区分度/捕获占优者及时性差**：`D5-phase` W5=66/1681（本轮最佳，`_dA_out.txt:199`），
  但 `latP50=105.151ms`（`:170`）、in50_strict=18/1681，已越过 :177 的 S+50ms。
- **零误报档召回收缩**：`D1-word-MMM` falseRate=0 但只命中 7/1681；
  `D2-run-M6` 在本语料零触发（`:59`，单列 DEGENERATE，不并入结论）。
- **口径 B 伪影单独计数**：`D1-word-LLL` 唯一 1 次触发是 `dfin≥100` 但
  `isRealMatch=False` 的窗尾终局冻结伪影（`CRITERIA_COMPARE.md:238-240` 同类 23 条），
  按口径 B 不计为误触发（falseRate=0），但它**仍消耗 1 个 W5 配额槽**
  （`_dA_data.json` 中 `Qfalse@W5=1`）；`D1-word-MMM` 的 8 次触发中也有 1 次同类伪影。
  故「falseRate=0」不等于「零配额占用」，与 `CRITERIA_COMPARE.md:238-240` 的计费口径缺口一致。
- 配额 `N=1/3/5` 单调不减且全部 `≤` 理想值（自检 `_dA_check.txt:5-6`）；
  每窗理想 26/73/117、每会话理想 12/31/47（`_dA_out.txt:29`）。

---

## 5 形式化证据：三者不可兼得（可判定的计数上/下界）

**证据① 配额硬上界（谓词无关，`_dA_out.txt:191-201`）**。
每游程最多 1 次触发（本 runner 的 `build_trig` 与 `CRITERIA_COMPARE.md:193-194` 同口径），
每配额组 `(trip,window)` 前 `N` 次触发消耗 `N` 槽，每槽最多对应 1 个真实事件，故
`captured ≤ Σ_w min(N, c_w) = 26/73/117`（N=1/3/5），与谓词、前缀形状、误触发多少
**完全无关**（误触发只会让 captured 更小）。实跑 W5 最佳 66/1681（`D5-phase`），
上确界 117/1681 = 6.96%。**即使存在一个「:177 全合规 + 零误触发」的完美谓词，
N=5 仍至少放弃 1564/1681 = 93.04% 真实事件**（`:254`）。

**证据② 存活集基准率（对任意 `(t,f)` 前缀谓词的单次触发查准率上界，`_dA_out.txt:203-224`）**。
若谓词在 `elapsed=τ` 处触发，该游程必须 `dfin>τ`（帧仍冻结），触发母体只能是
`A(τ)={r: dfin>τ}`，故 `P(该次为真实 | 在 τ 处触发) ≤ A_real(τ)/A(τ)`。
实跑（`逐 τ 计数`）：τ=10ms → 5.9322%，τ=30ms → 10.4958%，τ=40ms → 27.8727%，
**τ=50ms → 33.2279%**（`_dA_out.txt:216`）。该序列对 τ 单调不减（本次实跑 13 个 τ 全部
`monotone_up`，命令见 §7），故混合 `a≤50ms` 触发的谓词总查准率 `≤ max_{a≤50} = 33.2279%`。
只有 τ≥100ms 才能排除全部 `dfin<100` 假游程（τ=100 时 `A_falseB=0`，`:222`），
但那越过 :177 的 S+50ms 且被 `:190` 拒止（累计判定 ≥100ms 不合格，
`STALL_EVENT_DEFINITION.md:191`）。

**证据③ 前缀签名命中集下界（限定特征类，`_dA_out.txt:226-249`）**。
设 `σ(r,a)` = 平移不变前缀签名（间隔形状字 + 前一帧周期桶 + 前一游程长度桶），
`φ` 为仅依赖 `σ` 的确定性函数型谓词。每条 real 的可选前缀集 `S_R={σ(R,a): a≤τ}`，
`U=∪_R S_R`；`c(s)=#{F: dfin<100 且 s∈S_F}`。若 `φ` 覆盖全部有前缀 real，
其接受集 `W` 必须命中每条 `S_R`（命中集问题），强制误触发
`forced_FP(W)=#{F: S_F∩W≠∅}`（去重；每个 F 每游程最多触发 1 次）。
- 下界 `LB1 = max_R min_{s∈S_R} c(s)`：为覆盖最贵的那条 R，`W` 至少含一个 `s∈S_R`，
  该 `s` 单独就使 `≥ min_{S_R} c` 个不同 F 被强制触发。
  实跑 τ=18ms → `LB1=4056`，任意 φ 的 `precision ≤ 29.1899%`；
  τ=50ms → `LB1=1638`，`precision ≤ 50.6031%`（`:238,:243`）。
- `UB_naive = #{F: S_F∩U≠∅} = 26617`（τ=18..50 不变）是「朴素 φ=接受 U」的
  **一次实跑**，不是所有 φ 的公共下界；本件明确只把 `LB1` 当作通用下界，
  `UB_naive` 仅参考（`:244-246`）。
- **空前缀计数上界**：τ=18ms 有 **9 条 real** 在 `≤18ms` 内没有任何采样间隔前缀
  （首拍/掉拍），τ=50ms 仍有 3 条；故「τ 内触发全部 1681」在语料上**直接不可达**，
  与 φ 选法无关（`:247-248`）。
- 交叉核验：`_dA_probe.py` 用独立签名实现（含 1µs 全精度差值签名）给出同一
  `LB1=4056/1638` 与 `U_R=2980/15358`（`_dA_probe_out.txt:71-74`），两脚本一致。

**证据④ :177 严格合规 + 全召回 + 区分度三者不可兼得（`_dA_out.txt:251-257`）**。
`in50_strict ≤ 1621/1681`（e 硬上界，60 条 e 不可判定）、
`captured ≤ Σmin(N,c_w)`（证据①）、`precision(≤50ms) ≤ 33.2279%`（证据②），
三者上确界互不相容于「全都要」；证据③给出限定特征类下更紧的可判定下界。
**判定：不可兼得，且不是「调参」能绕过的** —— 证据①②④ 对任意 `(t,f)` 前缀谓词成立。

**诚实边界（不作过度断言）**：证据③的 `LB1` 限定于「形状/序数/相邻游程摘要」特征类。
对**任意实值函数型谓词**（利用绝对 t 值、跨窗全局身份、全精度 1µs 差值记忆），
`_dA_probe_out.txt:75-76` 显示 1µs 精确签名下 `LB1=0`、朴素 φ 的 `UB_naive=1`，
故本件**不作**「任意谓词皆不可能」的信息论级断言，单列于 U5。
但证据①配额硬上界、证据②存活集基准率、证据④ e 硬上界对这类谓词**仍无条件成立**。

---

## 6 未验项（单列，不并入结论）

`_dA_out.txt:275-283` 逐条列出 U1–U8，摘要：
1. 物理起点 S 的微秒点估计语料不可得，:177 严格闭环证明未验（`STALL_EVENT_DEFINITION.md:177`、`S_OBSERVABILITY.md §5.3`）。
2. 4 条 `startTick=0` 的真实事件 e 未验（S 落在观测窗外），按不合规计 0，未外推。
3. :190 端到端延迟、:191 累计判定、Q5 四项扰动：零采样代码，全部未验（`RULING_D30.md:22,78`）。
4. 内部状态旗标 IN_TACTICAL/SCORE_SCREEN/PAUSED/LOADING：语料缺（`RULING_D30.md:54`）。
5. 证据③ LB1 的特征类限定；对任意实值函数型谓词的信息论级断言未验（见 §5 诚实边界）。
6. 触发后保存动作是否成功、线程上下文是否在 S+50ms 内保存、跨硬件/场景外推：未验（`STALL_EVENT_DEFINITION.md:170,179`）。
7. D1–D5 字母表边界与游程长度是结构性定义，未做超参数敏感性扫描；按题给禁止项，本件不做 k/P95-P99/滑窗 N/CAP 扫描。
8. 配额「先到先得」是离线模拟，非在线保证；窗间 4s 空白与跨窗边界截断未验（`STALL_EVENT_DEFINITION.md:178`）。

---

## 7 实跑命令与输出（全部 `python -I -X utf8` + 绝对路径）

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dA_probe.py
  -> exit 0；输出 _dA_probe_out.txt（7976 bytes）、_dA_probe_stdout.txt
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dtrigger_round2_20261107/_dA_run.py
  -> exit 0；输出 _dA_out.txt / _dA_data.json / _dA_check.txt / _dA_stdout.txt
python -I -X utf8 -c '<内联只读核对>'
  -> 逐 τ 核对 base_rate 单调性（13 个 τ 全部 monotone_up）；
     逐 τ 核对真实事件 e 分布（e>50 n=56 / e 未验 n=4 / e<=50 n=1621）；
     核对 7 项题给上游指纹全部 MATCH。
```

自检 `_dA_check.txt:1-14`：`PASS=12 FAIL=0`。
题给上游 7 项指纹逐条 `MATCH`（`_dA_out.txt:13-19`），完整 64 位见
`_dA_check.txt:17-23`。

### 铁律 9 · 被核对象 SHA256

主被核对象（本轮比较基准）：

```
被核对象 SHA256 = 4a3424050125b98c0dd3a9a76ec6603fc03ad976e0b9fdecfb34d3b683b94726，字节数 = 48343    [lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md]
```

其余 6 项题给指纹（均 MATCH，`_dA_check.txt:18-23`）：

```
被核对象 SHA256 = 7e2533eabf795e8aa0063a16ee875d95742880dcefab55d596cfc5aa6e7f958b，字节数 = 17926    [lead/dtrigger_compare_20261107/CRITERIA_METRICS.json]
被核对象 SHA256 = e6c26896319acb0387f06384665d5db3668e0f15e29f7328cac97f4931c03cac，字节数 = 111044    [lead/dtrigger_compare_20261107/_cost_quota_data.json]
被核对象 SHA256 = f0177d2cbafdb4dbd388d6b38b97d14ae73688f36f58df4f0fff7edc31a59b66，字节数 = 5088     [lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt]
被核对象 SHA256 = d5afc90c50bbf57be1e58bf9000b1940392337b6c57a444e3b084fe57983d04f，字节数 = 13197    [lead/d30_ruling_20261106/RULING_D30.md]
被核对象 SHA256 = ed8951e72bd61cd322b1687c4496ec9fc0e8a362c1425d4020901228d885a001，字节数 = 27271    [lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md]
被核对象 SHA256 = 1d90325ca899c0611ac03dd49a6fb07ede4e21cde2062a5a793a7ea694c9da29，字节数 = 20133    [lead/dstart_observable_20261107/S_OBSERVABILITY.md]
```

另两项非题给、但本 runner 实读的输入件指纹（`_dA_check.txt:24-25`）：
`STALL_EVENTS.json` = `5bf152842b2c343bc6cf046fa824bf0a0f3eb7a0c83245339f449921ed053cad` / 659297 bytes；
`_stall_vs_gap_out.txt` = `4895abf439b45d39d3ffbb9be54a27cddcda621f8c4ad0f12f8899892dba201c` / 13909 bytes。

---

## 8 交付件清单（`lead/dtrigger_round2_20261107/` 下 `_dA_` 前缀新文件）

| 文件 | 作用 |
|---|---|
| `_dA_probe.py` / `_dA_probe_out.txt` / `_dA_probe_stdout.txt` | 结构探针：基准率、前缀签名碰撞、e / D 可得性、独立 LB1 交叉核验 |
| `_dA_run.py` / `_dA_out.txt` / `_dA_stdout.txt` | 主 runner：D1–D5 十一档 + CAL 四档、三维比较、四条形式化证据、未验项 |
| `_dA_data.json` | 机器可读结果（meta / criteria / bound_baserate / bound_prefix / unverified） |
| `_dA_check.txt` | 12 项实跑断言 + 铁律 9 指纹行 |
| `_dA_design.md`（本件） | 设计说明与结论汇总 |

**自指纹说明（诚实账）**：`_dA_check.txt:27-33` 列出的 `_dA_*` 输出件指纹由
`_dA_run.py` 在写 `_dA_check.txt` **之前**计算，故其中 `_dA_check.txt` 自身那一行是
「写入前内容」的哈希，与最终文件必然不同（自指不可自证）；其余 5 个输出件指纹与最终
文件逐字节一致（本次实跑核对：`_dA_probe_out.txt`=56a3e09b…、`_dA_out.txt`=8825e115…、
`_dA_data.json`=fb28e366…、`_dA_run.py`=edd6d6f5…、`_dA_probe.py`=5d281ae7… 全等）。
最终权威指纹以本轮最后一次 `python -I -X utf8 -c 'hashlib...'` 实跑为准：

```
_dA_check.txt      sha256=434e358b82ae7e795a2c3c6952ebccf128095e5a1523e250e7aa01e3a1563d1c bytes=2710
_dA_data.json      sha256=fb28e366a9c3a9977b5cde9a0664b907c94143009a8d92e5ae0810d652ba7d7c bytes=27246
_dA_design.md      自身哈希不可自证（写入即变），以外部实跑 hashlib 为准
_dA_out.txt        sha256=8825e115f92bdf407cf20dde724e5633adc4e08e3f97bcee58299b95a8cb6d43 bytes=29813
_dA_probe.py       sha256=5d281ae76649afbce5fcf8b7e1ed66566867e98a34bf68e381dc507b0d1a9155 bytes=16209
_dA_probe_out.txt  sha256=56a3e09bdd8453c3653aa480856e6358001a0bd4d54d751f7bf299e47cee6068 bytes=7976
_dA_probe_stdout.txt sha256=5d7863df680f4c85040ddb75cb9d18657235ae11f2f01407c3e222b5c72398d5 bytes=8078
_dA_run.py         sha256=edd6d6f55172eeb24bc96578342f4f38accbb961cfc32879f4516280bdd91c29 bytes=42495
_dA_stdout.txt     sha256=b7e6fa64c9929358a000b9ed66179c7cc1a9f69f672e1f6a6f8a5cee953b6bf1 bytes=30050
```

未改任何既有文件；未改台账、裁决书、母本；不 commit、不 push。
