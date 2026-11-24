"""Verify Draw-side gates for AnimClass +0x199/+0x19D (byte-level)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, insn_text, write_text
b=Bin(); m=md(detail=True,skipdata=True)
out=["=== AnimClass Draw-side fog/invisible gates (0x422CA0) ==="]
for va in [0x423014, 0x422FEC, 0x42301E, 0x42362C]:
    out.append("--- window at %08X ---"%va)
    for i in m.disasm(b.read(va,16),va):
        if i.id==0: continue
        out.append("  %08X %-38s ; %s"%(i.address,insn_text(i),i.bytes.hex()))
write_text("T3_anim_draw_gates.txt","\n".join(out)+"\n")
print("\n".join(out))
