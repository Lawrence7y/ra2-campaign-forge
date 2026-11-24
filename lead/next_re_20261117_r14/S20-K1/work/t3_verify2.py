"""T3 verify v2: disassemble from real function entries, filter by offset."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, insn_text, write_text

b=Bin(); m=md(detail=True,skipdata=True)

# (label, fn_entry, maxbytes, [offsets])
TASKS=[
 ("AnimClass::AI/Update 0x423AC0", 0x423AC0, 0x1800, [0xC8,0xCC,0x184,0x198,0x19D]),
 ("AnimClass::DrawIfVisible 0x422C70", 0x422C70, 0x40, [0x184]),
 ("AnimClass::ctor 0x421EA0", 0x421EA0, 0x1C0, [0x184,0xC8,0xCC,0x199,0x19D]),
 ("ParticleClass::Draw 0x62CEC0", 0x62CEC0, 0x800, [0x9C,0xA0,0xA4,0xAC,0x12C,0x12F]),
 ("ParticleClass::ctor 0x62B5E0", 0x62B5E0, 0x200, [0x9C,0xA4,0xAC,0x124,0x12C,0x12F]),
 ("PSys::Draw 0x62E280", 0x62E280, 0x600, [0x9C,0xAC,0xE0,0xFC,0xF4]),
 ("PSys::ctor 0x62DC50", 0x62DC50, 0x120, [0xAC,0xE0,0xF4,0xFC,0xBC]),
 ("PSys::Update 0x62DF20", 0x62DF20, 0x100, [0xAC,0xE0,0xFC,0xBC,0xF4]),
]
out=[]
for label,fn,nb,offs in TASKS:
    out.append("=== %s entry=%08X ==="%(label,fn))
    try: ins=list(m.disasm(b.read(fn,nb),fn))
    except Exception as e: out.append("  ERR %s"%e); continue
    for i in ins:
        if i.id==0: continue
        for op in i.operands:
            if op.type!=__import__('capstone').x86.X86_OP_MEM: continue
            if op.mem.base==0: continue
            d=op.mem.disp & 0xFFFFFFFF
            if d in offs:
                out.append("  %08X  %-40s ; %s"%(i.address,insn_text(i),i.bytes.hex()))
                break
        if i.mnemonic=="ret" and i.address>fn+16: break
    out.append("")
write_text("T3_field_semantic_functions.txt","\n".join(out)+"\n")
print("\n".join(out))
