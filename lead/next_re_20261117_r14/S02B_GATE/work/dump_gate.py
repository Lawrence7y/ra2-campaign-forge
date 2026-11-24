#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump full disassembly of the gate functions, no truncation. skipdata=True."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import peutil as P

# Function windows (start, max_bytes to decode). We scan generously and mark rets.
TARGETS = [
    ("47C620", 0x47C620, 0x4A0),   # gate main -> last ret 0x47CA79
    ("47C3D0", 0x47C3D0, 0x120),   # selector (head-A gate), contains 0x47C427 bit0 test
    ("47C4D0", 0x47C4D0, 0x100),   # 0x24 terrain check helper called with 0x24
    ("47C4A7", 0x47C4A7, 0x40),    # bit0 filter branch target
]

outdir = os.path.join(os.path.dirname(__file__), '..', 'EVIDENCE')
os.makedirs(outdir, exist_ok=True)

for name, va, n in TARGETS:
    lines = []
    lines.append("=== %s : %08X + %X bytes ===" % (name, va, n))
    lines.append("source: peutil.disasm (capstone 5.0.7 skipdata=True)")
    cnt = 0
    rets = []
    for insn in P.disasm(va, n):
        line = "%08X  %-26s  %s" % (insn.address, P.fmt_bytes(insn), P.fmt(insn).split(None, 2)[-1] if False else (insn.mnemonic + ' ' + insn.op_str))
        # simpler canonical line:
        line = "%08X  %-23s  %s %s" % (insn.address, P.fmt_bytes(insn), insn.mnemonic, insn.op_str)
        lines.append(line)
        cnt += 1
        if insn.mnemonic.startswith('ret'):
            rets.append((insn.address, insn.mnemonic, insn.op_str))
            # Do not stop; continue to show full window (no truncation)
    lines.append("--- ret list ---")
    for r in rets:
        lines.append("RET %08X %s %s" % r)
    lines.append("total_insns=%d" % cnt)
    out = os.path.join(outdir, "fresh_%s.txt" % name)
    with open(out, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", out, "insns=", cnt, "rets=", len(rets))
