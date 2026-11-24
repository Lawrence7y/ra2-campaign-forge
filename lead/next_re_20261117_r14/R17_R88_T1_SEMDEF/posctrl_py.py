#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""posctrl_py.py — R46-T1 Q5 正控 · 法 2（Python 独立实现）

与 decide_semdef.py 零代码共享：
  - 清单读法不同（读字节 → 归一换行 → 手工切列，不用 csv.DictReader）；
  - 分类谓词重写；「半证据」用补集定义，不再枚举一遍判据；
  - 甲用「实盘扫描 − 过程 − 不在档 A」算，而不是「档 A + 补集」。
短名单里的 225 / 228 之类差异来自自测量产物名单长度（对方脚本自己也在被扫），已在 Q5 里说明。
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

R = r"D:\Project\ra2-campaign-forge\lead"
R14 = R + r"\next_re_20261117_r14"
SIX = (".md", ".txt", ".json", ".tsv", ".log", ".csv")


def cols(path):
    with open(path, "rb") as fh:
        data = fh.read().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    nl = data.find("\n")
    hdr = data[:nl].split("\t")
    out = []
    for line in data[nl + 1:].split("\n"):
        if not line:
            continue
        out.append(dict(zip(hdr, [x.strip() for x in line.split("\t")])))
    return out


A = cols(R14 + r"\R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv")
CP = cols(R14 + r"\R17_R78_T1_RECLASS\files_tier_Cprime.tsv")
VD = cols(R14 + r"\R17_R81_T2_EVID\_verdicts.tsv")
OLDC = cols(R14 + r"\R17_R72_T1_CLEANSCALE\files_tier_C.tsv")

ab = {x["rel"]: int(x["bytes"]) for x in A}
vd = {x["rel"]: x["verdict"] for x in VD}
cp = {x["rel"]: x["why"] for x in CP}
old = {x["rel"] for x in OLDC}

# --- 自测量装置 / 清单（语义重写一遍，不导入对方名单）
SELF = set()
SELF_DIRS = ("R17_R72_T1_CLEANSCALE", "R17_R78_T1_RECLASS", "R17_R84_T2_EVID2",
             "R17_R81_T2_EVID", "R17_R70_T1_REPRO", "R17_R88_T1_SEMDEF")
SELF_NAMES = ("files_tier_A_snap2.tsv", "files_tier_A.tsv", "files_tier_A_snap1.tsv",
              "files_tier_B.tsv", "files_tier_C.tsv", "files_tier_Cprime.tsv",
              "files_excluded_prime.tsv", "selfartifacts_detail.tsv", "summary_snap2.json",
              "summary.json", "q1_tie_detail.tsv", "tie_dump.txt", "_verdicts.tsv",
              "_content_metrics.tsv", "_undead_evid.tsv", "scale_vs_baseline.json",
              "decide_semdef.py", "posctrl_py.py", "posctrl_ps.ps1", "closure.py",
              "xcheck.py", "audit_parts.py", "probe_evid_exts.ps1", "tier_final.tsv",
              "semi_items.tsv", "excluded_final.tsv", "other6_unknown.tsv", "semdef.json",
              "run_decide.log", "run_posctrl_py.log", "run_posctrl_ps.log",
              "run_closure.log", "run_xcheck.log")
for d in SELF_DIRS:
    for n in SELF_NAMES:
        SELF.add("next_re_20261117_r14/%s/%s" % (d, n))
# REPORT.md 只在本次目录里算自测量产物，其余目录的同名件不动
SELF.add("next_re_20261117_r14/R17_R88_T1_SEMDEF/REPORT.md")
SELF &= set(ab)

# --- 乙
keep = {r for r in ab if (r in cp and cp[r].startswith("P1a_")) or (r not in cp and vd.get(r) == "对象抄本")}
keep -= SELF
proc = {r for r in ab if r not in keep and (r in SELF or (r not in cp and vd.get(r) == "过程输出"))}
rest = set(ab) - keep - proc
bK = sum(ab[r] for r in keep)
bP = sum(ab[r] for r in proc)
bR = sum(ab[r] for r in rest)
print(f"PY 乙 KEEP={len(keep)}/{bK}  PROC={len(proc)}/{bP}  REST={len(rest)}/{bR}")
print(f"PY 乙 三分无重 {len(keep) + len(proc) + len(rest) == len(ab)} ; "
      f"字节 {bK + bP + bR == sum(ab.values())}")

kin = {r for r in keep if r in old}
print(f"PY KEEP∩oldC={len(kin)}/{sum(ab[r] for r in kin)}  "
      f"KEEP∖oldC={len(keep) - len(kin)}/{bK - sum(ab[r] for r in kin)}")
print(f"PY GB={bK / 1e9:.6f} GiB={bK / 2 ** 30:.6f}")

# --- 甲：实盘 6 扩展名
disk = {}
for root, ds, fs in os.walk(R):
    for fn in fs:
        if os.path.splitext(fn)[1].lower() in SIX:
            p = os.path.join(root, fn)
            disk[os.path.relpath(p, R).replace(os.sep, "/")] = os.path.getsize(p)
notA = {r for r in disk if r not in ab}
pA = {r for r in disk if r in proc}
nJia = len(disk) - len(pA) - len(notA)
bJia = sum(disk.values()) - sum(disk[r] for r in pA) - sum(disk[r] for r in notA)
print(f"PY 甲 disk={len(disk)}/{sum(disk.values())}  proc={len(pA)}/{sum(disk[r] for r in pA)}  "
      f"notA={len(notA)}/{sum(disk[r] for r in notA)}  JIA={nJia}/{bJia}")
print(f"PY 甲 GB={bJia / 1e9:.6f} GiB={bJia / 2 ** 30:.6f}")


# --- 甲（档 A 基底版，与 decide_semdef.py 同基底，便于逐一对照）
_A_proc = {r for r in ab if r in proc and r in ab}
nJ2 = len(ab) - len(_A_proc)
bJ2 = sum(ab.values()) - sum(ab[r] for r in _A_proc)
print(f"PY 甲(档A基底) = {len(ab)} - {len(_A_proc)} 件 ⇒ {nJ2}/{bJ2}")
