# -*- coding: utf-8 -*-
"""核验每行 vtable 安装点：上下文指令、所在函数、是否 atexit 析构器、是否调 delete。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone import *
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
R4 = json.load(open(os.path.join(WORK, "ring4.json"), encoding="utf-8"))
AN = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
out = open(os.path.join(WORK, "install_ctx.txt"), "w", encoding="utf-8")
def P(*a): print(*a, file=out)

for entry, v in R4.items():
    P("=" * 96)
    P("ROW %s  vt=%s  slot_off=%s  entry_body=[%s,%s)" % (
        entry, v.get("vtable"), v.get("slot_off"), entry,
        R.hx(int(entry, 16) + (AN[entry]["ring1"].get("atlas_size") or 0))))
    for i in v.get("installs", []):
        va = int(i["va"], 16)
        P("  install %s mem=%s in_func=%s atexit=%s" % (i["va"], i["mem"], i["in_func"], i["atexit"]))
        ctx = R.disasm(va - 24, R.read_va(va - 24, 56))
        for ins in ctx:
            mark = " <<<" if ins.address == va else ""
            P("     %08X: %-8s %s%s" % (ins.address, ins.mnemonic, ins.op_str, mark))
        if i["in_func"]:
            fs = int(i["in_func"], 16)
            fsize = R.ATLAS.get(i["in_func"], {}).get("size")
            body = R.disasm(fs, R.read_va(fs, fsize or 256))
            calls = set()
            for ins in body:
                if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_IMM:
                    calls.add(ins.operands[0].imm & 0xFFFFFFFF)
            P("     func %s size=%s n_call=%d calls=%s" % (
                i["in_func"], fsize, len(calls), ", ".join("%08X" % c for c in sorted(calls)[:12])))
            P("     uses_0x7C978A(atexit)=%s  uses_0x7C8B3D(delete)=%s" % (
                0x7C978A in calls, 0x7C8B3D in calls))
out.close()
print("ok")
