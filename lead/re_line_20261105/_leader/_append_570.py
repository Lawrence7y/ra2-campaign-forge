# -*- coding: utf-8 -*-
"""Append §570: D-20 步骤 A（离线半）——候选件 + 离线单测 67/67 通过（guarded）。"""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7570"

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
## §570 · D-20 步骤 A（**离线半**）完成：帧沿候选件写出，**67 项离线单测全通过**（2026-11-05）

> 依 D-20 定谳第 3 条：「按 D-19 帧沿规格实现四 VA + 帧号候选件，对读取、格式及 null 处理
> 运行离线单测并记录命令和输出；**通过后**使用隔离载体执行 3 趟小批真机验证通道，
> **保留 alpha 未校准与采样充分性未证标记**」。
> **本节只覆盖 A 的离线半。真机 3 趟一趟没跑。**

### 一、交付件

| 文件 | 作用 |
|---|---|
| `A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` | 候选件：`read_one` / `read_sample` / `classify_edge` / `FrameEdgeTracker` / JSONL 编解码 / 可选 `RpmReader` |
| `A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py` | 离线单测 **67 项 / 7 组** |
| `A1_SAMPLER_CANDIDATE/_test_out.txt` | 单测原始输出 |
| `A1_SAMPLER_CANDIDATE/A1_OFFLINE_DELIVERABLE.md` | 交付说明（含逐条对 D-19 第 4–6 条的落实表） |
| `A1_REVIEW/REVIEW_TASK.md` | 独立复核任务书（R1–R6 六问，判定规则写死） |
| `W3_COSTBOUND/ERRATA_D20B_20261105.md` | **A39 勘误落地**（见第三节） |

### 二、★ 实跑命令与输出（逐字）

```bash
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py"
```

退出码 **0**，输出尾部：

```text
==============================================================
SUMMARY  PASS=67  FAIL=0
==============================================================
```

**七组覆盖**：T1 读取语义（失败不补 0 / 越界 / `bool` 拒收 / reader 抛异常不外泄）、
T2 读序与时间戳（严格 6 次读、跨帧判定、后读失败记不可判）、
T3 帧沿分类（`df=0/1/>1/<0`/`None` 五态）、
T4 跟踪器（`df>1` 只出 1 个事件、归属标 `aggregate_over_N_frames`、**首样本单列不污染 `unjudgeable`**）、
T5 JSONL（单行、往返、schema 拒收）、
T6 静态交叉核对（四 VA + 帧号与 D-19/harness 常量**逐字**一致）、
T7 D-19 三条硬要求 + 铁律（源码无 hook/注入/挂线程/dump；`RpmReader` 默认关闭）。

### 三、★ A39 勘误已落地

`W3_COSTBOUND/ERRATA_D20B_20261105.md`：订正 `Q1_C2_RENDER.md` 的
「渲染主簇逐单位调 `DrawIfVisible`」——实测该簇（`0x6D8DB0..0x6DA1FB`，1603 条）内
**`call 0x5F4B10` = 0**、**写全局 dword = 0**、19 处 `inc/dec` **全为寄存器**。
**W3 原文一字未改**（append-only 惯例）；C2 结论方向不变。

### 四、两个未证标记的**机械化**落地

```python
MARKER_ALPHA_UNCALIBRATED   = "alpha_uncalibrated"
MARKER_SUFFICIENCY_UNPROVEN = "sampling_sufficiency_unproven"
```

**每条 `read_sample` 记录、每个 edge 事件、每份 `stats()` 都带 `markers` 字段** ——
「标记被删」这件事**可被下游机械检出**（缺字段或值不符即作废），不靠人记得。

### 五、诚实账

1. **我亲验**：`EXIT=0` 与 `SUMMARY PASS=67 FAIL=0`（上面命令与输出）。
2. **单测首轮曾 2 项 FAIL**，两处**都是我的测试写错**，已改后重跑，未放宽断言：
   (a) `T4.10` 期望值漏算 `104→103` 回退那一次 `unjudgeable`；
   (b) `T6.4` harness 路径上溯级数错一（已改为向上搜索祖先目录）。
3. **我未验**：**真机通道一趟没跑**；`RpmReader(enable=True)` 的真实读取行为（铁律禁止开句柄）；
   `df<0` 的三种成因（重置/回绕/进程重启）**当前确实不可区分**，候选件只合并标 `unjudgeable`；
   500 Hz 实达能力与慢窗/快窗漏沿率，**全未测**。
4. **已知前置缺口**：现有 harness（`qc151_trip.harness8_v4.py`）**不带四 VA 读取**，
   要跑真机通道必须先做**只加四个只读 VA** 的 harness 副本——这会改动真机发射路径，
   属 D-19 第 7 条两闸范围（用户已全开），**但仍须独立复核后再发**。
5. 本步**零真机、零注入、零母本改动、未 commit**。

### 六、下一步（最小动作）

1. **等独立复核回件**：`dwfrun-d10c0966`（`magpie/antigravity/gemini-3.8-flash$high`，
   两组并行复核 + 汇总 + 确定性门槛）。判 REFUTED/PARTIAL ⇒ **先改候选件再重跑单测**。
2. 复核过关后做 **harness 只读扩项副本**（四 VA + 帧沿触发），同样先离线单测。
3. **才考虑** 3 趟隔离载体真机通道验证。
4. **两个标记全链条不得移除。**
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION.encode("utf-8")))
