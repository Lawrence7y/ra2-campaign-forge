# -*- coding: utf-8 -*-
"""S02-K2 / T2: project-wide text scan. For every 6-8 hex digit address that equals an
UNNAMED S02 target, report the file:line and nearby text. Finds any symbol table / source
reference that names these functions (external evidence, not shape matching)."""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C

ROOT = C.ROOT
targets = C.load_targets()
unnamed = {r["entry"] for r in targets if r["named_L"]=="0"}
named = {r["entry"] for r in targets if r["named_L"]=="1"}
# also interesting off-target CRT addresses
extra = {"007C8B48","007C8E25","007CB302","007C5F00","007769D4","007C89D4"}

HEX_RE = re.compile(r'(?<![0-9A-Fa-f])(0[xX])?([0-9A-Fa-f]{6,8})(?![0-9A-Fa-f])')

# dirs to skip (huge/binary/noise)
SKIP_DIRS = {'.git','node_modules','__pycache__','_ghidra','.mimosa','out'}
EXTS = {'.h','.hpp','.cpp','.inl','.c','.md','.txt','.tsv','.json','.py','.log','.inc','.asm'}

hits = {a: [] for a in unnamed | extra}
filecount = 0
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for fn in files:
        ext = os.path.splitext(fn)[1].lower()
        if ext not in EXTS: continue
        path = os.path.join(root, fn)
        try:
            sz = os.path.getsize(path)
            if sz > 4_000_000: continue
            lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
        except Exception:
            continue
        filecount += 1
        for i, line in enumerate(lines):
            for m in HEX_RE.finditer(line):
                raw = m.group(2).upper()
                a = raw.zfill(8)
                key = None
                if a in hits: key = a
                elif len(raw)==6 and ('00'+raw) in hits: key='00'+raw
                if key is None: continue
                ctx = line.strip()[:200]
                hits[key].append((os.path.relpath(path,ROOT), i+1, ctx))

print("scanned files:", filecount, "target addrs:", len(hits))
found = 0
for a in sorted(hits):
    if not hits[a]: continue
    found += 1
    # dedupe (file,line)
    seen=set(); uniq=[]
    for h in hits[a]:
        k=(h[0],h[1])
        if k in seen: continue
        seen.add(k); uniq.append(h)
    print("\n0x%s  (%d refs):" % (a, len(uniq)))
    for h in uniq[:6]:
        print("   %s:%d  %s" % h)
print("\naddresses with >=1 text ref:", found)
with open(os.path.join(C.CARD,"work","textref_hits.json"),"w",encoding="utf-8") as f:
    json.dump({a:hits[a] for a in hits if hits[a]},f,ensure_ascii=False,indent=1)
