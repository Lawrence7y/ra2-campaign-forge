#!/usr/bin/env python3
"""Enumerate AI-related INI key pushes in RulesClass loader and their field offsets."""
from __future__ import annotations
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import wbase
import capstone

OUT = Path(__file__).resolve().parents[1] / "EVIDENCE"
TERMS = [
    "ai", "aitrigger", "buildspeed", "team", "basedef", "superdef",
    "harvester", "refinery", "credit", "cash", "turbine", "probability",
    "coefficient", "ratio", "multiplier", "speed", "amount", "threshold",
    "kills", "weight", "delay", "limit", "priority",
]
p = wbase.pe()
data = p.__data__

strings = {}
for m in re.finditer(rb"[A-Za-z][A-Za-z0-9]{3,}", data):
    s = m.group().decode("ascii", "replace")
    low = s.lower()
    if not any(t in low for t in TERMS):
        continue
    try:
        va = wbase.off_to_va(m.start())
    except ValueError:
        continue
    strings[va] = s

lines = [f"candidate_strings={len(strings)}"]
# Single raw pass: `68 imm32` candidates, decoded with capstone. False positives
# are harmless here because the immediate must equal one of our key-string VAs.
code_va, _raw, code_size, code_data = wbase.code_bytes()
by_key = {}
d = wbase.decoder()
for i in range(code_size - 4):
    if code_data[i] != 0x68:
        continue
    imm = int.from_bytes(code_data[i+1:i+5], "little")
    if imm not in strings:
        continue
    site = code_va + i
    insns = list(d.disasm(code_data[i:i+5], site, count=1))
    if not insns or insns[0].id != capstone.x86.X86_INS_PUSH:
        continue
    by_key.setdefault(imm, []).append((site, wbase.insn_text(insns[0])))

for va, s in sorted(strings.items()):
    sites = by_key.get(va, [])
    if not sites:
        continue
    lines.append(f"\n=== KEY {s} VA={va:#x} PUSH_SITES={len(sites)} ===")
    for site, push_text in sites:
        lines.append(f"PUSH@{site:#x}: {push_text}")
        insns = list(wbase.disasm_linear(site + 5, site + 5 + 160))
        store = []
        for ins in insns:
            t = wbase.insn_text(ins)
            lines.append("   " + t)
            m = re.search(r"(?:fstp\s+qword|mov\s+dword|mov\s+byte)\s+ptr \[(?:esi|ebp) \+ (0x[0-9a-f]+)\]", t)
            if m:
                store.append(m.group(1))
            if ins.mnemonic in ("ret",) and ins.address > site + 5:
                break
        lines.append("   STORE_OFFS=" + (",".join(store) if store else "(none in 12)"))

(OUT / "E13_rules_ai_key_stores.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", OUT / "E13_rules_ai_key_stores.txt", "keys_with_xrefs", sum(1 for v in strings.values() if v))
