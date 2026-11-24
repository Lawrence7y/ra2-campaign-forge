# -*- coding: utf-8 -*-
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
BOARD = os.path.join(D, "STATUS_BOARD.md"); ARCH = os.path.join(D, "BOARD_ARCHIVE.md")
def sha(b): return hashlib.sha256(b).hexdigest().upper()
raw = open(BOARD,"rb").read(); h0 = sha(raw); n0 = len(raw)
text = raw.decode("utf-8"); trailing = text.endswith("\n")
lines = text.split("\n")
if trailing: lines = lines[:-1]
i0 = 236; i1 = 247
assert lines[i0].startswith("## 🔴 R16 接手"), lines[i0][:40]
assert lines[i1+1].startswith("## 🔴 R16 第 1–7 轮"), lines[i1+1][:40]
seg = lines[i0:i1+1]
while seg and seg[-1].strip()=="": seg.pop()
arc_before = open(ARCH,"rb").read()
hdr = ["","---","",
  "## 📦 H41 归档（2026-11-21，R16 Lead 执行）：看板 R16 接手段",
  "",
  "> 来源：`STATUS_BOARD.md` 第 237–248 行（搬走前位置）。以下**逐字搬入**，未改一字；board 侧改为指针行。",
  f"> 归档前 board {n0} B / sha256 `{h0[:16]}…`，archive {len(arc_before)} B / sha256 `{sha(arc_before)[:16]}…`。",
  ""]
arc_add = ("\n".join(hdr)+"\n"+"\n".join(seg)+"\n").encode("utf-8")
open(ARCH,"ab").write(arc_add)
ptr = ["> 📦 ## 🔴 R16 接手（2026-11-20 22:1x）· 基线独立复算无漂移 + 三件裁决落地 + §1051 入账 已归档至 BOARD_ARCHIVE.md（2026-11-21 11:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H41）"]
new = lines[:i0] + ptr + lines[i1+1:]
open(BOARD,"wb").write(("\n".join(new)+("\n" if trailing else "")).encode("utf-8"))
arc_after = open(ARCH,"rb").read(); board_after = open(BOARD,"rb").read()
assert arc_after.startswith(arc_before) and arc_after[len(arc_before):]==arc_add
at = arc_after.decode("utf-8")
miss = [l for l in seg if l.strip() and l not in at]
expect = ("\n".join(lines[:i0]+ptr+lines[i1+1:]) + ("\n" if trailing else "")).encode("utf-8")
assert board_after == expect
print("=== H41 归档 ===")
print(f"board   : {n0} B -> {len(board_after)} B ; 行数 {len(lines)} -> {len(new)}")
print(f"archive : {len(arc_before)} B -> {len(arc_after)} B (+{len(arc_add)})")
print(f"missing 非空行未找到: {len(miss)}  ; board 重建 PASS ; archive 前缀 PASS")
