import struct, csv, os
import pefile
from capstone import *

BASE=r"D:\Project\ra2-campaign-forge"
EXE=os.path.join(BASE,r"ra2youli\gamemd.exe")
CLS=os.path.join(BASE,r"lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv")
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    secs.append((s.Name.rstrip(b'\x00').decode('latin-1'),IB+s.VirtualAddress,s.Misc_VirtualSize,s.get_data()))
def seg(va):
    for nm,sva,vs,d in secs:
        if sva<=va<sva+vs: return nm,d,va-sva
    return None,None,None
def u32(va):
    nm,d,o=seg(va)
    if d is None or o+4>len(d): return None
    return struct.unpack_from('<I',d,o)[0]
def cstr(va,ml=200):
    nm,d,o=seg(va)
    if d is None: return None
    e=d.find(b'\x00',o,min(o+ml,len(d)))
    if e<0:return None
    try:return d[o:e].decode('ascii')
    except:return d[o:e].decode('latin-1')
def valid_col(col):
    nm,_,_=seg(col)
    if nm not in ('.rdata','.data'): return None
    td=u32(col+0xC)
    if td is None: return None
    nm2,_,_=seg(td)
    if nm2 not in ('.rdata','.data'): return None
    name=cstr(td+8)
    if not name or not(name.startswith('.?AV') or name.startswith('.?AU')):return None
    return td,name

# 1) genuine RTTI vtable slot values (walk each real vtable extent)
rtti_slot_vals=set()
vt_count=0
for nm,sva,vs,data in secs:
    if nm!='.rdata':continue
    for off in range(0,vs-4,4):
        V=sva+off
        col=u32(V-4)
        if col is None:continue
        r=valid_col(col)
        if not r:continue
        vt_count+=1
        for s in range(0,400):
            sv=u32(V+4*s)
            if sv is None:break
            snm,_,_=seg(sv)
            if snm!='.text':break
            rtti_slot_vals.add(sv)
print("genuine RTTI vtables=%d  distinct .text slot values=%d"%(vt_count,len(rtti_slot_vals)))

# 2) full E8 sweep: target -> sites
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
for nm,sva,vs,data in secs:
    if nm=='.text': tva,tvs,tdata=sva,vs,data;break
from collections import defaultdict
tgt_sites=defaultdict(list)
for ins in md.disasm(tdata,tva):
    if ins.mnemonic=='call' and len(ins.bytes)==5 and ins.bytes[0]==0xE8:
        rel=u32(ins.address+1)
        if rel is None:continue
        tgt=(ins.address+5+rel)&0xffffffff
        tgt_sites[tgt].append(ins.address)

rows=list(csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t'))
s09=[r for r in rows if r['subsystem']=='S09']
# recompute has2 (RTTI slot hit) and has4_strict direct (site outside self-computed CFG extent)
a2=set(); a4dir=set(); a4loose=set()
for r in s09:
    e=int(r['entry'],16)
    if e in rtti_slot_vals: a2.add(r['entry'])
    lo=int(r['ext_lo'],16); hi=int(r['ext_hi'],16)
    sites=tgt_sites.get(e,[])
    out=[s for s in sites if not (lo<=s<hi)]
    if out: a4dir.add(r['entry'])
    # loose adds livevt valid
    if r['has4_loose']=='1': a4loose.add(r['entry'])
A_strict=a2 & a4dir
A_loose=a2 & a4loose
print("S09 rows=%d | recompute has2=%d has4_strict_direct=%d | A_strict(2&4dir)=%d | A_loose(2&4loose)=%d"%(len(s09),len(a2),len(a4dir),len(A_strict),len(A_loose)))
# compare to classification flags
cls_A_strict=set(r['entry'] for r in s09 if r['has2_rtti']=='1' and r['has4_strict']=='1')
print("classification A_strict=%d  match=%s  diff=%s"%(len(cls_A_strict),A_strict==cls_A_strict,sorted(A_strict^cls_A_strict)[:20]))
# write recomputed A list
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED2\EVIDENCE\A_recompute.tsv",'w',encoding='utf-8') as f:
    f.write("entry\tname\thas2_rtti\thas4dir_out\thas4_loose\tin_A_strict\tin_A_loose\n")
    for r in s09:
        en=r['entry']
        f.write("%s\t%s\t%d\t%d\t%s\t%d\t%d\n"%(en,r['name'],1 if en in a2 else 0,1 if en in a4dir else 0,r['has4_loose'],1 if en in A_strict else 0,1 if en in A_loose else 0))
print("wrote EVIDENCE/A_recompute.tsv")
