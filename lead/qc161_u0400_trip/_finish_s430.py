#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""§430 收尾（幂等）：ledger 已追加则跳过；D-09 插入「更新 5」用**唯一性更强**的标签，
且先复核本线 §424–§430 全部还在（[[shared-ledger-wholefile-rewrite-loss]] 纪律）。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TARGET = Path(r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md")
PEND = Path(r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md")

UPD5 = ("- **更新 5（2026-10-25，D-09 来源会话，选项不变，D-09-A 设计输入到手）**："
        "一趟硬件写断点定谳 **exitstate=1 的写入者=`0x6BE0B6 mov [0xA8EDD8],edi(edi=1)`**"
        "（主线程，WM_CLOSE 后 +5.8 s；阳性对照 P1=hwnd 写点 0x777814 同趟命中，"
        "顺带把 §398 清零块钉到指令粒度）；写入 1 后**再无人写**（断点+150 s 轮询双口径"
        "一致）⇒ 挂死=退出步骤长链（0x6BE0xx 每 ~0x48B 一块，`call esi`=被守卫跳过的"
        "成员函数族）卡在第 1 块完成条件。改法候选 a/b/c 见台账 §430 四（均属守卫件"
        "改造=他线写域，需 Lead 派工或授权本线出副本）。census v2 裁决：0x6BE0B6 "
        "运行时坐实为真；「=2 写点」维持幻影。\n")


def main() -> int:
    # 1) 本线台账自证：§424–§430 全在
    t = TARGET.read_text(encoding="utf-8", errors="replace")
    missing = [s for s in ("424", "425", "426", "427", "428", "429", "430")
               if not re.search(r"^# §" + s, t, re.M)]
    print("my sections missing:", missing or "none")
    assert not missing, "本线条目被并发重写吞掉，停手先恢复"

    # 2) ledger 幂等：§430 恰好 1 次
    n430 = len(re.findall(r"^# §430", t, re.M))
    print("§430 occurrences:", n430)
    assert n430 == 1, "§430 不唯一，查并发"

    # 3) PENDING：LF 件 + D-09 更新 5 未插 + 标签唯一（用长标签防与 D-07 的更新 5 撞）
    pb = PEND.read_bytes()
    assert pb.count(b"\r\n") == 0
    s = pb.decode("utf-8")
    anchor = "- **提出**：2026-10-24（§426 同轮）"
    assert s.count(anchor) == 1
    assert "更新 5（2026-10-25，D-09 来源会话" not in s, "已插过"
    tag = UPD5.split("）")[0] + "）"
    print("distinctive tag:", tag[:50])
    idx = s.index(anchor)
    ns = s[:idx] + UPD5 + s[idx:]
    assert ns.startswith(s[:idx]) and "\r\n" not in ns
    assert ns.count(tag) == 1
    # D-07 的 RE-ATLAS 更新保持逐字不动（只检查字节数不减）
    assert len(ns.encode("utf-8")) > len(pb)
    PEND.write_bytes(ns.encode("utf-8"))
    print("D-09 update5 inserted; %d -> %d bytes" % (len(pb), len(ns.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
