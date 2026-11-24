"""
S11-K2 T1: RTTI enumeration of LocomotionClass family, with:
  - class name via CORRECT chain COL+0xC -> TD+8 (fail-closed if unreadable)
  - TD / COL / vtable base / slot count (delimited from .rdata, not atlas)
  - parent class from CHD (ClassHierarchyDescriptor -> BaseClassArray)
Byte-level channel; independent of function_atlas.tsv.
"""
import re, json
from pehelp import (IMAGE_BASE, rd, u32, sections, section_of, in_section, is_code)

OUT = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S11-K2\EVIDENCE\t1_rtti_enum.txt'
lines=[]
def P(s=''):
    lines.append(str(s)); print(s)

SEC_RANGES=[]
for nm,vaoff,vsize,rsize,praw in sections():
    SEC_RANGES.append((nm, IMAGE_BASE+vaoff, IMAGE_BASE+vaoff+max(vsize,rsize)))

def read_name_at(va, maxb=128):
    b = rd(va, maxb)
    z = b.find(b'\x00')
    if z < 0: return None
    try: return b[:z].decode('latin1')
    except: return None

# ---------- step 1: TD via name pattern ----------
pat = re.compile(rb'\.\?A[UV][A-Za-z0-9_]*LocomotionClass@@\x00')
td_by_name={}
for nm,lo,hi in SEC_RANGES:
    blob=rd(lo,hi-lo)
    for m in pat.finditer(blob):
        name_va=lo+m.start()
        td=name_va-8
        td_by_name.setdefault(td, read_name_at(td+8))
P('=== STEP1: TD candidates by name pattern .?AV*LocomotionClass@@ ===')
for td,name in sorted(td_by_name.items()):
    try: v=u32(td); spare=u32(td+4)
    except: continue
    P('TD %08X name=%-44s vft=%08X spare=%d %s' % (td,name,v,spare,'OK' if (in_section(v,'.rdata') and spare==0) else 'BAD'))

# validate TD
valid_td={}
for td,name in td_by_name.items():
    try: v=u32(td); spare=u32(td+4)
    except: continue
    if in_section(v,'.rdata') and spare==0 and name and 'LocomotionClass' in name:
        valid_td[td]=name
P('valid TDs = %d' % len(valid_td))

# ---------- step 2: COL via references to TD (COL+0xC -> TD) ----------
td_set=set(valid_td)
cols=[]  # (col, td, off, cdOffset, chd)
for nm,lo,hi in SEC_RANGES:
    for va in range(lo,hi-4+1,4):
        try: v=u32(va)
        except: continue
        if v in td_set:
            col=va-0xC
            try:
                sig=u32(col); off=u32(col+4); cdoff=u32(col+8)
                chktd=u32(col+0xC); chd=u32(col+0x10)
            except: continue
            if sig==0 and chktd==v and in_section(chd,'.rdata'):
                cols.append((col,v,off,cdoff,chd))
P('\n=== STEP2: COLs (sig=0, COL+0xC->TD, CHD in .rdata) ===')
for col,td,off,cdoff,chd in sorted(cols):
    P('COL %08X off=%-3d cdoff=%-3d TD=%08X %-44s CHD=%08X' % (col,off,cdoff,td,valid_td[td],chd))

# ---------- step 3: CHD -> parent ----------
def chd_parents(chd):
    """Return list of base TD names from CHD base-class array."""
    try:
        sig=u32(chd); attr=u32(chd+4); nbase=u32(chd+8); bca=u32(chd+0xC)
    except: return (None,None,[])
    if not in_section(bca,'.rdata') or nbase==0 or nbase>64:
        return (sig,attr,[])
    names=[]
    for i in range(nbase):
        bcd=u32(bca+4*i)
        if not in_section(bcd,'.rdata'): names.append('?@%08X'%bcd); continue
        btd=u32(bcd)
        # TypeDescriptors live in .data (0x820xxx) or .rdata — accept both
        nm = read_name_at(btd+8) if (in_section(btd,'.rdata') or in_section(btd,'.data')) else None
        nm=nm or ('?@%08X'%btd)
        names.append(nm)
    return (sig,attr,names)

