"""W176 Task 1, channel A: full-image [reg+0x81] operand census (byte/dword/word), no atlas boundaries.

Independent byte-level channel: pure capstone 5.0.7 disasm of every .text raw byte with skipdata=True.
No function_atlas.tsv import.  All addresses are VA (ImageBase 0x400000).

Outputs: EVIDENCE/T1_byte81_channelA.txt, EVIDENCE/T1_byte81_all.json
"""
import json
import os
import struct
import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\EVIDENCE"
IB = 0x400000


class Bin:
    def __init__(self):
        self.pe = pefile.PE(EXE, fast_load=True)
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            va = self.ib + s.VirtualAddress
            self.sections.append(dict(name=name, va=va, vsize=s.Misc_VirtualSize,
                                      raw=s.PointerToRawData, rawsize=s.SizeOfRawData))

    def sec(self, name):
        return next(s for s in self.sections if s["name"] == name)

    def read(self, va, n):
        for s in self.sections:
            if s["va"] <= va and va + n <= s["va"] + s["rawsize"]:
                off = s["raw"] + (va - s["va"])
                return self.pe.__data__[off:off + n]
        raise ValueError("VA %08X+%d not in raw" % (va, n))

    def u8(self, va):
        return self.read(va, 1)[0]

    def u32(self, va):
        return struct.unpack("<I", self.read(va, 4))[0]


def md():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = True
    return m


def operand_info(ins, op):
    """Return dict for a X86_OP_MEM operand whose disp == 0x81."""
    mem = op.mem
    base = ins.reg_name(mem.base) if mem.base else "-"
    idx = ins.reg_name(mem.index) if mem.index else "-"
    acc = op.access
    return dict(va=ins.address, size=op.size, mnem=ins.mnemonic,
                op_str=ins.op_str, text="%s %s" % (ins.mnemonic, ins.op_str),
                base=base, index=idx, scale=mem.scale,
                kind=("abs" if mem.base == 0 and mem.index == 0 else "reg+disp"),
                read=bool(acc & capstone.CS_AC_READ),
                write=bool(acc & capstone.CS_AC_WRITE),
                access=acc, insn_id=ins.id, insn_size=ins.size,
                op_index=ins.operands.index(op))


def main():
    b = Bin()
    m = md()
    t = b.sec(".text")
    data = b.pe.__data__[t["raw"]:t["raw"] + t["rawsize"]]
    hits = []
    nins = nskip = 0
    for ins in m.disasm(data, t["va"]):
        if ins.id == 0:
            nskip += ins.size
            continue
        nins += 1
        for oi, op in enumerate(ins.operands):
            if op.type != capstone.x86.X86_OP_MEM:
                continue
            if (op.mem.disp & 0xFFFFFFFF) != 0x81:
                continue
            if op.mem.base == 0 and op.mem.index == 0 and (op.mem.disp & 0xFFFFFFFF) == 0x81:
                # absolute address 0x81 is not a plausible object field; keep for completeness
                pass
            d = operand_info(ins, op)
            d["op_index"] = oi
            hits.append(d)
    stats = dict(insns=nins, skipped_bytes=nskip, text_bytes=len(data), hits=len(hits))
    with open(os.path.join(OUT, "T1_byte81_all.json"), "w", encoding="utf-8") as f:
        json.dump(dict(stats=stats, hits=hits), f, indent=1)

    lines = []
    lines.append("W176 T1 channel A: every .text instruction with a memory operand [..+0x81]")
    lines.append("capstone=%s, skipdata=True; disasm=%d real instructions, %d skipped bytes, .text=%d bytes"
                 % (capstone.__version__, nins, nskip, len(data)))
    lines.append("total operand hits = %d (may exceed instruction count if 2 operands qualify)" % len(hits))
    lines.append("")
    for width in (1, 2, 4, 8):
        subset = [h for h in hits if h["size"] == width]
        lines.append("=== width=%d B : %d hits (write or RMW=%d, read-any=%d) ===" %
                     (width, len(subset),
                      sum(1 for h in subset if h["write"]),
                      sum(1 for h in subset if h["read"])))
        for h in subset:
            lines.append("  %08X  w=%d  %-55s base=%-5s idx=%-5s access=%d  op%d  insnsz=%d" %
                         (h["va"], h["size"], h["text"], h["base"], h["index"],
                          h["access"], h["op_index"], h["insn_size"]))
        lines.append("")
    with open(os.path.join(OUT, "T1_byte81_channelA.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("stats", stats)
    print("w1 writes", sum(1 for h in hits if h["size"] == 1 and h["write"]))
    print("w1 reads", sum(1 for h in hits if h["size"] == 1 and h["read"]))
    print("w4 writes", sum(1 for h in hits if h["size"] == 4 and h["write"]))
    print("w4 reads", sum(1 for h in hits if h["size"] == 4 and h["read"]))


if __name__ == "__main__":
    main()
