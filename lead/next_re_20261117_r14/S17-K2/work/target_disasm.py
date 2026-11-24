#!/usr/bin/env python3
"""S17-K2: disassemble target functions, find callers, identify IAT calls & strings.
Build full RTTI class->vtable map to resolve slot indices.
"""
import sys, struct, os, re, io
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-F1\work")
import pe_util as P
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S17-K2\EVIDENCE"
TARGETS = [
  0x004068E0,0x0040E340,0x0041D6E0,0x00427940,0x0042E410,0x00431B80,0x00433CF0,0x004355B0,0x0043A5D0,0x0043AE50,
  0x0049F740,0x0049F8B0,0x004B6BB0,0x00539AE0,0x0055AAC0,0x0067C690,0x00773450,
]
KNOWN = {0x00410410:"AbstractClass::Save", 0x0067CEF0:"Game_Save_Outer", 0x0067D300:"Game_Save_Core"}

def sec_of(va):
    for name, va_base, vsize, praw, rawsize, ch in P.sections():
        if va_base <= va < va_base + max(vsize, rawsize): return name
    return "?"

out=io.StringIO()
def p(*a): print(*a,file=out)

# ---- Build vtable map by scanning .rdata: every position where dword[-1] is a valid COL ----
def try_col(col):
    sig = P.u32(col)
    if sig != 0: return None
    td = P.u32(col+0xC)
    if td is None or not (0x400000 <= td <= 0x900000): return None
    raw = P.read(td+8, 100)
    if raw is None: return None
    nm = raw.split(b'\x00')[0]
    try: s=nm.decode('ascii')
    except: return None
    if not (s.startswith('.?AV') or s.startswith('.?AU')): return None
    return s

rdata = [s for s in P.sections() if s[0]=='.rdata'][0]
lo = rdata[1]; hi = lo + rdata[3]  # rawsize
data = P.read(lo, hi-lo)
vtmap = {}  # vtable_va -> (col, classname)
for i in range(4, len(data)-4, 4):
    va = lo+i
    col = struct.unpack_from('<I', data, i-4)[0]
    if col == 0: continue
    nm = try_col(col)
    if nm:
        m = re.match(r'\.\?A[UV]([A-Za-z0-9_]+)@@', nm)
        cls = m.group(1) if m else nm
        vtmap[va] = (col, cls)

p("="*100)
p("1. RTTI class -> vtable map (from .rdata scan; COL at vt[-4], TD=COL+0xC, name=TD+8)")
p(f"   total vtables resolved = {len(vtmap)}")
for va,(col,cls) in sorted(vtmap.items(), key=lambda x:x[0]):
    if cls in ('AbstractClass','AirstrikeClass','NeuronClass','ObjectClass','TechnoClass','FootClass','BuildingClass','SwizzleManagerClass','CStreamClass','CommBufferClass'):
        p(f"   0x{va:08X} COL=0x{col:08X} class={cls}")

# AbstractClass vtable slots
p("\n2. AbstractClass vtable dump (find slot for Save @0x410410)")
for va,(col,cls) in vtmap.items():
    if cls=='AbstractClass':
        p(f"   vtable 0x{va:08X} COL=0x{col:08X}")
        slots=[]
        for k in range(40):
            sv = P.u32(va+4*k)
            if sv is None: break
            if not (0x401000 <= sv < 0x800000): break
            slots.append(sv)
            p(f"     slot{k:2d} (+0x{4*k:X}) = 0x{sv:08X} {KNOWN.get(sv,'')}")
        break

# What is slot 13 in AirstrikeClass and NeuronClass?
p("\n3. slot13 owners for the two callgraph rows")
for t in (0x41D6E0,0x43A5D0):
    for hva,sname in P.scan_imm32_refs(t):
        if sname!='.rdata': continue
        base=hva
        txt=[s for s in P.sections() if s[0]=='.text'][0]
        for _ in range(100):
            prev=P.u32(base-4)
            if prev is None or not (txt[1]<=prev<txt[1]+txt[2]): break
            base-=4
        r=vtmap.get(base)
        p(f"   0x{t:08X} hit@0x{hva:08X} vtbase=0x{base:08X} slot={(hva-base)//4} classmap={r}")
        if r:
            p(f"      class={r[1]} slots:")
            for k in range(30):
                sv=P.u32(base+4*k)
                if sv is None or not (0x401000<=sv<0x800000): break
                p(f"        slot{k:2d} 0x{sv:08X} {KNOWN.get(sv,'')}")

# ---- Disassembly of each target ----
p("\n"+"="*100)
p("4. Target function disassembly (first 200 bytes, skipdata=True) + direct callers")
for t in TARGETS:
    p(f"\n### 0x{t:08X} ({sec_of(t)})")
    callers = P.scan_rel32_calls(t)
    p(f"   E8/E9 direct callers: {[(hex(a),hex(b)) for a,b in callers]}")
    insns=P.disasm(t, 200)
    for ins in insns[:55]:
        extra=""
        if ins.mnemonic in ('call','jmp'):
            for op in ins.operands:
                if op.type==X86_OP_IMM:
                    extra=f" -> 0x{op.imm:08X} {KNOWN.get(op.imm,'')}"
        p(f"   {ins.address:08X}  {ins.bytes.hex():<18s} {ins.mnemonic:<7s} {ins.op_str}{extra}")
    p("   ...")

with open(os.path.join(OUT,"target_disasm.txt"),"w",encoding="utf-8") as f:
    f.write(out.getvalue())
print("wrote target_disasm.txt")
