# -*- coding: utf-8 -*-
"""重建 board（事故恢复，v3）——目标：内容完整 + 段序正确，标注为事故重建版。
基底 pass4(21:39) 含到第 110 轮；第 111 轮段从 BOARD_ARCHIVE 的 H40 归档取回。
"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
MD = os.path.join(D, "R16_BASE", "board_rebuild")
P4 = os.path.join(D, "_hygiene", "H34", "pass4", "STATUS_BOARD.before.md")
ARC = os.path.join(D, "BOARD_ARCHIVE.md")
def sha8(b): return hashlib.sha256(b).hexdigest().upper()[:16]

def seg_of(lines, prefix):
    i0 = next(i for i,l in enumerate(lines) if l.startswith(prefix))
    j = i0+1
    while j < len(lines) and not lines[j].startswith("## "): j += 1
    i1 = j-1
    while i1>i0 and lines[i1].strip()=="": i1 -= 1
    return lines[i0:i1+1]

def drop(lines, prefix, ptr):
    i0 = next(i for i,l in enumerate(lines) if l.startswith(prefix))
    j = i0+1
    while j < len(lines) and not lines[j].startswith("## "): j += 1
    i1 = j-1
    while i1>i0 and lines[i1].strip()=="": i1 -= 1
    return lines[:i0] + [ptr] + lines[i1+1:]

base = open(P4,"rb").read().decode("utf-8").split("\n")
if base and base[-1]=="": base = base[:-1]
arc = open(ARC,"rb").read().decode("utf-8").split("\n")

# 第 111 轮段从 archive 取回（H40 头之后）
r111 = seg_of(arc, "## 🔴 第 111 轮")
print("从 archive 取回第111轮段:", len(r111), "行")

L = base
# 变换1：H38 指针（第96-98轮）
L = drop(L, "## 🔴 第 96–98 轮", "> 📦 ## 🔴 第 96–98 轮（2026-11-20 19:4x）· **`[已证]` 的 ④ 完整性缺口：1,347 行（81.4%）没写成文 ④** 已归档至 BOARD_ARCHIVE.md（2026-11-20 21:44，逐字搬，missing=0；本次由 Lead 执行，卫生员 H38）")
# pass4 里第 111 轮不存在 → 追加（R15 当日写的）
L = L + [""] + r111
print("补第111轮后:", len(L), "行")
# 变换2：H39 指针
L = drop(L, "## 🔴 第 105–106 轮", "> 📦 ## 🔴 第 105–106 轮（2026-11-20 21:1x）· 746 批判死；11 行「0 引用」实为名字错 已归档至 BOARD_ARCHIVE.md（2026-11-20 23:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H39）")
L = drop(L, "## 🔴 第 107–109 轮", "> 📦 ## 🔴 第 107–109 轮（2026-11-20 21:3x）· **`[已证]` 证据可解析率 28.90% → 50.73%** 已归档至 BOARD_ARCHIVE.md（2026-11-20 23:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H39）")
# 变换3：H40 指针
L = drop(L, "## 🔴 第 110 轮", "> 📦 ## 🔴 第 110 轮（2026-11-20 21:5x）· 证据指针修复收尾：R_OK 843 / 1,654（50.97%） 已归档至 BOARD_ARCHIVE.md（2026-11-21 09:5x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H40）")
L = drop(L, "## 🔴 第 111 轮", "> 📦 ## 🔴 第 111 轮（2026-11-20 22:0x）· 802 行 trace-only 探针：D-47 的第三个量化后果 已归档至 BOARD_ARCHIVE.md（2026-11-21 09:5x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H40）")
print("归档指针就位后:", len(L), "行")

# 变换4：追加 R16 四段
for fn in ["BOARD_R16_SEG.md","BOARD_R16_SEG2.md","BOARD_R16_SEG3.md","BOARD_R16_SEG4.md"]:
    s = open(os.path.join(D,"R16_BASE",fn),"rb").read().decode("utf-8").split("\n")
    if s and s[-1]=="": s = s[:-1]
    L = L + [""] + s
print("追加 R16 四段后:", len(L), "行")

# 变换5：H41 指针（R16 接手段）
L = drop(L, "## 🔴 R16 接手", "> 📦 ## 🔴 R16 接手（2026-11-20 22:1x）· 基线独立复算无漂移 + 三件裁决落地 + §1051 入账 已归档至 BOARD_ARCHIVE.md（2026-11-21 11:4x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H41）")
print("H41 指针后:", len(L), "行")

out = ("\n".join(L)+"\n").encode("utf-8")
open(os.path.join(MD,"board_rebuilt.md"),"wb").write(out)
print("\n重建产物:", len(out), "B  行数", len(L), " sha", sha8(out))
print("段标题数:", sum(1 for l in L if l.startswith("## ")))
