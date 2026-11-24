"""T3 semantic verification: dump disassembly windows around key field accesses.

Each (label, center_va, span_before, span_after) shows byte-level instructions
so a field's semantics can be justified by the class's own writer+reader.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, insn_text, write_text

b = Bin()
m = md(detail=True, skipdata=True)

WINDOWS = [
    # AnimClass +0x184 DelayTimer
    ("AnimCtor mov[+184],ecx @421FC2", 0x421FC2, 0x18, 0x18),
    ("AnimUpdate dec[+184] @424386",    0x424386, 0x20, 0x30),
    ("AnimDrawIfVisible read[+184] @422C70", 0x422C70, 0x0, 0x20),
    # AnimClass +0xC8/+0xCC frame/progress
    ("AnimCtor mov[+C8] @? from census writer", 0x421E00, 0x0, 0x0),  # placeholder replaced below
    # ParticleClass +0xAC Type
    ("ParticleCtor mov[+AC],eax @62B5F4", 0x62B5F4, 0x18, 0x18),
    ("ParticleDraw read[+AC] region @62CFxx", 0x62CF80, 0x0, 0x20),
    # ParticleSystem +0xF4 SpotlightRadius
    ("PSysCtor mov[+F4],1d @62DD??", 0x62DD00, 0x0, 0x40),
    ("PSysDraw read[+F4] @62E2xx", 0x62E300, 0x0, 0x30),
]
out=[]
for label, center, before, after in WINDOWS:
    if before==0 and after==0: continue
    st=center-before; n=before+after
    out.append("=== %s center=%08X ==="%(label,center))
    try:
        for i in m.disasm(b.read(st,n),st):
            if i.id==0: continue
            mark="*" if i.address==center else " "
            out.append(" %s %08X  %-34s ; %s"%(mark,i.address,insn_text(i),i.bytes.hex()))
    except Exception as e:
        out.append("  ERR %s"%e)
    out.append("")

write_text("T3_field_semantic_windows.txt","\n".join(out)+"\n")
print("\n".join(out[:140]))
