# -*- coding: utf-8 -*-
"""写盘：加事故重建说明头 + 压到 <300 行 + 安装为 STATUS_BOARD.md。"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
MD = os.path.join(D,"R16_BASE","board_rebuild")
BOARD = os.path.join(D,"STATUS_BOARD.md")
def sha8(b): return hashlib.sha256(b).hexdigest().upper()[:16]

L = open(os.path.join(MD,"board_final.md"),"rb").read().decode("utf-8").split("\n")
if L and L[-1]=="": L = L[:-1]

# 再归档「第 21 轮」段（11 行）压行数
def seg_of(lines, prefix):
    i0 = next(i for i,l in enumerate(lines) if l.startswith(prefix))
    j=i0+1
    while j<len(lines) and not lines[j].startswith("## "): j+=1
    i1=j-1
    while i1>i0 and lines[i1].strip()=="": i1-=1
    return i0,i1,lines[i0:i1+1]

i0,i1,seg = seg_of(L, "## 🔴 第 21 轮")
ptr = "> 📦 ## 🔴 第 21 轮：`0045A640` 两卡相反，第三方裁决**推翻审计** 已归档至 BOARD_ARCHIVE.md（2026-11-21 12:0x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H42·事故重建）"
L = L[:i0] + [ptr] + L[i1+1:]
print("归档第21轮（%d 行）→ %d 行" % (len(seg), len(L)))

# 写入 archive（这次是真的新段，先确认不存在）
ARC = os.path.join(D,"BOARD_ARCHIVE.md")
arcb = open(ARC,"rb").read()
has = "## 🔴 第 21 轮：`0045A640`".encode("utf-8") in arcb
print("archive 已含第21轮段?", has)
if not has:
    hdr = ["","---","",
      "## 📦 H42 归档（2026-11-21，R16 Lead 执行·事故重建期）：看板第 21 轮段",
      "",
      "> 来源：`STATUS_BOARD.md`（事故重建版）。以下**逐字搬入**，未改一字；board 侧改为指针行。",
      f"> 归档前 archive {len(arcb)} B / sha256 `{sha8(arcb)}…`。",
      ""]
    open(ARC,"ab").write(("\n".join(hdr)+"\n"+"\n".join(seg)+"\n").encode("utf-8"))
    print("已写入 archive")

# 事故说明头（插在第 1 行标题之后）
note = [
"",
"> ⚠️ **本文件于 2026-11-21 11:49 发生一次写入事故，此为事故重建版（非逐字节还原）。**",
"> 起因：Lead 一次 PowerShell 追加脚本中变量冲突（`$b` 被覆盖），把本文件写成只剩 1,829 B，原 41,860 B 内容丢失；该文件在 git 中为 untracked，无版本可回。",
"> 重建依据：① `_hygiene\\H34\\pass4\\STATUS_BOARD.before.md`（2026-11-20 21:39，含到第 110 轮）；② `BOARD_ARCHIVE.md` 中 H38/H39/H40/H41 四次的**逐字归档副本**（第 111 轮段从 H40 归档取回）；③ 本任自留的四段原文 `R16_BASE\\BOARD_R16_SEG{1..4}.md`。",
"> 重建方式：按本任**变换序列重放**（H38 指针 → 补第 111 轮 → H39/H40 指针 → 追加 R16 四段 → H41 指针 → 追加 R16-8 段 → 归档第 21 轮段）。**内容与段序已核对，段标题数 13、关键锚点（D-47/§12.6/口径 A/R16-6/R16-8/台账 4,213,918）全部命中；但字节级哈希已不可能与原件一致。**",
"> 归档去向：`R16_BASE\\board_rebuild\\`（`board_final.md` 为安装前的副本）、`R16_BASE\\rebuild_v3.py`/`rebuild_v4.py`（重建脚本，可复跑）。",
]
# 插到第 1 行之后
L = [L[0]] + note + L[1:]
out = ("\n".join(L)+"\n").encode("utf-8")
print("安装前:", len(out), "B  行数", len(L), " sha", sha8(out))
open(BOARD,"wb").write(out)
after = open(BOARD,"rb").read()
print("已安装 STATUS_BOARD.md:", len(after), "B  行数", len(after.decode().split("\n"))-1)
