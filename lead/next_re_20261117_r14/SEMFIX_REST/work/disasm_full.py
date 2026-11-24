# -*- coding: utf-8 -*-
"""Full-range disassembly (no early ret stop) for cited-address verification."""
import json, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EVIDENCE_DIR = os.path.join(ROOT, "lead", "next_re_20261117_r14", "SEMFIX_REST", "EVIDENCE")
WORK_DIR = os.path.join(ROOT, "lead", "next_re_20261117_r14", "SEMFIX_REST", "work")

pe = pefile.PE(EXE)
image_base = pe.OPTIONAL_HEADER.ImageBase
code = pe.get_memory_mapped_image()
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def disasm_full(entry_hex, max_bytes=16384, max_insns=4000):
    entry = int(entry_hex, 16)
    off = pe.get_offset_from_rva(entry - image_base)
    data = code[off:off+max_bytes]
    insns = []
    for insn in md.disasm(data, entry):
        insns.append({"addr": insn.address, "bytes": insn.bytes.hex(), "m": insn.mnemonic, "o": insn.op_str})
        if len(insns) >= max_insns:
            break
    return insns

def main():
    with open(os.path.join(WORK_DIR, "targets_41.json"), "r", encoding="utf-8") as f:
        targets = json.load(f)
    for t in targets:
        entry = t["entry"]
        insns = disasm_full(entry)
        ev_path = os.path.join(EVIDENCE_DIR, "DISASM_FULL_" + entry + ".txt")
        with open(ev_path, "w", encoding="utf-8") as f:
            f.write("; FULL entry=" + entry + " criterion=" + t["criterion"] + "\n")
            f.write("; byte_evidence=" + t["byteEvidence"] + "\n")
            f.write("; insn_count=" + str(len(insns)) + " last=" + (hex(insns[-1]["addr"]) if insns else "N/A") + "\n")
            for insn in insns:
                f.write("%08X  %-24s %-8s %s\n" % (insn["addr"], insn["bytes"], insn["m"], insn["o"]))
    print("Full disasm done for", len(targets), "functions")

if __name__ == "__main__":
    main()