P('\n=== STEP3: CHD parent chains ===')
col_chd={c[0]:c[4] for c in cols}
chd_cache={}
for col,td,off,cdoff,chd in sorted(cols):
    if chd not in chd_cache: chd_cache[chd]=chd_parents(chd)
    sig,attr,names=chd_cache[chd]
    P('COL %08X %-44s CHD %08X sig=%d attr=%d bases=%s' % (col,valid_td[td],chd,sig,attr,names))

# ---------- step 4: vtable via references to COL (ref = vtable-4, i.e. vtable[-1]=COL) ----------
col_set={c[0] for c in cols}
col_info={c[0]:c for c in cols}
vts=[]  # (vt, col, td, off, name)
for nm,lo,hi in SEC_RANGES:
    for va in range(lo,hi-4+1,4):
        try: v=u32(va)
        except: continue
        if v in col_set:
            vt=va+4
            # real vtables are in .rdata and slot0 is a .text code pointer
            if section_of(vt) != '.rdata':
                continue
            try:
                if not is_code(u32(vt)):
                    continue
            except:
                continue
            col,td,off,cdoff,chd=col_info[v]
            vts.append((vt,v,td,off,valid_td[td]))
P('\n=== STEP4: vtables (vtable[-1]=COL) ===')
for vt,col,td,off,name in sorted(vts):
    slot0=u32(vt) if True else 0
    P('VT %08X col=%08X off=%-3d TD=%08X %-44s slot0=%08X %s' % (vt,col,off,td,name,slot0,'CODE' if is_code(slot0) else 'noncode'))

# ---------- step 5: slot count from .rdata delimiting ----------
# A vtable is a run of consecutive .text code pointers; stop when next dword is not code,
# or equals a COL / known separator. We do NOT apply 16B alignment filter (would kill 6-byte GetSize).
SEP={0x00004E40,0x399D52A2,0x469D913F}
def count_slots(vt,maxn=200):
    n=0
    for i in range(maxn):
        a=vt+4*i
        if section_of(a)!='.rdata': break
        try: v=u32(a)
        except: break
        if v in col_set or v in SEP or not is_code(v): break
        n+=1
    return n

P('\n=== STEP5: per-class RTTI/vtable summary ===')
summary={}
for vt,col,td,off,name in sorted(vts):
    n=count_slots(vt)
    end=vt+4*n
    # what is at end (delimiter)?
    try: delim=u32(end) if section_of(end)=='.rdata' else None
    except: delim=None
    dtxt=('COL' if delim in col_set else ('SEP' if delim in SEP else ('noncode' if delim is not None and not is_code(delim) else hex(delim) if delim is not None else '?')))
    P('%-44s off=%-3d VT=%08X col=%08X TD=%08X slots=%-3d end=%08X delim=%s' % (name,off,vt,col,td,n,end,dtxt))
    summary.setdefault(name,[]).append(dict(vt=vt,col=col,td=td,off=off,slots=n,end=end))

P('\nCLASS COUNT = %d' % len(summary))

# JSON for downstream
outobj=dict(classes=summary,
            col_list=[dict(col=c[0],td=c[1],off=c[2],cdoff=c[3],chd=c[4],name=valid_td[c[1]]) for c in cols],
            chd_parents={('%08X'%col):chd_parents(c[4]) for col,c in [(x[0],x) for x in cols]})
with open(OUT,'w',encoding='utf-8') as f:
    f.write('\n'.join(lines)+'\n')
with open(OUT.replace('.txt','.json'),'w',encoding='utf-8') as f:
    json.dump(outobj,f,indent=1,ensure_ascii=False)
print('\nWROTE',OUT)
