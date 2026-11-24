"""S19 task 2c: reader evidence for VocClass fields in play/voice lifecycle."""
import os, re
import common as C

b = C.Bin(); E = os.path.join(C.CARD, "EVIDENCE")

# Function ranges to scan (VA, bytes, label)
ranges = [
    (0x4041D0, 0x400, "sample_update_4041D0"),
    (0x405190, 0x900, "voice_alloc_state_405190"),
    (0x750920, 0x180, "Play_750920"),
    (0x750AC0, 0x180, "PlayAt3D_750AC0"),
    (0x406650, 0x40,  "hasdelay_406650"),
]
offs = [0x10, 0x14, 0x18, 0x40, 0x44, 0x48, 0x4C, 0x50, 0x54,
        0x58, 0x5C, 0x60, 0x64, 0x68, 0x6C, 0x8C, 0x98, 0x138, 0x13C]

rx = re.compile(r"\[(e(?:ax|bx|cx|dx|si|di|bp)) \+ (0x[0-9a-f]+)\]")
out = []
for start, size, label in ranges:
    path = os.path.join(E, "task2_reader_%s.txt" % label)
    lines = C.dump(b, start, size, path)
    out.append("\n===== %s %08X..%08X =====" % (label, start, start + size))
    for insn in C.disasm(b, start, size):
        m = rx.search(insn.op_str)
        if m and int(m.group(2), 16) in offs:
            off = int(m.group(2), 16)
            out.append("  %08X %-6s %-30s ; off=+0x%X" %
                       (insn.address, insn.mnemonic, insn.op_str, off))
txt = "\n".join(out)
open(os.path.join(E, "task2_reader_summary.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
