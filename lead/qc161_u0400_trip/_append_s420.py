#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§420 追加器：字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §420 补 §416 的缺口：**三窗全通路径**下的冒烟判据，此前从没跑过

**轮次目标**：§416 用 `l1_20261023`（w0 就 `no_advance` 短路）验三形态，
但它只走到判档器 `:430` 那个**短路分支**的 `h7_smoke_section()` 调用。
真机 h7a 若顺利，走的是 `:536` 那个**正常完成路径**的调用——
那条路上 `h7_smoke_section` 前后还有三窗断言、[5] except、[6] 开机指纹。
**这条路径从未在 harness7 标记下跑过。**

## 一、盘上只有 5 趟三窗齐全，且都不是 harness7

| 趟 | w0 / w1 / w2 |
|---|---|
| l1a_20261020 | ok / ok / ok |
| l1c_20261021 | ok / ok / ok |
| l1d_20261021 | ok / ok / ok |
| l1e_20261021 | ok / ok / ok |
| l3_20261021 | ok / ok / ok |
| l1_20261023 / b / c、l3_20261023 | no_advance / — / — |

选 `l1c_20261021`（polls=247 / frame=123.704）造三形态 harness7 副本。
★ 这次必须拷**五份**文件（`_launch_result` + `fields` + `measure_w0/w1/w2`），
少一份就走不到 `[4b]`（§416 踩过的 `measure_w0` 漏拷坑，这次提前规避）。

## 二、结果：9/9 PASS

| 形态 | rc | 判型 | 冒烟断言 | 走到 [4b] |
|---|---:|---|---:|---|
| windowed | 1 | **windowed** | 3 条全 PASS | ✓ |
| short | 1 | **fullscreen_short** | 4 条全 PASS（frame=1.32 < 2.0） | ✓ |
| keep | 1 | **fullscreen_keep** | 4 条全 PASS（polls=247 ≥ 200） | ✓ |

★ `rc=1` 不是冒烟失败，是**源趟本身** `pre_fps15=8.023` 撞了 V11-a 硬门禁
（`min(pre_fps15) ≥ 25.0`）。**冒烟段与档位门禁是两件独立的事**，
这正好证明本预演能区分「冒烟过 / 档位不过」。

★ B 段证明**两段共存**：同一份输出里同时含 `[1] measure 三窗` 与 `[4b]`，
即三窗全通路径确实执行到了冒烟段（不是被前面 return 掉）。

★ C 段负控：短路臂 `frame=123.7`（不塌）⇒ 冒烟段红在 `frame_s_max`，
而**三窗段落零新增红项** ⇒ 两段互不干扰。

## 三、装置自身两次翻车（都记下来）

### 坑① 全红且红项一模一样 = 装置没跑起来

首跑 **1/9**，九条红项文字完全相同（`形态行缺失` / `smoke=0`）。
先怀疑装置：副本里 `JUDGE = Path(__file__).resolve().parent / "_judge_..."`，
在临时目录下指向**不存在的判档器** ⇒ 子进程 `rc=2`、**stderr 为空**、
每条都走「形态行缺失」。
⇒ 负控里必须**同时钉住两个锚点**：`ROOT` 与 `JUDGE`。
★ 只钉一个不够 —— §413 那次只钉了 ROOT 就够，是因为那个件没有第二个
`__file__.parent` 依赖。**每换一个件都要重新数它的路径锚点。**

### 坑② M2 变异存活，但那是判据性质不是缺陷

首版 M2 只改 `lr["harness_sha16"]` ⇒ **rc=0，存活**。
查判档器本体：

```python
is_h7_run = (lr.get("harness_sha16") == HARNESS7_SHA16) or (sk is not None) or (n2m is not None)
```

**三条独立退路**，任一条在场就认定 harness7。改一条不影响结论。
⇒ 要让 M2 真正模拟「非 harness7 趟」，必须**三路全撤**
（sha 换掉 + 不写 `h7_fs_rect_wait_skipped` + 不写 `h7_nav_to_measure`）。
改完立刻捕获。

★ 这是本轮第二重要的观察：**变异存活时，先问「是件错了还是尺子错了」**，
再问「是不是我的变异根本没改到判据真正依赖的量」。本例三条退路中，
`sk`/`n2m` 两条是**产物自证**，比 sha 更硬 —— 判据设计是对的，
错的是我的变异只打了一条。

## 四、交付件

| 件 | 说明 | 结果 |
|---|---|---|
| `_preview_h7_fullpath.py` | 三窗全通路径 × 三形态 + 两段共存 + 互不干扰负控 | **9/9** |
| `_verify_h7_fullpath.py` | 负控（M1 形态写错 / M2 三路全撤 / M3 缺 measure_w2） | **6/6** |

★ 本轮**不改**判档器、**不改** harness。它补的是「判档器在**真机会走的那条路**
上能不能正确工作」——§416 只证明了短路路径，本轮证明了完整路径。
★ 边界不变：盘上 harness7 产物仍为 **0**，两次预演证明的都是**判读能力**，
不是**被测物行为**。
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
