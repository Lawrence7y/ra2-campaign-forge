#!/usr/bin/env python3
# R17-R13-NAME-TABLE: read-only PE/RTTI extraction; writes only names.tsv and vtable_owner.tsv.
import hashlib, pathlib, re, struct, json
IMG = pathlib.Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
OUT = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R13_NAME_TABLE")
EXPECT = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
BASE = 0x400000
VTABLES = [0x7E3EBC,0x7E3EA0,0x7E3E98,0x7E3E90,0x7F4960,0x7F4944,0x7F493C,0x7F4934,0x7E4E78]

b = IMG.read_bytes()
sha = hashlib.sha256(b).hexdigest().upper()
assert sha == EXPECT, (IMG, sha)
e = struct.unpack_from('<I', b, 0x3c)[0]
nsec = struct.unpack_from('<H', b, e+6)[0]
optsz = struct.unpack_from('<H', b, e+20)[0]
opt = e+24
secs = {}
for i in range(nsec):
    s = opt+optsz+i*40
    name = b[s:s+8].rstrip(b'\0').decode('ascii')
    vs, va, rs, rp = struct.unpack_from('<IIII', b, s+8)
    secs[name] = (vs, va, rs, rp)
# Scan raw-backed bytes; clip .rdata at .data raw start to avoid aligned overlap.
rd = secs['.rdata']; da = secs['.data']
scan = [('.rdata', rd[1], rd[3], min(rd[2], da[3]-rd[3])),
        ('.data',  da[1], da[3], da[2])]
scan_bytes = sum(x[3] for x in scan)

def sec_of_va(va):
    rva = va-BASE
    for n,rva0,raw,ln in scan:
        if rva0 <= rva < rva0+ln: return n
    return None

def off_of_va(va):
    rva = va-BASE
    for n,rva0,raw,ln in scan:
        if rva0 <= rva < rva0+ln: return raw+(rva-rva0)
    return None

def rd32va(va):
    o = off_of_va(va)
    return None if o is None else struct.unpack_from('<I', b, o)[0]

def cstr_va(va):
    o = off_of_va(va)
    if o is None: return None
    j = b.index(0, o)
    return b[o:j].decode('ascii')

names = []
for n,rva0,raw,ln in scan:
    end = raw+ln
    i = raw
    while i < end:
        if b[i:i+2] == b'.?':
            if i == raw or b[i-1] == 0:
                j = i
                while j < end and b[j] != 0: j += 1
                s = b[i:j]
                if 4 <= len(s) <= 512 and all(0x20 <= c <= 0x7e for c in s):
                    names.append({'str':s.decode('ascii'), 'addr':BASE+rva0+(i-raw), 'sec':n, 'file':i})
            i += 2
        else:
            i += 1
names.sort(key=lambda x:x['file'])
def cat(s):
    for p in ('.?AV','.?AU','.?AW','??_7','.?A','.?'):
        if s.startswith(p): return p if p not in ('.?A','.?') else p+'-other'
    return 'other'
counts = {}
for n in names: counts[cat(n['str'])] = counts.get(cat(n['str']),0)+1
# TypeDescriptor header verification.
td_ok = sum(1 for n in names if struct.unpack_from('<II', b, n['file']-8) == (0x7F9594,0))
# Reference scan for exact names, td bases, and vtable VAs.
targets = {}
for i,n in enumerate(names):
    targets[n['addr']] = ('name',i)
    targets[(n['addr']-8)&0xffffffff] = ('td',i)
for v in VTABLES: targets[v] = ('vt',v)
refs = {k:[] for k in targets}
for n,rva0,raw,ln in scan:
    for o in range(raw, raw+ln-3):
        v = struct.unpack_from('<I', b, o)[0]
        if v in refs: refs[v].append(BASE+rva0+(o-raw))
name_refs = [refs[n['addr']] for n in names]
td_refs = [refs[(n['addr']-8)&0xffffffff] for n in names]
vt_refs = {hex(v):refs[v] for v in VTABLES}
# Stride-0x18 RTTI base-class arrays: [pTD,idx,0,FFFFFFFF,0,0], length>=4.
tdset = {(n['addr']-8)&0xffffffff for n in names}
tdname = {(n['addr']-8)&0xffffffff:n['str'] for n in names}
runs = []
for n,rva0,raw,ln in scan:
    if n != '.rdata': continue
    o = raw
    while o+24 <= raw+ln:
        if struct.unpack_from('<I',b,o)[0] in tdset and struct.unpack_from('<IIIII',b,o+4) == (0,0,0xffffffff,0,0):
            j,idx,cnt = o,0,0
            while j+24 <= raw+ln:
                a = struct.unpack_from('<I',b,j)[0]
                f = struct.unpack_from('<IIIII',b,j+4)
                if a not in tdset or f != (idx,0,0xffffffff,0,0): break
                cnt += 1; idx += 1; j += 24
            if cnt >= 4: runs.append((BASE+rva0+(o-raw),cnt,tdname[struct.unpack_from('<I',b,o)[0]],tdname[struct.unpack_from('<I',b,j-24)[0]]))
            o = j
        else: o += 4
# RTTI vtable resolution.
vt_rows = []
for v in VTABLES:
    colp = rd32va(v-4)
    row = {'vt':hex(v),'data_refs':len(vt_refs[hex(v)]),'col':hex(colp) if colp else None}
    if colp and off_of_va(colp) is not None:
        sig,off,cd,td,ch = struct.unpack_from('<IIIII',b,off_of_va(colp))
        row.update(col_fields=(sig,off,cd), td=hex(td), ch=hex(ch))
        if td and off_of_va(td) is not None:
            vf,sp = struct.unpack_from('<II',b,off_of_va(td))
            row.update(td_vf=hex(vf),td_spare=sp,name=cstr_va(td+8))
    vt_rows.append(row)
# Outputs.
with (OUT/'names.tsv').open('w',encoding='utf-8',newline='') as f:
    f.write('name\taddr\tsection\tdata_name_refs\tdata_tdbase_refs\n')
    for n,r,t in zip(names,name_refs,td_refs):
        f.write(f"{n['str']}\t0x{n['addr']:x}\t{n['sec']}\t{len(r)}\t{len(t)}\n")
with (OUT/'vtable_owner.tsv').open('w',encoding='utf-8',newline='') as f:
    f.write('vtable\tdata_va_refs\trtti_col\ttype_descriptor\tclass_name\t判定\n')
    for r in vt_rows:
        f.write(f"{r['vt']}\t{r['data_refs']}\t{r['col'] or '未取得'}\t{r.get('td','未取得')}\t{r.get('name','未取得')}\t字节证实(RTTI COL→TypeDescriptor)\n")
print(json.dumps({'image':str(IMG),'sha256':sha,'scan_bytes':scan_bytes,'counts':counts,'td_ok':td_ok,'pointer_array_runs':runs,'vtables':vt_rows},ensure_ascii=False,indent=2))
