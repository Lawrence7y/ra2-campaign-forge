# -*- coding: utf-8 -*-
"""Insert D-16 into PENDING_DECISIONS.md, anchored (no full rewrite)."""
import subprocess
import sys

PEND = r"D:/Project/ra2-campaign-forge/lead/PENDING_DECISIONS.md"
REPO = r"D:/Project/ra2-campaign-forge"

head = subprocess.run(
    ["git", "show", "HEAD:lead/PENDING_DECISIONS.md"],
    cwd=REPO, capture_output=True).stdout.replace(b"\r\n", b"\n")
wt = open(PEND, "rb").read()
# PENDING is NOT a prefix extension (entries are deleted when ruled); just report.
print("PENDING prefix-extension? %s (informational)" % wt.startswith(head))

ANCHOR = b"## \xe5\xbe\x85\xe8\xa3\x81\xe5\x86\xb3\xe4\xba\x8b\xe9\xa1\xb9\xef\xbc\x88\xe5\xbd\x93\xe5\x89\x8d\xef\xbc\x89\n\n"
idx = wt.find(ANCHOR)
if idx < 0:
    print("REFUSE: anchor not found")
    sys.exit(1)
print("anchor found at byte %d" % idx)

BLOCK = """- **D-16（2026-11-04 夜立，来源=GOAL-3T 线，台账 §545）**：**`p` 值截图判据的语义被目视推翻，D-15 须降级重裁**。
  **背景（新增事实，不是重新解释旧事实）**：D-15 的全部推论都架在一个判据上——
  用窗末截图的面板检测比值 `p` 把窗分成「p≈0.349 计分屏」与「p≈0.040 无面板」，
  再在散文里把「无面板」当成「纯战斗画面」使用。
  **本轮领队亲自目视了两张此前从未被任何人看过的图**：
  - `archive_T42/measure_w1_end_x.png` = **RA2 主菜单画面**（苏军步兵立绘 + 右侧灰暗菜单按钮栏），不是计分屏，也不是战斗画面；
  - `l1_20261023e4/measure_w2_end_x.png` = **ZCode 桌面客户端窗口**，根本不是游戏画面。
  ⇒ **`p` 判据只区分「有没有计分屏面板」，完全不区分「在战斗 / 不在战斗」。**
  「p 低 ⇒ 无面板 ⇒ 纯战斗画面 ⇒ 还在打 ⇒ 所以是引擎停摆」这条链**中段断裂**。
  **两条硬事实**（脚本只读读出，非推测）：
  1. 四张同字节图（`T33/w2`、`T42/w1`、`T42/w2`、`T45/w2`，整文件 sha256 `f61c9808…`）
     的 mtime 与各自 `qc151_fields.json` 声明的采集 ts **逐秒吻合**（11:46:35 / 16:12:05 / 16:12:30 / 17:48:34）
     ⇒ **不是文件拷贝**，是四次相隔数小时的独立采集产出了逐像素相同的主菜单画面。
  2. `l1_20261023e4/w2` 的 `qc151_fields.json` 明记
     `game_title=''`、`fg_title='BuddySwitch 整合预览版'`、`focus_ok=False`、`current_frame=None`、`empty_window=True`
     ⇒ 该窗采图时**游戏不在前台或已退出**，`df==0` 是「采样对象不在了」，既非终局态也非引擎停摆。
  **请裁**（三选一）：
  **(A)** 接受新事实，**D-15 整体降级为「先补证据再裁」**：把 `df==0` 明确登记为**多因状态**
  （至少含：终局计分屏 / 退回主菜单 / 游戏不在前台 / 计数回绕 / 采样管线异常），
  **撤回「11 个停摆窗是终局态」这条整组归类**，改为逐窗待归因；
  目标①数据面（22 真慢 / 8 趟）**维持不变**（它不依赖 `df==0` 的定性），
  `21/32` 覆盖数**维持不变**（它是「有计分屏证据的窗数」，本轮未推翻）；
  追加勘误时**必须写明 `p` 判据的适用边界**。**本线建议此项。**
  **(B)** 只改措辞不改结论：承认 `p` 判据语义不精确，但认为「多数冻结窗仍是终局态」方向成立，
  D-15 按原 (A) 裁决、仅追加一条脚注。
  **(C)** D-15 全部冻结：在新证据下**不再使用任何窗末截图作为终局/非终局判据**，
  把「冻结窗性质」整块从目标①叙事里移除，只留 `df==0` 这个事实本身。
  **另需一并裁**：本轮目视是**单次、无第二人复核**，是否要求先补一道异族全量目视
  （25 张逐张看）再据此改写台账？还是允许「先按 A 降级登记、全量目视作为后续独立事项」？
  **涉纪律**：本项推翻的是**已送裁决并已有 RULING 的判据**，且 RULING 由 GPT 6.1 在
  「p 判据成立」的未言明前提下作出 ⇒ 须用户明示才可改口径。
  **在裁决前**：本线新产出一律不得再单独引用「终局态」作为机制结论；
  凡引用 §543/§544 的终局归因，必须带「判据语义待重裁，见 D-16」标注。
  **证据**：台账 §545（本轮新增，含目视表、mtime/声明对照表、qc151_fields 原文摘录）；
  原图 `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/archive_T42/measure_w1_end_x.png`
  与 `.../l1_20261023e4/measure_w2_end_x.png`；
  独立复核工作流 `dwfrun-72de3cd1`（GLM-5.3-Flash，取证+核验各自目视）**在飞，未回件**。

"""

new = wt[: idx + len(ANCHOR)] + BLOCK.encode("utf-8") + wt[idx + len(ANCHOR):]
with open(PEND, "wb") as f:
    f.write(new)
print("inserted %d bytes; file now %d bytes" % (len(BLOCK.encode("utf-8")), len(new)))
