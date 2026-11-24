# -*- coding: utf-8 -*-
"""Fix line 1 of modified PANEL.md: insert M66 note cleanly after '覆盖面板（'."""
import hashlib
P = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md"
BAK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\MERGE_M66\PANEL.md.bak"

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1<<20),b""): h.update(c)
    return h.hexdigest().upper()

orig_lines = open(BAK, encoding="utf-8").read().split("\n")
cur_lines  = open(P, encoding="utf-8").read().split("\n")

orig1 = orig_lines[0]
prefix = "# PANEL — R14 coverage 覆盖面板（"
assert orig1.startswith(prefix), repr(orig1[:60])

TITLE_NOTE = ("M66 并表 29 行（NAMED_PUSH_AUDIT6 PASS 18 行 S22 TClassFactory 同族 + "
              "NAMED_PUSH_AUDIT5 PASS 11 行 S06 4/S20 7，均 atlas 内，仅改 coverage 第 4/5/6 列、"
              "第 1/2/3/7/8 列不动；coverage 18,498 行不变；全表 [已证] 1,527→1,556、"
              "atlas 内 1,521→1,550、atlas 外仍 6；面板 S22 proved 69→87、S06 126→130、"
              "S20 46→53；strict 按权威口径 [未证] 字面重算，达标判定不变（严格仍仅 S17）；不 git commit）；")

cur_lines[0] = prefix + TITLE_NOTE + orig1[len(prefix):]
open(P,"wb").write("\n".join(cur_lines).encode("utf-8"))
print("line1 fixed")
print("sha after:", sha256(P))
print("line1 head:", cur_lines[0][:120])
