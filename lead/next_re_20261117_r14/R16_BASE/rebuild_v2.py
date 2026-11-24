# -*- coding: utf-8 -*-
"""重建 board v2：以 pass4 为内容基底，按本任变换序列重放，产出【内容正确】的看板并标注为事故重建版。
不做逐字节还原（原文件已损坏且无 git 版本）；以「段集合完整」为验收标准。
"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
P4 = os.path.join(D, "_hygiene", "H34", "pass4", "STATUS_BOARD.before.md")
MD = os.path.join(D, "R16_BASE", "board_rebuild")
SEGS = [("BOARD_R16_SEG.md","R16 接手（2026-11-20 22:1x）"),
        ("BOARD_R16_SEG2.md","R16 第 1–7 轮"),
        ("BOARD_R16_SEG3.md","R16 第 8–21 轮"),
        ("BOARD_R16_SEG4.md","R16 第 22–32 轮")]

def sha8(b): return hashlib.sha256(b).hexdigest().upper()[:16]

raw = open(P4,"rb").read().decode("utf-8")
lines = raw.split("\n")
if lines and lines[-1]=="": lines = lines[:-1]

def drop_segment(lines, prefix, ptr=None):
    i0 = next(i for i,l in enumerate(lines) if l.startswith(prefix))
    j = i0+1
    while j < len(lines) and not lines[j].startswith("## "): j += 1
    i1 = j-1
    while i1>i0 and lines[i1].strip()=="": i1 -= 1
    return lines[:i0] + ([ptr] if ptr else []) + lines[i1+1:]

# --- 变换 1：H38 搬走的第 96–98 轮段（留指针）---
ptr38 = "> 📦 ## 🔴 第 96–98 轮（2026-11-20 19:4x）· **`[已证]` 的 ④ 完整性缺口：1,347 行（81.4%）没写成文 ④** 已归档至 BOARD_ARCHIVE.md（2026-11-20 21:44，逐字搬，missing=0；本次由 Lead 执行，卫生员 H38）"
lines = drop_segment(lines, "## 🔴 第 96–98 轮", ptr38)
print("变换1 后:", len(lines), "行")

# --- 变换 2：H39 搬走第 105–106 / 107–109（留 2 指针）---
p39a = "> 📦 ## 🔴 第 105–106 轮（2026-11-20 21:1x）· 746 批判死；11 行「0 引用」实为名字错 已归档至 BOARD_ARCHIVE.md（2026-11-20 23:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H39）"
p39b = "> 📦 ## 🔴 第 107–109 轮（2026-11-20 21:3x）· **`[已证]` 证据可解析率 28.90% → 50.73%** 已归档至 BOARD_ARCHIVE.md（2026-11-20 23:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H39）"
lines = drop_segment(lines, "## 🔴 第 105–106 轮", p39a)
lines = drop_segment(lines, "## 🔴 第 107–109 轮", p39b)
print("变换2 后:", len(lines), "行")

# --- 变换 3：H40 搬走第 110 / 111（留 2 指针）---
p40a = "> 📦 ## 🔴 第 110 轮（2026-11-20 21:5x）· 证据指针修复收尾：R_OK 843 / 1,654（50.97%） 已归档至 BOARD_ARCHIVE.md（2026-11-21 09:5x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H40）"
p40b = "> 📦 ## 🔴 第 111 轮（2026-11-20 22:0x）· 802 行 trace-only 探针：D-47 的第三个量化后果 已归档至 BOARD_ARCHIVE.md（2026-11-21 09:5x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H40）"
lines = drop_segment(lines, "## 🔴 第 110 轮", p40a)
lines = drop_segment(lines, "## 🔴 第 111 轮", p40b)
print("变换3 后:", len(lines), "行  （此即 H40 完成时的 board）")

# --- 变换 4：追加 R16 四段 ---
for fn, tag in SEGS:
    seg = open(os.path.join(D,"R16_BASE",fn),"rb").read().decode("utf-8")
    sl = seg.split("\n")
    if sl and sl[-1]=="": sl = sl[:-1]
    lines = lines + [""] + sl
    print(f"  + {fn}: {len(sl)} 行 → 累计 {len(lines)} 行")

# --- 变换 5：H41 搬走 R16 接手段（留指针）---
p41 = "> 📦 ## 🔴 R16 接手（2026-11-20 22:1x）· 基线独立复算无漂移 + 三件裁决落地 + §1051 入账 已归档至 BOARD_ARCHIVE.md（2026-11-21 11:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H41）"
lines = drop_segment(lines, "## 🔴 R16 接手", p41)
print("变换5 后:", len(lines), "行")

out = ("\n".join(lines) + "\n").encode("utf-8")
open(os.path.join(MD,"board_rebuilt.md"),"wb").write(out)
print()
print("重建产物:", len(out), "B  行数", len(lines), " sha", sha8(out))
