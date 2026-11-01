#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§416 追加器：字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §416 三趟形态预演 —— 判档器在**真实产物**上验过三臂，不是只验合成样本

**轮次目标**：§414 修完判型后，负控只有 `_verify_h2e_smoke.py` 的 S1–S10，
而它们全是 `mk_trip()` 手搓的最小 JSON（只含判档器要读的那几个键）。
**「判据逻辑对不对」验过了，「真实产物 + 真实键序 + 真实附加键下判型对不对」没验。**
本轮补这一层，并把 `polls_max: 5`、`frame_s_min: 100`、`frame_s_max: 2.0`
三个阈值逐个钉到实测分布上。

## 一、先把三条臂的**取值依据**从设计变成实测

盘上 `qc151_fields.json` 全量摊开（57 份，`find out -name` 收全），按
「`META.fullscreen` 在场 / `FRAME.h7_fs_rect_wait_skipped` 在场」分档：

| 分档 | 份数 | 依据 |
|---|---:|---|
| 窗口模式（fs 不在场 + polls 在场） | **29** | **polls 全部 = 0** |
| harness6 全屏（fs 在场、skipped **不**在场） | 14 | skipped 缺失是母本语义 |
| harness7 全屏（fs 在场 + skipped 在场） | **0** | ★ 真机还没跑过 |

★ **29/29 窗口趟 polls = 0** ⇒ `polls_max: 5` 不是拍脑袋的余量，是
「29 份实测全 0 + 留 5 轮抖动」。这也与 `S399 §九` 第 1 条
「历史窗口模式趟实测 0」独立吻合（两处不同来源同值）。

★ **9 份 harness6 全屏 frame 段分布**（升序）：

| 趟 | frame_s | polls |
|---|---:|---:|
| l3_20261021 | **48.157** | 96 |
| l3_20261023 | 122.140 | 244 |
| l1e_20261021 | 122.187 | 244 |
| l1c_20261021 | 123.704 | 247 |
| l1_20261023 / b / c | 125.7 / 125.7 / 126.7 | 251/251/253 |
| l1a / l1d_2026102x | 126.688 / 126.704 | 253/253 |

⇒ `frame_s_min: 100` 覆盖 8/9；**唯一例外 l3_20261021 是那趟 48 s 的短帧**，
而它正是 §414 用来抓循环论证的那份产物 —— 两件事互相印证：
**polls 与 frame 段是同源的时长量**（`frame_s ÷ polls = 0.5007 ± 0.0003`），
所以 `polls_min: 200` 与 `frame_s_min: 100` 实质是**同一条判据的两种写法**。
★ 这不是缺陷，是**冗余校验**：两者同时不成立才算真违约，只塌一个说明
「等待被短路了但没归零」这类中间态。

## 二、预演装置：拿真实产物改造，不是手搓

`_preview_h7_forms.py`：复制 `l1_20261023`（harness6 全屏，polls=251 /
frame=125.703）到临时目录，**纯加法**改造成三种形态：

| 形态 | 改动 |
|---|---|
| `windowed` | **删除** `META.fullscreen` 行；`polls`→0；`frame`→0.14 |
| `short` | append `skipped={"skipped":True,...}`；`polls`→0；`frame`→1.32 |
| `keep` | append `skipped={"skipped":False,...}`；polls/frame 保持真实值 |

三份都 append `MEASURE.h7_nav_to_measure`（harness7 无条件写）。
★ 改法是**顶替末次同名键 + append**，不删任何真实行 ⇒ 真实键序、真实附加键、
真实 `count`/`note`/`source` 字段全部保留。

## 三、结果：8/8 PASS

