# M51 PROGRESS — 并表 a-P0-ADJ5 审计确认的 19 行外部取址证据入口

## 0. 来源与筛选（VERDICT 无逐行清单）
- VERDICT.md §3/§5 仅给计数 19 与判据（push 立即数取址 / mov [reg+d],立即数取址），无逐行地址清单；按卡规改走自筛路线。
- 判据落地：读 audit 现成逐行证据表（reliable_subset.tsv 的 REAL-EVIDENCE 层 + ab_channel.tsv 的 addr_taken_real 标志 + ADJ_100.tsv 的 54 个 FUNC 行）三表求交并剔 0042FF70；脚本如下（纯标准库，无 venv/pip）：
```python
import re
R="D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/P0_ADJ5"
def load(p):
    L=[x.rstrip() for x in open(p,encoding="utf-8-sig") if x.strip()]
    h=L[0].split("\t"); return [dict(zip(h,x.split("\t"))) for x in L[1:]]
adj=load(R+"/ADJ_100.tsv")
ab =load(R+"/_audit/EVIDENCE/ab_channel.tsv")
rel=load(R+"/_audit/EVIDENCE/reliable_subset.tsv")
d54={r["address"] for r in adj if r["verdict"]=="FUNC"}       # 54 delta 行
taken={r["address"] for r in ab if r["addr_taken_real"]=="1" and r["my_verdict"]=="FUNC"}
real={r["address"] for r in rel if r["tier"]=="REAL-EVIDENCE" and re.search(r"push 0x[0-9a-f]+|mov \[[a-z]+\+0x[0-9a-f]+\],0x[0-9a-f]+",r["evidence"])}
sel=sorted(d54 & taken & real - {"0042FF70"})
assert len(sel)==19 and sel==sorted(real)   # 与审计 REAL-EVIDENCE 层逐行一致
```
- 筛出 19 行与 reliable_subset REAL-EVIDENCE 层逐行一致；0042FF70 落在 STRUCT-ONLY 层（N6 体不连贯：salc/in al,0xfe），本就不在 sel 中。

## 1. 并入规则
- 先核盘：19 行改前全部 NOT_IN coverage；grade 一律 [静态推断]；subsystem S22；name 用 delta 值（sub_+8 位 hex）；evidence_path 用 delta 值；n_sources=1、conflict=0。
- one_line_semantics：delta 原文写「结构证据入口…语义未证」，与实为外部证据不符，按实际改写为「有外部取址证据（push 立即数取址 <取址指令>；来源 P0_ADJ5/_audit/EVIDENCE/reliable_subset.tsv REAL-EVIDENCE，审计 a-P0-ADJ5 VERDICT §3/§5 确认）；语义未证」；末尾保留「（P0 入口闭合用；归属待 P1，不计入任何子系统百分比）」。

## 2. 必做自检 (a)-(f)
- (a) 最终并入 **19** 行：0040BDA0 0040BE10 0040C1F0 0040C7E0 0040CBC0 0040D220 0040D380 0040D400 0040D480 0040D500 0040E7B0 0040EE80 0040F4D0 0040FB70 0041D2C0 004200C0 00420920 004301C0 00438590；与审计 19 差 **0**（三表求交逐行复现 REAL-EVIDENCE，未凑数）。
- (b) coverage 数据行 改前 **18,479** → 改后 **18,498**（=18,479+19）。
- (c) 改后 entry group by：重复组 **0**（18,498 unique / 18,498 行）；19 个新 entry 各出现恰好 1 次。
- (d) grade（第 5 列）改前自算 `[已证]`1,460 / `[静态推断]`5,995 / `[未证]`11,024，和 18,479；改后 `[已证]`**1,460**(±0) / `[静态推断]`**6,014**(+19) / `[未证]`**11,024**(±0)，和 18,498=18,479+19。
- (e) `0042FF70` 改后不在 coverage（present=NO）；剔除生效（未并入）。
- (f) coverage.tsv SHA-256 改前 `8036bf8b82a9ffaf0b01903e4c2c27dbca70da810625b9bfdcfff68856e7b7ed` → 改后 `b4c998c06f91e9b23c0a34ea459a308eee8212671d761b0189b7135dfbcbe94c`（备份 `_hygiene/coverage.M51.bak`，SHA 与改前一致）；8 列格式/无 BOM/LF 保持。

## 3. C 口径与边界
- 改后 C 口径 = **18,498**（改前 18,479 + 19 行）；19 行全在 atlas 之外且 subsystem=S22，不进 A 分母、不计入任何子系统百分比。
- 本卡未改 PANEL，C 口径待下卡同步（A/B 及面板行级数值同样留待下卡统一处理）。
- 改前/改后 conflict==1 均 254；未改 PANEL.md、CONFLICTS.tsv、PENDING_CORRECTIONS.tsv、台账、R14_COMMON.md、STATUS_BOARD.md、ra2youli；未 git commit、未建 venv、未 pip install。
- 逐行明细见 `MERGE_LOG.tsv`（19 行 MERGED_NEW）。