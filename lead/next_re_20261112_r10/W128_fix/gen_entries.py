#!/usr/bin/env python3
"""W128a: compute the minimal whole-instruction relocation length at each of the 6
guard entries, and the exact entry-patch bytes.

Why: an inline hook at a function entry must overwrite >=5 bytes (E9 rel32) and
must cut on an instruction boundary. The relocated bytes are executed verbatim in
the stub before jumping back, so ESP/ECX/registers stay consistent.

Output is consumed by the DLL source and by the verifier.
"""
import json

import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W128_fix\entries.json"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

# function, stack-arg bytes to pop (0 -> plain ret), returns_bool, decompiler sig
FNS = [
    (0x007241A0, 4,  False, "void __thiscall (char)"),
    (0x00724520, 4,  False, "void __thiscall (u32)"),
    (0x00724530, 0,  False, "void __fastcall ()"),
    (0x00724540, 0,  False, "void __fastcall ()"),
    (0x00724580, 4,  True,  "u32 __thiscall (ptr) -> al"),
    (0x00724730, 4,  False, "void __thiscall (int)"),
]

result = []
for va, pop, ret_bool, sig in FNS:
    blob = img[va - ib: va - ib + 32]
    need = 5
    taken = 0
    insns = []
    boundary_ok = False
    for ins in md.disasm(blob, va):
        insns.append({
            "addr": "0x%08X" % ins.address,
            "bytes": ins.bytes.hex(),
            "text": ("%s %s" % (ins.mnemonic, ins.op_str)).strip(),
        })
        taken += ins.size
        if taken >= need:
            boundary_ok = True
            break
    orig = img[va - ib: va - ib + taken].hex()
    entry = {
        "fn": "0x%08X" % va,
        "sig": sig,
        "pop_bytes": pop,
        "returns_al": ret_bool,
        "relocate_len": taken,
        "relocate_bytes": orig,
        "resume_at": "0x%08X" % (va + taken),
        "instructions": insns,
        "boundary_ok": boundary_ok,
    }
    result.append(entry)
    print("\n=== 0x%08X  %s" % (va, sig))
    print("  relocate %d bytes: %s" % (taken, orig))
    for i in insns:
        print("     %s  %-20s %s" % (i["addr"], i["bytes"], i["text"]))
    print("  resume at 0x%08X   (boundary ok: %s)" % (va + taken, boundary_ok))
    # sanity: the resume address must be an instruction start in a linear sweep
    print("  bytes at resume: %s" % img[va + taken - ib: va + taken - ib + 6].hex(" "))

print("\nall boundaries ok:", all(e["boundary_ok"] for e in result))
print("min relocate len:", min(e["relocate_len"] for e in result),
      "max:", max(e["relocate_len"] for e in result))

import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"imagebase": ib, "entries": result}, open(OUT, "w"), indent=2)
print("\nwrote", OUT)
