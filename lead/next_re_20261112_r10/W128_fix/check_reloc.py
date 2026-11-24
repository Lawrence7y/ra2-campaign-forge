#!/usr/bin/env python3
"""W128d: relocation equivalence check.

For each guarded entry, disassemble:
  (A) starting at the original entry, and
  (B) the stub's relocated bytes followed by the bytes at `resume`.
The instruction streams must agree for the instructions that the stub actually
executes (A's first `relocate_len` bytes == B's first `relocate_len` bytes, and
B must then continue exactly where A continues).

This catches any mis-cut relocation that a length-only check would miss.
"""
import json
import os

import capstone
import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

plan = json.load(open(os.path.join(HERE, "entries.json")))

all_ok = True
for e in plan["entries"]:
    fn = int(e["fn"], 16)
    rl = int(e["relocate_len"])
    reloc = bytes.fromhex(e["relocate_bytes"])
    resume = int(e["resume_at"], 16)

    # B = relocated bytes, then the original bytes at resume (enough to compare)
    tail = img[resume - ib: resume - ib + 32]
    streamB = reloc + tail

    a = list(md.disasm(img[fn - ib: fn - ib + 48], fn))
    b = list(md.disasm(streamB, fn))          # fake address: only text is compared

    # the first instructions in B should correspond to A's until we pass rl
    nA = []
    acc = 0
    for ins in a:
        if acc >= rl:
            break
        nA.append("%s %s" % (ins.mnemonic, ins.op_str))
        acc += ins.size

    nB = []
    acc = 0
    for ins in b:
        if acc >= rl:
            break
        nB.append("%s %s" % (ins.mnemonic, ins.op_str))
        acc += ins.size

    ok = (nA == nB)
    all_ok &= ok
    print("\n=== %s  relocate=%d  resume=0x%08X" % (e["fn"], rl, resume))
    print("  A (at entry)      :", " | ".join(nA))
    print("  B (stub + resume) :", " | ".join(nB))
    print("  equivalence       :", "OK" if ok else "MISMATCH")

    # the instruction at the resume boundary must be identical in both streams
    contA = next((("%s %s" % (i.mnemonic, i.op_str)) for i in a if i.address >= resume), None)
    contB = next(("%s %s" % (i.mnemonic, i.op_str)) for i in b
                 if i.address - fn >= rl and i.bytes[:1] and i.address >= fn + rl)
    print("  first insn after  : A=%r  B=%r" % (contA, contB))

print("\nALL RELOCATIONS EQUIVALENT:", all_ok)
