# -*- coding: utf-8 -*-
"""D37-CENSUS step 1+2: S22 scale + RTTI nameability census.

Vtable boundaries are derived ONLY from .rdata (maximal runs of .text-pointer
dwords preceded by a valid COL: sig in {0,1}, COL+0xC -> TD, TD+8 = .?AV/.?AU).
function_atlas.tsv entry+size is used ONLY for the atlas in/out split of S22
rows, NEVER to bound vtables (R14_COMMON 8.1 error 7).

Target: ra2youli/gamemd.exe  SHA-256 73201CC0...F67476  READ ONLY.
"""
import os, re, sys, struct, collections
import pefile

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..','..','..'))
EXE  = os.path.join(PROJ, 'ra2youli', 'gamemd.exe')
COV  = os.path.join(PROJ, 'lead','next_re_20261117_r14','COVERAGE','coverage.tsv')
ATL  = os.path.join(PROJ, 'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
OUT  = os.path.dirname(os.path.abspath(__file__))

TAB = chr(9)
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
SZIMG = pe.OPTIONAL_HEADER.SizeOfImage

def sec(name):
    for s in pe.sections:
        if s.Name.rstrip(b'\x00').decode('latin1') == name:
            return s
    raise KeyError(name)

txt = sec('.text'); rdat = sec('.rdata')
TLO = IB + txt.VirtualAddress
THI = TLO + txt.Misc_VirtualSize
RLO = IB + rdat.VirtualAddress
RSZ = rdat.SizeOfRawData
print('IB=%08X SizeOfImage=%08X' % (IB, SZIMG))
print('.text=[%08X,%08X)  .rdata=[%08X,+%08X)' % (TLO, THI, RLO, RSZ))

# ---- raw byte reader by VA ----
blob = open(EXE,'rb').read()
def va_off(va):
    rva = va - IB
    if rva < 0 or rva >= SZIMG: return None
    for s in pe.sections:
        sv = s.VirtualAddress; vs = max(s.Misc_VirtualSize, s.SizeOfRawData)
        if sv <= rva < sv + vs:
            off = s.PointerToRawData + (rva - sv)
            if off < 0 or off >= len(blob): return None
            return off
    return None

def u32(va):
    o = va_off(va)
    if o is None or o+4 > len(blob): return None
    return struct.unpack_from('<I', blob, o)[0]

def cstr(va, cap=256):
    o = va_off(va)
    if o is None or o+cap > len(blob): return b''
    b = blob[o:o+cap]
    z = b.find(b'\x00')
    return b[:z] if z>0 else b''

def demangle(s):
    t = s.decode('latin1')
    if t.startswith('.?AV') or t.startswith('.?AU'):
        t = t[4:]
    if t.endswith('@@'):
        t = t[:-2]
    # demangled name for reporting (template ?$ -> T_; @ -> ::)
    return t.replace('?$','T_').replace('@','::')

def col_info(colp):
    """Return demangled class name if colp is a valid COL, else None."""
    if not (IB <= colp < IB + SZIMG): return None
    d = [u32(colp+4*i) for i in range(5)]
    if any(x is None for x in d): return None
    sig, off, cd, tdp, pcd = d
    if sig not in (0,1): return None
    if not (IB <= tdp < IB + SZIMG): return None
    nm = cstr(tdp+8)
    if not (nm.startswith(b'.?AV') or nm.startswith(b'.?AU')): return None
    return demangle(nm)

# ---- read .rdata as aligned dwords ----
rdata_blob = blob[rdat.PointerToRawData:rdat.PointerToRawData+RSZ]
nw = len(rdata_blob)//4
words = struct.unpack_from('<%dI' % nw, rdata_blob, 0)

def in_text(v): return TLO <= v < THI

# maximal runs of consecutive .text pointers
runs = []
i = 0
while i < nw:
    if in_text(words[i]):
        j = i
        while j < nw and in_text(words[j]):
            j += 1
        runs.append((i,j))
        i = j
    else:
        i += 1
print('slot runs (consecutive .text pointers) = %d, total slots = %d'
      % (len(runs), sum(j-i for i,j in runs)))

tables = []
for i,j in runs:
    va = RLO + 4*i
    colp = words[i-1] if i>=1 else 0
    cls = col_info(colp)
    if cls is None: continue
    tables.append(dict(vt=va, n=j-i, slots=list(words[i:j]), col=colp, cls=cls))
n_tables = len(tables)
n_slots = sum(t['n'] for t in tables)
print('SELF-ATTEST: vftables = %d, slots = %d  (baseline 1214 / 14044)' % (n_tables, n_slots))

# func_map: slot value -> list of (cls, vt, slot)
fmap = collections.defaultdict(list)
for t in tables:
    for k,S in enumerate(t['slots']):
        fmap[S].append((t['cls'], t['vt'], k))
print('distinct func slot values = %d, memberships = %d' % (len(fmap), sum(len(v) for v in fmap.values())))

# ---- read coverage.tsv ----
cov_rows = []
with open(COV, encoding='utf-8', errors='replace') as f:
    header = f.readline().rstrip('\n').split(TAB)
    for line in f:
        p = line.rstrip('\n').split(TAB)
        if len(p) < 5: continue
        cov_rows.append(dict(entry=p[0].upper(), sub=p[1], name=p[2], sem=p[3], grade=p[4]))
print('coverage data rows = %d' % len(cov_rows))

# ---- read atlas entries (set) ----
atlas = set()
with open(ATL, encoding='utf-8', errors='replace') as f:
    f.readline()
    for line in f:
        p = line.rstrip('\n').split(TAB)
        if p and p[0]: atlas.add(p[0].upper())
print('atlas entries = %d' % len(atlas))

# ---- S22 scale ----
s22 = [r for r in cov_rows if r['sub']=='S22']
print('\n=== S22 scale ===')
print('S22 total rows = %d' % len(s22))
s22_in = [r for r in s22 if r['entry'] in atlas]
s22_out = [r for r in s22 if r['entry'] not in atlas]
print('S22 in atlas = %d, outside atlas = %d' % (len(s22_in), len(s22_out)))
gc = collections.Counter(r['grade'] for r in s22)
for g in ['[已证]','[静态推断]','[未证]']:
    print('  grade %s = %d' % (g, gc.get(g,0)))
for g,n in sorted(gc.items()):
    if g not in ('[已证]','[静态推断]','[未证]'):
        print('  grade OTHER %r = %d' % (g,n))

# ---- nameability ----
nameable = 0
unnameable = 0
cls_counter = collections.Counter()
detail = []
for r in s22:
    e = int(r['entry'],16)
    mem = fmap.get(e)
    if mem:
        nameable += 1
        # distinct classes for this entry
        classes = sorted(set(m[0] for m in mem))
        slots = [(m[0], m[2]) for m in mem]
        for c in classes:
            cls_counter[c] += 1
        detail.append((r['entry'], r['grade'], 'YES', classes, slots, r['name']))
    else:
        unnameable += 1
        detail.append((r['entry'], r['grade'], 'NO', [], [], r['name']))
print('\n=== RTTI nameability ===')
print('S22 nameable = %d, unnameable = %d, ratio = %.4f%%' % (nameable, unnameable, 100.0*nameable/len(s22)))
print('Top 20 class names among nameable S22 rows:')
for c,n in cls_counter.most_common(20):
    print('  %5d  %s' % (n, c))

# ---- write intermediate JSON for step 3 ----
import json
out = dict(n_tables=n_tables, n_slots=n_slots,
           s22_total=len(s22), s22_in=len(s22_in), s22_out=len(s22_out),
           grade=dict(gc), nameable=nameable, unnameable=unnameable,
           top20=cls_counter.most_common(20),
           detail=[dict(entry=d[0],grade=d[1],nameable=d[2],classes=d[3],slots=d[4],name=d[5]) for d in detail])
with open(os.path.join(OUT,'census_raw.json'),'w',encoding='utf-8') as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
print('\nwrote census_raw.json')
