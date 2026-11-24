# -*- coding: utf-8 -*-
"""Dump host function bodies + context around ambiguous install sites. Read-only."""
import io, os, sys, json, bisect
import capstone
HERE=os.path.dirname(os.path.abspath(__file__)); R14=os.path.dirname(HERE)
ROOT=os.path.dirname(os.path.dirname(R14))
EXE=os.path.join(ROOT,"ra2youli","gamemd.exe")
PROBE=os.path.join(R14,"R16_PROBE_4FINAL"); AUD=os.path.join(R14,"R16_AUDIT_D1_WIDE_B1")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
sys.path.insert(0,PROBE); sys.dont_write_bytecode=True
import final as F
IB=F.IMAGE_BASE; img=F.Image(EXE); buf=img.buf
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True; md.skipdata=True
def dis(va,n):
    o=va-IB
    if o<0 or o>=len(buf): return []
    return list(md.disasm(bytes(buf[o:o+n]),va))

# dump raw window around a site (linear disasm from a chosen start)
WINDOWS = {
 "006C6588_ctx":(0x006C6560,0x80),
 "006C6610_host":(0x006C6610,0x60),
 "006C6880_host":(0x006C6880,0x50),
 "007BA590_host":(0x007BA590,0x60),
 "006CF0C0_abs":(0x006CF0A0,0x90),
 "006F2B40_host":(0x006F2B40,0x100),   # TechnoClass ctor candidate (site 006F3130)
 "006F4300_host":(0x006F4300,0x130),   # site 006F4413
 "006F4500_host":(0x006F4500,0x40),    # site 006F450D
 "00413D20_host":(0x00413D20,0x90),    # Aircraft ctor (site 00413D87)
 "00414080_host":(0x00414080,0x40),    # site 0041408A
 "0041B430_host":(0x0041B430,0x50),    # site 0041B4E1
 "00771C70_host":(0x00771C70,0x120),   # WeaponType ctor (site 00771E77)
 "00771F00_host":(0x00771F00,0x70),    # site 00771F28
 "007730F0_host":(0x007730F0,0x40),    # deleting dtor itself (site 007730F7)
}
out=[]
for tag,(va,n) in WINDOWS.items():
    out.append('===== %s  @%08X  (%d bytes) ====='%(tag,va,n))
    for x in dis(va,n):
        mark=''
        if x.mnemonic in ('ret','retf'): mark='  <-- RET'
        if '0x7f' in x.op_str.lower() or '0x7e' in x.op_str.lower(): mark+='  <== VPTR?' 
        out.append('  %08X: %-20s %s%s'%(x.address,x.bytes.hex(),'%s %s'%(x.mnemonic,x.op_str),mark))
    out.append('')
io.open(os.path.join(HERE,'host_dump_py.txt'),'w',encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
