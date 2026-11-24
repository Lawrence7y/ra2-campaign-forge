import struct, sys, re
import pefile
from capstone import *
from capstone.x86 import *

PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs.append((nm, IB+s.VirtualAddress, s.Misc_VirtualSize, s.get_data()))

def seg(va):
    for nm,sva,vs,data in secs:
        if sva<=va<sva+vs: return nm,data,va-sva
    return None,None,None
def u32(va):
    nm,d,o=seg(va)
    if d is None or o+4>len(d): return None
    return struct.unpack_from('<I',d,o)[0]
def u8(va):
    nm,d,o=seg(va)
    if d is None or o>=len(d): return None
    return d[o]

md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True

# full .text E8-at-boundary sweep
for nm,sva,vs,data in secs:
    if nm=='.text':
        tva,tvs,tdata=sva,vs,data; break
boundary_E8=set()
nins=0
for ins in md.disasm(tdata, tva):
    nins+=1
    if ins.mnemonic=='call' and ins.bytes and ins.bytes[0]==0xE8 and len(ins.bytes)==5:
        boundary_E8.add(ins.address)
print("TEXT [%08X,%08X) insns=%d E8@boundary=%d" % (tva,tva+tvs,nins,len(boundary_E8)))

# candidates: entry, ext_lo, ext_hi, sites(from classification, for cross-check only)
cands=[
 ('006A5840','006A5840','006A5BE8',['006D02BB']),
 ('006D0680','006D0680','006D09B6',['006922F4']),
 ('0063FB20','0063FB20','0063FDB8',['006A6FFC']),
 ('005BE6D0','005BE6D0','005BE935',['0067D3B1']),
 ('004E2690','004E2690','004E2830',['004E2B5E','006B214F']),
 ('00654320','00654320','0065448C',['006403A3']),
 ('0069DEB0','0069DEB0','0069DFB6',['006531CB','006531D6','00653501','0065350C','006A6E88','006A6E93']),
 ('00557730','00557730','005577F4',['004882F0','004883CF','004886C5','00488700','0048894E']),
]

# build reverse map: target->sites (full sweep, all E8 at boundary, non-self handled below)
from collections import defaultdict
target_sites=defaultdict(list)
for site in boundary_E8:
    rel=u32(site+1)
    if rel is None: continue
    tgt=(site+5+rel)&0xffffffff
    target_sites[tgt].append(site)

for ent_s,lo_s,hi_s,sites in cands:
    ent=int(ent_s,16); lo=int(lo_s,16); hi=int(hi_s,16)
    all_tgt_sites=sorted(target_sites.get(ent,[]))
    print("=== %s entry=%08X body=[%08X,%08X) all_E8_target_sites=%d" % (ent_s,ent,lo,hi,len(all_tgt_sites)))
    for site in all_tgt_sites:
        b=u8(site); rel=u32(site+1); calc=(site+5+rel)&0xffffffff
        in_body = lo<=site<hi
        selfloop = in_body  # site inside its own body
        print("  site=%08X byte=%02X rel=%08X calc=%08X match=%s in_body=%s selfloop=%s" % (
            site,b,rel,calc,calc==ent,in_body,selfloop))
    # cross-check against classification sites
    miss=[s for s in sites if int(s,16) not in all_tgt_sites]
    if miss: print("  CLASSIFICATION SITES NOT FOUND AT E8 BOUNDARY:",miss)
