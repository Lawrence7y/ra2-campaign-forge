"""Diagnose RTTI COL/slot discrepancy vs audit baseline 1214 tables / 14044 slots."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin
from collections import Counter

b = Bin()
RLO, RHI = b.sec_range(".rdata")
TLO, THI = b.sec_range(".text")
DLO, DHI = b.sec_range(".data")
rdata = b.section_bytes(".rdata")

# broad COLs: sig=0, td in .data, chd in .rdata (relax name filter + obj/cd offset cap)
broad = []
for off in range(0, len(rdata)-0x14, 4):
    sig = struct.unpack_from("<I", rdata, off)[0]
    if sig != 0: continue
    td = struct.unpack_from("<I", rdata, off+0xC)[0]
    if not (DLO <= td < DHI): continue
    chd = struct.unpack_from("<I", rdata, off+0x10)[0]
    if not (RLO <= chd < RHI): continue
    broad.append((RLO+off, td, chd))
print("broad COL candidates:", len(broad))

prefixes = Counter()
for _, td, _ in broad:
    try: nm = b.read(td+8, 6)
    except Exception: nm = b'?'
    prefixes[nm[:4]] += 1
print("TD name prefixes:", prefixes.most_common(12))

broadcol = set(c for c,_,_ in broad)
vt_broad=[]
for off in range(0, len(rdata)-4,4):
    v=struct.unpack_from("<I",rdata,off)[0]
    if v in broadcol:
        vt_broad.append((RLO+off+4, v, RLO+off))
print("vtables from broad COLs:", len(vt_broad))

def slot_count(vt):
    cnt=0; a=vt
    while True:
        try: v=b.u32(a)
        except Exception: break
        if TLO<=v<THI: cnt+=1; a+=4
        else: break
    return cnt,a
tot=sum(slot_count(v)[0] for v,_,_ in vt_broad)
print("total slots (broad):", tot)

print("\nSample: tables whose end dword nonzero but outside .text:")
shown=0
for vt,col,loc in vt_broad:
    c,end=slot_count(vt)
    v=b.u32(end)
    if v!=0 and not (TLO<=v<THI) and shown<25:
        print(" vt=%08X col=%08X slots=%d end=%08X endval=%08X sec=%s" %
              (vt,col,c,end,v, (b.sec_of(v) or {}).get('name','?')))
        shown+=1

cnt=Counter(slot_count(v)[0] for v,_,_ in vt_broad)
print("\nslot-count distribution (top):", cnt.most_common(20))
