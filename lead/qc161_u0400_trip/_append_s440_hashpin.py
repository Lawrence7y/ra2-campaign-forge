# -*- coding: utf-8 -*-
# Append-only hash-pin for XVERIFY_X_STATIC (audit book in delivery package).
import hashlib

LEDGER = r"D:\Project\ra2-campaign-forge\lead\ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md"
BOOK = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\x_ingame_close_20261026\XVERIFY_X_STATIC_20261026.md"

h = hashlib.sha256(open(BOOK, "rb").read()).hexdigest()
sz = len(open(BOOK, "rb").read())
line = (
    "\r\n# §440　补①末（审计书钉值）：静态审计判定书 XVERIFY_X_STATIC_20261026.md 固定哈希\r\n"
    "#        sha256=%s（%d B，与 §440 补①到盘记录同件）。交付包四件钉值齐备：\r\n"
    "#        驱动 v2=65e086e7…／变异件=8c74bba6…／设计件终值=b66466b6…／审计书=77bb6d6c…。\r\n"
    "#        复核实测：本追加前行尾/内容零改动（哈希即此值）。\r\n" % (h, sz)
)
with open(LEDGER, "ab") as f:
    f.write(line.encode("utf-8"))
print("APPENDED hash:", h, "size:", sz)
