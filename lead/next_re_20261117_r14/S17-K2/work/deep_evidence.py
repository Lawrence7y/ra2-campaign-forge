#!/usr/bin/env python3
"""S17-K2: deep evidence for naming candidates — IAT names, strings, full disasm, vtable chain bytes."""
import sys, struct, os, re, io
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K2\EVIDENCE"
out=io.StringIO()
def p(*a): print(*a,file=out)

def cstr(va, n=120):
    b=P.read(va,n)
    if b is None: return None
    s=b.split(b'\x00')[0]
    try: return s.decode('ascii')
    except: return repr(s)

# ---- IAT resolution ----
p("="*100); p("1. IAT slot resolution (pefile channel)")
for va in [0x7E1244,0x7E1238,0x7E100C,0x7E15F8,0x7E15FC,0x7C8B3D,0x7C8E17,0x7C8FB0,0x4CAC40,0x4A1D50,0x6CF240]:
    p(f"  0x{va:08X} -> {P.iat_name(va)}")

# ---- strings ----
p("\n2. String constants referenced by candidates")
for va in [0x81F51C,0x81F4FC,0x81F5B8,0x81F554,0xA9FAB4,0x827FC0,0x8495CC,0x83D564]:
    p(f"  0x{va:08X} = {cstr(va)!r}")

# ---- vtable RTTI byte chain for the 3 key vtables ----
p("\n3. RTTI byte chain (vt[-4] -> COL -> COL+0xC TD -> TD+8 name)")
for vt,label in [(0x7E1F50,'AbstractClass primary'),(0x7E29A8,'AirstrikeClass'),(0x7E3DF0,'NeuronClass'),
                 (0x7E3A2C,'BufferIOFileClass'),(0x7F743C,'WebBrowser'),(0x7F4108,'SwizzleManagerClass')]:
    cp=P.u32(vt-4)
    td=P.u32(cp+0xC) if cp else None
    p(f"  {label}: vt=0x{vt:08X}; [vt-4]=0x{cp:08X}; COL.sig=0x{P.u32(cp):X}; TD=COL+0xC=0x{td:08X}; name@TD+8={cstr(td+8)!r}" if cp else f"  {label}: vt=0x{vt:08X} no COL")

# ---- key instruction boundary verification ----
p("\n4. Key instruction boundary verification (capstone skipdata, exact byte at address)")
checks=[
 (0x41D6E0,'8b442404'),(0x41D6E5,'e8262dffff'),(0x43A5D0,'56'),(0x43A5D9,'e8325efdff'),
 (0x410410,' AbstractClass::Save'),
 (0x4B6BC2,'6810c1b000'),(0x4B6BC7,'e874862100'),
 (0x67C6A4,'ff500c'),(0x67C6B5,'8b3df8157e00'),
 (0x431B89,'c7062c3a7e00'),
 (0x773458,'6814040000'),(0x77348E,'c7063c747f00'),
 (0x49F769,'50'),(0x49F76A,'ff1544127e00'),(0x49F8C8,'ff1538127e00'),
]
for va,exp in checks:
    if exp.startswith(' '): continue
    b=P.read(va,len(exp)//2)
    ok = (b is not None and b.hex()==exp)
    p(f"  0x{va:08X} expect={exp} actual={b.hex() if b else None} {'OK' if ok else 'MISMATCH'}")

# ---- deeper full disassembly of naming candidates ----
p("\n"+"="*100); p("5. Full disassembly of naming candidates (target bytes, skipdata=True)")
for t,lim in [(0x41D6E0,0x41D6ED),(0x43A5D0,0x43A5F5),(0x4B6BB0,0x4B6BDD),
              (0x67C690,0x67C6E0),(0x431B80,0x431BD0),(0x773450,0x773500),
              (0x49F740,0x49F7A0),(0x49F8B0,0x49F910),(0x55AAC0,0x55AB40),(0x539AE0,0x539B30)]:
    p(f"\n### 0x{t:08X}")
    for ins in P.disasm(t, lim-t):
        extra=""
        if ins.mnemonic.startswith('.'):  # skipdata pseudo-instruction
            p(f"  {ins.address:08X} {ins.bytes.hex():<20s} {ins.mnemonic:<7s} {ins.op_str}")
            continue
        if ins.mnemonic in ('call','jmp'):
            for op in ins.operands:
                if op.type==X86_OP_IMM: extra=f" -> 0x{op.imm:08X} {P.iat_name(op.imm) or ''}"
        if ins.operands and ins.operands[0].type==X86_OP_MEM and ins.operands[0].mem.base==0 and ins.operands[0].mem.index==0:
            disp = ins.operands[0].mem.disp + ins.address + ins.size
            nm=P.iat_name(disp)
            if nm: extra+=f" [IAT {nm}]"
        p(f"  {ins.address:08X} {ins.bytes.hex():<20s} {ins.mnemonic:<7s} {ins.op_str}{extra}")

with open(os.path.join(OUT,"naming_candidates_evidence.txt"),"w",encoding="utf-8") as f: f.write(out.getvalue())
print("wrote naming_candidates_evidence.txt")
