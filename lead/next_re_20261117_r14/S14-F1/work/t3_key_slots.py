#!/usr/bin/env python3
"""Find pointer-table slots for INI key strings and code xrefs to those slots.

Channel A: raw PE dword scan + capstone skipdata linear decode; no atlas.
"""
from __future__ import annotations
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import wbase
import capstone

OUT = Path(__file__).resolve().parents[1] / "EVIDENCE"
KEYS = {
    0x83B770: "AITriggerTrackRecordCoefficient",
    0x83B790: "AITriggerFailureWeightDelta",
    0x83B7AC: "AITriggerSuccessWeightDelta",
    0x83BE2C: "BuildSpeed",
    0x83E0A4: "IgnoreGlobalAITriggers",
    0x8180F8: "AITriggerTypes",
    0x8180E0: "AITriggerTypesEnable",
}

p = wbase.pe()
data = p.__data__

# all code instructions once, with detail
code_va, _raw, code_size, _ = wbase.code_bytes()
insns = list(wbase.disasm_linear(code_va, code_va + code_size))

def xrefs_to(slot_va: int):
    out = []
    for ins in insns:
        if ins.id == 0 or (ins.mnemonic or "").startswith("."):
            continue
        try:
            ops = list(ins.operands)
        except Exception:
            continue
        for op in ops:
            if op.type == capstone.x86.X86_OP_IMM and (op.imm & 0xffffffff) == slot_va:
                out.append(wbase.insn_text(ins)); break
            if op.type == capstone.x86.X86_OP_MEM and (op.mem.disp & 0xffffffff) == slot_va:
                out.append(wbase.insn_text(ins)); break
    return out

lines = []
for key_va, name in KEYS.items():
    pat = struct.pack("<I", key_va)
    slots = []
    for i in range(len(data) - 3):
        if data[i:i+4] == pat:
            try:
                sva = wbase.off_to_va(i)
            except ValueError:
                continue
            xr = xrefs_to(sva)
            slots.append((sva, xr))
    lines.append(f"\n=== {name} key_va={key_va:#x} data_ptr_slots={len(slots)} ===")
    for sva, xr in slots:
        lines.append(f"SLOT {sva:#x} CODE_XREFS={len(xr)}")
        for t in xr[:30]:
            lines.append("  " + t)

(OUT / "E12_ai_key_slots.txt").write_text("\n".join(lines)+"\n", encoding="utf-8")
print("wrote", OUT / "E12_ai_key_slots.txt")
