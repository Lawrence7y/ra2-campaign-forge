#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§421b 追加器：字节级追加，不动既有 CRLF。"""
from __future__ import annotations
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"

SECTION = """
---

# §421b 把「修过头差点没抓到」变成承重断言

§421 修正 n2m 注入时，我第一版**删过头**（连 short 也删了）。
真机 short 臂**会**写 n2m（`:4970`），删了它会让判档器 `:266`
「短路臂记录了 nav_to_measure_s」FAIL。但**当时的 forms 件 8/8 照样全绿** ——
因为它的段 A 只 grep 形态行，不看 FAIL 行。**过度修正靠推理才抓到，测试没抓到。**

补两段 F 断言堵这个盲区（forms → **10/10**）：

| 断言 | 真机依据 |
|---|---|
| short 臂**必须**记录 nav_to_measure_s | `:4970` 短路臂写 |
| keep 臂**不得**有 n2m ⇒ late_start=None 通过 | 短路臂条件不成立 ⇒ 不写 |

★ **承重试验**（把 short 的 n2m 注入删掉重跑）⇒
**唯一红项 = `short 臂必须记录 nav_to_measure_s | FAIL None`**，其余 9 条仍绿。
证明这两条断言**确实抓得住**合成失真，不是恒绿。

★ 试验自身踩了 §420 坑①：临时副本第一次全红「形态行缺失」，因为 forms 的
`JUDGE = Path(__file__).resolve().parent / ...` 没跟着拷到临时目录。
把判档器拷到副本旁后正常。**负控的负控也要跑，否则「能红」是我说的、不是证出来的。**

| 件 | 状态 |
|---|---|
| `_preview_h7_forms.py` | **10/10**（8 + F 两条） |
| `_preview_h7_fullpath.py` | 9/9（n2m 已按 short-only 注入） |
| `_verify_h2e_smoke.py` | 25/25 |
| `_verify_h7_fullpath.py` | 6/6 |
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
    assert after.count(b"\r\n") == crlf0, "CRLF 数变了"
    LEDGER.write_bytes(after)
    print("appended %d bytes; %d -> %d" % (len(payload), len(before), len(after)))
    print("CRLF preserved: %d" % crlf0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
