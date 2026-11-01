#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§421 追加器：字节级追加，不动既有 CRLF 行。"""
from __future__ import annotations

import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §421 预演件的合成失真：我给三形态都注入了 n2m，而真机只有短路臂写它

**轮次目标**：真机 h7a 前最后一遍自审。§420 自己写的合成样本里发现一处失真，
它恰好污染了 keep 臂 `late_start` 断言的验证语义。

## 一、失真与证据

§416/§420 两个预演件都给 **三形态**注入了 `MEASURE.h7_nav_to_measure`。
但 harness7 本体（`:4970`）：

```python
if _h7_nav_end is not None and _H7_STATE["fs_rect_wait_skipped"]:
    rec.add("MEASURE", "h7_nav_to_measure", {...})
```

`fs_rect_wait_skipped` 初值 False（`:3868`），仅 `--fullscreen` **且未 opt-out**
才置 True ⇒ **keep 臂与窗口臂现实中根本不写这条记录**。
我造样本时把「判据需要什么」当成了「产物会有什么」——注入是**愿望**不是**复刻**。

## 二、连带的判据语义发现（修正后才看得清）

修正注入后单跑 keep 臂副本：

```
⇒ 形态: fullscreen_keep
★★ 对照臂 late_start 不得出现    PASS  late_start=None
```

判据写的是 `late is not True`，n2m 缺席 ⇒ `late=None` ⇒ 绿。
⇒ **该断言在真机 keep 臂的现实形态下永远绿，除非 harness7 错误地
把短路闸装到了 keep 臂上**（写出一条 `late_start=True` 的记录）。

这不是缺陷——它验的正是 S399 §九 第 3 条的本意：
「证明**前置条件按设计生效**」，即验**设计不变量**（闸没被误装），
不验运行时时机。性质与 §419 的 `windowed.polls_max` 同族：
**哨兵型判据，绿≠信息，红才有信息**。区别是本轮是**先修正合成失真、
后看清语义**——若留着失真，我会误以为这条断言验的是「n2m 在场且 False」，
真机跑出来 n2m 缺席时反而要疑惑「判据没执行？」。

## 三、改动与回归

| 件 | 改动 | 回归 |
|---|---|---|
| `_preview_h7_fullpath.py` | n2m 只在 short 臂注入 | **9/9** |
| `_preview_h7_forms.py` | 同一失真同修（§416 件） | **8/8** |
| `_verify_h7_fullpath.py` | 未改（M1–M3 与 n2m 无涉） | **6/6** |
| `_verify_h2e_smoke.py` | 未改（合成样本走 mk_trip 另一条构造路，且其 S1–S10 的 n2m 都是有条件的） | **25/25** |

★ 全仓搜同类：注入逻辑只存在于这两个预演件；smoke 验证器的 `n2m` 参数
默认 None、按样本显式传——**修一处必全仓搜同类**（记忆的既有纪律），
搜完确认零残留。

## 四、纪律沉淀

**合成样本的每个字段都要回答「真机会写它吗」，而不是「判据要读它吗」。**
判据要读而不写 ⇒ 断言验的是缺席分支；判据不读而偏写 ⇒ 白增噪声。
两者都是失真。本轮就是前者：**判据（late_start not True）读 n2m，
真机 keep 臂却不写它** ⇒ 我在合成样本里替真机「补写」了它，
于是预演验证的语义从「设计不变量」漂移成了「在场且 False」。

（另注：本轮开头他人会话第三次把 20 个 `re_atlas/` 文件加进我的暂存区，
已第三次移出；未提交他人文件。）
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
