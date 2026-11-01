#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§426b 勘误：趟数口径（12→10 次有数据发射，abort 的 2 次不称「实跑」）。

同轮自纠（[[gate-assert-values-not-existence]] 变种 L 的教训：发现口径错
就当场钉，不留到下轮）。追加式，不重写 §426 原文。
"""
from __future__ import annotations

import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")
PEND = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

BODY = """# §426b　勘误（§426/D-09 同轮）：趟数口径统一为「10 次有数据发射」

§426 首句写「6 批 12 次实跑趟」，与表体自相矛盾（表体 4+2+1+3=**10**）。
批次 2 的 2 次 B 臂趟在 `carrier_create_failed` 处返回，**进程从未启动** ⇒
不得计入「实跑」。正确口径：**6 批发射，10 趟有数据（崩溃形态 7 + 真开臂 3），
另 2 趟 abort 无数据**。D-09 同步更正（该条来源=本线，同轮自纠不算改他人条目）。
判读结论**零影响**：全部计数（7/7 dump、真开臂 3/3 零 AV、7/7 崩溃复现）本就按
「有数据」口径统计。

"""


def main() -> int:
    before = TARGET.read_bytes()
    crlf0 = before.count(b"\r\n")
    assert crlf0 == 86
    assert before.endswith(b"\n")
    payload = BODY.lstrip("\n").encode("utf-8")
    after = before + payload
    assert after.startswith(before) and after.count(b"\r\n") == crlf0
    TARGET.write_bytes(after)
    print("ledger appended; %d -> %d" % (len(before), len(after)))

    # D-09 就地更正（唯一锚点，前后 assert；他人条目零触碰）
    t = PEND.read_text(encoding="utf-8")
    old = "同开机会话（10:36 起）共 6 批 12 次实跑趟。"
    new = "同开机会话（10:36 起）共 6 批发射、**10 趟有数据**（另 2 趟载体创建期 abort，进程未启动）。"
    assert t.count(old) == 1, t.count(old)
    t2 = t.replace(old, new)
    old2 = "SYNCPOINT 2026-10-24 晚：②-A 守卫首验 12 趟已跑"
    new2 = "SYNCPOINT 2026-10-24 晚：②-A 守卫首验已跑（10 趟有数据）"
    assert t2.count(old2) == 1
    t2 = t2.replace(old2, new2)
    assert t2.count("\r\n") == t.count("\r\n")  # 行尾风格不变（纯 LF=0）
    PEND.write_text(t2, encoding="utf-8", newline="")
    print("D-09 corrected in place")
    return 0


if __name__ == "__main__":
    sys.exit(main())
