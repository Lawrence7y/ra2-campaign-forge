# -*- coding: utf-8 -*-
"""Classify the 11 direct bit0-clearing [reg+0x14] writes.
Use FUNCTION INTERVAL CONTAINMENT (prologue..ret), not entry_at_or_before.
For each site: dump containing function, this-source chain, callers, RTTI via vtable slot (fail-closed).
"""
import pefile, struct, bisect
from capstone import *
from capstone.x86 import *
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(EXE,"rb").read()
pe = pefile.PE(EXE, fast_load=True); BASE=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b"\x00").decode("latin1")
    secs.append(dict(name=nm,va=BASE+s.VirtualAddress,vsize=s.Misc_VirtualSize,raw=s.PointerToRawData,rawsize=s.SizeOfRawData))
def sec_of(va):
    for s in secs:
        if s["va"]<=va<s["va"]+max(s["vsize"],s["rawsize"]): return s
def rd(va,n):
    s=sec_of(va)
    if s is None: return b""
    o=s["raw"]+(va-s["va"]); return data[o:o+n]
def u32(va):
    b=rd(va,4); return struct.unpack("<I",b)[0] if len(b)==4 else None
TEXT=[s for s in secs if s["name"]==".text"][0]; T0,T1=TEXT["va"],TEXT["va"]+TEXT["rawsize"]; TRAW=TEXT["raw"]
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
def disasm(start,end):
    out=[]; va=start
    while va<end:
        got=list(md.disasm(rd(va,16),va,count=1))
        if not got: out.append((va,1,"?","")); va+=1; continue
        i=got[0]; out.append((i.address,i.size,i.mnemonic,i.op_str)); va+=i.size
    return out

# ALL E8 call targets in .text (for caller finding) - raw byte scan, no atlas
callers={}
for va in range(T0,T1-4):
    if data[TRAW+(va-T0)]==0xE8:
        rel=int.from_bytes(data[TRAW+(va+1-T0):TRAW+(va+5-T0)],"little",signed=True)
        t=(va+5+rel)&0xFFFFFFFF
        if T0<=t<T1: callers.setdefault(t,[]).append(va)

# RTTI: find function addr as aligned dword in any section -> vtable -> COL -> TD -> name
def rtti_of_fn(fa):
    results=[]
    for s in secs:
        if s["name"]==".text": continue
        raw=open(EXE,"rb").read()
        # scan aligned dwords in section raw
        for off in range(0, s["rawsize"]-3, 4):
            v=struct.unpack_from("<I",raw,s["raw"]+off)[0]
            if v==fa:
                slotva=s["va"]+off
                # vtable base: scan backward for entry 0 or non-code; report slotva
                results.append(('slot',slotva))
    names=[]
    for kind,slotva in results:
        # find COL: dword in rdata/data whose value points into vtable region; approximate: scan for value in [slotva-0x100,slotva+0x100]
        for s in secs:
            if s["name"]==".text": continue
            raw=open(EXE,"rb").read()
            for off in range(0,s["rawsize"]-3,4):
                v=struct.unpack_from("<I",raw,s["raw"]+off)[0]
                if s["va"]<=v<s["va"]+s["rawsize"] and abs(v-slotva)<0x200:
                    colva=s["va"]+off
                    td=u32(colva+0xC)
                    if td and sec_of(td):
                        name_va=td+8
                        b=rd(name_va,80); z=b.find(b"\x00")
                        nm=b[:z].decode("latin1") if z!=-1 else b.decode("latin1")
                        if nm.startswith('.?AV'):
                            names.append((hex(colva),hex(td),nm))
    return results,names[:6]

# The 11 sites (from t3_u3_bit0_counts.txt imm bit0==0)
SITES=[0x4CCA64,0x5C0247,0x5C0920,0x76AB55,0x77A74D,0x7B23F4,0x7CD0C0,0x7CD0C9,0x7CD0F7,0x7CD12D,0x7CD1B8]
for sa in SITES:
    print("\n"+"="*80)
    print("SITE %08X" % sa)
    # find function interval: walk back to a likely prologue and forward to ret
    ins=disasm(sa-0x100,sa+0x120)
    # find ret after site
    end=None
    for a,sz,mn,op in ins:
        if a>sa and mn=='ret': end=a+sz; break
    # find prologue: nearest 'push ebp' or 'push ebx;mov ebx,ecx' or sub esp before site with no ret between
    start=None
    for a,sz,mn,op in reversed(ins):
        if a>=sa: continue
        if mn=='ret' or mn.startswith('jmp'):
            start=a+sz; break
    print("  interval guess: [%s, %s)" % (hex(start) if start else '?', hex(end) if end else '?'))
    # dump +-0x60 around site
    for a,sz,mn,op in disasm(sa-0x50,sa+0x40):
        mark=">>>" if a==sa else "   "
        print("  %s %08X %-7s %s"%(mark,a,mn,op))
    # callers: find the function entry containing site via E8 targets <= sa
    e8targets=[t for t in callers if t<=sa]
    fnentry=max(e8targets) if e8targets else None
    print("  nearest E8 target <= site: %s (callers there: %s)" % (hex(fnentry) if fnentry else '?', [hex(x) for x in callers.get(fnentry,[])][:6]))
    slots,names=rtti_of_fn(fnentry) if fnentry else ([],[])
    print("  vtable slots for fnentry: %s" % [hex(x[1]) for x in slots][:8])
    print("  RTTI names: %s" % names)
