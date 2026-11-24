"""_rsv_diffset.py — step 5: independently verify the 13-file difference-set claim.
The 13 files are taken from S604_REFSYNC_FULL.md:42-54 (read verbatim this session).
Run: python -I -X utf8 ".../_rsv_diffset.py"
"""
import os, re
from collections import defaultdict
ROOT = r"D:/Project/ra2-campaign-forge/lead"
NEEDLES = ["只能判「不可复现」", "不能定位当年错误步骤"]

# 13 files, transcribed from S604_REFSYNC_FULL.md:42-54 (column "件")
THIRTEEN = {
"slowframe_r3_20261108/S604_GAP_RECHECK.md",
"s604_attribution_20261108/S604_ATTRIBUTION.md",
"s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
"ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md",
"ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
"ledger_appendix_20261108/_lad_tpl.md",
"s604_script_gap_20261109/S604_SCRIPT_GAP.md",
"s604_script_gap_20261109/_sg_FINDINGS.md",
"s604_exclusive_20261109/S604_EXCLUSIVITY.md",
"s604_exclusive_20261109/_ex_EXCLUSIVITY.md",
"slowwindow_n8_20261108/SLOW_WINDOW_LIMITS.md",
"direction_ruling_20261108/RULING_DIRECTION.md",
"direction_ruling_20261108/_dr_RULING.md",
}
WD = "refsync_scope_20261109/"

def carriers():
    out={}
    for dp,dn,fn in os.walk(ROOT):
        rel=os.path.relpath(dp,ROOT).replace("\\","/")
        d=0 if rel=="." else rel.count("/")+1
        if d>2: continue
        for f in fn:
            if not f.lower().endswith(".md"): continue
            p=os.path.join(dp,f); r=os.path.relpath(p,ROOT).replace("\\","/")
            if r.startswith(WD): continue     # author's own outputs, created after scan
            b=open(p,'rb').read(); ls=b.decode('utf-8','replace').splitlines()
            ln=[i for i,L in enumerate(ls,1) if any(n in L for n in NEEDLES)]
            if ln: out[r]=ln
    return out

C = carriers()
print("=== independent d2 carrier set ===")
print(f"  carrier files={len(C)} hit lines={sum(len(v) for v in C.values())}")
inter = sorted(set(C) & THIRTEEN)
only13 = sorted(THIRTEEN - set(C))
diff = sorted(set(C) - THIRTEEN)
print(f"\n13 ∩ carriers = {len(inter)} files:")
for x in inter: print("   ", x)
print(f"\n13-only (carrier not, i.e. outdated point is another phrase) = {len(only13)} files:")
for x in only13: print("   ", x)
print(f"\ncarriers − 13 = {len(diff)} files (claimed '12 漏掉载体'):")
for x in diff: print("   ", x, C[x])

print("\n=== per-item 'REALLY ENTERS LEDGER' audit (independent block detection) ===")
START = re.compile(r"^\s*(?:<!--[^>]*草案正文[^>]*逐字转录开始[^>]*-->|#{1,6}\s*↓{2,}[^\n]*草案正文[^\n]*|↓{3,}\s*草案正文\s*↓{3,})\s*$")
END   = re.compile(r"^\s*(?:<!--[^>]*草案正文[^>]*逐字转录结束[^>]*-->|#{1,6}\s*↑{2,}[^\n]*草案正文[^\n]*|↑{3,}\s*草案正文[^\n]*↑{3,})\s*$")
def blocks(rel):
    L=open(os.path.join(ROOT,rel),'r',encoding='utf-8',newline='').read().splitlines()
    st=[]; pr=[]
    for i,x in enumerate(L,1):
        if START.match(x): st.append(i)
        elif END.match(x) and st: pr.append((st.pop(),i))
    return L,pr
for rel in diff:
    L,pr=blocks(rel)
    inside_all=[n for n in C[rel] if any(s<n<e for s,e in pr)]
    print(f"  {rel}")
    print(f"     blocks={pr}  needle_lines={C[rel]}  IN_BLOCK={inside_all}")
    for n in C[rel]:
        txt=L[n-1]
        print(f"       :{n} {'[IN-BLOCK]' if any(s<n<e for s,e in pr) else '[OUT-OF-BLOCK]'} {txt[:150]}")
