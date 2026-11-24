"""Independent full scan for NAMED_PUSH_AUDIT18.
For each entry: find vtable slot(s) in .rdata by scanning u32==entry, parse RTTI,
disassemble body, scan .text for install points (imm32 == vt base).
Writes detailed dump to scan_all.txt.
"""
import sys
from re_lib import *

ENTRIES = [0x006E3E30,0x006E57A0,0x006E6470,0x0071F930,0x0071FA80,
           0x00726860,0x007268D0,0x00726950,0x00727BF0,0x00727C80]

def find_rdata_refs(entry):
    """All VA in .rdata (and whole image) where u32 == entry."""
    hits=[]
    r0=None;r1=None
    for name,v0,v1,rva,vsz,raw,rsz in SECS:
        if name=='.rdata':
            r0,r1=v0,v1
    va=r0
    while va+4<=r1:
        if u32(va)==entry:
            hits.append(va)
        va+=4
    return hits

def try_vt_base(slot_va, maxback=24):
    """Walk back from slot_va trying candidate vt bases; validate via RTTI."""
    cands=[]
    for k in range(0,maxback+1):
        vt=slot_va-4*k
        if not mapped(vt-4,4): continue
        col=u32(vt-4)
        if not mapped(col,20): continue
        sig=u32(col)
        if sig!=0: continue
        ptd=u32(col+0xC)
        if not mapped(ptd,12): continue
        magic=bytes_at(ptd+8,4)
        if magic[:3]!=b'.?A': continue
        cands.append((vt,k,cstr(ptd+8)))
    return cands

def find_installs(vt):
    """Scan .text for instructions whose immediate operand == vt (install points)."""
    res=[]
    # byte scan for little-endian imm32 of vt anywhere in .text
    pat = vt.to_bytes(4,'little')
    data = bytes_at(TEXT_VA, TEXT_END-TEXT_VA)
    start=0
    while True:
        i = data.find(pat, start)
        if i<0: break
        va = TEXT_VA+i
        res.append(va)
        start=i+1
    return res

def classify_install_site(va, vt):
    """Disassemble a window around va to identify the instruction + host context."""
    base = max(TEXT_VA, va-40)
    win = disasm(base, 120)
    target=None
    for a,m,o,b,t in win:
        if a==va:
            target=(m,o,b.hex(),t)
    # find context: previous call to base ctor + install instruction form
    return win, target

out=[]
def P(s=''):
    out.append(str(s)); print(s)

P('=== NAMED_PUSH_AUDIT18 INDEPENDENT SCAN ===')
P('IMAGE_BASE=%08X .text=[%08X,%08X)'%(IMAGE_BASE,TEXT_VA,TEXT_END))
P()

for e in ENTRIES:
    P('#'*80)
    P('ENTRY %08X'%e)
    refs=find_rdata_refs(e)
    P('  .rdata refs where u32==entry: %s'%(' '.join('%08X'%x for x in refs) if refs else 'NONE'))
    vts={}
    for r in refs:
        cands=try_vt_base(r)
        P('    slot_va %08X candidate vt bases: %s'%(r, '; '.join('vt=%08X slot#%d %s'%(vt,k,nm) for vt,k,nm in cands) if cands else 'NONE'))
        for vt,k,nm in cands:
            vts[vt]=(k,nm)
    # body disasm 320 bytes
    P('  BODY (from entry, 320 bytes, capstone skipdata=True):')
    for a,m,o,b,t in disasm(e,320):
        P('    '+t)
        if m.startswith('ret'): break
    # installs for each vt
    for vt,(k,nm) in vts.items():
        ins=find_installs(vt)
        P('  INSTALL sites for vt=%08X (%s): %s'%(vt,nm, ' '.join('%08X'%x for x in ins) if ins else 'NONE'))
    P()

open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT18\work\scan_all.txt','w',encoding='utf-8').write('\n'.join(out))
print('WROTE scan_all.txt')
