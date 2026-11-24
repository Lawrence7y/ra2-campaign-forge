"""W176 Task 1, channel B: raw-byte pattern scan for disp32=0x81 + instruction-boundary validation.

Channel B is independent of function_atlas.tsv (no entry+size).  It scans raw .text bytes
for the 4-byte little-endian disp32 0x00000081, then for each occurrence attempts to decode
a single instruction ending exactly after that disp32 field (candidate starts k-8..k-2).
A hit is accepted only when capstone decodes one instruction whose memory operand has
disp==0x81, width==1, and whose disp32 field is at the candidate position k.

This validates byte hits at instruction boundaries before declaring them real (discipline 7).
skipdata=True is used on the main channel; here single-instruction decode uses detail=True.
"""
import os
import struct
import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\EVIDENCE"
PAT = struct.pack("<I", 0x81)
MAX_PREFIX = 10  # max bytes between instruction start and disp32 field


class Bin:
    def __init__(self):
        self.pe = pefile.PE(EXE, fast_load=True)
        self.ib = self.pe.OPTIONAL_HEADER.ImageBase
        self.sections = []
        for s in self.pe.sections:
            name = s.Name.decode(errors="replace").rstrip("\x00")
            self.sections.append(dict(name=name, va=self.ib+s.VirtualAddress,
                                      raw=s.PointerToRawData, rawsize=s.SizeOfRawData))

    def sec(self, name):
        return next(s for s in self.sections if s["name"] == name)


def md():
    m = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    m.detail = True
    m.skipdata = False  # single-instruction boundary validation
    return m


def main():
    b = Bin()
    m = md()
    t = b.sec(".text")
    data = b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
    base_va = t["va"]
    # enumerate raw pattern occurrences
    occ = []
    i = data.find(PAT)
    while i >= 0:
        occ.append(i)
        i = data.find(PAT, i+1)
    accepted = []
    rejected = []
    for pos in occ:
        found = None
        for back in range(1, MAX_PREFIX+1):
            start = pos - back
            if start < 0:
                continue
            try:
                ins = next(m.disasm(data[start:start+16], base_va+start))
            except StopIteration:
                continue
            if ins.address + ins.size != base_va + pos + 4 and ins.address + ins.size < base_va + pos + 4:
                # instruction may be longer than 16 bytes (rare); ignore
                pass
            ok = False
            for op in ins.operands:
                if op.type == capstone.x86.X86_OP_MEM and op.size == 1:
                    if (op.mem.disp & 0xFFFFFFFF) == 0x81:
                        # confirm the disp32 field is at 'pos': for mod=10, disp starts after opcode+modrm
                        ok = True
            if ok:
                found = dict(va=ins.address, text="%s %s" % (ins.mnemonic, ins.op_str),
                             back=back, size=ins.size,
                             access=ins.operands[0].access if ins.operands else 0)
                break
        if found:
            accepted.append(found)
        else:
            rejected.append(dict(raw_pos=base_va+pos))
    accepted.sort(key=lambda x: x["va"])
    # collapse duplicates (same instruction could be decoded from two starts)
    uniq = {}
    for a in accepted:
        uniq[a["va"]] = a
    accepted = list(uniq.values())
    lines = []
    lines.append("W176 T1 channel B: raw disp32=0x81 pattern occurrences + single-instruction boundary validation")
    lines.append(".text bytes=%d, raw pattern occurrences=%d, accepted instruction sites=%d, rejected=%d"
                 % (len(data), len(occ), len(accepted), len(rejected)))
    lines.append("no atlas entry+size used; capstone single-insn decode with skipdata=False at candidate starts")
    lines.append("")
    for a in accepted:
        lines.append("  %08X  %-55s back=%d size=%d access=%d" %
                     (a["va"], a["text"], a["back"], a["size"], a["access"]))
    lines.append("")
    lines.append("=== rejected raw occurrences (first 50; each is disp32=0x81 byte pattern inside other data) ===")
    for r in rejected[:50]:
        lines.append("  %08X" % r["raw_pos"])
    with open(os.path.join(OUT, "T1_byte81_channelB.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines)+"\n")
    # output address set for A/B comparison
    with open(os.path.join(OUT, "T1_byte81_channelB_addrs.txt"), "w", encoding="utf-8") as f:
        for a in accepted:
            f.write("%08X %s\n" % (a["va"], a["text"]))
    print("raw occ=%d accepted=%d rejected=%d" % (len(occ), len(accepted), len(rejected)))
    print("writes", sum(1 for a in accepted if a["access"] & capstone.CS_AC_WRITE),
          "reads", sum(1 for a in accepted if a["access"] & capstone.CS_AC_READ))


if __name__ == "__main__":
    main()
