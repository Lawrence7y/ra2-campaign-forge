# -*- coding: utf-8 -*-
"""逐 entry 全字节反汇编导出。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

HERE = os.path.dirname(os.path.abspath(__file__))
CANDS = json.load(open(os.path.join(HERE, "candidates.json"), encoding="utf-8"))

for c in CANDS:
    e = int(c["entry"], 16); size = int(c["size"])
    lines = []
    lines.append("### %s  %s  %s  size=%d" % (hx(e), c["subsystem"], c["name"], size))
    data = va_read(e, size)
    for ins in np_core._md.disasm(data, e):
        b = va_read(ins.address, ins.size).hex(" ").ljust(24)
        lines.append("  %s  %-24s %-8s %s" % (hx(ins.address), b, ins.mnemonic, ins.op_str))
        if ins.id == X86_INS_RET:
            # keep going (padding / other paths)
            pass
    txt = "\n".join(lines)
    open(os.path.join(HERE, "dis_%s.txt" % c["entry"]), "w", encoding="utf-8").write(txt)
    print(txt)
    print()
