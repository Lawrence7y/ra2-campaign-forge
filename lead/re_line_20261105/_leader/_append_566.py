# -*- coding: utf-8 -*-
"""Append §566: W1 + W3 final intake (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7566"

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
## §566 · W3 + W1 双双收官：**C3 可静态排除**、**C4 的「索敌」其实是弹药装填**、**挂起与慢爬完全正交**（2026-11-05）

> **本节的地位**：同日回收两条推进流水线。
> - **W3** `dwfrun-1aeaeb17`（`magpie/antigravity/gemini-3.8-flash$high`，**49.1M tokens**，2h，
>   六阶段跑完，门槛 `exit=0`）。定稿 `W3_COSTBOUND/W3_COSTBOUND.md`（49.6 KB）。
>   复核：**渲染 CONFIRMED(2) / 寻路与物理 CONFIRMED(2) / 帧沿统计 PARTIAL(5) / 挂起核对 CONFIRMED(3)**。
> - **W1** `dwfrun-3eee0767`（`magpie/work/cn:hy4free$high`，**48.7M tokens**，4h，
>   门槛 `exit=0`）。定稿 `W1_HOLD_SURFACE/W1_HOLD_SURFACE.md`（55.9 KB / 467 行）。
>   复核：**Q1 PARTIAL(5) / Q2 CONFIRMED(10) / Q3 PARTIAL(11) / Q3b CONFIRMED(6)**。
> **按纪律：PARTIAL 的条目不得当 confirmed 引用。**

### 一、★ W3 的核心结论：四个成本中心里**只有一个能静态排除**

| 成本中心 | 静态可排除? | 数量级依据 |
|---|---|---|
| **C3 战斗物理** | **✅ 可排除** | 单帧 ≤0.05–0.1 ms，与 134.8 ms 赤字差 **2–3 个数量级** |
| C1 寻路 | ❌ 不可 | 1200 单位极端并发上界 **720–3600 ms**，高出实测预算 **1 个数量级** |
| C2 渲染 | ❌ 不可 | 全入屏 **100–150 ms** vs 全裁剪 0.05 ms，跨度与赤字**差 0 个数量级** |
| C4 微观索敌 | ❌ 不可 | 全扫上界 **19–36 ms**（长程 125 ms），与赤字**同阶** |

### 二、★★ W3 抓到两个必须记账的**实质纠正**

**(a) C1 还有第二道硬闸 `0x2710`（10000）**
除 §562/§563 记的 `0xFFF7`（65527）外，`0x42A3DE..0x42A3F6` 还有
`cmp ecx,0x2710` 与 `cmp ecx,[esp+0x70]` **两条**超限失败判据
⇒ **实际有效上限是 10000 而非 65527**（两者取先到者）。这修正了 §562「32.76 倍」的另一半。

**(b) ★★ `SelectAutoTarget 0x6FB010` 不是索敌，是弹药装填（UpdateReload）**
W3 断言、**我实跑反汇编复核确认**：

```
006FB01C  mov eax,[eax+0x684]   ; Ammo
006FB022  cmp eax,-1
006FB025  je  0x6FB06E          ; 无弹药 → 直接返回（<2ns）
006FB05B  mov [esi+0x2FC],edi   ; 计数递增
006FB069  call 0x6FB080         ; 重装周期
```

⇒ **`docs/re/targeting_spatial.md` 把它当索敌入口是误标**；
且**「8/100 帧限频」在 C4 里不存在**（那属 `HouseClass::Update` 的宏观 AI，
`0x4F8E24`/`0x4F8F9C`）。
真正的索敌核心 `Greatest_Threat 0x6F8DF0` **无计时器限频**
（仅 `0x6F8DF3` 递增全局重入计数 `0x00A8EC34`）。

**(c) `DrawIfVisible 0x5F4B10` 裁剪失败跳过整条绘制——我亲验**
```
005F4B71  7515      jne 0x5F4B88      ; 可见 → 继续
005F4B77  ff522c    call [edx+0x2C]
005F4B7D  7409      je  0x5F4B88
005F4B7F  32c0      xor al,al         ; ← 早退点
005F4B82  83c420    add esp,0x20
005F4B85  c20c00    ret 0xC
```
⇒ **不是「只省 blit」**，而是跳过了 `0x5F4B88` 起的体素旋转/阴影/光栅化整链。
这坐实了 C2 是**强解释源**。

### 三、★ W3 的挂起/慢爬正交性（CONFIRMED，3 异议已吸收）

| | 挂起（`+0x62C≠0`） | 慢爬 |
|---|---|---|
| 控制流 | `0x55D826` 分叉 → 冻结体 → `0x55D877 ret` | `0x55D878..0x55DE40` **48 处**世界模拟照跑 |
| 帧号 | 在 `0x55DE7E inc edx` **前 1543 字节早退** | 正常连续递增 |
| 数据 | `logic_frames=0`、`max_stall=25.00s`（29 窗） | 推进 **118–463 帧**、`max_stall≤0.75s`（22 窗） |
| 调度 | 单次微秒级 ⇒ 必须 Sleep 满 32 ms | `elapsed≥target` 恒成立 ⇒ **0 ms Sleep、CPU 打满** |

⇒ **「挂起造成慢窗」这一可能性被彻底排除。**

### 四、W3 的 PARTIAL 项（帧沿形态）—— 复核推翻四处统计推断

| 复核指出的问题 | 后果 |
|---|---|
| KS 检验自由度损失 / Lilliefors 效应 | 已修正 |
| 孤立小样本被当作大数定律外推 | 已纠正 |
| 长尾压低 BC 系数、掩盖局域双峰 | **「22 窗零多峰」的证据强度下降** |
| 「宏观连续」推「微观单一函数」是逻辑混淆 | 已纠正 |
| **17.4 ms 固定成本假说** | **证伪**（w0→w1 差 −76~+32 ms 连续弥散） |

仍成立：22 窗偏度**全正**（中位 0.860）；16 ms 直方图无梳状量化
⇒ 判死「定时器量化/整倍数跳帧」「固定周期」「固定成本切除」「偶发脉冲」四假说。
**但 `Δt = Σ T_Ci` 是单方程四未知数，永远无法拆解。**

### 五、W1 的降级（按纪律执行）

**Q1 的肯定结论被降级**：「无任何地图脚本动作时 `0xB45B68` 仍会非 0」
→ **「静态无已知路径 / 未验」**。三处反证：
① `0x5BF260` 只调 `0x5BED40`（**354 条窗口内 0 处** Count/`0x62C` 引用）；
② `0x5BF2B0` 静态零 xref；③ §559 已裁「Q3 对、Q1 错」。

**Q3 的 5 处数字被复核更正**（我采信）：
「256 等距 `0x22B`」→ **间距 550–555，仅 33/255 恰为 `0x22B`**；
`0x68361E` → **`0x6839CE`**；dump 130 → **291/354**；31.7 KB → **43,283 B**；
补 `0x53A747` 分类与 `0x5BF2F9` pause 旗标。

**Q2 / Q3b CONFIRMED**：
`0x6579E0` = `RadarClass` 影片队列状态机（`0x653100` 的唯一调用者 `0x653446`，
三条调试串 `"Radar: Movie done/Next movie/full redrawn"`）；
地图普查 **265 图 / 154 有 `[Actions]` / 1261 记录 / 5309 动作 / 110=127=0**。

**★ Q3b 另发现**：`ra2youli/` 下 265 图**无一命中** 10 个测量 map_sha
—— 测量用的是 `_src_*`/`_maps_fixed/` 的 `XMP29U2.MAP` 族；`U0400` 是**同名不同文件**
（`ra2youli` 92,332 B vs 载体内 222,799 B）。这解释了我 §556 抽查 `ra2youli` 为何与测量图对不上。

### 六、★ 由此产生的**新冲突**：已立 D-19 并派裁决

- **W3**：「**4 个正交 VA + 1 Hz 已完全充分**」（`Q3_SAMPLE_PLAN.md:195`），
  并给了两档设计（1 Hz 基线 / ~30 Hz 帧沿触发）。
- **D-17 定谳**：「**1 Hz 只是起点，不保证三类成本可分解**」。

**已立 `D-19`** 并派 `dwfrun-1682f511`（`magpie/codex/gpt-6.1-sol$medium`）裁决。
本线倾向：4 个 VA 采纳、频率按 §A6 的「同趟 1.56 倍变化」要求更高，
且 W3 `:145`（纯宏观时序永远无法定谳）与 `:195`（1 Hz 充分）**自相矛盾**，需裁。

### 七、诚实账

1. **我亲验**：`0x6FB010` 全反汇编（弹药语义）、`0x5F4B10`/`0x5F4B7F` 早退点、
   `0x6FB025 je` 早退、W1/W3 定稿的复核判定与关键数字。
2. **我未验**：W3 的「每节点 800 指令」「全绘 100–150 ms」「C4 19–36 ms」等**数量级估算**——
   **采信其复核 CONFIRMED**，我未重算；这些是**估算不是实测**。
3. **我未验**：W1 的 265 行地图表（采信其复核 CONFIRMED + 我上轮独立复现过 265/154/1261/5309）。
4. **我未验**：W3 列的 4 个 VA 中 `0x00B0CE88` / `0x00A8ED50`（**已列入 D-19 的核证项**）。
5. **我不改** W1/W3 原文（append-only）。
6. 本轮**零真机**、**零母本改动**、**未 commit**。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
