# -*- coding: utf-8 -*-
"""Rigorous vtable-slot -> COL -> TD -> name (fail-closed) for the 11 write fn entries; plus direct callers' ecx source."""
import pefile, struct
from capstone import *
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
def dis(start,end):
    va=start
    while va<end:
        got=list(md.disasm(rd(va,16),va,count=1))
        if not got: va+=1; continue
        i=got[0]; print("    %08X  %-7s %s"%(i.address,i.mnemonic,i.op_str)); va+=i.size

def all_slots_of_fn(fn):
    """all aligned dword locations in non-text sections whose value==fn"""
    out=[]
    for s in secs:
        if s["name"]==".text": continue
        for off in range(0,s["rawsize"]-3,4):
            v=struct.unpack_from("<I",data,s["raw"]+off)[0]
            if v==fn: out.append((s["va"]+off,s["name"]))
    return out

def col_td_name(vslot):
    """find COL whose vptr points within [vslot-0x200, vslot+0x200], report TD+8 name"""
    out=[]
    for s in secs:
        if s["name"]==".text": continue
        for off in range(0,s["rawsize"]-3,4):
            v=struct.unpack_from("<I",data,s["raw"]+off)[0]
            if s["va"]<=v<s["va"]+s["rawsize"] and abs(v-vslot)<=0x300:
                colva=s["va"]+off
                sig=u32(colva); td=u32(colva+0xC)
                if sig!=0: continue
                if td and sec_of(td):
                    b=rd(td+8,96); z=b.find(b"\x00")
                    nm=b[:z].decode("latin1") if z!=-1 else ""
                    if nm.startswith('.?AV'): out.append((hex(colva),hex(v),hex(td),nm))
    return out[:8]

FNentries=[0x4CCA20,0x5C0240,0x5C07D0,0x76AAF0,0x77A700,0x7B23B0,0x7CCFFC]
for fn in FNentries:
    print("\n"+"="*70)
    print("FN %08X"%fn)
    slots=all_slots_of_fn(fn)
    print("  dword slots: %s"%[hex(x[0]) for x in slots][:12])
    for slot,sname in slots[:5]:
        names=col_td_name(slot)
        print("    slot %08X (%s) -> COL/TD/name: %s"%(slot,sname,names))
    # direct E8 callers
    calls=[]
    for va in range(T0,T1-4):
        if data[TRAW+(va-T0)]==0xE8:
            rel=int.from_bytes(data[TRAW+(va+1-T0):TRAW+(va+5-T0)],"little",signed=True)
            if (va+5+rel)&0xFFFFFFFF==fn: calls.append(va)
    print("  direct E8 callers: %s"%[hex(x) for x in calls][:12])
    for c in calls[:1]:
        print("  -- context at first caller %08X --"%c)
        dis(c-0x20,c+0x10)
