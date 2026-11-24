# -*- coding: utf-8 -*-
"""Append a correction note to D-16 in PENDING_DECISIONS.md (append into the entry, not a rewrite)."""
import subprocess
import sys

PEND = r"D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md"

text = open(PEND, "rb").read().decode("utf-8")
ANCHOR = "  **证据**：台账 §545（本轮新增，含目视表、mtime/声明对照表、qc151_fields 原文摘录）；"
if ANCHOR not in text:
    print("REFUSE: anchor not found")
    sys.exit(1)
print("anchor found")

NOTE = """  **★ 立条目后 30 分钟内的自我订正（同日，台账 §546）——请以本节为准**：
  上面「`p` 低 ⇒ 不是纯战斗画面」这条**方向成立**，但我据此写的推论「`df==0 ⇒ 终局态` 至少两趟不成立」
  **是错的**，已由 §546 订正。补看两张真正的计分屏（`archive_T34/w1` 屏显 `00:00:10`↔冻结帧 302、
  `archive_T41/w1` 屏显 `00:00:28`↔冻结帧 860，两组均与 `帧号/31.2` 自洽）后：
  1. **§543 的计分屏判读是对的**，`p≈0.349` 类确实是对局结束界面；
  2. **`df==0 ⇒ 终局态` 只在 `l1_20261023e4/w2` 这 1 趟上不成立**（游戏不在前台），
     `T42` 的 `df==0` 是**退回主菜单，仍属「对局已结束」**，不算反例；
  3. ⇒ **(A) 里的「撤回『11 个停摆窗是终局态』整组归类」这句话请降为**：
     **「11 个停摆窗里至少 1 个（`e4/w2`）不是终局态而是采样环境问题，其余 10 个未逐窗复核」**。
  4. **`p` 判据的正确用法（本条目真正要裁的东西，未被 §546 削弱）**：
     `p≈0.349` 可单方向判「已结束」；`p` 低**不能**反推「还在战斗」。
     凡以「`p` 低 ⇒ 纯战斗画面 ⇒ 引擎停摆」为链条的推论仍须全部标废。
  5. **新增一条待查（本轮只提出未验证）**：`T34` 的 w0 在 25 秒内只推进 9 帧（`avg=0.36`/`p50=31.61`），
     说明该趟**从 w0 就已冻住**，与 `T41`（w0 正常 29.12、w1 才冻）**不是同一失败模式**。
     「零建筑 + ShortGame 规则判负」是引自 T55 系的候选解释，**本轮未验证是否适用于 `archive_T*` 本批**。
"""

new = text.replace(ANCHOR, NOTE + ANCHOR, 1)
with open(PEND, "wb") as f:
    f.write(new.encode("utf-8"))
print("inserted %d bytes; file now %d bytes" % (len(NOTE.encode("utf-8")), len(new.encode("utf-8"))))
