"""T2 Channel B: find `push <GetSize>` allocation points in .text.

For each class size, scan .text for 68 <size32> (push imm32), then check if a
call to an allocator follows within a few instructions, and whether the site
lies in a function that writes the class's main vtable (ctor/factory ownership).
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import Bin, md, disasm_window, insn_text, write_tsv, write_text

b = Bin()
TLO, THI = b.sec_range(".text")
text = b.section_bytes(".text")

# Channel A values (hardcoded from t2_getsize.py output to avoid re-import side effects)
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

# known allocators to watch (from KB: 0x7C8E17 = operator new wrapper; verify by body)
ALLOC_HINTS = {0x7C8E17: "operator new[] wrapper?", 0x7C8B3D: "operator delete?"}

def classify_call(fn):
    if fn in ALLOC_HINTS:
        return ALLOC_HINTS[fn]
    ins = disasm_window(b, fn, 24, skipdata=False)
    sig = "; ".join(insn_text(i) for i in ins[:4])
    return sig

allrows = []
detail = []
for cls, (size, vt) in SIZES.items():
    pat = b"\x68" + struct.pack("<I", size)
    hits = []
    pos = 0
    while True:
        j = text.find(pat, pos)
        if j < 0: break
        pos = j + 1
        va = TLO + j
        hits.append(va)
    detail.append("=== %s size=0x%X vt=%08X : push sites=%d ===" % (cls, size, vt, len(hits)))
    for va in hits:
        # disassemble window around site (start a little before to see prev insn)
        start = va - 16 if va - 16 >= TLO else va
        ins = disasm_window(b, start, 48, skipdata=True)
        # find the instruction exactly at va
        idx = next((k for k,i in enumerate(ins) if i.address == va), None)
        ctx = []
        if idx is not None:
            for i in ins[max(0,idx-2):min(len(ins),idx+7)]:
                ctx.append("%08X %s" % (i.address, insn_text(i)))
                if i.mnemonic == "call" and i.op_str.startswith("0x"):
                    pass
        # detect call target right after push
        call_tgt = None
        if idx is not None:
            for i in ins[idx+1:idx+5]:
                if i.mnemonic == "call" and i.op_str.startswith("0x"):
                    call_tgt = int(i.op_str, 16)
                    break
        note = classify_call(call_tgt) if call_tgt else "-"
        detail.append("  push@%08X call=%s note=%s" % (va, ("%08X"%call_tgt) if call_tgt else "-", note))
        for c in ctx:
            detail.append("      "+c)
        allrows.append([cls, "0x%X"%size, "%08X"%vt, "%08X"%va,
                        ("%08X"%call_tgt) if call_tgt else "-", note])

write_tsv("T2_getsize_channelB.tsv",
          "class\tsize\tvtable\tpush_site\tcall_target\tnote", allrows)
write_text("T2_getsize_channelB.txt", "\n".join(detail) + "\n")
print("\n".join(detail[:120]))
print("... total push sites:", len(allrows))
