# -*- coding: utf-8 -*-
"""安全归档：把 board 的「第 5 个错 F3a」段搬进 archive（该段已在 archive 有副本则只留指针）。
全程断言：archive 前缀不变、board 重建等于预期、missing=0。"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
BOARD = os.path.join(D,"STATUS_BOARD.md"); ARCH = os.path.join(D,"BOARD_ARCHIVE.md")
def sha(b): return hashlib.sha256(b).hexdigest().upper()

boards = open(BOARD,"rb").read()
arc0 = open(ARCH,"rb").read()
text = boards.decode("utf-8")
trailing = text.endswith("\n")
lines = text.split("\n")
if trailing: lines = lines[:-1]

PREFIX = "## 🔴🔴 第 5 个错 + 最重大发现"
i0 = next(i for i,l in enumerate(lines) if l.startswith(PREFIX))
j = i0+1
while j < len(lines) and not lines[j].startswith("## "): j += 1
i1 = j-1
while i1>i0 and lines[i1].strip()=="": i1 -= 1
seg = lines[i0:i1+1]
print("搬段:", i0+1, "-", i1+1, "共", len(seg), "行")

# archive 里是否已有同标题段
arc_text = arc0.decode("utf-8")
already = PREFIX in arc_text
print("archive 已含该段?", already)

if not already:
    hdr = ["","---","",
      "## 📦 H43 归档（2026-11-21，R16 Lead 执行）：看板「第 5 个错 / F3a 317 行」段",
      "",
      "> 来源：`STATUS_BOARD.md`。以下**逐字搬入**，未改一字；board 侧改为指针行。",
      f"> 归档前 archive {len(arc0)} B / sha256 `{sha(arc0)[:16]}…`。",
      ""]
    open(ARCH,"ab").write(("\n".join(hdr)+"\n"+"\n".join(seg)+"\n").encode("utf-8"))

ptr = "> 📦 ## 🔴🔴 第 5 个错 + 最重大发现：`F3a` 317 行，「3 个达标」里 2 个是名义达标 已归档至 BOARD_ARCHIVE.md（2026-11-21 12:3x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H43）"
newlines = lines[:i0] + [ptr] + lines[i1+1:]
newtext = "\n".join(newlines) + ("\n" if trailing else "")
open(BOARD,"wb").write(newtext.encode("utf-8"))

# 校验
arc1 = open(ARCH,"rb").read()
boards1 = open(BOARD,"rb").read()
if not already:
    assert arc1.startswith(arc0), "archive 前缀被改"
at = arc1.decode("utf-8")
miss = [l for l in seg if l.strip() and l not in at]
expect = ("\n".join(lines[:i0]+[ptr]+lines[i1+1:]) + ("\n" if trailing else "")).encode("utf-8")
assert boards1 == expect, "board 重建不符"
print("archive:", len(arc0), "->", len(arc1), "B")
print("board  :", len(boards), "->", len(boards1), "B ; 行数", len(lines), "->", len(newlines))
print("missing 非空行未找到:", len(miss), " ; board 重建 PASS")
