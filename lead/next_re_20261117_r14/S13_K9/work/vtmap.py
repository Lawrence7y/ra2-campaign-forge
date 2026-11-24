# Build vtable map: for each vtable base (aligned window of 8 slots in .rdata), what entries at what slots
import sys,struct,json
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\work')
from common import *
ENTRIES={0x40B880:'11a',0x40B930:'11a',0x40F7C0:'11a',0x40FD90:'11a',0x40FE40:'11a',0x46B7E0:'11a',0x46B890:'11a',0x62B250:'11a',0x62B300:'11a',0x65C0D0:'11a',0x65C180:'11a',0x48AD60:'miss6',0x54E8E0:'miss6',0x48AD70:'miss1'}
# find all positions in .rdata where dword == entry
vtmap={}
for e in ENTRIES:
    refs=[]
    pat=struct.pack('<I',e)
    for n,v,vs,pr,rs in SECS:
        if n!='.rdata': continue
        start=pr; end=pr+min(vs,rs)
        i=DATA.find(pat,start,end)
        while i!=-1:
            va=IB+v+(i-pr)
            refs.append(va)
            i=DATA.find(pat,i+1,end)
    vtmap[e]=refs
    print(hex(e),ENTRIES[e],'refs',[hex(x) for x in refs])
# Determine vtable base for each ref: scan backwards while previous dword is .text, up to 8 slots; forward 8 slots
def vtable_at(slotaddr):
    # walk back to start: a vtable is contiguous .text slots 0..6 then data at slot7
    a=slotaddr
    while a-4>=0x7e1000:
        p=u32(a-4)
        if p and sec_of(p)=='.text': a-=4
        else: break
    return a
for e,refs in vtmap.items():
    for r in refs:
        base=vtable_at(r)
        slot=(r-base)//4
        # dump 8 slots
        slots=[u32(base+4*i) for i in range(8)]
        print('  entry',hex(e),'slotaddr',hex(r),'vtable_base',hex(base),'slot',slot,'slots',[hex(x) if x else None for x in slots])
json.dump({hex(e):[hex(x) for x in r] for e,r in vtmap.items()},open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\EVIDENCE\vtmap.json','w'),indent=1)
