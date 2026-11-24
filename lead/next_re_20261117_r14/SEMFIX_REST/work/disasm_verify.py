# -*- coding: utf-8 -*-
"""Disassemble target functions and verify cited offsets appear in body.
Read-only on gamemd.exe. Writes evidence to SEMFIX_REST/EVIDENCE/.
"""
import json, os, re, sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
EVIDENCE_DIR = os.path.join(ROOT, "lead", "next_re_20261117_r14", "SEMFIX_REST", "EVIDENCE")
WORK_DIR = os.path.join(ROOT, "lead", "next_re_20261117_r14", "SEMFIX_REST", "work")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

pe = pefile.PE(EXE)
image_base = pe.OPTIONAL_HEADER.ImageBase
code = pe.get_memory_mapped_image()
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

def disasm_func(entry_hex, max_bytes=8192):
    entry = int(entry_hex, 16)
    rva = entry - image_base
    off = pe.get_offset_from_rva(rva)
    data = code[off:off+max_bytes]
    insns = []
    count = 0
    for insn in md.disasm(data, entry):
        insns.append({"addr": insn.address, "bytes": insn.bytes.hex(), "mnemonic": insn.mnemonic, "op_str": insn.op_str})
        count += 1
        if count >= 2000:
            break
        if count >= 5 and insn.mnemonic in ("ret", "retf"):
            break
    return insns

def main():
    with open(os.path.join(WORK_DIR, "targets_41.json"), "r", encoding="utf-8") as f:
        targets = json.load(f)
    results = []
    for t in targets:
        entry = t["entry"]
        insns = disasm_func(entry)
        ev_path = os.path.join(EVIDENCE_DIR, "DISASM_" + entry + ".txt")
        with open(ev_path, "w", encoding="utf-8") as f:
            f.write("; entry=" + entry + " subsystem=" + t["subsystem"] + " name=" + t["name"] + "\n")
            f.write("; criterion=" + t["criterion"] + "\n")
            f.write("; byte_evidence=" + t["byteEvidence"] + "\n")
            f.write("; insn_count=" + str(len(insns)) + "\n")
            for insn in insns:
                f.write("%08X  %-24s %-8s %s\n" % (insn["addr"], insn["bytes"], insn["mnemonic"], insn["op_str"]))
        results.append({"entry": entry, "insn_count": len(insns), "body_start": hex(insns[0]["addr"]) if insns else None, "body_end": hex(insns[-1]["addr"]) if insns else None, "ev_path": ev_path})
    with open(os.path.join(WORK_DIR, "disasm_index.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Disassembled", len(results), "functions")
    for r in results:
        print(r["entry"], r["insn_count"], r["body_start"], r["body_end"])

if __name__ == "__main__":
    main()
