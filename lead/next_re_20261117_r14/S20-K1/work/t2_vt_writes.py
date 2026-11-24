"""Find constructors via vtable-immediate writes, then tie `push <size>; call new` to them."""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, disasm_window, insn_text, write_tsv, write_text

b = Bin()
TLO, THI = b.sec_range(".text")
text = b.section_bytes(".text")

SIZES = {
    "AnimClass":               (0x1C8, 0x7E3354),
    "ParticleClass":           (0x138, 0x7EF954),
    "ParticleSystemClass":     (0x100, 0x7EFB9C),
    "VoxelAnimClass":          (0x148, 0x7F6318),
    "AnimTypeClass":           (0x378, 0x7E3608),
    "ParticleTypeClass":       (0x318, 0x7F0188),
    "ParticleSystemTypeClass": (0x310, 0x7F00A8),
    "VoxelAnimTypeClass":      (0x308, 0x7F6548),
}

m = md(detail=True, skipdata=True)

def find_vt_writes(vt):
    """Return (va, insn_text) for instructions that install vt as an immediate."""
    pat = struct.pack("<I", vt)
    out = []
    pos = 0
    while True:
        j = text.find(pat, pos)
        if j < 0: break
        pos = j + 1
        va = TLO + j
        for back in range(0, 9):
            st = va - back
            if st < TLO: break
            try:
                ins = list(m.disasm(b.read(st, 24), st))
            except Exception:
                continue
            if ins and ins[0].address == st:   # st is a real insn boundary
                i = ins[0]
                # does this instruction cover va and carry vt as an immediate operand?
                if (i.mnemonic in ("mov", "push") and
                        ("0x%x" % vt) in i.op_str.lower() and
                        st <= va < st + i.size):
                    out.append((st, insn_text(i), back))
                    break
    return out

rows = []
detail = []
for cls, (size, vt) in SIZES.items():
    writes = find_vt_writes(vt)
    detail.append("=== %s vt=%08X size=0x%X : imm-write sites=%d ===" % (cls, vt, size, len(writes)))
    for va, t, bk in writes:
        detail.append("  imm@%08X back=%d  %s" % (va, bk, t))
        rows.append([cls, "%08X"%vt, "%08X"%size, "imm_write", "%08X"%va, t])
        st = va-12 if va-12>=TLO else va
        for i in disasm_window(b, st, 40, skipdata=True)[:7]:
            detail.append("      %08X %s" % (i.address, insn_text(i)))

write_tsv("T2_vtable_writes.tsv", "class\tvtable\tsize\tkind\tsite\tinsn", rows)
write_text("T2_vtable_writes.txt", "\n".join(detail)+"\n")
print("\n".join(detail[:110]))
