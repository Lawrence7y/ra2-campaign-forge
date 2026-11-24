#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C09 探索：本片 slice 的类/字符串/导入/已知名概览（只读，帮助设计分类规则）。"""
import os, re, json, glob
from collections import Counter, defaultdict

ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, "lead\\next_re_20261112_r10\\W130_atlas")
WORK  = os.path.join(ROOT, "lead\\next_re_20261117_r14\\C09_census\\work")

fa = os.path.join(ATLAS, "function_atlas.tsv")
lines = open(fa, encoding="utf-8", errors="replace").read().splitlines()
hdr = lines[0].split("\t")
data = [ln for ln in lines[1:] if ln.strip()]
slicef = data[10336:11628]
def parse(ln):
    p = ln.split("\t"); r = dict(zip(hdr, p))
    return dict(entry=int(r["entry"],16), size=int(r["size"]),
                first_import=r.get("first_import",""), strings=r.get("strings",""))
F = [parse(ln) for ln in slicef]
lo = min(f["entry"] for f in F); hi = max(f["entry"]+f["size"] for f in F)
print("slice n=%d  range %08X..%08X" % (len(F), lo, hi))

# vtables_v2 slots -> 类（探索用，正式槽数走独立 RTTI）
v2 = json.load(open(os.path.join(ATLAS,"vtables_v2.json"), encoding="utf-8"))["vtables"]
vt_by_tgt = defaultdict(list)
for v in v2:
    c = v.get("class") or v.get("cls") or v.get("name") or "?"
    for i in range(int(v.get("slots",0))):
        sl = v.get("slots_list") or v.get("funcs") or []
        if i < len(sl):
            try: vt_by_tgt[int(sl[i],16) if isinstance(sl[i],str) else int(sl[i])].append((c,i,v.get("vt")))
            except Exception: pass
# print keys sample
print("v2 sample keys:", list(v2[0].keys()) if v2 else None)

# known names
known = defaultdict(set)
KW_SKIP={"if","while","for","switch","return","sizeof"}
for h in glob.glob(os.path.join(ROOT,"YRpp","**","*.h"), recursive=True):
    cls=os.path.basename(h)[:-2]; txt=open(h,encoding="utf-8",errors="replace").read(); hl=txt.splitlines()
    for li,line in enumerate(hl):
        for m in re.finditer(r'JMP_(?:THIS|STD)\((0x[0-9A-Fa-f]+)\)', line):
            addr=int(m.group(1),16)
            ids=[x for x in re.findall(r'\b([A-Za-z_]\w*)\s*\(', " ".join(hl[max(0,li-1):li+1])) if x not in KW_SKIP]
            meth=ids[-1] if ids else cls
            known[addr].add(f"{cls}::{meth}")
for md in glob.glob(os.path.join(ROOT,"re_atlas","kb","*.md")):
    txt=open(md,encoding="utf-8",errors="replace").read()
    for m in re.finditer(r'`0x([0-9A-Fa-f]{6,8})`[^\n`]{0,90}`([A-Za-z_][\w:]*(?:::\w+)?)`', txt):
        known[int(m.group(1),16)].add(m.group(2))

# imports distribution
imps = Counter(f["first_import"] for f in F if f["first_import"])
print("\n== imports in slice ==")
for k,n in imps.most_common(40): print("  %3d %s" % (n,k))

# strings with .CPP
cpp = Counter()
for f in F:
    for m in re.findall(r'[A-Za-z0-9_]+\.CPP', f["strings"], re.I):
        cpp[m]+=1
print("\n== .CPP strings in slice ==")
for k,n in cpp.most_common(40): print("  %3d %s"%(n,k))

# known names in slice
print("\n== self known names in slice (count=%d) ==" % sum(1 for f in F if known.get(f["entry"])))
for f in F:
    kn=known.get(f["entry"])
    if kn: print("  %08X %s"%(f["entry"],"|".join(sorted(kn))))

# vtable classes in slice (from v2)
cls_count = Counter()
for f in F:
    for c,i,vt in vt_by_tgt.get(f["entry"],[]): cls_count[c]+=1
print("\n== vtable classes in slice (v2, exploration only) ==")
for c,n in cls_count.most_common(80): print("  %3d %s"%(n,c))
