#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify 0x431B80 destructor evidence: IAT symbol for free, callers, base dtor class."""
import sys, struct
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P

out=[]
# 1. IAT name for 0x7C8B3D
for t in (0x7C8B3D, 0x65CA00):
    out.append(f"IAT {t:08X} = {P.iat_name(t)}")

# 2. callers of 0x431B80 via scan_rel32_calls
callers = P.scan_rel32_calls(0x431B80)
out.append(f"\nDirect E8 callers of 0x431B80: {len(callers)}")
for site, op in callers:
    out.append(f"  call site {site:08X} (op {op:02X})")

# 3. Is 0x65CA00 a destructor? find its vtable slot / class name by scanning
#    (reuse rtti logic minimal)
sections=P.sections(); rdata=[s for s in sections if s[0]=='.rdata'][0]
_,rdva,rdvs,praw,rawsz,_=rdata; text=[s for s in sections if s[0]=='.text'][0]
txt_lo,txt_hi=text[1],text[1]+text[4]
with open(P.EXE,'rb') as f: f.seek(praw); rd=f.read(rawsz)
def cstr(va,maxn=120):
    off=P.va2off(va)
    if off is None:return None
    with open(P.EXE,'rb') as f:f.seek(off);b=f.read(maxn)
    z=b.find(b'\x00');return b[:z if z>=0 else maxn]
vbclass={}
for i in range(0,len(rd)-4,4):
    p=struct.unpack_from('<I',rd,i)[0]
    if not(rdva<=p<rdva+rdvs):continue
    if P.u32(p)!=0:continue
    td=P.u32(p+0xC)
    if td is None:continue
    nm=cstr(td+8)
    if nm and nm.startswith(b'.?AV') and b'@@' in nm:
        vbclass[rdva+i+4]=nm.decode('latin1','replace')
def slots(f):
    r=[]
    for vb,cls in vbclass.items():
        for k in range(0,600):
            sv=P.u32(vb+4*k)
            if sv is None or not(txt_lo<=sv<txt_hi):break
            if sv==f:r.append((vb,cls,k));break
    return r
out.append(f"\n0x65CA00 vtable slots: {slots(0x65CA00)}")

# 4. disassemble the deleting-dtor thunks (callers) to confirm they call 0x431B80
for site,op in callers:
    # find enclosing function via atlas
    pass
out.append("\n=== caller context (disasm +-16 around call site) ===")
for site,op in callers:
    b=P.read(site-16,48)
    if b is None:continue
    from capstone import Cs,CS_ARCH_X86,CS_MODE_32
    md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
    out.append(f"-- around {site:08X} --")
    for ins in md.disasm(b,site-16):
        out.append(f"  {ins.address:08X}: {ins.bytes.hex():<16s} {ins.mnemonic} {ins.op_str}")

txt="\n".join(out)+"\n"
import io,os
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K3"
with io.open(os.path.join(CARD,"EVIDENCE","dtor_431B80_evidence.txt"),"w",encoding="utf-8") as f:f.write(txt)
sys.stdout.write(txt)