| # | 断言 | 结果 |
|---|---|---|
| A1 | `windowed` ⇒ 判型 windowed，四条判据全 PASS | ✓ |
| A2 | `short` ⇒ 判型 fullscreen_short，`frame=1.32 < 2.0` PASS | ✓ |
| A3 | `keep` ⇒ 判型 fullscreen_keep，`polls=251 ≥ 200`、`frame=125.7 ≥ 100` | ✓ |
| B | **承重性**：三形态判型互不相同 | ✓ |
| C | 负控：窗口臂写了 `skipped` ⇒ 冒烟判据**变红**（FAIL 行=1） | ✓ |
| D | 负控：短路臂 `frame=125.7` ⇒ 红在 `frame_s_max`（实测 125.7） | ✓ |
| E | 负控：对照臂 `polls=96` ⇒ 仍判 keep，**红在 polls_min**（实测 96） | ✓ |
| E' | ★ 承重：该趟**不得**被判成 windowed（§414 的旧缺陷） | ✓ |

★ E' 是 §414 那条循环论证的**真实产物版回归**：`polls=96` 的对照臂
在新判法下依然识别为 `fullscreen_keep`，然后如实报「polls 不足」。
旧判法在同一份产物上会把它判成 `windowed`，进而去报
「窗口模式不该写 skipped」—— 红在错误的原因上。

## 四、装置自身的坑（记下来，下次不再踩）

首跑 **1/8**，七条全红，`rc=4`。按「全红无细节先怀疑装置没跑起来」排查：

- `rc=4` = `measure_w0.json 不存在 ⇒ 产物丢失`。我复制了
  `_launch_result.json` + `qc151_fields.json`，**漏了 `measure_w0.json`**。
- 判档器在 `[1]` 段就 return 4，**根本到不了 `[4b]` 冒烟段**。
- 补齐第三份文件后立刻 8/8。

★ 与我先前记的「照抄相邻样本参数」是同一族教训的不同面：
**造样本时「该目录下判档器会读的文件」必须齐全，漏一个就静默走不到目标段落。**
`rc=4` 这个非零值就是唯一线索 —— 如果我只按「判型缺失」去查判据逻辑，
会一路查错方向。

## 五、副产品：判档器在全部真实产物上的回归

对 7 趟有 `_launch_result.json` 的真实产物逐一跑判档器：

| 趟 | rc | 冒烟段 |
|---|---:|---|
| l1_20261023 / b / l3_20261023 | 3 | `[跳过] 本趟不是 harness7` |
| l1c / l1d / l1e / l3_20261021 | 1 | `[跳过] 本趟不是 harness7` |
| l1b_20261021 | 4 | —（产物丢失档，与冒烟无关） |

★ **7/7 全部正确跳过，零误断言**。这是 §414 改判型后的**真实产物回归**：
老趟（harness6 全屏、fs 在场但 skipped 缺失）一律落进
「全屏但未跑到矩形等待 ⇒ 不是冒烟样本」分支，没有被拿去判 keep/short。
若按 §414 前的判法，它们会因 `polls ≥ 200` 被判成 `fullscreen_keep`
然后报「skipped 应 == False 而实测 None」—— **7 趟全假红**。

## 六、交付件与状态

| 件 | 说明 | 结果 |
|---|---|---|
| `_preview_h7_forms.py` | 真实产物三形态预演 + 4 负控 | **8/8 PASS** |
| 台账 §416 | 本节 | 本件 |

★ 本轮**不改**判档器、**不改** harness、**不收**新阈值结论 ——
它只做一件事：把「判档器能在真实产物上正确分三臂」从**推断**变成**实测**。
真机三趟未跑，两个全屏臂的**产物形态**仍属设计预期（盘上 harness7 产物 = 0 份），
预演证明的是**判读能力**，不是**被测物行为**。这条区别必须留在台账里。
"""


def main() -> int:
    before = LEDGER.read_bytes()
    assert b"\r\n" in before
    crlf0 = before.count(b"\r\n")
    assert before.endswith(b"\n")

    body = SECTION.lstrip("\n")
    payload = body.replace("\r\n", "\n").encode("utf-8")

    after = before + payload
    assert after.startswith(before), "前缀必须逐字节保持"
    assert after.count(b"\r\n") == crlf0, (
        "CRLF 数必须不变：before=%d after=%d" % (crlf0, after.count(b"\r\n")))

    LEDGER.write_bytes(after)
    print("appended %d bytes; total %d -> %d"
          % (len(payload), len(before), len(after)))
    print("CRLF preserved: %d" % crlf0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
