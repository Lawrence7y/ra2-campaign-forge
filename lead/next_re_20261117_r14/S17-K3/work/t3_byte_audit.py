#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T3 independent byte-level audit of 5 S17 [已证] rows.
For each: dump function bytes, resolve calls/IAT/strings, verify the semantic claim.
NEVER reuse another card's conclusion; all checks read gamemd.exe directly.
"""
import sys, struct, io, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;md.skipdata=True
out=[]

def dis(va,size):
    b=P.read(va,size); r=[]
    for ins in md.disasm(b,va):
        line=f"{ins.address:08X}: {ins.bytes.hex():<18s} {ins.mnemonic:<7s} {ins.op_str}"
        if ins.mnemonic in ('call','jmp') and ins.operands and ins.operands[0].type==X86_OP_IMM:
            nm=P.iat_name(ins.operands[0].imm)
            if nm: line+=f" ; IAT={nm}"
        if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
            t=ins.operands[0].imm; off=P.va2off(t)
            if off is not None:
                with open(P.EXE,'rb') as f: f.seek(off);sb=f.read(80)
                z=sb.find(b'\x00')
                if 2<=z<=70 and all(32<=c<127 for c in sb[:z]):
                    line+=f" ; str={sb[:z]!r}"
        r.append(line)
    return r

# ---- 1. 0x41D6E0 AirstrikeClass::Save ----
out.append("===== [已证] #1 0x0041D6E0 AirstrikeClass::Save =====")
out.append("claim: slot13(+0x34) of AirstrikeClass vt; body push arg; call 0x410410; ret 4")
out.append("bytes: "+P.read(0x41D6E0,13).hex(' '))
out.extend("  "+l for l in dis(0x41D6E0,13))
# RTTI slot13 check via vtable 0x7E29A8 found earlier
col=P.u32(0x7E29A4); td=P.u32(col+0xC) if col else None
out.append(f"  vt 0x7E29A8 slot13 = {P.u32(0x7E29A8+0x34):08X}; pCOL={col:08X}; TD={td:08X}")
o=P.va2off(td+8) if td else None
if o is not None:
    with open(P.EXE,'rb') as f:f.seek(o);nm=f.read(40)
    z=nm.find(b'\x00')
    out.append(f"  RTTI name = {nm[:z if z>=0 else 30]!r}")

# ---- 2. 0x43A5D0 NeuronClass::Save ----
out.append("\n===== [已证] #2 0x0043A5D0 NeuronClass::Save =====")
out.append("claim: slot13(+0x34) of NeuronClass vt; calls 0x410410 then frame-delta via 0x4A1D50")
out.append("bytes: "+P.read(0x43A5D0,37).hex(' '))
out.extend("  "+l for l in dis(0x43A5D0,37))
col=P.u32(0x7E3DEC);td=P.u32(col+0xC) if col else None
out.append(f"  vt 0x7E3DF0 slot13 = {P.u32(0x7E3DF0+0x34):08X}; pCOL={col:08X}; TD={td:08X}")
if td:
    o=P.va2off(td+8)
    if o is not None:
        with open(P.EXE,'rb') as f:f.seek(o);nm=f.read(40)
        out.append(f"  RTTI name = {nm[:30]!r}")

# ---- 3. 0x4B6BB0 Swizzle_RegisterPointerArray ----
out.append("\n===== [已证] #3 0x004B6BB0 Swizzle_RegisterPointerArray =====")
out.append("claim: for i<[this+0x10]: push &[this+0x14+4i]; push 0xB0C110; call 0x6CF240")
out.append("bytes: "+P.read(0x4B6BB0,43).hex(' '))
out.extend("  "+l for l in dis(0x4B6BB0,43))

# ---- 4. 0x67C690 Load_COM_ObjectVector ----
out.append("\n===== [已证] #4 0x0067C690 Load_COM_ObjectVector =====")
out.append("claim: IStream::Read u32 count via [vptr+0xC]; OleLoadFromStream(ole32!0x7E15F8) count times with IID 0x7F7C90")
out.append("bytes: "+P.read(0x67C690,78).hex(' '))
out.extend("  "+l for l in dis(0x67C690,78))
out.append(f"  IAT 0x7E15F8 = {P.iat_name(0x7E15F8)}")
# dump the two IID candidates
for iid in (0x7F7C80,0x7F7C90):
    out.append(f"  IID @ {iid:08X}: bytes {P.read(iid,16).hex(' ')}")

# ---- 5. 0x6CF240 Here_I_Am ----
out.append("\n===== [已证] #5 0x006CF240 Here_I_Am =====")
out.append("claim(sem): 'Here_I_Am：YRpp/kb 地址名；归属 存档/序列化/Swizzle（名字已证，语义据名）[未证]'")
out.append("evidence_path = EVIDENCE/classification_trace.tsv#006CF240  (trace, not byte evidence)")
out.append("bytes: "+P.read(0x6CF240,118).hex(' '))
out.extend("  "+l for l in dis(0x6CF240,118))
# callers
callers=P.scan_rel32_calls(0x6CF240)
out.append(f"  direct E8 callers = {len(callers)}")

txt="\n".join(out)+"\n"
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K3"
with io.open(os.path.join(CARD,"EVIDENCE","t3_byte_audit.txt"),"w",encoding="utf-8") as f:f.write(txt)
sys.stdout.write(f"written {len(txt)} chars\n")
