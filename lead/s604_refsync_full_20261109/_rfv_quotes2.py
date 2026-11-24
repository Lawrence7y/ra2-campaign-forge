# -*- coding: utf-8 -*-
"""_rfv_quotes2.py — 精确核 28 处「原文逐字」：显式 (文件,行) -> 草案 §3 引文片段"""
import re
ROOT = "D:/Project/ra2-campaign-forge/lead"
DRAFT = ROOT + "/s604_refsync_full_20261109/_rf_FULL_REFSYNC_DRAFT.md"
with open(DRAFT, encoding="utf-8") as f: dl = f.read().splitlines()

FA = "s604_attribution_20261108/S604_ATTRIBUTION.md"
FB = "s604_attribution_20261108/_sa_ATTRIBUTION_S604.md"
FC = "ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md"
FD = "s604_script_gap_20261109/S604_SCRIPT_GAP.md"
FE = "s604_script_gap_20261109/_sg_FINDINGS.md"
FF = "s604_exclusive_20261109/S604_EXCLUSIVITY.md"
FG = "s604_exclusive_20261109/_ex_EXCLUSIVITY.md"
FH = "slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md"
FI = "direction_ruling_20261108/RULING_DIRECTION.md"
FJ = "direction_ruling_20261108/_dr_RULING.md"

# (标题ID, 文件, 行, 草案中引文所在行号[1-based], 引文起始特征)
P = [
 ("A1",FA,154,71), ("A2",FA,165,77), ("A3",FA,171,84), ("A4",FA,174,91),
 ("B1",FB,24,99), ("B2",FB,69,105), ("B3",FB,92,111), ("B4",FB,108,117), ("B5",FB,112,123),
 ("C1",FC,215,131), ("D1",FD,10,141), ("D2",FD,55,None), ("D3",FD,56,None), ("D4",FD,57,None),
 ("D5",FD,59,152),
 ("E1",FE,13,160), ("E2",FE,21,166), ("E3",FE,71,172),
 ("F1",FF,202,180), ("F2",FF,214,186),
 ("G1",FG,136,193), ("G2",FG,138,198),
 ("H1",FH,91,206), ("I1",FI,17,215),
 ("J1",FJ,48,223), ("J2",FJ,82,229), ("J3",FJ,147,235),
]
cache = {}
def get(fp):
    if fp not in cache: cache[fp] = open(ROOT+"/"+fp, encoding="utf-8").read().splitlines()
    return cache[fp]

print("=== 28 处「原文逐字」核对（草案引文片段 ∈ 真实 file:line）===")
n_ok=0
for tid,fp,ln,ql in P:
    real = get(fp)[ln-1] if ln <= len(get(fp)) else ""
    if ql is None:
        print("  %-4s %s:%-4d (保留/无引文块) REAL[:80]=%r" % (tid,fp.split('/')[-1],ln,real[:80]))
        n_ok += 1
        continue
    qline = dl[ql-1]
    segs = re.findall(r"`([^`]+)`", qline)
    # 取最长反引号段作为「原文逐字」
    q = max(segs, key=len) if segs else ""
    # 去掉首尾省略号
    parts = [p for p in re.split(r"…|\.\.\.", q) if len(p) >= 8]
    ok = any(p in real for p in parts) if parts else (q in real)
    if ok: n_ok += 1
    print("  %-4s %s:%-4d %s  parts=%d real_len=%d" % (tid,fp.split('/')[-1],ln,"MATCH" if ok else "MISMATCH",len(parts),len(real)))
    if not ok:
        print("      Q=%r" % q[:180])
        print("      R=%r" % real[:180])
print("引文核对 = %d/28（含 3 保留行免检）" % n_ok)

# 补：#C2 = _lad_tpl:151 与 #C1 同文
print("=== #C2 _lad_tpl:151 独立核对 ===")
tpl = get("ledger_appendix_20261108/_lad_tpl.md")[150]
led = get(FC)[214]
print("  _lad_tpl:151 == LEDGER:215 : %s" % (tpl == led))
print("  与 #C1 草案引文一致 : %s" % (max(re.findall(r"`([^`]+)`", dl[130]), key=len) in tpl))

# 三处「改」候选的引文安全：ATTRIBUTION:171 / LEDGER:215 / _lad_tpl:151 是否有第三方逐字引用
print("=== 改文候选反链（是否他件逐字引用原句）===")
import os
targets = {
 "ATTRIBUTION:171": "确切错误机理无法归属",
 "LEDGER:215": "不能定位当年错误步骤",
}
for k, phrase in targets.items():
    hits=[]
    for dp,dn,fn in os.walk(ROOT):
        for f in fn:
            if not f.endswith('.md'): continue
            p=os.path.join(dp,f)
            try: L=open(p,encoding='utf-8',errors='ignore').read().splitlines()
            except Exception: continue
            for i,l in enumerate(L):
                if phrase in l: hits.append(os.path.relpath(p,ROOT).replace(chr(92),'/')+":"+str(i+1))
    non_self=[h for h in hits if 'refsync' not in h and 'verdict_entry' not in h]
    print("  %s phrase=%r 命中 %d；剔除草案/定谳件转述后 = %d : %s" % (k,phrase,len(hits),len(non_self),non_self))
