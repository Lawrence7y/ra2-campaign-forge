# -*- coding: utf-8 -*-
"""重建 board 最终版：再归档第 99–104 轮段 + 补回 R16-8 段 + 加事故重建头。"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
MD = os.path.join(D, "R16_BASE", "board_rebuild")
ARC = os.path.join(D, "BOARD_ARCHIVE.md")
def sha8(b): return hashlib.sha256(b).hexdigest().upper()[:16]

L = open(os.path.join(MD,"board_rebuilt.md"),"rb").read().decode("utf-8").split("\n")
if L and L[-1]=="": L = L[:-1]

def seg_of(lines, prefix):
    i0 = next(i for i,l in enumerate(lines) if l.startswith(prefix))
    j=i0+1
    while j<len(lines) and not lines[j].startswith("## "): j+=1
    i1=j-1
    while i1>i0 and lines[i1].strip()=="": i1-=1
    return i0,i1,lines[i0:i1+1]

# 归档第 99–104 轮段
i0,i1,seg = seg_of(L, "## 🔴 第 99–104 轮")
ptr = "> 📦 ## 🔴 第 99–104 轮（2026-11-20 20:4x）· 91 行 ④ 补写成文：13.78% → 19.29% 已归档至 BOARD_ARCHIVE.md（2026-11-21 12:0x，逐字搬，missing=0；本次由 Lead 执行，卫生员 H42·事故重建）"
L = L[:i0] + [ptr] + L[i1+1:]
print("归档第99-104轮（%d 行）→ %d 行" % (len(seg), len(L)))

# 该段写入 archive
arcb = open(ARC,"rb").read()
hdr = ["","---","",
  "## 📦 H42 归档（2026-11-21，R16 Lead 执行·事故重建期）：看板第 99–104 轮段",
  "",
  "> 来源：`STATUS_BOARD.md`（事故重建版）。以下**逐字搬入**，未改一字；board 侧改为指针行。",
  f"> 归档前 archive {len(arcb)} B / sha256 `{sha8(arcb)}…`。",
  ""]
open(ARC,"ab").write(("\n".join(hdr)+"\n"+"\n".join(seg)+"\n").encode("utf-8"))
print("已写入 archive")

# 补回 R16-8 段
R168 = """
## 🔴 R16 续线（2026-11-21 11:4x）· 证据底座收口：791 行的正确分解与 Lead 错误 R16-8

- **R16-8（Lead 错误，已作废我上一轮的建议）**：我在收官后建议「先派卡测 791 行里有多少能连到盘上已有的 `PROOF_*`」——**这个测量已经做过了**。`PROBE_802_ANCHOR` 已对 802 行做完全量分类，791 正是 802 减去已修的 11 行。该建议与**我自己前面记录的结论直接矛盾**，属「推荐已做过的工作」。
- **791 行的正确分解（照录实测）**：`= 116 行 dump-only + 675 行零候选`。116 行是那 127 个文件名命中行里「锚点只是逐 entry dump」的部分（已判不做）；675 行是文件名**零命中**者。
- **真正的缺口（本续线要补的）**：`PROBE_802_ANCHOR` 只对 **127 个文件名命中行**做过**内容级**判定；那 **675 行零候选**只做过**文件名索引**，**从未做过内容级搜索**。存在「文件名不含 entry、但内容里锚定了 entry」的可能（按函数名命名、按卡号命名、或在汇总表里以 `entry` 列出现）。
- **已派**：`R16-MEASURE-EVID675`（只读、deepseek），对 675 行做**有界内容级搜索**（限 `.tsv/.txt/.json/.md/.csv/.log`、先报规模再决定是否分片），四桶（`CTX_STRONG/MEDIUM/WEAK/NONE`），并**顺带用同一判据重跑 116 行**复核「不做」结论是否仍成立。抽样 ≤18 行。
- **口径提醒（续线引用数字时必读）**：`ct-only` 与 `trace-only` 在本盘**同为 791**（把第 6 列按 `;|,` 切段、所有段都是 `classification_trace` 的行数 = 791，与 `resolve.py` 的 `R_TRACE_ONLY` 逐值相同）。若用「含 ct」子串匹配会数出 **892**——多出的 90 行是 ct 与其它来源**并列**，不是 trace-only。
"""
SL = [l for l in R168.split("\n")]
while SL and SL[0]=="": SL.pop(0)
while SL and SL[-1]=="": SL.pop()
L = L + [""] + SL
print("补回 R16-8 段（%d 行）→ %d 行" % (len(SL), len(L)))

out = ("\n".join(L)+"\n").encode("utf-8")
open(os.path.join(MD,"board_final.md"),"wb").write(out)
print("\n最终重建版:", len(out), "B  行数", len(L), " sha", sha8(out))
